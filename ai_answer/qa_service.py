
"""
论文问答服务
整合所有组件,提供完整的论文问答功能
"""
from typing import List, Dict, Optional
from parser import MinerUParser
from chunker import TextChunker
from embedder import BGEEmbedder
from vector_store import ChromaVectorStore
from bm25_retriever import BM25Retriever
from reranker import BGEReranker
from hybrid_retriever import HybridRetriever
import os


class PaperQAService:
    """
    论文问答服务
    
    提供论文上传、解析、索引和问答的完整流程
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化论文问答服务
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 初始化各组件
        self._init_components()
    
    def _init_components(self):
        """初始化所有组件"""
        # 1. 文档解析器
        self.parser = MinerUParser(
            output_dir=self.config.get("parsed_docs_dir", "./parsed_docs")
        )
        
        # 2. 文本分块器
        self.chunker = TextChunker(
            chunk_size=self.config.get("chunk_size", 800),
            chunk_overlap=self.config.get("chunk_overlap", 150)
        )
        
        # 3. 向量化器
        self.embedder = BGEEmbedder(
            api_key=self.config.get("embedder_api_key"),
            api_url=self.config.get("embedder_api_url"),
            use_local=self.config.get("use_local_embedder", False)
        )
        
        # 4. 向量存储
        self.vector_store = ChromaVectorStore(
            collection_name=self.config.get("collection_name", "papers"),
            persist_directory=self.config.get("chroma_db_dir", "./chroma_db")
        )
        
        # 5. BM25检索器
        self.bm25_retriever = BM25Retriever()
        
        # 6. 重排序器
        self.reranker = BGEReranker(
            api_key=self.config.get("reranker_api_key"),
            api_url=self.config.get("reranker_api_url"),
            use_local=self.config.get("use_local_reranker", False)
        )
        
        # 7. 混合检索器
        self.hybrid_retriever = HybridRetriever(
            vector_store=self.vector_store,
            bm25_retriever=self.bm25_retriever,
            embedder=self.embedder,
            reranker=self.reranker
        )

        # 8. LLM配置
        self.llm_api_key = self.config.get("llm_api_key", os.getenv("QWEN_API_KEY", ""))
        self.llm_api_url = self.config.get("llm_api_url",
                                           "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        self.llm_model = self.config.get("llm_model", "qwen-plus")
    
    def ingest_paper(self, file_path: str, paper_id: str = None) -> Dict:
        """
        导入论文
        
        Args:
            file_path: PDF文件路径
            paper_id: 论文ID,可选
            
        Returns:
            导入结果
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 1. 解析文档
        print(f"正在解析文档: {file_path}")
        parsed_result = self.parser.parse(file_path)
        text_content = parsed_result['text']
        metadata = parsed_result['metadata']
        
        # 2. 文本分块
        print("正在进行文本分块...")
        chunks_with_metadata = self.chunker.split_with_metadata(
            text_content, 
            metadata=metadata
        )
        
        # 3. 向量化
        print("正在进行向量化...")
        texts = [chunk['text'] for chunk in chunks_with_metadata]
        chunk_metadatas = [chunk['metadata'] for chunk in chunks_with_metadata]
        
        embeddings = self.embedder.embed(texts)
        
        # 4. 存储到向量库
        print("正在存储到向量库...")
        if paper_id:
            ids = [f"{paper_id}_{i}" for i in range(len(texts))]
        else:
            ids = None
        
        self.vector_store.add_documents(
            texts=texts,
            embeddings=embeddings,
            metadatas=chunk_metadatas,
            ids=ids
        )
        
        # 5. 更新BM25索引
        print("正在更新BM25索引...")
        self.bm25_retriever.build_index(texts, ids)
        
        return {
            "status": "success",
            "paper_id": paper_id or "auto_generated",
            "chunks_count": len(texts),
            "metadata": metadata
        }

    def ask(self, query: str, top_k: int = 5, use_llm: bool = True) -> Dict:
        """
        问答查询

        Args:
            query: 问题文本
            top_k: 返回相关片段数量
            use_llm: 是否使用LLM生成答案

        Returns:
            问答结果
        """
        # 1. 混合检索相关片段
        print(f"正在检索相关问题: {query}")
        relevant_chunks = self.hybrid_retriever.retrieve(query, top_k=top_k)

        # 2. 构建上下文
        context = self._build_context(relevant_chunks)

        # 3. 使用LLM生成答案
        answer = ""
        if use_llm and relevant_chunks:
            print("正在调用LLM生成答案...")
            answer = self._generate_answer(query, context)

        return {
            "query": query,
            "answer": answer,
            "relevant_chunks": relevant_chunks,
            "context": context
        }

    def _generate_answer(self, query: str, context: str) -> str:
        """
        调用LLM生成答案

        Args:
            query: 用户问题
            context: 检索到的相关上下文

        Returns:
            LLM生成的答案
        """
        import httpx

        # 构建提示词
        prompt = self._build_prompt(query, context)

        # 构建请求
        payload = {
            "model": self.llm_model,
            "messages": [
                {"role": "system",
                 "content": "你是一个专业的学术论文助手,基于提供的论文片段回答问题。如果片段中没有相关信息,请明确说明。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        headers = {
            "Authorization": f"Bearer {self.llm_api_key}",
            "Content-Type": "application/json"
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    self.llm_api_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()

                # 提取答案
                answer = result["choices"][0]["message"]["content"]
                return answer

        except Exception as e:
            return f"调用LLM失败: {str(e)}"

    def _build_prompt(self, query: str, context: str) -> str:
        """
        构建提示词

        Args:
            query: 用户问题
            context: 检索到的上下文

        Returns:
            完整的提示词
        """
        prompt = f"""请基于以下论文片段回答问题。

    问题: {query}

    相关论文片段:
    {context}

    请根据上述片段提供准确、简洁的回答。如果片段中没有包含问题的答案,请说明"根据提供的片段,无法回答此问题"。

    回答:"""

        return prompt
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """
        构建上下文文本
        
        Args:
            chunks: 相关片段列表
            
        Returns:
            上下文文本
        """
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[片段{i}]:\n{chunk['text']}")
        
        return "\n\n".join(context_parts)

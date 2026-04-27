
"""
重排序模块
使用bge-reranker-v2-m3对检索结果进行重排序
"""
from typing import List, Dict


class BGEReranker:
    """
    BGE重排序器
    
    使用bge-reranker-v2-m3模型对检索结果进行精排
    """
    
    def __init__(self, api_key: str = None, api_url: str = None, use_local: bool = False):
        """
        初始化重排序器
        
        Args:
            api_key: API密钥
            api_url: API地址
            use_local: 是否使用本地模型
        """
        self.api_key = api_key
        self.api_url = api_url or "https://api.example.com/v1/rerank"
        self.use_local = use_local
        
        if use_local:
            self._init_local_model()
    
    def _init_local_model(self):
        """初始化本地重排序模型"""
        try:
            from FlagEmbedding import FlagReranker
            self.reranker = FlagReranker(
                'BAAI/bge-reranker-v2-m3',
                use_fp16=True
            )
        except ImportError:
            raise ImportError("请安装FlagEmbedding: pip install FlagEmbedding")
    
    def rerank(self, query: str, documents: List[Dict], top_k: int = 3) -> List[Dict]:
        """
        对检索结果进行重排序
        
        Args:
            query: 查询文本
            documents: 待重排序的文档列表
            top_k: 返回结果数量
            
        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []
        
        # 提取文档文本
        texts = [doc['text'] for doc in documents]
        
        # 计算相关性得分
        if self.use_local:
            scores = self._rerank_local(query, texts)
        else:
            scores = self._rerank_api(query, texts)
        
        # 将得分添加到文档中
        for i, doc in enumerate(documents):
            doc['rerank_score'] = float(scores[i])
        
        # 按得分排序
        ranked_docs = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
        
        # 返回top_k
        return ranked_docs[:top_k]
    
    def _rerank_local(self, query: str, texts: List[str]) -> List[float]:
        """使用本地模型进行重排序"""
        pairs = [[query, text] for text in texts]
        scores = self.reranker.compute_score(pairs, normalize=True)
        
        # 如果只有一个文档,返回单个分数
        if len(pairs) == 1:
            return [scores]
        
        return scores
    
    def _rerank_api(self, query: str, texts: List[str]) -> List[float]:
        """
        使用API进行重排序
        
        这里以通用API格式为例
        """
        import httpx
        
        payload = {
            "model": "bge-reranker-v2-m3",
            "query": query,
            "documents": texts
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                self.api_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            # 提取得分
            scores = [item['score'] for item in result['results']]
            return scores


"""
混合检索引擎
结合BM25和向量检索,并使用Reranker进行重排序
"""
from typing import List, Dict
from vector_store import ChromaVectorStore
from bm25_retriever import BM25Retriever
from reranker import BGEReranker
from embedder import BGEEmbedder


class HybridRetriever:
    """
    混合检索引擎
    
    结合关键词检索(BM25)和向量检索(Vector),
    使用Reranker进行重排序
    """
    
    def __init__(self, vector_store: ChromaVectorStore, bm25_retriever: BM25Retriever,
                 embedder: BGEEmbedder, reranker: BGEReranker):
        """
        初始化混合检索引擎
        
        Args:
            vector_store: 向量存储
            bm25_retriever: BM25检索器
            embedder: 向量化器
            reranker: 重排序器
        """
        self.vector_store = vector_store
        self.bm25_retriever = bm25_retriever
        self.embedder = embedder
        self.reranker = reranker
    
    def retrieve(self, query: str, top_k: int = 5, 
                bm25_weight: float = 0.3, vector_weight: float = 0.7) -> List[Dict]:
        """
        执行混合检索
        
        Args:
            query: 查询文本
            top_k: 最终返回结果数量
            bm25_weight: BM25权重
            vector_weight: 向量检索权重
            
        Returns:
            检索结果列表
        """
        # 1. BM25检索
        bm25_results = self.bm25_retriever.search(query, top_k=top_k * 2)
        
        # 2. 向量检索
        query_embedding = self.embedder.embed_query(query)
        vector_results = self.vector_store.search(query_embedding, top_k=top_k * 2)
        
        # 3. 合并结果(去重)
        merged_results = self._merge_results(bm25_results, vector_results, 
                                             bm25_weight, vector_weight)
        
        # 4. 重排序
        ranked_results = self.reranker.rerank(query, merged_results, top_k=top_k)
        
        return ranked_results
    
    def _merge_results(self, bm25_results: List[Dict], vector_results: List[Dict],
                      bm25_weight: float, vector_weight: float) -> List[Dict]:
        """
        合并BM25和向量检索结果
        
        使用加权融合策略
        """
        # 使用字典存储合并结果,key为文档ID
        merged = {}
        
        # 归一化BM25得分
        if bm25_results:
            max_bm25_score = max(r['score'] for r in bm25_results)
            if max_bm25_score > 0:
                for result in bm25_results:
                    normalized_score = result['score'] / max_bm25_score
                    doc_id = result['id']
                    merged[doc_id] = {
                        'id': doc_id,
                        'text': result['text'],
                        'metadata': result.get('metadata', {}),
                        'combined_score': normalized_score * bm25_weight
                    }
        
        # 归一化向量检索得分(距离越小越相似,需要转换)
        if vector_results:
            distances = [r.get('distance', 1.0) for r in vector_results]
            max_distance = max(distances) if distances else 1.0
            
            for result in vector_results:
                # 将距离转换为相似度得分
                distance = result.get('distance', 1.0)
                similarity_score = 1.0 - (distance / max_distance if max_distance > 0 else 0)
                
                doc_id = result['id']
                if doc_id in merged:
                    # 已存在,累加得分
                    merged[doc_id]['combined_score'] += similarity_score * vector_weight
                else:
                    merged[doc_id] = {
                        'id': doc_id,
                        'text': result['text'],
                        'metadata': result.get('metadata', {}),
                        'combined_score': similarity_score * vector_weight
                    }
        
        # 按综合得分排序
        sorted_results = sorted(merged.values(), key=lambda x: x['combined_score'], reverse=True)
        
        return sorted_results

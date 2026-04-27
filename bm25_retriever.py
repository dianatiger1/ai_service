
"""
BM25关键词检索模块
"""
from typing import List, Dict
from rank_bm25 import BM25Okapi
import jieba


class BM25Retriever:
    """
    BM25关键词检索器
    
    使用jieba进行中文分词,结合BM25算法进行关键词检索
    """
    
    def __init__(self):
        """初始化BM25检索器"""
        self.bm25 = None
        self.documents = []
        self.doc_ids = []
    
    def build_index(self, documents: List[str], doc_ids: List[str] = None):
        """
        构建BM25索引
        
        Args:
            documents: 文档列表
            doc_ids: 文档ID列表
        """
        self.documents = documents
        self.doc_ids = doc_ids or [str(i) for i in range(len(documents))]
        
        # 使用jieba进行中文分词
        tokenized_docs = [self._tokenize(doc) for doc in documents]
        
        # 创建BM25索引
        self.bm25 = BM25Okapi(tokenized_docs)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        if self.bm25 is None:
            raise ValueError("请先调用build_index构建索引")
        
        # 对查询进行分词
        tokenized_query = self._tokenize(query)
        
        # 获取BM25得分
        scores = self.bm25.get_scores(tokenized_query)
        
        # 按得分排序,获取top_k
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # 只返回有得分的结果
                results.append({
                    'id': self.doc_ids[idx],
                    'text': self.documents[idx],
                    'score': float(scores[idx])
                })
        
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """
        使用jieba进行中文分词
        
        Args:
            text: 待分词文本
            
        Returns:
            分词结果列表
        """
        return list(jieba.cut(text))

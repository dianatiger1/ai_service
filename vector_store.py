
"""
向量存储模块
使用ChromaDB存储和检索向量
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import uuid


class ChromaVectorStore:
    """
    ChromaDB向量存储
    
    支持向量的存储、检索和管理
    """
    
    def __init__(self, collection_name: str = "papers", persist_directory: str = "./chroma_db"):
        """
        初始化ChromaDB向量存储
        
        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # 创建ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
        )
    
    def add_documents(self, texts: List[str], embeddings: List[List[float]], 
                     metadatas: List[Dict] = None, ids: List[str] = None):
        """
        添加文档到向量库
        
        Args:
            texts: 文本列表
            embeddings: 向量列表
            metadatas: 元数据列表
            ids: ID列表,如果不提供则自动生成
        """
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        if metadatas is None:
            metadatas = [{} for _ in range(len(texts))]
        
        self.collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def search(self, query_embedding: List[float], top_k: int = 5, 
              where: Dict = None) -> Dict:
        """
        向量检索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            where: 过滤条件
            
        Returns:
            检索结果
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )
        
        return self._format_results(results)
    
    def delete(self, ids: List[str]):
        """
        删除文档
        
        Args:
            ids: 要删除的文档ID列表
        """
        self.collection.delete(ids=ids)
    
    def count(self) -> int:
        """获取文档总数"""
        return self.collection.count()
    
    def clear(self):
        """清空集合"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
    
    def _format_results(self, results: Dict) -> List[Dict]:
        """格式化检索结果"""
        formatted = []
        
        if not results['ids'][0]:
            return formatted
        
        for i in range(len(results['ids'][0])):
            formatted.append({
                'id': results['ids'][0][i],
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted

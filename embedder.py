
"""
向量化模块
使用BGE-M3模型进行文本向量化
"""
from typing import List
import numpy as np


class BGEEmbedder:
    """
    BGE-M3向量化器
    
    支持通过API调用或本地模型加载
    """
    
    def __init__(self, api_key: str = None, api_url: str = None, use_local: bool = False):
        """
        初始化向量化器
        
        Args:
            api_key: API密钥(如果使用API方式)
            api_url: API地址(如果使用API方式)
            use_local: 是否使用本地模型
        """
        self.api_key = api_key
        self.api_url = api_url or "https://api.example.com/v1/embeddings"
        self.use_local = use_local
        
        if use_local:
            self._init_local_model()
    
    def _init_local_model(self):
        """初始化本地BGE-M3模型"""
        try:
            from FlagEmbedding import BGEM3FlagModel
            self.model = BGEM3FlagModel(
                'BAAI/bge-m3',
                use_fp16=True
            )
        except ImportError:
            raise ImportError("请安装FlagEmbedding: pip install FlagEmbedding")
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        将文本转换为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        if self.use_local:
            return self._embed_local(texts)
        else:
            return self._embed_api(texts)
    
    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """使用本地模型进行向量化"""
        embeddings = self.model.encode(texts, batch_size=16)['dense_vecs']
        return embeddings.tolist()
    
    def _embed_api(self, texts: List[str]) -> List[List[float]]:
        """
        使用API进行向量化
        
        这里以通用API格式为例,实际使用时需要根据具体API调整
        """
        import httpx
        
        embeddings = []
        
        # 批量处理,避免单次请求过大
        batch_size = 50
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            payload = {
                "model": "bge-m3",
                "input": batch
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
                
                # 提取向量
                for item in result["data"]:
                    embeddings.append(item["embedding"])
        
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        将单个查询文本转换为向量
        
        Args:
            query: 查询文本
            
        Returns:
            向量
        """
        result = self.embed([query])
        return result[0]

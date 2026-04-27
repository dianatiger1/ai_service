
"""
文本分块模块
使用RecursiveCharacterTextSplitter进行智能文本分割
"""
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter


class TextChunker:
    """
    文本分块器
    
    使用递归字符分割策略,保持语义完整性
    """
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        """
        初始化文本分块器
        
        Args:
            chunk_size: 每个文本块的大小(字符数)
            chunk_overlap: 文本块之间的重叠大小(字符数)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 创建递归字符分割器
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )
    
    def split(self, text: str) -> List[str]:
        """
        将文本分割成多个块
        
        Args:
            text: 待分割的文本
            
        Returns:
            文本块列表
        """
        chunks = self.splitter.split_text(text)
        return chunks
    
    def split_with_metadata(self, text: str, metadata: dict = None) -> List[dict]:
        """
        将文本分割成多个块,并附加元数据
        
        Args:
            text: 待分割的文本
            metadata: 元数据字典
            
        Returns:
            包含文本块和元数据的字典列表
        """
        chunks = self.splitter.split_text(text)
        
        result = []
        for idx, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk)
            })
            
            result.append({
                "text": chunk,
                "metadata": chunk_metadata
            })
        
        return result

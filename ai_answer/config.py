"""
论文问答系统配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 配置字典
PAPER_QA_CONFIG = {
    # 文本分块配置
    "chunk_size": 800,
    "chunk_overlap": 150,

    # 向量化器配置(API方式)
    "embedder_api_key": os.getenv("BGE_API_KEY", ""),
    "embedder_api_url": os.getenv("BGE_API_URL", "https://api.example.com/v1/embeddings"),
    "use_local_embedder": False,

    # 重排序器配置(API方式)
    "reranker_api_key": os.getenv("RERANKER_API_KEY", ""),
    "reranker_api_url": os.getenv("RERANKER_API_URL", "https://api.example.com/v1/rerank"),
    "use_local_reranker": False,

    # LLM配置(用于生成答案)
    "llm_api_key": os.getenv("QWEN_API_KEY", "sk-abda31cb2b35418b8e66c214551548b8"),
    "llm_api_url": os.getenv("LLM_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"),
    "llm_model": os.getenv("LLM_MODEL", "qwen-plus"),

    # 存储配置
    "chroma_db_dir": "./chroma_db",
    "parsed_docs_dir": "./parsed_docs",
    "collection_name": "papers"
}
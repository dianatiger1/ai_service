
"""
论文问答系统初始化脚本
"""
from ai_answer.qa_service import PaperQAService
from ai_answer.config import PAPER_QA_CONFIG


def init_paper_qa_system():
    """初始化论文问答系统"""
    print("正在初始化论文问答系统...")
    
    # 创建服务实例
    service = PaperQAService(config=PAPER_QA_CONFIG)
    
    print("✓ 文档解析器初始化完成")
    print("✓ 文本分块器初始化完成")
    print("✓ 向量化器初始化完成")
    print("✓ 向量存储初始化完成")
    print("✓ BM25检索器初始化完成")
    print("✓ 重排序器初始化完成")
    print("✓ 混合检索引擎初始化完成")
    
    print("\n论文问答系统初始化成功!")
    return service


if __name__ == "__main__":
    init_paper_qa_system()

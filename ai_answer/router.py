
"""
论文问答API接口
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from ai_answer.qa_service import PaperQAService
import os
import uuid


# 创建路由器
router = APIRouter(prefix="/paper-qa", tags=["论文问答"])

# 全局服务实例
qa_service: Optional[PaperQAService] = None


def get_qa_service() -> PaperQAService:
    """获取问答服务实例"""
    global qa_service
    if qa_service is None:
        qa_service = PaperQAService()
    return qa_service


# 请求模型
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    query: str
    relevant_chunks: list
    context: str


@router.post("/ingest")
async def ingest_paper(
    file: UploadFile = File(...),
    paper_id: Optional[str] = None,
    service: PaperQAService = Depends(get_qa_service)
):
    """
    上传并导入论文
    
    Args:
        file: PDF文件
        paper_id: 论文ID(可选)
        
    Returns:
        导入结果
    """
    # 检查文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    # 保存临时文件
    temp_dir = "./temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
    
    try:
        # 读取并保存文件
        content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(content)
        
        # 导入论文
        result = service.ingest_paper(temp_file_path, paper_id)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    service: PaperQAService = Depends(get_qa_service)
):
    """
    提问
    
    Args:
        request: 查询请求
        
    Returns:
        查询结果
    """
    try:
        result = service.ask(request.query, request.top_k)
        return QueryResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/stats")
async def get_stats(service: PaperQAService = Depends(get_qa_service)):
    """
    获取统计信息
    
    Returns:
        统计信息
    """
    return {
        "total_documents": service.vector_store.count()
    }


@router.delete("/clear")
async def clear_database(service: PaperQAService = Depends(get_qa_service)):
    """
    清空数据库
    
    Returns:
        操作结果
    """
    try:
        service.vector_store.clear()
        return {"status": "success", "message": "数据库已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")

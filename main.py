from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Security, Depends ,File, UploadFile, Response
from PIL import Image
import io
from fastapi.security.api_key import APIKeyHeader
import httpx
from fastapi.responses import StreamingResponse
from fastapi import APIRouter
import json
from abc import ABC, abstractmethod
from PIL import Image
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, UserRecord
import os


# 定义 Header 中 API Key 的键名
API_KEY_NAME = "SYJ-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# 模拟数据库中的 Key
DATABASE_KEYS = {"my_app_01": "secret_key_12345","syj": "123"}

async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key in DATABASE_KEYS.values():
        return api_key
    else:
        raise HTTPException(
            status_code=403, detail="无效的 API Key 或 Key 已缺失"
        )

# 初始化 FastAPI 实例
app = FastAPI(title="我的第一个微服务")

@app.get("/data")
async def get_private_data(api_key: str = Depends(get_api_key)):
    return {"message": "鉴权成功，这是受保护的数据"}


@app.get("/")
async def read_root(api_key: str = Depends(get_api_key)):
    """
    这是一个基础的 Hello World 接口
    """
    return {"message": "Hello ", "status": "success"} #返回json格式

@app.get("/item/{item_id}")
async def read_item(item_id: int, q: str = None,api_key: str = Depends(get_api_key)):
    """
    带参数的示例接口
    """
    return {"item_id": item_id, "query": q}

# 定义请求体的数据结构
class CalculationInput(BaseModel):
    a: float
    b: float

@app.post("/multiply")
async def multiply(data: CalculationInput,api_key: str = Depends(get_api_key)):
    # 直接通过属性访问，FastAPI 已自动完成 JSON 解析和类型转换
    result = data.a * data.b

    return {"result": result}


# 策略模式的核心：定义统一的接口，不同的算法可以互换
class ImageProcessingStrategy(ABC):
    # 图片处理策略抽象基类定义
    # 定义统一的图片处理接口，所有具体的图片处理算法
    # 都应继承此类并实现 process 方法

    @abstractmethod  # ← 这是个装饰器，告诉 Python："这是个抽象方法"
    def process(self, image: Image.Image) -> Image.Image:
        pass


class GrayscaleStrategy(ImageProcessingStrategy):
    def process(self, image: Image.Image) -> Image.Image:
        return image.convert("L")

class ResizeStrategy(ImageProcessingStrategy):
    def __init__(self, width: int = 100, height: int = 200):
        #接收参数并保存为对象属性，让对象"记住"配置,不用每次都传参
        self.width = width
        self.height = height

    def process(self, image: Image.Image) -> Image.Image:
        return image.resize((self.width, self.height))

class RotateStrategy(ImageProcessingStrategy):
    def __init__(self, degree: int = 90):
        self.degree = degree

    def process(self, image: Image.Image) -> Image.Image:
        return image.rotate(self.degree)


GRAYSCALE_STRATEGY = GrayscaleStrategy()
ROTATE_STRATEGY = RotateStrategy(90)
RESIZE_STRATEGY = ResizeStrategy(200, 200)


class ImageStrategyFactory:
    """
    图片处理策略工厂

    根据动作类型返回对应的策略实例（单例）
    """

    _strategies = {
        "grayscale": GRAYSCALE_STRATEGY,
        "rotate": ROTATE_STRATEGY,
        "resize": RESIZE_STRATEGY
    }

    @classmethod
    def get_strategy(cls, action: str) -> ImageProcessingStrategy:
        """
        根据动作名称获取对应的策略

        Args:
            action (str): 动作类型（grayscale/rotate/resize）

        Returns:
            ImageProcessingStrategy: 对应的策略实例

        Raises:
            HTTPException: 当动作类型不支持时抛出 400 错误
        """
        strategy = cls._strategies.get(action)
        if not strategy:
            raise HTTPException(status_code=400, detail="不支持的处理类型")
        return strategy


@app.post("/image/process/{action}")
#{action}，URL 中的占位符，表示可变部分，如 grayscale、rotate、resize
async def process_image(
    action: str,
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
):
    # 1. 读取图片
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))

    # 2. 通过工厂获取策略（使用单例，避免重复创建）
    strategy = ImageStrategyFactory.get_strategy(action)

    # 3. 执行策略
    processed_image = strategy.process(image) #方法调用

    # 4. 返回结果
    img_byte_arr = io.BytesIO()
    processed_image.save(img_byte_arr, format="PNG")
    return Response(content=img_byte_arr.getvalue(), media_type="image/png")






# 配置信息（从环境变量读取，避免泄露）
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "sk-your-default-key")
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"


class ChatMessage(BaseModel):
    message: str
    model_type: str = "external"



@app.post("/chat/free")
async def free_chat(data: ChatMessage, api_key: str = Depends(get_api_key)):
    user_msg = data.message

    payload = {
        "model": "qwen-plus",
        "messages": [
            {"role": "system", "content": "你是一个有用的助手"},
            {"role": "user", "content": user_msg}
        ],
        "stream": True
    }

    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }

    async def stream_generator():
        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    QWEN_BASE_URL,
                    json=payload,
                    headers=headers,
                    timeout=60.0
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            if line.startswith("data: "):
                                line = line[6:]
                            if line == "[DONE]":
                                break
                            yield line + "\n"
            except Exception as e:
                error_msg = json.dumps({"error": f"AI 服务调用失败: {str(e)}"})
                yield error_msg

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )



@app.get("/db/user/{user_id}")
async def get_user_from_db(
        user_id: int,
        db: Session = Depends(get_db),
        api_key: str = Depends(get_api_key)
):
    """
    通过 ID 从本地 SQLite 数据库读取用户信息

    Args:
        user_id (int): 待查询的用户唯一标识符
        db (Session): 数据库会话对象，通过依赖注入自动获取
        api_key (str): API 鉴权密钥，通过依赖注入从请求头中提取并验证

    Returns:
        dict: 包含状态码和用户详细信息（ID、姓名、API Key）的字典

    Raises:
        HTTPException: 当数据库中不存在对应 ID 的用户时，抛出 404 错误
    """
    # 逻辑：在 UserRecord 表中查询第一个 ID 匹配的记录，
    # SQLAlchemy ORM（对象关系映射） 的核心查询语句，它的作用是从数据库中查找特定用户
    user = db.query(UserRecord).filter(UserRecord.id == user_id).first()
    #  user = db.query(UserRecord).all()  返回一个包含所有用户对象的列表
    if not user:
        raise HTTPException(status_code=404, detail="数据库中未找到该用户")

    return {
        "status": "success",
        "data": {
            "id": user.id,
            "name": user.name,
            "key": user.api_key_value
        }
    }



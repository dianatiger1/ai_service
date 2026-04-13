from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. 定义数据库文件位置 (在当前目录下创建 test.db)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# 2. 创建数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# 3. 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 定义基类，用于模型继承
Base = declarative_base()


# 5. 定义数据模型 (对应数据库里的一张表)
class UserRecord(Base):
    __tablename__ = "users_info"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    api_key_value = Column(String)


# 6. 初始创建表 (如果表不存在则创建)
Base.metadata.create_all(bind=engine)


# 7. 依赖项：用于在 FastAPI 接口中获取数据库 Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
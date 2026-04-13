import redis
import json
import os

# Redis 连接配置（从环境变量读取）
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))


# 创建 Redis 连接池（单例模式，避免重复创建连接）
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True  # 自动将字节转换为字符串
)

# 获取 Redis 客户端实例
def get_redis_client():
    """获取 Redis 客户端连接"""
    return redis.Redis(connection_pool=redis_pool)

# 测试连接
def test_redis_connection():
    """测试 Redis 连接是否正常"""
    try:
        client = get_redis_client()
        client.ping()
        print("✅ Redis 连接成功！")
        return True
    except redis.ConnectionError as e:
        print(f"❌ Redis 连接失败: {e}")
        return False

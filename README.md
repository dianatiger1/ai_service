# My First Microservice 🚀

这是一个基于 **FastAPI** 构建的高性能微服务项目。它集成了 AI 智能对话、图像处理算法、SQLite 持久化存储以及 Redis 高速缓存，并采用了策略模式、工厂模式和单例模式等设计模式，代码结构清晰且易于扩展。

## 🌟 功能特性

- **🤖 AI 聊天助手**: 集成阿里云通义千问（Qwen）模型，支持实时流式响应。
- **🖼️ 图像处理中心**: 支持图片灰度化、旋转、缩放（采用策略模式 + 工厂模式实现）。
- **💾 数据持久化**: 使用 SQLAlchemy 操作 SQLite 数据库，管理用户信息。
- **⚡ 高速缓存**: 集成 Redis 缓存热点数据，显著提升查询性能。
- **🔐 安全鉴权**: 基于 Header 的 API Key 验证机制，保护接口安全。

## 🛠️ 环境要求

- Python 3.8+
- Redis Server (推荐使用 Docker 运行)
- Git

## ⚙️ 快速开始

### 1. 克隆项目
bash 
git clone https://github.com/你的用户名/first_service.git cd first_service
### 2. 创建虚拟环境并安装依赖
pip install -r requirements.txt
### 3. 配置环境变量
在项目根目录下创建 `.env` 文件，并填入以下配置：
env 
QWEN_API_KEY=sk-your-actual-api-key-here 
REDIS_HOST=localhost 
REDIS_PORT=6379
### 4. 启动 Redis 服务
如果你安装了 Docker，可以直接运行：
docker run -d --name redis-cache -p 6379:6379 redis:latest
### 5. 初始化数据库
运行脚本生成初始用户数据：
python test_init_db.py
### 6. 启动服务
uvicorn main:app --reload
服务启动后，访问 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 查看交互式 API 文档。

## 📂 项目结构
text 
first_service/ 
├── main.py # 核心业务逻辑与 API 路由 
├── database.py # SQLite 数据库配置与模型定义 
├── redis_client.py # Redis 客户端封装（单例模式） 
├── test_init_db.py # 数据库初始化工具 
├── first_request.py # 客户端测试脚本 
├── .env # 环境变量配置（不上传至 Git） 
├── .gitignore # Git 忽略文件配置 
└── README.md # 项目说明文档


# “心青年”智能体平台 (Young Hearts Agent Platform) - Backend

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-green)
![License](https://img.shields.io/badge/License-GPLv3-red)

**“心青年”智能体平台** 是一个基于 **RAG（检索增强生成）** 技术的专业咨询平台，旨在解决孤独症家庭面临的“专业知识获取难”与“个性化建议匮乏”问题。本项目为平台的后端服务。

---

## 📖 项目简介

本平台利用大语言模型（LLM）与向量检索技术，结合专业知识库，提供 7x24 小时、有权威依据的问答服务。同时，平台集成了志愿者管理与专家协同功能，形成一站式服务中心。

## ✨ 核心功能

- [x] **用户鉴权与管理 (RBAC)**: 支持家属、志愿者、专家、管理员等多角色身份认证与权限控制 (Session/Cookie)。
- [x] **RAG 智能咨询引擎**: 
    - [x] 知识库文档上传、解析与切片 (支持多模态预留)。
    - [x] 向量存储与检索 (ChromaDB)。
    - [x] 基于 LangChain 与 Doubao API (Ark API) 的流式问答生成。
    - [x] 会话管理与自动主题生成。
- [x] **知识库管理**:
    - [x] 知识条目 CRUD 与状态流转 (草稿、待审核、已发布)。
    - [x] 异步文档处理与向量化 (Celery + Redis)。
- [x] **统一服务中心**:
    - [x] 志愿者/专家注册与审核流程。

## 🛠 技术栈

| 模块 | 技术选型 | 说明 |
|---|---|---|
| **Web 框架** | `FastAPI` | 高性能异步 Python Web 框架 |
| **语言** | `Python 3.12+` | 核心开发语言 |
| **ORM / 数据库** | `SQLAlchemy` / `MySQL` (或 `SQLite`) | 关系型数据存储 (用户、会话、知识库元数据等) |
| **向量数据库** | `ChromaDB` | 知识库向量索引存储 |
| **LLM 编排** | `LangChain` | RAG 流程编排 |
| **大语言模型** | `Doubao API (Ark API)` | 文本生成与 Embedding 模型 |
| **任务队列** | `Celery` + `Redis` | 异步任务 (文档解析、向量化) |

## 📂 项目结构

```text
Young-Hearts-Agent-Platform-backend/
├── app/
│   ├── api/            # API 路由与端点 (v1)
│   ├── core/           # 核心配置 (Config, Celery App)
│   ├── db/             # 数据库会话与初始化
│   ├── models/         # SQLAlchemy ORM 模型
│   ├── schemas/        # Pydantic 数据验证模型
│   ├── services/       # 业务逻辑层 (Auth, Consult, Knowledge, RAG)
│   ├── tasks/          # Celery 异步任务 (知识库处理)
│   ├── utils/          # 工具函数 (OpenAPI 生成等)
│   └── main.py         # 应用入口
├── data/               # 本地数据存储 (原始文档等)
├── docs/               # 主要功能与设计文档
├── scripts/            # 实用脚本 (如数据初始化、测试脚本)
├── tests/              # 测试用例
├── pyproject.toml      # 项目配置与依赖
└── requirements.txt    # 依赖列表
```

## 🚀 快速开始

### 1. 环境准备 (Prerequisites)

- Python 3.12+
- MySQL (可选，开发环境默认使用 SQLite)
- Redis (必须，用于 Celery 异步任务)
- ChromaDB (本地运行或 Docker 部署)

### 2. 安装依赖 (Installation)

```bash
# 创建并激活虚拟环境 (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 配置环境 (Configuration)

在项目根目录创建 `.env` 文件，配置数据库连接、Redis、ChromaDB 以及 Doubao API 密钥：

```env
DB_URL='sqlite:///./dev.db'

# ChromaDB 配置
CHROMADB_HOST=localhost
CHROMADB_PORT=8001
CHROMA_COLLECTION_NAME=knowledge_base

# AI 对话模型配置
ARK_API_KEY='your_ark_api_key'
ARK_BASE_URL='https://ark.cn-beijing.volces.com/api/v3'
ARK_MODEL='your_model_endpoint'

# 向量模型配置
DOUBAO_EMBEDDING_API_KEY='your_embedding_api_key'
DOUBAO_EMBEDDING_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'
DOUBAO_EMBEDDING_MODEL='your_embedding_model_endpoint'

REDIS_URL='redis://localhost:6379/0'
```

### 4. 初始化数据库

```bash
# 初始化数据库表结构
python scripts/init_db.py
```

### 5. 启动服务 (Usage)

启动 FastAPI 后端服务：

```bash
# 启动开发服务器 (热重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动 Celery Worker (处理知识库解析与向量化等异步任务)：

```bash
# Windows 环境下建议使用 solo pool
celery -A app.core.celery_app worker -l info --pool=solo
```

服务启动后，访问 API 文档：
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -q
```

## 📄 许可证

本项目遵循 [GPLv3 License](LICENSE) 许可证。


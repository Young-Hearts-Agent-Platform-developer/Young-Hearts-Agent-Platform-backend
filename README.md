
# “心青年”智能体平台 (Young Hearts Agent Platform) - Backend

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)
![License](https://img.shields.io/badge/License-GPLv3-red)

**“心青年”智能体平台** 是一个基于 **RAG（检索增强生成）** 技术的专业咨询平台，旨在解决孤独症家庭面临的“专业知识获取难”与“个性化建议匮乏”问题。本项目为平台的后端服务。

---

## 📖 项目简介

本平台利用大语言模型（LLM）与向量检索技术，结合专业知识库，提供 7x24 小时、有权威依据的问答服务。同时，平台集成了志愿者管理与专家协同功能，形成一站式服务中心。

## ✨ 核心功能 (MVP)

- [x] **用户鉴权与管理 (RBAC)**: 支持家属、志愿者、专家、管理员等多角色身份认证与权限控制 (JWT)。
- [ ] **RAG 智能咨询引擎**: 
    - [ ] 知识库文档上传与解析 (PDF/Markdown)。
    - [ ] 向量存储与检索 (ChromaDB/Qdrant)。
    - [ ] 基于 LangChain 的问答生成。
- [ ] **统一服务中心**:
    - [ ] 志愿者/专家注册与审核流程。
    - [ ] 咨询工单管理。

## 🛠 技术栈

| 模块 | 技术选型 | 说明 |
|---|---|---|
| **Web 框架** | `FastAPI` | 高性能异步 Python Web 框架 |
| **语言** | `Python 3.10+` |  |
| **ORM / 数据库** | `SQLAlchemy` / `PostgreSQL` | 关系型数据存储 (用户、工单等) |
| **向量数据库** | `ChromaDB` (或 `Qdrant`) | 知识库向量索引存储 |
| **LLM 编排** | `LangChain` | RAG 流程编排 |
| **任务队列** | `Celery` + `Redis` | 异步任务 (文档处理、邮件发送) |
| **部署** | `Docker` | 容器化部署 |

## 📂 项目结构

```text
Young-Hearts-Agent-Platform-backend/
├── app/
│   ├── api/            # API 路由与端点
│   ├── core/           # 核心配置 (Config, Security)
│   ├── db/             # 数据库会话与模型初始化
│   ├── knowledge/      # 知识库管理逻辑
│   ├── models/         # SQLAlchemy ORM 模型
│   ├── rag/            # RAG 核心逻辑 (Chains, Embeddings)
│   ├── schemas/        # Pydantic 数据验证模型
│   ├── services/       # 业务逻辑层
│   └── main.py         # 应用入口
├── alembic/            # 数据库迁移脚本
├── docs/               # 主要功能与设计文档
├── scripts/            # 实用脚本 (如数据初始化)
├── tests/              # 测试用例
├── .env.example        # 环境变量示例
├── pyproject.toml      # 项目配置
└── requirements.txt    # 依赖列表
```

## 🚀 快速开始

### 1. 环境准备 (Prerequisites)

- Python 3.10+
- PostgreSQL (可选，开发环境可使用 SQLite 或 Docker)
- Redis (可选，用于异步任务)

### 2. 安装依赖 (Installation)

```bash
# 创建并激活虚拟环境 (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 配置环境 (Configuration)

复制环境变量示例文件并根据需要修改：

```powershell
cp .env.example .env
# 编辑 .env 配置数据库连接、密钥等
```

### 4. 初始化数据库

```bash
# 初始化数据库表结构 (开发环境)
python -c "from app.db.session import init_db; init_db()"
```

### 5. 启动服务 (Usage)

```bash
# 启动开发服务器 (热重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动 Celery Worker (处理异步任务)
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


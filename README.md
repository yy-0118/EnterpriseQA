# 企业知识库智能问答系统

基于 **LangChain + RAG + Ollama** 的企业内部知识库智能问答系统。支持知识文档管理、智能检索问答、用户权限管理和数据统计分析。

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | Python Flask |
| **前端框架** | Vue 3 + Element Plus |
| **数据库** | MySQL 8.0 (端口3308) |
| **向量数据库** | Chroma |
| **LLM大模型** | Ollama + qwen3:8b |
| **嵌入模型** | Ollama + qwen3-embedding:4b |
| **RAG框架** | LangChain |
| **图表库** | ECharts 5 |

## 项目结构

```
EnterpriseQA/
├── server/                     # 后端服务
│   ├── app.py                  # Flask应用主入口
│   ├── config.py               # 配置文件（数据库、Ollama、Chroma）
│   ├── models.py               # SQLAlchemy数据模型
│   ├── auth.py                 # 用户认证（登录/注册/JWT）
│   ├── qa.py                   # 智能问答API（RAG检索）
│   ├── kb.py                   # 知识库管理API（文档CRUD）
│   ├── admin.py                # 管理员API（统计/用户管理）
│   ├── rag_engine.py           # RAG检索引擎（LangChain+Chroma）
│   ├── db.sql                  # 数据库建表SQL和测试数据
│   └── requirements.txt        # Python依赖
│
├── client/                     # 前端应用
│   ├── src/
│   │   ├── main.js             # Vue3应用入口
│   │   ├── App.vue             # 根组件
│   │   ├── router/index.js     # 路由配置（含权限守卫）
│   │   ├── api/index.js        # API接口封装（axios）
│   │   ├── views/
│   │   │   ├── Login.vue       # 登录页面
│   │   │   ├── Register.vue    # 注册页面
│   │   │   ├── UserHome.vue    # 用户主页（Q&A聊天界面）
│   │   │   └── AdminHome.vue   # 管理员后台（统计+管理）
│   │   └── assets/style.css    # 全局样式
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## 快速开始

### 1. 环境准备

- **Python** >= 3.10
- **Node.js** >= 18.x
- **MySQL** 8.0 (端口3308)
- **Ollama** (需安装并拉取模型)

### 2. 安装Ollama并拉取模型

```bash
# 安装Ollama (https://ollama.com)
# 拉取对话模型
ollama pull qwen3:8b

# 拉取嵌入模型
ollama pull qwen3-embedding:4b

# 验证模型已安装
ollama list
```

### 3. 初始化数据库

```bash
# 连接MySQL执行
mysql -uroot -p123456 -P3308 < server/db.sql
```

数据库 `db_enterprise_qa` 会被创建，并包含：
- 4个测试用户 (admin/zhangsan/lisi/wangwu，密码均为 123456)
- 8个知识分类
- 6个测试知识文档
- 5条测试问答记录

### 4. 启动后端服务

```bash
cd server

# 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动Flask服务（端口5000）
python app.py
```

### 5. 启动前端服务

```bash
cd client

# 安装依赖
npm install

# 启动开发服务器（端口3000）
npm run dev
```

访问 http://localhost:3000 即可使用。

## 测试账号

| 角色 | 用户名 | 密码 | 说明 |
|------|--------|------|------|
| 管理员 | `admin` | `123456` | 可访问管理后台 |
| 普通用户 | `zhangsan` | `123456` | 可使用知识问答 |
| 普通用户 | `lisi` | `123456` | 可使用知识问答 |
| 普通用户 | `wangwu` | `123456` | 可使用知识问答 |

## 功能说明

### 用户端
- **用户注册/登录**：支持新用户注册，密码MD5加密存储
- **智能问答**：基于RAG技术，从企业知识库中检索并生成回答
- **问答历史**：查看历史问答记录
- **反馈评价**：对回答进行满意/不满意评价
- **参考来源**：每次回答都会标注引用的知识文档

### 管理员端
- **数据概览**：系统核心指标统计（用户数、文档数、问答数、向量块数）
- **统计图表**：近7天趋势折线图、知识分类饼图、月度趋势柱状图、用户活跃度排行
- **用户管理**：查看/编辑/禁用用户，修改角色权限
- **知识库管理**：上传/查看/删除知识文档（自动向量化到Chroma）
- **问答记录**：查看所有用户的问答历史

## API接口

### 认证模块 `/api/auth`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/register` | 用户注册 |
| GET | `/api/auth/userinfo` | 获取用户信息 |

### 智能问答 `/api/qa`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/qa/ask` | RAG智能问答 |
| GET | `/api/qa/history` | 问答历史 |
| POST | `/api/qa/feedback/:id` | 提交反馈 |

### 知识库 `/api/kb`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/kb/documents` | 文档列表 |
| POST | `/api/kb/documents` | 上传文档 |
| GET | `/api/kb/documents/:id` | 文档详情 |
| PUT | `/api/kb/documents/:id` | 更新文档 |
| DELETE | `/api/kb/documents/:id` | 删除文档 |
| GET | `/api/kb/categories` | 分类列表 |
| POST | `/api/kb/categories` | 添加分类 |

### 管理员 `/api/admin`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/dashboard` | 仪表盘数据 |
| GET | `/api/admin/users` | 用户列表 |
| PUT | `/api/admin/users/:id` | 更新用户 |
| DELETE | `/api/admin/users/:id` | 删除用户 |
| GET | `/api/admin/qa/history` | 所有问答记录 |

## 配置说明

主要配置在 `server/config.py`，可通过环境变量覆盖：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `MYSQL_HOST` | 127.0.0.1 | MySQL主机 |
| `MYSQL_PORT` | 3308 | MySQL端口 |
| `MYSQL_USER` | root | MySQL用户 |
| `MYSQL_PASSWORD` | 123456 | MySQL密码 |
| `OLLAMA_BASE_URL` | http://127.0.0.1:11434 | Ollama服务地址 |
| `LLM_MODEL` | qwen3:8b | 对话模型 |
| `EMBEDDING_MODEL` | qwen3-embedding:4b | 嵌入模型 |
| `CHUNK_SIZE` | 500 | 文本块大小 |
| `CHUNK_OVERLAP` | 50 | 文本块重叠大小 |
| `RETRIEVAL_TOP_K` | 4 | 检索返回文档数 |

## RAG工作流程

```
用户提问 → 嵌入向量化 → Chroma相似度检索 → 召回Top-K文档
    → 构建上下文Prompt → Ollama LLM生成回答 → 返回结果+来源
```

## License

MIT License - 仅供学习交流使用

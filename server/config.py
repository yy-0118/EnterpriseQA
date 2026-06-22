"""
企业知识库问答系统 - 配置文件
包含数据库连接、Ollama服务、Chroma向量数据库等配置
"""
import os


class Config:
    """应用配置类"""

    # ==================== Flask基础配置 ====================
    SECRET_KEY = os.environ.get('SECRET_KEY', 'enterprise-qa-secret-key-2024')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    # ==================== 数据库配置 ====================
    # 默认使用 SQLite（无需安装 MySQL，开箱即用）
    # 切换到 MySQL：设置环境变量 USE_MYSQL=true，并提前执行 server/db.sql
    MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3308))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '123456')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'db_enterprise_qa')

    _use_mysql = os.environ.get('USE_MYSQL', '').lower() == 'true'
    if _use_mysql:
        SQLALCHEMY_DATABASE_URI = (
            f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}'
            f'@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
            '?charset=utf8mb4'
        )
    else:
        # 默认 SQLite，文件生成在 server/ 目录下
        # 注意：Windows路径的反斜杠必须转成正斜杠，否则SQLAlchemy URI解析失败
        _db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'enterprise_qa.db')
        _db_path = _db_path.replace('\\', '/')  # Windows 兼容
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{_db_path}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 设为True可查看SQL日志

    # ==================== Ollama LLM配置 ====================
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    LLM_MODEL = os.environ.get('LLM_MODEL', 'qwen3:4b')  # 大语言模型
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'qwen3-embedding:4b')  # 嵌入模型

    # ==================== Chroma向量数据库配置 ====================
    CHROMA_PERSIST_DIR = os.environ.get(
        'CHROMA_PERSIST_DIR',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chroma_db')
    )
    CHROMA_COLLECTION_NAME = os.environ.get('CHROMA_COLLECTION_NAME', 'enterprise_knowledge')

    # ==================== 文档分块配置 ====================
    CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', 500))  # 每个文本块的大小
    CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', 50))  # 文本块之间的重叠大小

    # ==================== RAG检索配置 ====================
    RETRIEVAL_TOP_K = int(os.environ.get('RETRIEVAL_TOP_K', 4))  # 检索返回的相关文档数

    # ==================== JWT Token配置 ====================
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-enterprise-qa-secret')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24小时

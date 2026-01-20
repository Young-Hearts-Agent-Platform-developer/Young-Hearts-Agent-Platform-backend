from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "心青年智能体平台 - Backend"
    DB_URL: str = "sqlite:///./dev.db"
    VECTOR_STORE: str = "chroma"

    # auth settings
    SECRET_KEY: str = "dev-secret-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # session/cookie 策略
    SESSION_COOKIE_NAME: str = "session_id"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SECURE: bool = False
    SESSION_EXPIRE_MINUTES: int = 60 * 24  # 默认 24 小时

    # 火山引擎 (豆包) 配置
    ARK_API_KEY: str 
    ARK_BASE_URL: str
    
    # 聊天模型 ID (用于生成答案)
    ARK_MODEL: str 
    
    # Embedding 模型 ID (用于检索)
    ARK_EMBEDDING_MODEL: str
    
    # 检索阈值
    RAG_SCORE_THRESHOLD: float = 0.6
    # Chroma 路径
    CHROMA_PATH: str = "./chroma_db_data"

    class Config:
        env_file = ".env"
        # 允许 .env 里有额外的变量而不报错
        extra = "ignore"



settings = Settings()

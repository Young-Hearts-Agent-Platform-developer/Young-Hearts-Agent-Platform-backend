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

    # ark api key
    ark_api_key: str | None = None
    ark_base_url: str | None = None
    ark_model: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()

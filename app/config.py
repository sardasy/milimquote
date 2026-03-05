from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/pricing_db"
    EXCHANGE_RATE_API_URL: str = "https://api.exchangerate.host/latest"
    EXCHANGE_RATE_UPDATE_INTERVAL: int = 3600  # 초 단위 (기본 1시간)

    model_config = {"env_file": ".env"}


settings = Settings()

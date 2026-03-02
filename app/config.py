from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Game Item Trading API"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite:///./trading.db"

    # JWT settings
    SECRET_KEY: str = "change-this-to-a-strong-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"


settings = Settings()

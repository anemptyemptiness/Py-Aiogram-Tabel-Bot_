from aiogram.fsm.storage.redis import Redis
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TOKEN: str

    ADMIN_ID: int

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    REDIS_HOST: str

    @property
    def get_url_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = "../.env"


settings = Settings()
redis = Redis(host=settings.REDIS_HOST)

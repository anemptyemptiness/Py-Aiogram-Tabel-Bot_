from dataclasses import dataclass
from aiogram.fsm.storage.redis import Redis
from environs import Env


@dataclass
class TgBot:
    token: str


@dataclass
class Config:
    tg_bot: TgBot
    employees: list
    admin_chats: list
    places: list[str]
    redis: Redis
    user_db: str
    password_db: str
    database: str
    host_db: str
    admins: list


def load_config() -> Config:
    env = Env()
    env.read_env()

    return Config(tg_bot=TgBot(token=env("TOKEN")),
                  employees=[int(f"{env(f'employee_{i}')}") for i in range(1, 12)],
                  admins=[int(f"{env(f'admin_{i}')}") for i in range(1, 4)],
                  admin_chats=[f"{env(f'chat_id_{i}')}" for i in range(1, 6)],
                  places=[f"{env(f'place_{i}')}" for i in range(1, 6)],
                  redis=Redis(host=f"{env('redis_host')}"),
                  user_db=env("user"),
                  password_db=env("password"),
                  database=env("database"),
                  host_db=env("host"))


config: Config = load_config()
place_chat: dict = {config.places[i]: config.admin_chats[i] for i in range(len(config.places))}

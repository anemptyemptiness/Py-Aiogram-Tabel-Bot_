from aiogram.filters import BaseFilter
from aiogram.types import Message
from src.db import cached_admins, cached_employees


class CheckUserFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user_id = int(message.from_user.id)
        return not (user_id in cached_employees or user_id in cached_admins)

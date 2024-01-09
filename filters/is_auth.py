from aiogram.filters import BaseFilter
from aiogram.types import Message

from db import DB


class isUserAuthFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return not DB.user_exists(message.from_user.id)

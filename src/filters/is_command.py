from aiogram.filters import BaseFilter
from aiogram.types import Message


class IsCommandFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.text.startswith("/")
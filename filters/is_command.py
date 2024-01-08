from aiogram.filters import BaseFilter
from aiogram.types import Message


class isCommandFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.text.startswith("/")

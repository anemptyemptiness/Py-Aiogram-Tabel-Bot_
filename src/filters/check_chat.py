from aiogram.filters import BaseFilter
from aiogram.types import Message
from src.db import cached_chat_ids


class CheckChatFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return not int(message.chat.id) not in cached_chat_ids

from aiogram.filters import BaseFilter
from aiogram.types import Message


class CheckChatFilter(BaseFilter):
    def __init__(self, chat_ids: list):
        self.chat_ids = chat_ids

    async def __call__(self, message: Message) -> bool:
        return not str(message.chat.id) not in self.chat_ids

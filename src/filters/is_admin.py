from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from src.db import cached_admins


class IsAdminFilterMessage(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return int(message.from_user.id) in cached_admins


class IsNotAdminFilterCallback(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return not int(callback.message.chat.id) in cached_admins

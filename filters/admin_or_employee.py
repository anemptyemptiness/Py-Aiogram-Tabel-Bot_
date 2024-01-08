from aiogram.filters import BaseFilter
from aiogram.types import Message


class CheckUserFilter(BaseFilter):
    def __init__(self, admins: list, employees: list):
        self.admins = admins
        self.employees = employees

    async def __call__(self, message: Message) -> bool:
        return not (message.from_user.id in self.admins or message.from_user.id in self.employees)

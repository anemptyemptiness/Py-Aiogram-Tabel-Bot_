from aiogram.filters.callback_data import CallbackData


class EmployeeCallbackFactory(CallbackData, prefix="employee"):
    user_id: int
from aiogram.filters.callback_data import CallbackData


class AdminCallbackFactory(CallbackData, prefix="admin"):
    user_id: int
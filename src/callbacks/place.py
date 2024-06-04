from aiogram.filters.callback_data import CallbackData


class PlaceCallbackFactory(CallbackData, prefix="place"):
    title: str
    chat_id: int
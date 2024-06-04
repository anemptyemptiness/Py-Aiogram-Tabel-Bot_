from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

from src.callbacks.place import PlaceCallbackFactory
from src.db import cached_places


def create_yes_no_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="yes"),
             InlineKeyboardButton(text="Нет", callback_data="no")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel")],
        ],
    )


def create_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")],
        ],
        resize_keyboard=True,
    )


def create_places_kb() -> InlineKeyboardMarkup:
    kb = []

    for title, chat_id in cached_places.items():
        kb.append([
            InlineKeyboardButton(text=title, callback_data=PlaceCallbackFactory(
                title=title,
                chat_id=int(chat_id),
                ).pack(),
            )
        ])

    kb.append([InlineKeyboardButton(text="Отмена", callback_data="cancel")])

    return InlineKeyboardMarkup(
        inline_keyboard=kb,
    )


def create_rules_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Согласен", callback_data="agree")],
        ],
    )

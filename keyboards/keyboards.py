from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

from db import DB


async def create_yes_no_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="Да"), KeyboardButton(text="Нет")],
        [KeyboardButton(text="Отмена")]
    ]

    return ReplyKeyboardMarkup(keyboard=kb,
                               resize_keyboard=True)


async def create_cancel_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="Отмена")]
    ]

    return ReplyKeyboardMarkup(keyboard=kb,
                               resize_keyboard=True)


async def create_places_kb() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="Щелковский")],
        [KeyboardButton(text="Белая Дача")],
        [KeyboardButton(text="Ривьера")],
        [KeyboardButton(text="Вегас Кунцево")],
        [KeyboardButton(text="Рига Молл")],
    ]

    return ReplyKeyboardMarkup(keyboard=kb,
                               resize_keyboard=True)


async def create_inline_kb() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(
            text="Согласен",
            callback_data="agree")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=kb)


async def create_names_kb() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text=name[0])] for name in DB.get_names()]

    return ReplyKeyboardMarkup(keyboard=kb,
                               resize_keyboard=True)


async def create_money_or_visitors_kb() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(
            text="Посетители",
            callback_data="visitors",
        )],
        [InlineKeyboardButton(
            text="Финансы",
            callback_data="money",
        )],
        [InlineKeyboardButton(
            text="Выход",
            callback_data="exit",
        )],
    ]

    return InlineKeyboardMarkup(inline_keyboard=kb)


async def create_admin_kb() -> InlineKeyboardMarkup:
    kb = [
        [InlineKeyboardButton(
            text="Статистика за последнюю неделю",
            callback_data="last_week",
        )],
        [InlineKeyboardButton(
            text="Статистика за последний месяц",
            callback_data="last_month",
        )],
        [InlineKeyboardButton(
            text="Статистика за последний год",
            callback_data="last_year",
        )],
        [InlineKeyboardButton(
            text="Задать вручную",
            callback_data="by_hand",
        )],
        [InlineKeyboardButton(
            text="Назад",
            callback_data="back",
        )],
        [InlineKeyboardButton(
            text="Выход",
            callback_data="exit",
        )],
    ]

    return InlineKeyboardMarkup(inline_keyboard=kb)

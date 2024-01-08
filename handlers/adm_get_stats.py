from datetime import datetime, timezone, timedelta
import time

from aiogram.types import Message, CallbackQuery
from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from db import DB
from fsm.fsm import FSMAdmin
from filters.is_admin import isAdminFilter
from config.config import config
from keyboards.keyboards import create_admin_kb, create_money_or_visitors_kb

router_adm = Router()


async def report_visitors_in_range(date_from: str, date_to: str, msg: Message):
    rows = DB.get_statistics_visitors(date_from=date_from, date_to=date_to)
    places = {
        "Белая Дача": sum([row[0].count("Белая Дача") for row in rows]),
        "Ривьера": sum([row[0].count("Ривьера") for row in rows]),
        "Рига Молл": sum([row[0].count("Рига Молл") for row in rows]),
        "Вегас Кунцево": sum([row[0].count("Вегас Кунцево") for row in rows]),
        "Щелковский": sum([row[0].count("Щелковский") for row in rows]),
    }

    report = f"📊Статистика по посетителям точек\n<b>от</b> {date_from} <b>до</b> {date_to}\n\n"
    index_place = 0
    index_rows = 0

    for count in places.values():
        if count:
            report += f"Рабочая точка: <b>{rows[index_place][0]}</b>\n"

            for i in range(count):
                report += f"📝Работник: <em>{rows[index_rows][1]}</em>\n└"
                report += f"посетителей: <em>{rows[index_rows][3]}</em>\n\n"

                index_rows += 1

            report += "\n"
            index_place += count

    await msg.answer(
        text=report,
        parse_mode="html",
        reply_markup=await create_admin_kb()
    )


async def report_money_in_range(date_from: str, date_to: str, msg: Message):
    rows = DB.get_statistics_money(date_from=date_from, date_to=date_to)
    places = {
        "Белая Дача": sum([row[0].count("Белая Дача") for row in rows]),
        "Ривьера": sum([row[0].count("Ривьера") for row in rows]),
        "Рига Молл": sum([row[0].count("Рига Молл") for row in rows]),
        "Вегас Кунцево": sum([row[0].count("Вегас Кунцево") for row in rows]),
        "Щелковский": sum([row[0].count("Щелковский") for row in rows]),
    }

    report = f"📊Статистика по приходу финансов на точках\n<b>от</b> {date_from} <b>до</b> {date_to}\n\n"
    index_place = 0
    index_rows = 0

    for count in places.values():
        if count:
            report += f"Рабочая точка: <b>{rows[index_place][0]}</b>\n"

            for i in range(count):
                report += f"📝Работник: <em>{rows[index_rows][1]}</em>\n└"
                report += f"выручка: <em>{rows[index_rows][3]}</em> <b>₽</b>\n\n"

                index_rows += 1

            report += "\n"
            index_place += count

    total_money = DB.get_total_money(date_from=date_from, date_to=date_to)

    await msg.answer(
        text=f"{report}"
             f"💰Суммарно денег заработано:\n└<em>{total_money}</em> <b>₽</b>",
        parse_mode="html",
        reply_markup=await create_admin_kb(),
    )


@router_adm.message(Command(commands="stats"), isAdminFilter(config.admins))
async def process_get_stats_command(message: Message, state: FSMContext):
    await state.set_state(FSMAdmin.stats)
    await message.answer(text="⏳Выберите нужную кнопку снизу",
                         reply_markup=await create_money_or_visitors_kb())


@router_adm.callback_query(isAdminFilter(config.admins), StateFilter(FSMAdmin.stats), F.data == "visitors")
async def get_visitors_menu(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(FSMAdmin.visitors)
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id
    )
    await callback.message.answer(text="⏳Выберите временной диапазон",
                                  reply_markup=await create_admin_kb())


@router_adm.callback_query(isAdminFilter(config.admins), StateFilter(FSMAdmin.visitors), F.data == "last_week")
async def get_stats_week(callback: CallbackQuery, bot: Bot):
    try:
        date_to = datetime.now(tz=timezone(timedelta(hours=3.0)))
        date_from = date_to - timedelta(days=7)

        await callback.answer(text="⏳")

        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        time.sleep(0.5)

        await report_visitors_in_range(date_from.strftime("%d.%m.%Y"), date_to.strftime("%d.%m.%Y"), callback.message)
    except Exception as e:
        await callback.message.bot.send_message(text=f"Get stats-visitors last week error: {e}\n"
                                                     f"User_id: {callback.message.from_user.id}",
                                                chat_id=config.admins[0])
        await callback.message.answer(text="⚠️ ВНИМАНИЕ ⚠️\n\n"
                                           "Возникла <b>ошибка</b> при сборе данных, "
                                           "проверьте правильность введенных значений и повторите команду",
                                      parse_mode="html")


@router_adm.callback_query(isAdminFilter(config.admins), StateFilter(FSMAdmin.visitors), F.data == "last_month")
async def get_stats_month(callback: CallbackQuery, bot: Bot):
    try:
        date_to = datetime.now(tz=timezone(timedelta(hours=3.0)))
        date_from = date_to - timedelta(days=30)

        await callback.answer(text="⏳")

        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        time.sleep(0.5)

        await report_visitors_in_range(date_from.strftime("%d.%m.%Y"), date_to.strftime("%d.%m.%Y"), callback.message)
    except Exception as e:
        await callback.message.bot.send_message(text=f"Get stats-visitors last month error: {e}\n"
                                                     f"User_id: {callback.message.from_user.id}",
                                                chat_id=config.admins[0])
        await callback.message.answer(text="⚠️ ВНИМАНИЕ ⚠️\n\n"
                                           "Возникла <b>ошибка</b> при сборе данных, "
                                           "проверьте правильность введенных значений и повторите команду",
                                      parse_mode="html")


@router_adm.callback_query(isAdminFilter(config.admins), StateFilter(FSMAdmin.visitors), F.data == "last_year")
async def get_stats_year(callback: CallbackQuery, bot: Bot):
    try:
        date_to = datetime.now(tz=timezone(timedelta(hours=3.0)))
        date_from = date_to - timedelta(days=365)

        await callback.answer(text="⏳")

        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        time.sleep(0.5)

        await report_visitors_in_range(date_from.strftime("%d.%m.%Y"), date_to.strftime("%d.%m.%Y"), callback.message)
    except Exception as e:
        await callback.message.bot.send_message(text=f"Get stats-visitors last year error: {e}\n"
                                                     f"User_id: {callback.message.from_user.id}",
                                                chat_id=config.admins[0])
        await callback.message.answer(text="⚠️ ВНИМАНИЕ ⚠️\n\n"
                                           "Возникла <b>ошибка</b> при сборе данных, "
                                           "проверьте правильность введенных значений и повторите команду",
                                      parse_mode="html")


@router_adm.callback_query(isAdminFilter(config.admins), StateFilter(FSMAdmin.visitors), F.data == "by_hand")
async def prepare_for_get_stats_by_hand(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(FSMAdmin.visitors_by_hand)
    await callback.answer(text="👌🏻")
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )
    await callback.message.answer(text="⏳Введите диапазон дат <b>через пробел</b>\n\n"
                                       "Например: <em>31.12.2023 06.01.2024</em>",
                                  parse_mode="html")


@router_adm.message(isAdminFilter(config.admins), StateFilter(FSMAdmin.visitors_by_hand), F.text)
async def get_stats_by_hand(message: Message, bot: Bot):
    try:
        date_from, date_to = message.text.split()

        await bot.delete_message(
            chat_id=message.from_user.id,
            message_id=message.message_id,
        )

        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
        )

        await report_visitors_in_range(date_from, date_to, message)
    except Exception as e:
        await message.bot.send_message(text=f"Get stats-visitors by hand error: {e}\n"
                                            f"User_id: {message.from_user.id}",
                                       chat_id=config.admins[0])
        await message.answer(text="⚠️ ВНИМАНИЕ ⚠️\n\n"
                                  "Возникла <b>ошибка</b> при сборе данных, "
                                  "проверьте правильность введенных значений и повторите команду",
                             parse_mode="html")


@router_adm.message(isAdminFilter(config.admins), StateFilter(FSMAdmin.visitors_by_hand))
async def warning_get_stats_by_hand(message: Message):
    await message.answer(
        text="⏳Введите диапазон дат <b>через пробел</b>\n\n"
             "Например: <em>31.12.2023 06.01.2024</em>",
        parse_mode="html",
    )


@router_adm.callback_query(isAdminFilter(config.admins), StateFilter(FSMAdmin.stats), F.data == "money")
async def get_money_menu(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(FSMAdmin.money)
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id
    )
    await callback.message.answer(text="💵Выберите временной диапазон",
                                  reply_markup=await create_admin_kb())


@router_adm.callback_query(isAdminFilter(config.admins), StateFilter(FSMAdmin.money), F.data == "last_week")
async def get_stats_week_money(callback: CallbackQuery, bot: Bot):
    try:
        date_to = datetime.now(tz=timezone(timedelta(hours=3.0)))
        date_from = date_to - timedelta(days=7)

        await callback.answer(text="⏳")

        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        time.sleep(0.5)

        await report_money_in_range(date_from.strftime("%d.%m.%Y"), date_to.strftime("%d.%m.%Y"), callback.message)
    except Exception as e:
        await callback.message.bot.send_message(text=f"Get stats-money last week error: {e}\n"
                                                     f"User_id: {callback.message.from_user.id}",
                                                chat_id=config.admins[0])
        await callback.message.answer(text="⚠️ ВНИМАНИЕ ⚠️\n\n"
                                           "Возникла <b>ошибка</b> при сборе данных, "
                                           "проверьте правильность введенных значений и повторите команду",
                                      parse_mode="html")


@router_adm.callback_query(isAdminFilter(config.admins), StateFilter(FSMAdmin.money), F.data == "last_month")
async def get_stats_month_money(callback: CallbackQuery, bot: Bot):
    try:
        date_to = datetime.now(tz=timezone(timedelta(hours=3.0)))
        date_from = date_to - timedelta(days=30)

        await callback.answer(text="⏳")

        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        time.sleep(0.5)

        await report_money_in_range(date_from.strftime("%d.%m.%Y"), date_to.strftime("%d.%m.%Y"), callback.message)
    except Exception as e:
        await callback.message.bot.send_message(text=f"Get stats-money last month error: {e}\n"
                                                     f"User_id: {callback.message.from_user.id}",
                                                chat_id=config.admins[0])
        await callback.message.answer(text="⚠️ ВНИМАНИЕ ⚠️\n\n"
                                           "Возникла <b>ошибка</b> при сборе данных, "
                                           "проверьте правильность введенных значений и повторите команду",
                                      parse_mode="html")


@router_adm.callback_query(isAdminFilter(config.admins), StateFilter(FSMAdmin.money), F.data == "last_year")
async def get_stats_year_money(callback: CallbackQuery, bot: Bot):
    try:
        date_to = datetime.now(tz=timezone(timedelta(hours=3.0)))
        date_from = date_to - timedelta(days=365)

        await callback.answer(text="⏳")

        await bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )

        time.sleep(0.5)

        await report_money_in_range(date_from.strftime("%d.%m.%Y"), date_to.strftime("%d.%m.%Y"), callback.message)
    except Exception as e:
        await callback.message.bot.send_message(text=f"Get stats-money last year error: {e}\n"
                                                     f"User_id: {callback.message.from_user.id}",
                                                chat_id=config.admins[0])
        await callback.message.answer(text="⚠️ ВНИМАНИЕ ⚠️\n\n"
                                           "Возникла <b>ошибка</b> при сборе данных, "
                                           "проверьте правильность введенных значений и повторите команду",
                                      parse_mode="html")


@router_adm.callback_query(isAdminFilter(config.admins), StateFilter(FSMAdmin.money), F.data == "by_hand")
async def prepare_for_get_stats_money_by_hand(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(FSMAdmin.money_by_hand)
    await callback.answer(text="👌🏻")
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )
    await callback.message.answer(text="⏳Введите диапазон дат <b>через пробел</b>\n\n"
                                       "Например: <em>31.12.2023 06.01.2024</em>",
                                  parse_mode="html")


@router_adm.message(isAdminFilter(config.admins), StateFilter(FSMAdmin.money_by_hand), F.text)
async def get_stats_by_hand(message: Message, bot: Bot):
    try:
        date_from, date_to = message.text.split()

        await bot.delete_message(
            chat_id=message.from_user.id,
            message_id=message.message_id,
        )

        await bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id - 1,
        )

        await report_money_in_range(date_from, date_to, message)
    except Exception as e:
        await message.bot.send_message(text=f"Get stats-money by hand error: {e}\n"
                                            f"User_id: {message.from_user.id}",
                                       chat_id=config.admins[0])
        await message.answer(text="⚠️ ВНИМАНИЕ ⚠️\n\n"
                                  "Возникла <b>ошибка</b> при сборе данных, "
                                  "проверьте правильность введенных значений и повторите команду",
                             parse_mode="html")


@router_adm.message(isAdminFilter(config.admins), StateFilter(FSMAdmin.money_by_hand))
async def warning_get_stats_by_hand(message: Message):
    await message.answer(
        text="⏳Введите диапазон дат <b>через пробел</b>\n\n"
             "Например: <em>31.12.2023 06.01.2024</em>",
        parse_mode="html",
    )


@router_adm.callback_query(
    isAdminFilter(config.admins),
    StateFilter(FSMAdmin.visitors),
    F.data == "back"
)
async def adm_visitors_back_command(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(FSMAdmin.stats)
    await callback.answer(text="👌🏻")
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )
    await callback.message.answer(text="⏳Выберите нужную кнопку снизу",
                                  reply_markup=await create_money_or_visitors_kb())


@router_adm.callback_query(
    isAdminFilter(config.admins),
    StateFilter(FSMAdmin.money),
    F.data == "back"
)
async def adm_visitors_back_command(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(FSMAdmin.stats)
    await callback.answer(text="👌🏻")
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )
    await callback.message.answer(text="⏳Выберите нужную кнопку снизу",
                                  reply_markup=await create_money_or_visitors_kb())


@router_adm.callback_query(
    isAdminFilter(config.admins),
    F.data == "exit"
)
async def adm_cancel_command(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer(text="👋")
    await bot.delete_message(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )
    await callback.message.answer(text="Вы вернулись в главное меню")
    await state.clear()
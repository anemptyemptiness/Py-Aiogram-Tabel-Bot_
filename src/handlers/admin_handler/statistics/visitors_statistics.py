from datetime import datetime, timezone, timedelta, date

from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.db.queries.dao.dao import AsyncOrm
from src.fsm.fsm import FSMStatisticsVisitors, FSMStatistics
from src.handlers.admin_handler import router_admin
from src.keyboards.adm_keyboard import create_stats_kb, create_stats_visitors_kb

router_adm_visitors = Router()
router_admin.include_router(router_adm_visitors)


async def get_report_visitors_by_date(
        date_from: date,
        date_to: date
):
    places = dict()
    data = await AsyncOrm.get_visitors_data_from_reports_by_date(
        date_from=date_from,
        date_to=date_to,
    )

    for place_title, fullname, _, total_visitors in data:
        places.setdefault(place_title, []).append((fullname, total_visitors))

    report = f"📊Статистика по посетителям точек\n<b>от</b> {date_from.strftime('%d.%m.%Y')}" \
             f" <b>до</b> {date_to.strftime('%d.%m.%Y')}\n\n"

    for key in sorted(places.keys()):
        if places[key]:
            report += f"Рабочая точка: <b>{key}</b>\n"

            for fullname, visitors in places[key]:
                report += f"📝Работник: <em>{fullname}</em>\n└"
                report += f"посетителей: <em>{visitors}</em>\n"

            report += "\n"

    return report


@router_adm_visitors.callback_query(StateFilter(FSMStatisticsVisitors.in_stats), F.data == "adm_visitors_is_here")
async def process_adm_visitors_is_here_command(callback: CallbackQuery):
    await callback.answer(text="Вы уже нажали эту кнопку")


@router_adm_visitors.callback_query(StateFilter(FSMStatisticsVisitors.in_stats), F.data == "adm_exit")
async def process_adm_exit_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Вы вернулись в главное меню!",
    )
    await callback.answer()
    await state.clear()


@router_adm_visitors.callback_query(StateFilter(FSMStatisticsVisitors.in_stats), F.data == "adm_stats_visitors_back")
async def process_adm_stats_visitors_back_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Выберите статистику:",
        reply_markup=create_stats_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStatistics.in_stats)


@router_adm_visitors.callback_query(StateFilter(FSMStatisticsVisitors.in_stats), F.data == "adm_visitors_by_week")
async def process_adm_visitors_by_week_command(callback: CallbackQuery):
    date_now = datetime.now(tz=timezone(timedelta(hours=3.0))).date()
    date_last_week = date_now - timedelta(days=7)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Неделя✅", callback_data="adm_visitors_is_here"),
        InlineKeyboardButton(text="Месяц", callback_data="adm_visitors_by_month"),
        InlineKeyboardButton(text="Год", callback_data="adm_visitors_by_year"),
    )
    builder.row(
        InlineKeyboardButton(text="Задать дату вручную", callback_data="adm_visitors_by_custom"),
    )
    builder.row(
        InlineKeyboardButton(text="➢ Назад", callback_data="adm_stats_visitors_back"),
        InlineKeyboardButton(text="➢ Выход", callback_data="adm_exit"),
    )

    await callback.message.edit_text(
        text=await get_report_visitors_by_date(
            date_from=date_last_week,
            date_to=date_now,
        ),
        reply_markup=builder.as_markup(),
        parse_mode="html",
    )
    await callback.answer()


@router_adm_visitors.callback_query(StateFilter(FSMStatisticsVisitors.in_stats), F.data == "adm_visitors_by_month")
async def process_adm_visitors_by_month_command(callback: CallbackQuery):
    date_now = datetime.now(tz=timezone(timedelta(hours=3.0))).date()
    date_last_week = date_now - timedelta(days=30)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Неделя", callback_data="adm_visitors_by_week"),
        InlineKeyboardButton(text="Месяц✅", callback_data="adm_visitors_is_here"),
        InlineKeyboardButton(text="Год", callback_data="adm_visitors_by_year"),
    )
    builder.row(
        InlineKeyboardButton(text="Задать дату вручную", callback_data="adm_visitors_by_custom"),
    )
    builder.row(
        InlineKeyboardButton(text="➢ Назад", callback_data="adm_stats_visitors_back"),
        InlineKeyboardButton(text="➢ Выход", callback_data="adm_exit"),
    )

    await callback.message.edit_text(
        text=await get_report_visitors_by_date(
            date_from=date_last_week,
            date_to=date_now,
        ),
        reply_markup=builder.as_markup(),
        parse_mode="html",
    )
    await callback.answer()


@router_adm_visitors.callback_query(StateFilter(FSMStatisticsVisitors.in_stats), F.data == "adm_visitors_by_year")
async def process_adm_visitors_by_year_command(callback: CallbackQuery):
    date_now = datetime.now(tz=timezone(timedelta(hours=3.0))).date()
    date_last_week = date_now - timedelta(days=365)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Неделя", callback_data="adm_visitors_by_week"),
        InlineKeyboardButton(text="Месяц", callback_data="adm_visitors_by_year"),
        InlineKeyboardButton(text="Год✅", callback_data="adm_visitors_is_here"),
    )
    builder.row(
        InlineKeyboardButton(text="Задать дату вручную", callback_data="adm_visitors_by_custom"),
    )
    builder.row(
        InlineKeyboardButton(text="➢ Назад", callback_data="adm_stats_visitors_back"),
        InlineKeyboardButton(text="➢ Выход", callback_data="adm_exit"),
    )

    await callback.message.edit_text(
        text=await get_report_visitors_by_date(
            date_from=date_last_week,
            date_to=date_now,
        ),
        reply_markup=builder.as_markup(),
        parse_mode="html",
    )
    await callback.answer()


@router_adm_visitors.callback_query(StateFilter(FSMStatisticsVisitors.in_stats), F.data == "adm_visitors_by_custom")
async def process_adm_visitors_by_custom_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➢ Назад", callback_data="adm_stats_visitors_back_from_custom"))

    await callback.message.edit_text(
        text="Пожалуйста, введите нужную Вам дату в <b>корректном формате</b>, "
             "иначе я не смогу понять Вас!\n\n"
             "Нужно ввести первой датой значение, <b>от</b> которого мне нужно искать (включая эту дату), "
             "а второй датой введите значение, <b>до</b> которого мне нужно искать (тоже включая эту дату)\n\n"
             "Например: <em><b>01.01.24 31.12.24</b></em>\n"
             "Такая запись означает, что я буду формировать статистику из данных за период "
             "от 1 января 2024 до 31 декабря 2024 года",
        reply_markup=builder.as_markup(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMStatisticsVisitors.custom_date)


@router_adm_visitors.message(StateFilter(FSMStatisticsVisitors.custom_date), F.text)
async def process_adm_visitors_custom_date_command(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="➢ Назад", callback_data="adm_stats_visitors_back_from_custom"))

    date_from: str = ""
    date_to: str = ""

    try:
        date_from, date_to = message.text.split(sep=" ", maxsplit=1)
    except ValueError:
        await message.answer(
            text="Вы ввели некорректную дату, попробуйте еще раз!\n\n"
                 "У меня не получилось прочитать дату из Вашего сообщения, "
                 "проверьте её корректность, пожалуйста!\n\n"
                 "Я ожидаю получить сообщения с двумя датами, которые я могу разделить "
                 "<b>одним</b> пробелом\n\n"
                 'Например: <em>"дд.мм.гг дд.мм.гг"</em>\n'
                 'Видите? Тут всего лишь один пробел',
            reply_markup=builder.as_markup(),
            parse_mode="html",
        )
        return

    if date_from and date_to and len(message.text.split()) == 2 and date_to.count(".") == 2 and date_from.count(".") == 2:
        try:
            date_from: date = datetime.strptime(date_from, "%d.%m.%y").date()
            date_to: date = datetime.strptime(date_to, "%d.%m.%y").date()

            await message.answer(
                text=await get_report_visitors_by_date(
                    date_from=date_from,
                    date_to=date_to,
                ),
                reply_markup=create_stats_visitors_kb(),
                parse_mode="html",
            )
            await state.set_state(FSMStatisticsVisitors.in_stats)
        except ValueError:
            try:
                date_from: date = datetime.strptime(date_from, "%d.%m.%Y").date()
                date_to: date = datetime.strptime(date_to, "%d.%m.%Y").date()

                await message.answer(
                    text=await get_report_visitors_by_date(
                        date_from=date_from,
                        date_to=date_to,
                    ),
                    reply_markup=create_stats_visitors_kb(),
                    parse_mode="html",
                )
                await state.set_state(FSMStatisticsVisitors.in_stats)
            except ValueError:
                await message.answer(
                    text="Вы ввели некорректную дату, попробуйте еще раз!\n\n"
                         "Я ожидаю от Вас либо такой формат:\n"
                         "<em><b>дд.мм.гг</b></em>, где все цифры двузначны,\n"
                         "либо такой формат:\n"
                         "<em><b>дд.мм.гггг</b></em>, где все день и месяц двузначны, "
                         "а год - четырёхзначное число",
                    reply_markup=builder.as_markup(),
                    parse_mode="html",
                )
                return
    else:
        await message.answer(
            text="Вы ввели некорректную дату, попробуйте еще раз!\n\n"
                 "Я ожидаю увидеть дату с нужным расположением точек!\n"
                 "Например, не дд<b>..</b>мм.гг, а дд<b>.</b>мм<b>.</b>гг",
            reply_markup=builder.as_markup(),
            parse_mode="html",
        )


@router_adm_visitors.callback_query(StateFilter(FSMStatisticsVisitors.custom_date), F.data == "adm_stats_visitors_back_from_custom")
async def process_adm_stats_visitors_back_from_custom_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Статистика посетителей:",
        reply_markup=create_stats_visitors_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStatisticsVisitors.in_stats)


@router_adm_visitors.callback_query(StateFilter(FSMStatisticsVisitors.in_stats), F.data == "adm_stats_visitors_back_from_custom")
async def process_adm_stats_visitors_back_from_custom_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Статистика посетителей:",
        reply_markup=create_stats_visitors_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStatisticsVisitors.in_stats)
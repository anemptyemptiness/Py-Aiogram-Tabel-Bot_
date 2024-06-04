from datetime import datetime, timezone, timedelta

from typing import Dict, Any, Union

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command
from aiogram.fsm.state import default_state
from aiogram.exceptions import TelegramAPIError

from src.config import settings
from src.callbacks.place import PlaceCallbackFactory
from src.lexicon.lexicon_ru import LEXICON_RU
from src.fsm.fsm import FSMAttractionsCheck
from src.keyboards.keyboard import create_yes_no_kb, create_places_kb, create_cancel_kb
from src.db.queries.dao.dao import AsyncOrm
from src.db import cached_places
import logging

router_attractions = Router()
logger = logging.getLogger(__name__)


async def report(dictionary: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return "📝Проверка аттракционов:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {await AsyncOrm.get_current_name(user_id=user_id)}\n\n" \
           f"Купюроприемники рабочие: <em>{dictionary['bill_acceptors']}</em>\n\n" \
           f"Номера нерабочих купюроприемников: <em>{dictionary['defects_on_bill_acceptors'] if dictionary['bill_acceptors'] == 'no' else 'None'}</em>\n\n" \
           f"Дефекты на аттракционах: <em>{dictionary['attracts']}</em>\n\n" \
           f"Номера аттракционов с дефектами: <em>{dictionary['defects_on_attracts'] if dictionary['attracts'] == 'yes' else 'None'}</em>"


async def send_report(message: Message, state: FSMContext, data: dict, date: str, chat_id: Union[str, int]):
    try:
        await message.bot.send_message(
            chat_id=chat_id,
            text=await report(
                dictionary=data,
                date=date,
                user_id=message.chat.id,
            ),
            parse_mode="html",
        )

        await message.answer(
            text="Отлично, отчёт сформирован...\nОтправляю начальству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramAPIError as e:
        logger.exception("Ошибка в check_attractions.py")
        await message.bot.send_message(
            text=f"Check attractions report error: {e}\n"
                 f"User_id: {message.from_user.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    finally:
        await state.clear()


@router_attractions.message(Command(commands="check_attractions"), StateFilter(default_state))
async def process_place_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=create_places_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMAttractionsCheck.place)


@router_attractions.callback_query(StateFilter(FSMAttractionsCheck.place), PlaceCallbackFactory.filter())
async def process_bill_acceptor_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await state.update_data(place=callback_data.title)
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Все купюроприемники работают?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAttractionsCheck.bill_acceptor)


@router_attractions.message(StateFilter(FSMAttractionsCheck.place))
async def warning_place_command(message: Message):
    await message.answer(
        text="Выберите рабочую точку ниже из выпадающего списка",
        reply_markup=await create_cancel_kb(),
    )


@router_attractions.callback_query(StateFilter(FSMAttractionsCheck.bill_acceptor), F.data == "yes")
async def process_bill_acceptor_command_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(bill_acceptors="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Все купюроприемники работают?\n\n"
             f"➢ Да",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Были ли обнаружены дефекты на аттракционах?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAttractionsCheck.attracts)


@router_attractions.callback_query(StateFilter(FSMAttractionsCheck.bill_acceptor), F.data == "no")
async def process_bill_acceptor_command_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(bill_acceptors="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Все купюроприемники работают?\n\n"
             f"➢ Нет",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Напишите номера (наименование) неработающих купюроприемников в <b>одном</b> сообщении!",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAttractionsCheck.defects_on_bill_acceptor)


@router_attractions.message(StateFilter(FSMAttractionsCheck.bill_acceptor))
async def warning_bill_accepton_command(message: Message):
    await message.answer(text="Выберите ответ ниже на появившихся кнопках")


@router_attractions.message(StateFilter(FSMAttractionsCheck.defects_on_bill_acceptor), F.text)
async def process_defects_on_bill_command(message: Message, state: FSMContext):
    await state.update_data(defects_on_bill_acceptors=message.text)
    await message.answer(
        text="Были ли обнаружены дефекты на аттракционах?",
        reply_markup=create_yes_no_kb(),
    )
    await state.set_state(FSMAttractionsCheck.attracts)


@router_attractions.message(StateFilter(FSMAttractionsCheck.defects_on_bill_acceptor))
async def warning_defects_on_bill_command(message: Message):
    await message.answer(
        text="Введите номера неработающих купюроприемников <b>текстом</b> в <b>одном</b> сообщении",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="html",
    )


@router_attractions.callback_query(StateFilter(FSMAttractionsCheck.attracts), F.data == "yes")
async def process_attracts_command_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(attracts="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Были ли обнаружены дефекты на аттракционах?\n\n"
             f"➢ Да",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Напишите аттракцион и опишите его дефект в <b>одном</b> сообщении",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAttractionsCheck.defects_on_attracts)


@router_attractions.callback_query(StateFilter(FSMAttractionsCheck.attracts), F.data == "no")
async def process_attracts_command_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(attracts="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Были ли обнаружены дефекты на аттракционах?\n\n"
             f"➢ Нет",
        parse_mode="html",
    )
    check_attractions_dict = await state.get_data()

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {LEXICON_RU[day_of_week]}')

    await send_report(
        message=callback.message,
        state=state,
        data=check_attractions_dict,
        date=date,
        chat_id=cached_places[check_attractions_dict["place"]],
    )
    await callback.answer()


@router_attractions.message(StateFilter(FSMAttractionsCheck.attracts))
async def warning_attracts_command(message: Message):
    await message.answer(text="Выберите ответ ниже на появившихся кнопках")


@router_attractions.message(StateFilter(FSMAttractionsCheck.defects_on_attracts), F.text)
async def process_defects_on_attracts_command(message: Message, state: FSMContext):
    await state.update_data(defects_on_attracts=message.text)
    check_attractions_dict = await state.get_data()

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {LEXICON_RU[day_of_week]}')

    await send_report(
        message=message,
        state=state,
        data=check_attractions_dict,
        date=date,
        chat_id=cached_places[check_attractions_dict["place"]],
    )


@router_attractions.message(StateFilter(FSMAttractionsCheck.defects_on_attracts))
async def warning_process_defects_on_attrs_command(message: Message):
    await message.answer(text="Напишите аттракцион и опишите его дефект в <b>одном</b> сообщении",
                         reply_markup=ReplyKeyboardRemove(),
                         parse_mode="html")

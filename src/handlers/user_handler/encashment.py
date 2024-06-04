from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, InputMediaPhoto, CallbackQuery
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.exceptions import TelegramAPIError

from typing import Dict, Any, Union

from src.config import settings
from src.callbacks.place import PlaceCallbackFactory
from src.fsm.fsm import FSMEncashment
from src.lexicon.lexicon_ru import LEXICON_RU
from src.keyboards.keyboard import create_cancel_kb, create_places_kb
from src.middlewares.album_middleware import AlbumsMiddleware
from src.db.queries.dao.dao import AsyncOrm
from src.db import cached_places
import logging

router_encashment = Router()
router_encashment.message.middleware(middleware=AlbumsMiddleware(2))
logger = logging.getLogger(__name__)


async def report(dictionary: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return "📝Инкассация:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {await AsyncOrm.get_current_name(user_id=user_id)}\n\n" \
           f"Дата инкассации: <em>{dictionary['date']}</em>\n" \
           f"Сумма инкассации: <em>{dictionary['summary']}</em>"


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

        if data['photo_of_check'] != "0":
            media_check = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото чека инкассации" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data['photo_of_check'])]
            await message.bot.send_media_group(
                chat_id=chat_id,
                media=media_check,
            )

        await message.answer(
            text="Отлично, все данные отправлены начальству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramAPIError as e:
        logger.exception("Ошибка в encashment.py")
        await message.bot.send_message(
            text=f"Encashment report error: {e}\n"
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


@router_encashment.message(Command(commands="encashment"), StateFilter(default_state))
async def process_place_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=create_places_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMEncashment.place)


@router_encashment.callback_query(StateFilter(FSMEncashment.place), PlaceCallbackFactory.filter())
async def process_photo_of_check_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await state.update_data(place=callback_data.title)
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Пожалуйста, пришлите сюда фото чека инкассации\n\n"
             "Если инкассации нет, напишите 0",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMEncashment.photo_of_check)


@router_encashment.message(StateFilter(FSMEncashment.place))
async def warning_place_command(message: Message):
    await message.answer(
        text="Выберите рабочую точку ниже из выпадающего списка",
    )


@router_encashment.message(StateFilter(FSMEncashment.photo_of_check))
async def process_wait_for_check_command(message: Message, state: FSMContext):
    if message.photo:
        if 'photo_of_check' not in await state.get_data():
            await state.update_data(photo_of_check=[message.photo[-1].file_id])

        await message.answer(
            text="Отлично, а теперь пришлите сумму инкассации числом",
            reply_markup=create_cancel_kb(),
        )
        await state.set_state(FSMEncashment.summary)
    elif message.text == "0":
        await state.update_data(photo_of_check="0")

        encashment_dict = await state.get_data()
        encashment_dict['summary'] = "0"
        encashment_dict['date'] = "None"

        day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
        date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {LEXICON_RU[day_of_week]}')

        await send_report(
            message=message,
            state=state,
            data=encashment_dict,
            date=date,
            chat_id=cached_places[encashment_dict['place']],
        )
    else:
        await message.answer(
            text="Введите 0 или отправьте фото чека!",
            reply_markup=create_cancel_kb(),
        )


@router_encashment.message(StateFilter(FSMEncashment.photo_of_check))
async def warning_wait_for_check_command(message: Message):
    await message.answer(
        text="Пришлите фото чека или 0, если инкассации не было!",
        reply_markup=create_cancel_kb(),
    )


@router_encashment.message(StateFilter(FSMEncashment.summary), F.text.isdigit())
async def process_wait_for_summary_command(message: Message, state: FSMContext):
    await state.update_data(summary=int(message.text))
    await message.answer(
        text="Отлично, а теперь пришлите дату, за которую делали инкассацию",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMEncashment.date_of_cash)


@router_encashment.message(StateFilter(FSMEncashment.summary))
async def warning_wait_for_summary_command(message: Message):
    await message.answer(
        text="Пришлите сумму числом!",
        reply_markup=create_cancel_kb(),
    )


@router_encashment.message(StateFilter(FSMEncashment.date_of_cash), F.text)
async def process_wait_for_date_command(message: Message, state: FSMContext):
    await state.update_data(date=message.text)

    encashment_dict = await state.get_data()

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {LEXICON_RU[day_of_week]}')

    await send_report(
        message=message,
        state=state,
        data=encashment_dict,
        date=date,
        chat_id=cached_places[encashment_dict['place']],
    )


@router_encashment.message(StateFilter(FSMEncashment.date_of_cash))
async def warning_wait_for_date_command(message: Message):
    await message.answer(
        text="Отправьте дату инкассации!",
        reply_markup=create_cancel_kb(),
    )

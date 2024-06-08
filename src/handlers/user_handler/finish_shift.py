from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, InputMediaPhoto, InputMediaVideo, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.filters import StateFilter, Command
from aiogram.exceptions import TelegramAPIError
from src.db.queries.dao.dao import AsyncOrm

from src.callbacks.place import PlaceCallbackFactory
from src.fsm.fsm import FSMFinishShift
from src.lexicon.lexicon_ru import LEXICON_RU
from src.keyboards.keyboard import create_cancel_kb, create_yes_no_kb, create_places_kb
from src.middlewares.album_middleware import AlbumsMiddleware
from src.config import settings
from src.db import cached_places

from decimal import Decimal
from typing import Dict, Any, Union
import re
import logging

router_finish = Router()
router_finish.message.middleware(middleware=AlbumsMiddleware(2))
logger = logging.getLogger(__name__)


async def report(dictionary: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return "📝Закрытие смены:\n\n"\
           f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {await AsyncOrm.get_current_name(user_id=user_id)}\n\n" \
           f"Количество посетителей: <em>{dictionary['visitors']}</em>\n" \
           f"Были ли льготники: <em>{'yes' if dictionary['beneficiaries'] != 'no' else 'no'}</em>\n" \
           f"Паровоз поставлен на зарядку: <em>{dictionary['charge']}</em>\n" \
           f"Общая выручка: <em>{dictionary['summary']}</em>\n" \
           f"Наличные: <em>{dictionary['cash']}</em>\n" \
           f"Безнал: <em>{dictionary['online_cash']}</em>\n" \
           f"QR-код: <em>{dictionary['qr_code']}</em>\n" \
           f"Расход: <em>{dictionary['expenditure']}</em>\n" \
           f"Зарплата: <em>{dictionary['salary']}</em>\n" \
           f"Инкассация: <em>{dictionary['encashment']}</em>\n"


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

        if 'photo_of_beneficiaries' in data:
            media_beneficiaries = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото льготников" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data['photo_of_beneficiaries'])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=media_beneficiaries,
            )

        media_necessary = [
            InputMediaPhoto(
                media=photo_file_id,
                caption="Чеки и необходимые фото за смену" if i == 0 else ""
            ) for i, photo_file_id in enumerate(data['necessary_photos'])
        ]

        await message.bot.send_media_group(
            chat_id=chat_id,
            media=media_necessary,
        )

        video_necessary = [
            InputMediaVideo(
                media=video_file_id,
                caption="Видео аккумулятора и внешнего вида поезда" if i == 0 else ""
            ) for i, video_file_id in enumerate(data['charge_video'])
        ]

        await message.bot.send_media_group(
            chat_id=chat_id,
            media=video_necessary,
        )

        await AsyncOrm.set_data_to_reports(
            user_id=message.chat.id,
            place=data["place"],
            visitors=data["visitors"],
            revenue=int(data["summary"].replace('.', '').replace(',', '')),
        )

        await message.answer(
            text="Отлично! Формирую отчёт...\nОтправляю начальству!",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Вы вернулись в главное меню",
        )
    except Exception as e:
        logger.exception("Ошибка не с телеграм в finish_shift.py")
        await message.bot.send_message(
            text=f"Finish shift report error: {e}\n"
                 f"User_id: {message.from_user.id}",
            chat_id=settings.ADMIN_ID,
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramAPIError as e:
        logger.exception("Ошибка с телеграм в finish_shift.py")
        await message.bot.send_message(
            text=f"Finish shift report error: {e}\n"
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


@router_finish.message(Command(commands="finish_shift"), StateFilter(default_state))
async def process_place_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=create_places_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMFinishShift.place)


@router_finish.callback_query(StateFilter(FSMFinishShift.place), PlaceCallbackFactory.filter())
async def process_finish_start_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await state.update_data(place=callback_data.title)
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Сколько было посетителей за сегодня? (Пришлите ответ числом)",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.count_of_visitors)


@router_finish.message(StateFilter(FSMFinishShift.place))
async def warning_place_command(message: Message):
    await message.answer(
        text="Выберите рабочую точку ниже из выпадающего списка",
        reply_markup=create_cancel_kb(),
    )


@router_finish.message(StateFilter(FSMFinishShift.count_of_visitors), F.text.isdigit())
async def process_visitors_command(message: Message, state: FSMContext):
    await state.update_data(visitors=int(message.text))
    await message.answer(
        text="Были ли льготники за сегодня?",
        reply_markup=create_yes_no_kb(),
    )
    await state.set_state(FSMFinishShift.beneficiaries)


@router_finish.message(StateFilter(FSMFinishShift.count_of_visitors))
async def warning_visitors_command(message: Message):
    await message.answer(
        text="Пришлите количество посетителей <b>числом</b>",
        parse_mode="html",
        reply_markup=create_cancel_kb(),
    )


@router_finish.callback_query(StateFilter(FSMFinishShift.beneficiaries), F.data == "yes")
async def process_beneficiaries_command_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(beneficiaries="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Были ли льготники за сегодня?\n\n"
             f"➢ Да",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Прикрепите подтвреждающее фото (справка, паспорт родителей)",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.photo_of_beneficiaries)


@router_finish.callback_query(StateFilter(FSMFinishShift.beneficiaries), F.data == "no")
async def process_beneficiaries_command_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(beneficiaries="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Были ли льготники за сегодня?\n\n"
             f"➢ Нет",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Введите общую выручку за сегодня",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.summary)


@router_finish.message(StateFilter(FSMFinishShift.beneficiaries))
async def warning_beneficiaries_command(message: Message):
    await message.answer(
        text="Выберите ответ ниже на появившихся кнопках",
    )


@router_finish.message(StateFilter(FSMFinishShift.photo_of_beneficiaries))
async def process_photo_of_beneficiaries_command(message: Message, state: FSMContext):
    if message.photo:
        if 'photo_of_beneficiaries' not in await state.get_data():
            await state.update_data(photo_of_beneficiaries=[message.photo[-1].file_id])

        await message.answer(
            text="Введите общую выручку за сегодня",
            reply_markup=create_cancel_kb(),
        )
        await state.set_state(FSMFinishShift.summary)
    else:
        await message.answer(
            text="Это не похоже на фото, отправьте фото чеков",
            reply_markup=create_cancel_kb(),
        )


@router_finish.message(StateFilter(FSMFinishShift.summary), F.text)
async def process_summary_command(message: Message, state: FSMContext):
    money_message = message.text.lower()
    pattern = r'\b\w*рубл[ьяей]?\w*\b'

    if "," in message.text:
        money_message = message.text.replace(",", ".")

    money_message = re.sub(pattern, '', money_message)

    await state.update_data(summary=str(Decimal(money_message)))
    await message.answer(
        text="Введите сумму наличных за сегодня",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.cash)


@router_finish.message(StateFilter(FSMFinishShift.summary))
async def warning_summary_command(message: Message):
    await message.answer(
        text="Введите общую сумму <b>числом<b>!",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.cash), F.text)
async def process_cash_command(message: Message, state: FSMContext):
    await state.update_data(cash=message.text)
    await message.answer(
        text="Введите сумму безнала за сегодня",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.online_cash)


@router_finish.message(StateFilter(FSMFinishShift.cash))
async def warning_cash_command(message: Message):
    await message.answer(
        text="Введите сумму наличных числом!",
        reply_markup=create_cancel_kb(),
    )


@router_finish.message(StateFilter(FSMFinishShift.online_cash), F.text)
async def process_online_cash_command(message: Message, state: FSMContext):
    await state.update_data(online_cash=message.text)
    await message.answer(
        text="Введите сумму оплаты по QR-коду за сегодня",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.qr_code)


@router_finish.message(StateFilter(FSMFinishShift.online_cash))
async def warning_online_cash_command(message: Message):
    await message.answer(
        text="Введите сумму безнала <b>числом</b>!",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.qr_code), F.text)
async def process_qr_code_command(message: Message, state: FSMContext):
    await state.update_data(qr_code=message.text)
    await message.answer(
        text="Введите сумму расхода за сегодня",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.expenditure)


@router_finish.message(StateFilter(FSMFinishShift.qr_code))
async def warning_qr_code_command(message: Message):
    await message.answer(
        text="Введите сумму по QR-коду <b>числом</b>!",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.expenditure), F.text)
async def process_expenditure_command(message: Message, state: FSMContext):
    await state.update_data(expenditure=message.text)
    await message.answer(
        text="Введите сумму, сколько Вы взяли сегодня зарплатой\n\n"
             "Если Вы не брали сегодня зарплату, то введите 0",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.salary)


@router_finish.message(StateFilter(FSMFinishShift.expenditure))
async def warning_expenditure_command(message: Message):
    await message.answer(
        text="Введите сумму расхода <b>числом</b>!",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.salary), F.text.isdigit())
async def process_salary_command(message: Message, state: FSMContext):
    await state.update_data(salary=message.text)
    await message.answer(
        text="Введите сумму инкассации\n\n"
             "Если нет инкассации - напишите 0",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.encashment)


@router_finish.message(StateFilter(FSMFinishShift.salary))
async def warning_salary_command(message: Message):
    await message.answer(
        text="Введите зарплату <b>числом</b>!",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.encashment), F.text)
async def process_encashment_command(message: Message, state: FSMContext):
    await state.update_data(encashment=message.text)
    await message.answer(
        text="Прикрепите чеки и необходимые фотографии за смену "
             "(чеки о закрытии смены, оплата QR-кода, чек расхода)",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMFinishShift.necessary_photos)


@router_finish.message(StateFilter(FSMFinishShift.encashment))
async def warning_encashment_command(message: Message):
    await message.answer(
        text="Пришлите сумму инкассации <b>числом</b>!",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_finish.message(StateFilter(FSMFinishShift.necessary_photos))
async def process_necessary_photos_command(message: Message, state: FSMContext):
    if message.photo:
        if 'necessary_photos' not in await state.get_data():
            await state.update_data(necessary_photos=[message.photo[-1].file_id])

        await message.answer(
            text="Вы поставили паровоз на зарядку?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMFinishShift.charge)
    else:
        await message.answer(
            text="Это не похоже на фото, отправьте фото!",
            reply_markup=create_cancel_kb(),
        )


@router_finish.callback_query(StateFilter(FSMFinishShift.charge), F.data == "yes")
async def process_charge_command_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(charge="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы поставили паровоз на зарядку?\n\n"
             f"➢ Да",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Прикрепите видео аккумулятора и внешнего вида поезда!",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.charge_video)


@router_finish.callback_query(StateFilter(FSMFinishShift.charge), F.data == "no")
async def process_charge_command_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(charge="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы поставили паровоз на зарядку?\n\n"
             f"➢ Нет",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Поставьте на зарядку и прикрепите видео аккумулятора и внешнего вида поезда!",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMFinishShift.charge_video)


@router_finish.message(StateFilter(FSMFinishShift.charge))
async def warning_charge_command(message: Message):
    await message.answer(
        text="Выберите ответ на появившихся кнопках",
    )


@router_finish.message(StateFilter(FSMFinishShift.charge_video))
async def process_charge_video_command(message: Message, state: FSMContext):
    if message.video:
        if 'charge_video' not in await state.get_data():
            await state.update_data(charge_video=[message.video.file_id])

        finish_shift_dict = await state.get_data()

        day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
        date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d-%m-%Y - {LEXICON_RU[day_of_week]}')

        await send_report(
            message=message,
            state=state,
            data=finish_shift_dict,
            date=date,
            chat_id=cached_places[finish_shift_dict['place']],
        )
    else:
        await message.answer(
            text="Это не похоже на видео, прикрепите видео аккумулятора и внешнего вида поезда!",
            reply_markup=create_cancel_kb(),
        )

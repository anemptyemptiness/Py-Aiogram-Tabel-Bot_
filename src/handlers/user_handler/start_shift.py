from typing import Dict, Any, Union
from datetime import datetime, timezone, timedelta

from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove, InputMediaPhoto, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError

from src.callbacks.place import PlaceCallbackFactory
from src.fsm.fsm import FSMStartShift
from src.keyboards.keyboard import create_yes_no_kb, create_cancel_kb, create_places_kb, create_rules_kb
from src.middlewares.album_middleware import AlbumsMiddleware
from src.lexicon.lexicon_ru import LEXICON_RU, rules
from src.config import settings
from src.db.queries.dao.dao import AsyncOrm
from src.db import cached_places
import logging

router_start_shift = Router()
router_start_shift.message.middleware(middleware=AlbumsMiddleware(2))
logger = logging.getLogger(__name__)


async def report(dictionary: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return "📝Открытие смены:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {await AsyncOrm.get_current_name(user_id=user_id)}\n\n" \
           f"Наличие дефектов: <em>{'no' if dictionary['train_has_defects'] == 'no' else 'фото ниже'}</em>\n" \
           f"Проверка колёс: <em>{dictionary['wheels_pumped']}</em>\n" \
           f"Свет и подсветка на паровозе: <em>{dictionary['train_flash']}</em>\n" \
           f"Паровоз чистый: <em>{dictionary['train_clean']}</em>\n" \
           f"Магнитофон включен: <em>{dictionary['is_recorder_on']}</em>\n" \
           f"Томас включен: <em>{dictionary['is_thomas_on']}</em>"


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
        await message.bot.send_photo(
            chat_id=chat_id,
            photo=data['photo'],
            caption='Фото сотрудника',
        )
        await message.bot.send_video(
            chat_id=chat_id,
            video=data['video'],
            caption='Видео сотрудника',
        )

        if data['train_has_defects'] != "no":
            media_defects = [
                InputMediaPhoto(
                    media=photo_file_id,
                    caption="Фото дефектов" if i == 0 else ""
                ) for i, photo_file_id in enumerate(data['train_has_defects'])
            ]

            await message.bot.send_media_group(
                chat_id=chat_id,
                media=media_defects,
            )
        await message.answer(
            text="Отлично! Отчёт сформирован... Отправляю начальству!",
            reply_markup=ReplyKeyboardRemove(),
        )
        await message.answer(
            text="Вы вернулись в главное меню",
        )

    except Exception as e:
        logger.exception("Ошибка не с телеграм в start_shift.py")
        await message.bot.send_message(
            text=f"Start shift report error: {e}\n"
                 f"User_id: {message.from_user.id}",
            chat_id=settings.ADMIN_ID)
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
        )
    except TelegramAPIError as e:
        logger.exception("Ошибка с телеграм в start_shift.py")
        await message.bot.send_message(
            text=f"Start shift report error: {e}\n"
                 f"User_id: {message.from_user.id}",
            chat_id=settings.ADMIN_ID)
        await message.answer(
            text="Упс... что-то пошло не так, сообщите руководству!",
        )
    finally:
        await state.clear()


@router_start_shift.message(Command(commands="start_shift"), StateFilter(default_state))
async def process_place_command(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>",
        reply_markup=create_places_kb(),
        parse_mode="html",
    )
    await state.set_state(FSMStartShift.place)


@router_start_shift.callback_query(StateFilter(FSMStartShift.place), PlaceCallbackFactory.filter())
async def process_start_shift_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await state.update_data(place=callback_data.title)
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Пожалуйста, выберите свою рабочую точку из списка <b>ниже</b>\n\n"
             f"➢ {callback_data.title}",
        parse_mode="html",
    )
    await callback.message.answer(
        text=f"{rules}",
        reply_markup=create_rules_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMStartShift.policy)


@router_start_shift.message(StateFilter(FSMStartShift.place))
async def warning_place_command(message: Message):
    await message.answer(
        text="Выберите рабочую точку ниже из выпадающего списка",
        reply_markup=create_cancel_kb(),
    )


@router_start_shift.callback_query(StateFilter(FSMStartShift.policy), F.data == "agree")
async def process_policy_command(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.update_data(policy="agree")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text=f"{rules}\n\n"
             "➢ Согласен",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Пожалуйста, отправьте Ваше фото на рабочем месте",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.my_photo)


@router_start_shift.message(StateFilter(FSMStartShift.policy))
async def warning_policy_command(message: Message):
    await message.answer(
        text="Для согласия с правилами нажмите на кнопку под самими правилами!",
        reply_markup=create_cancel_kb(),
    )


@router_start_shift.message(StateFilter(FSMStartShift.my_photo), F.photo)
async def process_get_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer(
        text="Отлично, а теперь пришлите видео паровоза (в окружении)",
        reply_markup=create_cancel_kb(),
    )
    await state.set_state(FSMStartShift.my_video)


@router_start_shift.message(StateFilter(FSMStartShift.my_photo))
async def warning_get_photo(message: Message):
    await message.answer(
        text="Это не похоже на фото, попробуйте ещё раз",
        reply_markup=create_cancel_kb(),
    )


@router_start_shift.message(StateFilter(FSMStartShift.my_video), F.video)
async def process_get_video(message: Message, state: FSMContext):
    await state.update_data(video=message.video.file_id)
    await message.answer(
        text="Отлично, а теперь я задам ряд вопросов, на которые Вам предстоит ответить!\n\n"
             "Проверьте паровоз на наличие дефектов. Есть ли дефекты?",
        reply_markup=create_yes_no_kb(),
    )
    await state.set_state(FSMStartShift.wait_for_defects)


@router_start_shift.message(StateFilter(FSMStartShift.my_video))
async def warning_get_video(message: Message):
    await message.answer(
        text="Это не похоже на видео, попробуйте еще раз",
        reply_markup=create_cancel_kb(),
    )


@router_start_shift.callback_query(StateFilter(FSMStartShift.wait_for_defects), F.data == "yes")
async def process_defects_true(callback: CallbackQuery, state: FSMContext):
    await state.update_data(train_has_defects="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Отлично, а теперь я задам ряд вопросов, на которые Вам предстоит ответить!\n\n"
             "Проверьте паровоз на наличие дефектов. Есть ли дефекты?\n\n"
             "➢ Да",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Пришлите фото дефектов",
        reply_markup=create_cancel_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.photo_of_defects)


@router_start_shift.callback_query(StateFilter(FSMStartShift.wait_for_defects), F.data == "no")
async def process_defects_false(callback: CallbackQuery, state: FSMContext):
    await state.update_data(train_has_defects="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Отлично, а теперь я задам ряд вопросов, на которые Вам предстоит ответить!\n\n"
             "Проверьте паровоз на наличие дефектов. Есть ли дефекты?\n\n"
             "➢ Нет",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Вы проверили колёса у паровоза, достаточно ли они накачены?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.wheels)


@router_start_shift.message(StateFilter(FSMStartShift.wait_for_defects))
async def warning_process_defects(message: Message):
    await message.answer(
        text="Выберите ответ ниже на появившихся кнопках",
    )


@router_start_shift.message(StateFilter(FSMStartShift.photo_of_defects))
async def process_need_to_photo_of_defects(message: Message, state: FSMContext):
    if message.photo:
        if 'train_has_defects' not in await state.get_data():
            await state.update_data(train_has_defects=[message.photo[-1].file_id])

        await message.answer(
            text="Вы проверили колёса у паровоза, достаточно ли они накачены?",
            reply_markup=create_yes_no_kb(),
        )
        await state.set_state(FSMStartShift.wheels)
    else:
        await message.answer(
            text="Это не похоже на фото, отправьте фото дефектов",
            reply_markup=create_cancel_kb(),
        )


@router_start_shift.callback_query(StateFilter(FSMStartShift.wheels), F.data == "yes")
async def process_wheels_command_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(wheels_pumped="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы проверили колёса у паровоза, достаточно ли они накачены?\n\n"
             "➢ Да",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Включили ли Вы свет и подсветку на паровозе?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.train_flash)


@router_start_shift.callback_query(StateFilter(FSMStartShift.wheels), F.data == "no")
async def process_wheels_command_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(wheels_pumped="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы проверили колёса у паровоза, достаточно ли они накачены?\n\n"
             "➢ Нет",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Нужно подкачать колёса!\n\nВы включили свет и подсветку на паровозе?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.train_flash)


@router_start_shift.message(StateFilter(FSMStartShift.wheels))
async def warning_process_wheels(message: Message):
    await message.answer(
        text="Выберите ответ ниже на появившихся кнопках",
    )


@router_start_shift.callback_query(StateFilter(FSMStartShift.train_flash), F.data == "yes")
async def process_train_flash_command_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(train_flash="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы включили свет и подсветку на паровозе?\n\n"
             "➢ Да",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Вы протёрли паровоз от пыли?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.train_clean)


@router_start_shift.callback_query(StateFilter(FSMStartShift.train_flash), F.data == "no")
async def process_train_flash_command_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(train_flash="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы включили свет и подсветку на паровозе?\n\n"
             "➢ Нет",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Нужно включить подсветку!\n\nВы протёрли паровоз от пыли?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.train_clean)


@router_start_shift.message(StateFilter(FSMStartShift.train_flash))
async def warning_process_train_flash(message: Message):
    await message.answer(
        text="Выберите ответ ниже на появившихся кнопках",
    )


@router_start_shift.callback_query(StateFilter(FSMStartShift.train_clean), F.data == "yes")
async def process_train_clean_command_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(train_clean="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы протёрли паровоз от пыли?\n\n"
             "➢ Да",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Вы включили магнитофон?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.recorder)


@router_start_shift.callback_query(StateFilter(FSMStartShift.train_clean), F.data == "no")
async def process_train_clean_command_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(train_clean="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы протёрли паровоз от пыли?\n\n"
             "➢ Нет",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Нужно обязательно протереть паровоз!\n\nВы включили магнитофон?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.recorder)


@router_start_shift.callback_query(StateFilter(FSMStartShift.recorder), F.data == "yes")
async def process_recorder_command_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_recorder_on="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы включили магнитофон?\n\n"
             "➢ Да",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Вы включили Томас?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.thomas)


@router_start_shift.callback_query(StateFilter(FSMStartShift.recorder), F.data == "no")
async def process_recorder_command_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_recorder_on="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы включили магнитофон?\n\n"
             "➢ Нет",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Вставьте флешку и включите!\n\nВы включили Томас?",
        reply_markup=create_yes_no_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStartShift.thomas)


@router_start_shift.message(StateFilter(FSMStartShift.recorder))
async def warning_process_train_clean(message: Message):
    await message.answer(
        text="Выберите ответ ниже на появившихся кнопках",
    )


@router_start_shift.callback_query(StateFilter(FSMStartShift.thomas), F.data == "yes")
async def process_thomas_command_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_thomas_on="yes")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы включили Томас?\n\n"
             "➢ Да",
        parse_mode="html",
    )

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {LEXICON_RU[day_of_week]}')

    start_shift_dict = await state.get_data()

    await send_report(
        message=callback.message,
        state=state,
        data=start_shift_dict,
        date=current_date,
        chat_id=cached_places[start_shift_dict['place']],
    )
    await callback.answer()


@router_start_shift.callback_query(StateFilter(FSMStartShift.thomas), F.data == "no")
async def process_thomas_command_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_thomas_on="no")
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Вы включили Томас?\n\n"
             "➢ Нет",
        parse_mode="html",
    )
    await callback.message.answer(
        text="Надо включить!",
    )

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {LEXICON_RU[day_of_week]}')

    start_shift_dict = await state.get_data()

    await send_report(
        message=callback.message,
        state=state,
        data=start_shift_dict,
        date=current_date,
        chat_id=cached_places[start_shift_dict['place']],
    )
    await callback.answer()


@router_start_shift.message(StateFilter(FSMStartShift.thomas))
async def warning_thomas_command(message: Message):
    await message.answer(
        text="Выберите ответ ниже из выпадающего списка!",
        reply_markup=create_yes_no_kb(),
    )

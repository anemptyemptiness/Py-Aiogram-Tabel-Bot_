import time
from typing import Dict, Any, Union
from datetime import datetime, timezone, timedelta

from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyKeyboardRemove, InputMediaPhoto, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext

from fsm.fsm import FSMStartShift
from keyboards.keyboards import create_yes_no_kb, create_cancel_kb, create_places_kb, create_inline_kb, create_names_kb
from middlewares.album_middleware import AlbumsMiddleware
from lexicon.lexicon_ru import LEXICON_RU, rules
from config.config import config, place_chat
from db import DB

router_start_shift = Router()
router_start_shift.message.middleware(middleware=AlbumsMiddleware(2))


async def report(dictionary: Dict[str, Any], date: str, user_id: Union[str, int]) -> str:
    return "📝Открытие смены:\n\n" \
           f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {DB.get_current_name(user_id=user_id)}\n" \
           f"Фото сотрудника: фото_1\n" \
           f"Видео сотрудника: видео_1\n" \
           f"Наличие дефектов: {'no' if dictionary['train_has_defects'] == 'no' else 'фото_2'}\n" \
           f"Проверка колёс: {dictionary['wheels_pumped']}\n" \
           f"Свет и подсветка на паровозе: {dictionary['train_flash']}\n" \
           f"Паровоз чистый: {dictionary['train_clean']}\n" \
           f"Магнитофон включен: {dictionary['is_recorder_on']}\n" \
           f"Томас включен: {dictionary['is_thomas_on']}"


@router_start_shift.message(Command(commands="start_shift"), StateFilter(default_state))
async def process_place_command(message: Message, state: FSMContext):
    await message.answer(text="Выберите точку, на которой Вы сейчас находитесь",
                         reply_markup=await create_places_kb())
    await state.set_state(FSMStartShift.place)


@router_start_shift.message(StateFilter(FSMStartShift.place), F.text)
async def process_start_shift_command(message: Message, state: FSMContext, bot: Bot):
    if message.text in config.places:
        await state.update_data(place=message.text)
        message_entity = await message.answer(text="Сохраняю...",
                                              reply_markup=ReplyKeyboardRemove())
        await bot.delete_message(chat_id=message_entity.chat.id,
                                 message_id=message_entity.message_id)
        await message.answer(text=rules,
                             reply_markup=await create_inline_kb(),
                             parse_mode="html",)
        await state.set_state(FSMStartShift.policy)
    else:
        await message.answer(text="Выберите рабочую точку ниже из выпадающего списка")


@router_start_shift.message(StateFilter(FSMStartShift.place))
async def warning_place_command(message: Message):
    await message.answer(text="Выберите рабочую точку ниже из выпадающего списка",
                         reply_markup=await create_cancel_kb())


@router_start_shift.callback_query(StateFilter(FSMStartShift.policy), F.data == "agree")
async def process_policy_command(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.update_data(policy="agree")
    await callback.answer(text="✅")
    await bot.delete_message(chat_id=callback.message.chat.id,
                             message_id=callback.message.message_id)
    await callback.message.answer(text="Пожалуйста, отправьте Ваше фото на рабочем месте")
    await state.set_state(FSMStartShift.my_photo)


@router_start_shift.message(StateFilter(FSMStartShift.policy))
async def warning_policy_command(message: Message):
    await message.answer(text="Для согласия с правилами нажмите на кнопку под самими правилами!",
                         reply_markup=await create_cancel_kb())


@router_start_shift.message(StateFilter(FSMStartShift.my_photo), F.photo)
async def process_get_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await message.answer(text="Отлично, а теперь пришлите видео паровоза (в окружении)",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMStartShift.my_video)


@router_start_shift.message(StateFilter(FSMStartShift.my_photo))
async def warning_get_photo(message: Message):
    await message.answer(text="Это не похоже на фото, попробуйте ещё раз",
                         reply_markup=await create_cancel_kb())


@router_start_shift.message(StateFilter(FSMStartShift.my_video), F.video)
async def process_get_video(message: Message, state: FSMContext):
    await state.update_data(video=message.video.file_id)
    await message.answer(text="Отлично, а теперь я задам ряд вопросов, на которые Вам предстоит ответить!\n\n"
                              "Проверьте паровоз на наличие дефектов. Есть ли дефекты?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMStartShift.wait_for_defects)


@router_start_shift.message(StateFilter(FSMStartShift.my_video))
async def warning_get_video(message: Message):
    await message.answer(text="Это не похоже на видео, попробуйте еще раз",
                         reply_markup=await create_cancel_kb())


@router_start_shift.message(StateFilter(FSMStartShift.wait_for_defects), F.text == "Да")
async def process_defects_true(message: Message, state: FSMContext):
    await message.answer(text="Пришлите фото дефектов",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMStartShift.photo_of_defects)


@router_start_shift.message(StateFilter(FSMStartShift.wait_for_defects), F.text == "Нет")
async def process_defects_false(message: Message, state: FSMContext):
    await state.update_data(train_has_defects="no")
    await message.answer(text="Вы проверили колёса у паровоза, достаточно ли они накачены?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMStartShift.wheels)


@router_start_shift.message(StateFilter(FSMStartShift.wait_for_defects))
async def warning_process_defects(message: Message):
    await message.answer(text="Выберите ответ ниже на появившихся кнопках")


@router_start_shift.message(StateFilter(FSMStartShift.photo_of_defects))
async def process_need_to_photo_of_defects(message: Message, state: FSMContext):
    if message.photo:
        if 'train_has_defects' not in await state.get_data():
            await state.update_data(train_has_defects=[message.photo[-1].file_id])

        await message.answer(text="Вы проверили колёса у паровоза, достаточно ли они накачены?",
                             reply_markup=await create_yes_no_kb())
        await state.set_state(FSMStartShift.wheels)
    else:
        await message.answer(text="Это не похоже на фото, отправьте фото дефектов",
                             reply_markup=await create_cancel_kb())


@router_start_shift.message(StateFilter(FSMStartShift.wheels), F.text == "Да")
async def process_wheels_command_yes(message: Message, state: FSMContext):
    await state.update_data(wheels_pumped="yes")
    await message.answer(text="Включили ли Вы свет и подсветку на паровозе?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMStartShift.train_flash)


@router_start_shift.message(StateFilter(FSMStartShift.wheels), F.text == "Нет")
async def process_wheels_command_no(message: Message, state: FSMContext):
    await state.update_data(wheels_pumped="no")
    await message.answer(text="Нужно подкачать колёса!\n\nВы включили свет и подсветку на паровозе?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMStartShift.train_flash)


@router_start_shift.message(StateFilter(FSMStartShift.wheels))
async def warning_process_wheels(message: Message):
    await message.answer(text="Выберите ответ ниже на появившихся кнопках")


@router_start_shift.message(StateFilter(FSMStartShift.train_flash), F.text == "Да")
async def process_train_flash_command_yes(message: Message, state: FSMContext):
    await state.update_data(train_flash="yes")
    await message.answer(text="Вы протёрли паровоз от пыли?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMStartShift.train_clean)


@router_start_shift.message(StateFilter(FSMStartShift.train_flash), F.text == "Нет")
async def process_train_flash_command_no(message: Message, state: FSMContext):
    await state.update_data(train_flash="no")
    await message.answer(text="Нужно включить подсветку!\n\nВы протёрли паровоз от пыли?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMStartShift.train_clean)


@router_start_shift.message(StateFilter(FSMStartShift.train_flash))
async def warning_process_train_flash(message: Message):
    await message.answer(text="Выберите ответ ниже на появившихся кнопках")


@router_start_shift.message(StateFilter(FSMStartShift.train_clean), F.text == "Да")
async def process_train_clean_command_yes(message: Message, state: FSMContext):
    await state.update_data(train_clean="yes")
    await message.answer(text="Вы включили магнитофон?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMStartShift.recorder)


@router_start_shift.message(StateFilter(FSMStartShift.train_clean), F.text == "Нет")
async def process_train_clean_command_no(message: Message, state: FSMContext):
    await state.update_data(train_clean="no")
    await message.answer(text="Нужно обязательно протереть паровоз!\n\nВы включили магнитофон?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMStartShift.recorder)


@router_start_shift.message(StateFilter(FSMStartShift.recorder), F.text == "Да")
async def process_recorder_command_yes(message: Message, state: FSMContext):
    await state.update_data(is_recorder_on="yes")
    await message.answer(text="Вы включили Томас?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMStartShift.thomas)


@router_start_shift.message(StateFilter(FSMStartShift.recorder), F.text == "Нет")
async def process_recorder_command_no(message: Message, state: FSMContext):
    await state.update_data(is_recorder_on="no")
    await message.answer(text="Вставьте флешку и включите!\n\nВы включили Томас?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMStartShift.thomas)


@router_start_shift.message(StateFilter(FSMStartShift.recorder))
async def warning_process_train_clean(message: Message):
    await message.answer(text="Выберите ответ ниже на появившихся кнопках")


@router_start_shift.message(StateFilter(FSMStartShift.thomas), F.text == "Да")
async def process_thomas_command_yes(message: Message, state: FSMContext):
    await state.update_data(is_thomas_on="yes")

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {LEXICON_RU[day_of_week]}')

    start_shift_dict = await state.get_data()

    try:
        await message.bot.send_message(chat_id=place_chat[start_shift_dict['place']],
                                       text=await report(start_shift_dict, current_date, message.from_user.id))
        await message.bot.send_photo(chat_id=place_chat[start_shift_dict['place']],
                                     photo=start_shift_dict['photo'],
                                     caption='Фото сотрудника')
        await message.bot.send_video(chat_id=place_chat[start_shift_dict['place']],
                                     video=start_shift_dict['video'],
                                     caption='Видео сотрудника')

        if start_shift_dict['train_has_defects'] != "no":
            media_defects = [InputMediaPhoto(media=photo_file_id,
                                             caption="Фото дефектов" if i == 0 else "")
                             for i, photo_file_id in enumerate(start_shift_dict['train_has_defects'])]

            await message.bot.send_media_group(chat_id=place_chat[start_shift_dict['place']],
                                               media=media_defects)
        await message.answer(text="Отлично! Отчёт сформирован... Отправляю начальству!",
                             reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.bot.send_message(text=f"Start shift report error: {e}\n"
                                            f"User_id: {message.from_user.id}",
                                       chat_id=config.admins[0])
        await message.answer(text="Упс... что-то пошло не так, сообщите руководству!")
    finally:
        await state.clear()


@router_start_shift.message(StateFilter(FSMStartShift.thomas), F.text == "Нет")
async def process_thomas_command_no(message: Message, state: FSMContext):
    await state.update_data(is_thomas_on="no")
    await message.answer(text="Надо включить!",
                         reply_markup=await create_cancel_kb())

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    current_date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {LEXICON_RU[day_of_week]}')

    start_shift_dict = await state.get_data()

    try:
        await message.bot.send_message(chat_id=place_chat[start_shift_dict['place']],
                                       text=await report(start_shift_dict, current_date, message.from_user.id))
        await message.bot.send_photo(chat_id=place_chat[start_shift_dict['place']],
                                     photo=start_shift_dict['photo'],
                                     caption='Фото сотрудника')
        await message.bot.send_video(chat_id=place_chat[start_shift_dict['place']],
                                     video=start_shift_dict['video'],
                                     caption='Видео сотрудника')

        if start_shift_dict['train_has_defects'] != "no":
            media_defects = [InputMediaPhoto(media=photo_file_id,
                                             caption="Фото дефектов" if i == 0 else "")
                             for i, photo_file_id in enumerate(start_shift_dict['train_has_defects'])]

            await message.bot.send_media_group(chat_id=place_chat[start_shift_dict['place']],
                                               media=media_defects)
        await message.answer(text="Отлично! Отчёт сформирован... Отправляю начальству!",
                             reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.bot.send_message(text=f"Start shift report error: {e}\n"
                                            f"User_id: {message.from_user.id}",
                                       chat_id=config.admins[0],
                                       reply_markup=ReplyKeyboardRemove())
        await message.answer(text="Упс... что-то пошло не так, сообщите руководству!",
                             reply_markup=ReplyKeyboardRemove())
    finally:
        await state.clear()


@router_start_shift.message(StateFilter(FSMStartShift.thomas))
async def warning_thomas_command(message: Message):
    await message.answer(text="Выберите ответ ниже из выпадающего списка!",
                         reply_markup=await create_yes_no_kb())

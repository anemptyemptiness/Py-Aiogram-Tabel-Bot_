from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.filters import StateFilter, Command

import db
from fsm.fsm import FSMFinishShift
from lexicon.lexicon_ru import LEXICON_RU
from keyboards.keyboards import create_cancel_kb, create_yes_no_kb, create_places_kb
from middlewares.album_middleware import AlbumsMiddleware
from config.config import place_chat, config

router_finish = Router()
router_finish.message.middleware(middleware=AlbumsMiddleware(2))


async def report(dictionary: dict, date) -> str:
    return f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n" \
           f"Имя: {dictionary['name']}\n" \
           f"Количество посетителей: {dictionary['visitors']}\n\n" \
           f"Были ли льготники: {'yes' if dictionary['beneficiaries'] != 'no' else 'no'}\n" \
           f"Паровоз поставлен на зарядку: {dictionary['charge']}\n" \
           f"Общая выручка: {dictionary['summary']}\n" \
           f"Наличные: {dictionary['cash']}\n" \
           f"Безнал: {dictionary['online_cash']}\n" \
           f"QR-код: {dictionary['qr_code']}\n" \
           f"Расход: {dictionary['expenditure']}\n" \
           f"Зарплата: {dictionary['salary']}\n" \
           f"Инкассация: {dictionary['encashment']}\n"


@router_finish.message(Command(commands="finish_shift"), StateFilter(default_state))
async def process_place_command(message: Message, state: FSMContext):
    await message.answer(text="Выберите точку, на которой Вы сейчас находитесь",
                         reply_markup=await create_places_kb())
    await state.set_state(FSMFinishShift.place)


@router_finish.message(StateFilter(FSMFinishShift.place), F.text)
async def process_finish_start_command(message: Message, state: FSMContext):
    if message.text in config.places:
        await state.update_data(place=message.text)
        await message.answer(text="Сколько было посетителей за сегодня? (Пришлите ответ числом)",
                             reply_markup=await create_cancel_kb())
        await state.set_state(FSMFinishShift.count_of_visitors)
    else:
        await message.answer(text="Выберите рабочую точку ниже из выпадающего списка")


@router_finish.message(StateFilter(FSMFinishShift.place))
async def warning_place_command(message: Message):
    await message.answer(text="Выберите рабочую точку ниже из выпадающего списка",
                         reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.count_of_visitors), F.text.isdigit())
async def process_visitors_command(message: Message, state: FSMContext):
    await state.update_data(visitors=int(message.text))
    await message.answer(text="Были ли льготники за сегодня?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMFinishShift.beneficiaries)


@router_finish.message(StateFilter(FSMFinishShift.count_of_visitors))
async def warning_visitors_command(message: Message):
    await message.answer(text="Пришлите количество посетителей <b>числом</b>",
                         parse_mode="html",
                         reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.beneficiaries), F.text == "Да")
async def process_beneficiaries_command_yes(message: Message, state: FSMContext):
    await state.update_data(beneficiaries="yes")
    await message.answer(text="Прикрепите подтвреждающее фото (справка, паспорт родителей)",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.photo_of_beneficiaries)


@router_finish.message(StateFilter(FSMFinishShift.beneficiaries), F.text == "Нет")
async def process_beneficiaries_command_no(message: Message, state: FSMContext):
    await state.update_data(beneficiaries="no")
    await message.answer(text="Введите общую выручку за сегодня",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.summary)


@router_finish.message(StateFilter(FSMFinishShift.beneficiaries))
async def warning_beneficiaries_command(message: Message):
    await message.answer(text="Выберите ответ ниже на появившихся кнопках")


@router_finish.message(StateFilter(FSMFinishShift.photo_of_beneficiaries))
async def process_photo_of_beneficiaries_command(message: Message, state: FSMContext):
    if message.photo:
        if 'photo_of_beneficiaries' not in await state.get_data():
            await state.update_data(photo_of_beneficiaries=[message.photo[-1].file_id])

        await message.answer(text="Введите общую выручку за сегодня",
                             reply_markup=await create_cancel_kb())
        await state.set_state(FSMFinishShift.summary)
    else:
        await message.answer(text="Это не похоже на фото, отправьте фото чеков",
                             reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.summary), F.text)
async def process_summary_command(message: Message, state: FSMContext):
    await state.update_data(summary=message.text)
    await message.answer(text="Введите сумму наличных за сегодня",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.cash)


@router_finish.message(StateFilter(FSMFinishShift.summary))
async def warning_summary_command(message: Message):
    await message.answer(text="Введите общую сумму числом!",
                         reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.cash), F.text)
async def process_cash_command(message: Message, state: FSMContext):
    await state.update_data(cash=message.text)
    await message.answer(text="Введите сумму безнала за сегодня",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.online_cash)


@router_finish.message(StateFilter(FSMFinishShift.cash))
async def warning_cash_command(message: Message):
    await message.answer(text="Введите сумму наличных числом!",
                         reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.online_cash), F.text)
async def process_online_cash_command(message: Message, state: FSMContext):
    await state.update_data(online_cash=message.text)
    await message.answer(text="Введите сумму оплаты по QR-коду за сегодня",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.qr_code)


@router_finish.message(StateFilter(FSMFinishShift.online_cash))
async def warning_online_cash_command(message: Message):
    await message.answer(text="Введите сумму безнала числом!",
                         reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.qr_code), F.text)
async def process_qr_code_command(message: Message, state: FSMContext):
    await state.update_data(qr_code=message.text)
    await message.answer(text="Введите сумму расхода за сегодня",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.expenditure)


@router_finish.message(StateFilter(FSMFinishShift.qr_code))
async def warning_qr_code_command(message: Message):
    await message.answer(text="Введите сумму по QR-коду числом!",
                         reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.expenditure), F.text)
async def process_expenditure_command(message: Message, state: FSMContext):
    await state.update_data(expenditure=message.text)
    await message.answer(text="Введите сумму, сколько Вы взяли сегодня зарплатой\n\n"
                              "Если Вы не брали сегодня зарплату, то введите 0",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.salary)


@router_finish.message(StateFilter(FSMFinishShift.expenditure))
async def warning_expenditure_command(message: Message):
    await message.answer(text="Введите сумму расхода числом!",
                         reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.salary), F.text.isdigit())
async def process_salary_command(message: Message, state: FSMContext):
    await state.update_data(salary=message.text)
    await message.answer(text="Введите сумму инкассации\n\n"
                              "Если нет инкассации - напишите 0",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.encashment)


@router_finish.message(StateFilter(FSMFinishShift.salary))
async def warning_salary_command(message: Message):
    await message.answer(text="Введите зарплату числом!",
                         reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.encashment), F.text)
async def process_encashment_command(message: Message, state: FSMContext):
    await state.update_data(encashment=message.text)
    await message.answer(text="Прикрепите чеки и необходимые фотографии за смену "
                              "(чеки о закрытии смены, оплата QR-кода, чек расхода)",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.necessary_photos)


@router_finish.message(StateFilter(FSMFinishShift.encashment))
async def warning_encashment_command(message: Message):
    await message.answer(text="Пришлите сумму инкассации числом!",
                         reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.necessary_photos))
async def process_necessary_photos_command(message: Message, state: FSMContext):
    if message.photo:
        if 'necessary_photos' not in await state.get_data():
            await state.update_data(necessary_photos=[message.photo[-1].file_id])

        await message.answer(text="Вы поставили паровоз на зарядку?",
                             reply_markup=await create_yes_no_kb())
        await state.set_state(FSMFinishShift.charge)
    else:
        await message.answer(text="Это не похоже на фото, отправьте фото!",
                             reply_markup=await create_cancel_kb())


@router_finish.message(StateFilter(FSMFinishShift.charge), F.text == "Да")
async def process_charge_command_yes(message: Message, state: FSMContext):
    await state.update_data(charge="yes")
    await message.answer(text="Прикрепите видео аккумулятора и внешнего вида поезда!",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.charge_video)


@router_finish.message(StateFilter(FSMFinishShift.charge), F.text == "Нет")
async def process_charge_command_no(message: Message, state: FSMContext):
    await state.update_data(charge="no")
    await message.answer(text="Поставьте на зарядку и прикрепите видео аккумулятора и внешнего вида поезда!",
                         reply_markup=await create_cancel_kb())
    await state.set_state(FSMFinishShift.charge_video)


@router_finish.message(StateFilter(FSMFinishShift.charge))
async def warning_charge_command(message: Message):
    await message.answer(text="Выберите ответ ниже на появившихся кнопках")


@router_finish.message(StateFilter(FSMFinishShift.charge_video))
async def process_charge_video_command(message: Message, state: FSMContext):
    if message.video:
        if 'charge_video' not in await state.get_data():
            await state.update_data(charge_video=[message.video.file_id])
        finish_shift_dict = await state.get_data()
        finish_shift_dict['name'] = db.DB.get_current_name(message.from_user.id)

        day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
        date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d-%m-%Y - {LEXICON_RU[day_of_week]}')

        try:
            if 'photo_of_beneficiaries' in finish_shift_dict:
                media_beneficiaries = [InputMediaPhoto(media=photo_file_id,
                                                       caption="Фото льготников" if i == 0 else "")
                                       for i, photo_file_id in enumerate(finish_shift_dict['photo_of_beneficiaries'])]
                await message.bot.send_media_group(chat_id=place_chat[finish_shift_dict['place']],
                                                   media=media_beneficiaries)

            media_necessary = [InputMediaPhoto(media=photo_file_id,
                                               caption="Чеки и необходимые фото за смену" if i == 0 else "")
                               for i, photo_file_id in enumerate(finish_shift_dict['necessary_photos'])]

            video_necessary = [InputMediaVideo(media=video_file_id,
                                               caption="Видео аккумулятора и внешнего вида поезда" if i == 0 else "")
                               for i, video_file_id in enumerate(finish_shift_dict['charge_video'])]

            await message.bot.send_message(chat_id=place_chat[finish_shift_dict['place']],
                                           text=await report(finish_shift_dict, date=date))

            await message.bot.send_media_group(chat_id=place_chat[finish_shift_dict['place']],
                                               media=media_necessary)
            await message.bot.send_media_group(chat_id=place_chat[finish_shift_dict['place']],
                                               media=video_necessary)

            db.DB.set_data(
                user_id=message.from_user.id,
                date=datetime.now(tz=timezone(timedelta(hours=3.0))).strftime("%d.%m.%Y"),
                place=finish_shift_dict['place'],
                count=finish_shift_dict['visitors']
            )

            await message.answer(text="Отлично! Формирую отчёт...\nОтправляю начальству!",
                                 reply_markup=ReplyKeyboardRemove())

        except Exception as e:
            await message.bot.send_message(text=f"Finish shift report error: {e}\n"
                                                f"User_id: {message.from_user.id}",
                                           chat_id=config.admins[0],
                                           reply_markup=ReplyKeyboardRemove())
            await message.answer(text="Упс... что-то пошло не так, сообщите руководству!",
                                 reply_markup=ReplyKeyboardRemove())
        finally:
            await state.clear()

    else:
        await message.answer(text="Это не похоже на видео, прикрепите видео аккумулятора и внешнего вида поезда!",
                             reply_markup=await create_cancel_kb())

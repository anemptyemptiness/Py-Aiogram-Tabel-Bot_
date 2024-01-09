from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command
from aiogram.fsm.state import default_state

from config.config import config
from lexicon.lexicon_ru import LEXICON_RU
from fsm.fsm import FSMAttractionsCheck
from keyboards.keyboards import create_yes_no_kb, create_places_kb, create_cancel_kb
from config.config import place_chat

router_attractions = Router()


async def report(dictionary: dict, date) -> str:
    return f"Дата: {date}\n" \
           f"Точка: {dictionary['place']}\n\n" \
           f"Купюроприемники рабочие: {dictionary['bill_acceptors']}\n\n" \
           f"Номера нерабочих купюроприемников: <em>{dictionary['defects_on_bill_acceptors'] if dictionary['bill_acceptors'] == 'no' else 'None'}</em>\n\n" \
           f"Дефекты на аттракционах: {dictionary['attracts']}\n\n" \
           f"Номера аттракционов с дефектами: <em>{dictionary['defects_on_attracts'] if dictionary['attracts'] == 'yes' else 'None'}</em>"


@router_attractions.message(Command(commands="check_attractions"), StateFilter(default_state))
async def process_place_command(message: Message, state: FSMContext):
    await state.set_state(FSMAttractionsCheck.place)
    await message.answer(text="Выберите точку, на которой Вы сейчас находитесь",
                         reply_markup=await create_places_kb())


@router_attractions.message(StateFilter(FSMAttractionsCheck.place), F.text)
async def process_bill_acceptor_command(message: Message, state: FSMContext):
    if message.text in config.places:
        await state.update_data(place=message.text)
        await message.answer(text="Все купюроприемники работают?",
                             reply_markup=await create_yes_no_kb())
        await state.set_state(FSMAttractionsCheck.bill_acceptor)
    else:
        await message.answer(text="Выберите рабочую точку ниже из выпадающего списка")

@router_attractions.message(StateFilter(FSMAttractionsCheck.place))
async def warning_place_command(message: Message):
    await message.answer(text="Выберите рабочую точку ниже из выпадающего списка",
                         reply_markup=await create_cancel_kb())


@router_attractions.message(StateFilter(FSMAttractionsCheck.bill_acceptor), F.text == "Да")
async def process_bill_acceptor_command_yes(message: Message, state: FSMContext):
    await state.update_data(bill_acceptors="yes")
    await message.answer(text="Были ли обнаружены дефекты на аттракционах?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMAttractionsCheck.attracts)


@router_attractions.message(StateFilter(FSMAttractionsCheck.bill_acceptor), F.text == "Нет")
async def process_bill_acceptor_command_no(message: Message, state: FSMContext):
    await state.update_data(bill_acceptors="no")
    await message.answer(text="Напишите номера (наименование) неработающих купюроприемников в <b>одном</b> сообщении!",
                         reply_markup=ReplyKeyboardRemove(),
                         parse_mode="html")
    await state.set_state(FSMAttractionsCheck.defects_on_bill_acceptor)


@router_attractions.message(StateFilter(FSMAttractionsCheck.bill_acceptor))
async def warning_bill_accepton_command(message: Message):
    await message.answer(text="Выберите ответ ниже на появившихся кнопках")


@router_attractions.message(StateFilter(FSMAttractionsCheck.defects_on_bill_acceptor), F.text)
async def process_defects_on_bill_command(message: Message, state: FSMContext):
    await state.update_data(defects_on_bill_acceptors=message.text)
    await message.answer(text="Были ли обнаружены дефекты на аттракционах?",
                         reply_markup=await create_yes_no_kb())
    await state.set_state(FSMAttractionsCheck.attracts)


@router_attractions.message(StateFilter(FSMAttractionsCheck.defects_on_bill_acceptor))
async def warning_defects_on_bill_command(message: Message):
    await message.answer(text="Введите номера неработающих купюроприемников <b>текстом</b> в <b>одном</b> сообщении",
                         reply_markup=ReplyKeyboardRemove(),
                         parse_mode="html")


@router_attractions.message(StateFilter(FSMAttractionsCheck.attracts), F.text == "Да")
async def process_attracts_command_yes(message: Message, state: FSMContext):
    await state.update_data(attracts="yes")
    await message.answer(text="Напишите аттракцион и опишите его дефект в <b>одном</b> сообщении",
                         reply_markup=ReplyKeyboardRemove(),
                         parse_mode="html")
    await state.set_state(FSMAttractionsCheck.defects_on_attracts)


@router_attractions.message(StateFilter(FSMAttractionsCheck.attracts), F.text == "Нет")
async def process_attracts_command_no(message: Message, state: FSMContext):
    await state.update_data(attracts="no")

    check_attractions_dict = await state.get_data()
    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {LEXICON_RU[day_of_week]}')

    try:
        await message.bot.send_message(chat_id=place_chat[check_attractions_dict['place']],
                                       text=await report(check_attractions_dict, date=date),
                                       parse_mode="html")

        await message.answer(text="Отлично, отчёт сформирован...\nОтправляю начальству!",
                             reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.bot.send_message(text=f"Check attractions report error: {e}\n"
                                            f"User_id: {message.from_user.id}",
                                       chat_id=config.config.config.admins[0],
                                       reply_markup=ReplyKeyboardRemove())
        await message.answer(text="Упс... что-то пошло не так, сообщите руководству!",
                             reply_markup=ReplyKeyboardRemove())
    finally:
        await state.clear()


@router_attractions.message(StateFilter(FSMAttractionsCheck.attracts))
async def warning_attracts_command(message: Message):
    await message.answer(text="Выберите ответ ниже на появившихся кнопках")


@router_attractions.message(StateFilter(FSMAttractionsCheck.defects_on_attracts), F.text)
async def process_defects_on_attracts_command(message: Message, state: FSMContext):
    await state.update_data(defects_on_attracts=message.text)

    check_attractions_dict = await state.get_data()

    day_of_week = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime('%A')
    date = datetime.now(tz=timezone(timedelta(hours=3.0))).strftime(f'%d/%m/%Y - {LEXICON_RU[day_of_week]}')

    try:
        await message.bot.send_message(chat_id=place_chat[check_attractions_dict['place']],
                                       text=await report(check_attractions_dict, date=date),
                                       parse_mode="html")

        await message.answer(text="Отлично, отчёт сформирован...\nОтправляю начальству!",
                             reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.bot.send_message(text=f"Check attractions report error: {e}\n"
                                            f"User_id: {message.from_user.id}",
                                       chat_id=config.config.config.admins[0],
                                       reply_markup=ReplyKeyboardRemove())
        await message.answer(text="Упс... что-то пошло не так, сообщите руководству!",
                             reply_markup=ReplyKeyboardRemove())
    finally:
        await state.clear()


@router_attractions.message(StateFilter(FSMAttractionsCheck.defects_on_attracts))
async def warning_process_defects_on_attrs_command(message: Message):
    await message.answer(text="Напишите аттракцион и опишите его дефект в <b>одном</b> сообщении",
                         reply_markup=ReplyKeyboardRemove(),
                         parse_mode="html")

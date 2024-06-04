from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.keyboards.adm_keyboard import create_admin_kb, check_add_place
from src.keyboards.keyboard import create_cancel_kb
from src.fsm.fsm import FSMAdmin
from src.handlers.admin_handler.adding.add_employee import router_admin
from src.db.queries.dao.dao import AsyncOrm
from src.db import cached_places, cached_chat_ids

router_add_place = Router()
router_admin.include_router(router_add_place)


@router_add_place.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "add_place")
async def process_add_place_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Чтобы добавить рабочую точку, Вам нужно "
             "написать её название\n\n"
             "<em>Например: Мега Белая Дача</em>\n\n"
             "Пожалуйста, пишите название корректно",
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.add_place)


@router_admin.message(StateFilter(FSMAdmin.add_place), F.text)
async def process_collect_place_command(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer(
        text="Теперь введите id чата, куда Бот будет присылать отчёты сотрудников\n\n"
             "Сервис по поиску id - @getmyid_bot\n\n"
             "<em>Пример id: -1009284727</em>",
        parse_mode="html",
    )
    await state.set_state(FSMAdmin.add_place_id)


@router_admin.message(StateFilter(FSMAdmin.add_place))
async def warning_collect_place_command(message: Message):
    await message.answer(
        text="Чтобы добавить рабочую точку, Вам нужно "
             "написать её <b>название</b>\n\n"
             "<em>Например: Мега Белая Дача</em>\n\n"
             "Пожалуйста, пишите название корректно",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )


@router_admin.message(StateFilter(FSMAdmin.add_place_id), F.text)
async def process_collect_place_id_chat_command(message: Message, state: FSMContext):
    await state.update_data(chat_id=int(message.text))

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"название: {data['title']}\n"
             f"chat_id: {data['chat_id']}\n\n"
             f"Всё ли корректно?",
        reply_markup=check_add_place(),
    )
    await state.set_state(FSMAdmin.check_place)


@router_admin.message(StateFilter(FSMAdmin.add_place_id))
async def warning_collect_place_id_chat_command(message: Message):
    await message.answer(
        text="Теперь введите id чата <b>ЧИСЛОМ</b>, куда Бот будет присылать отчёты сотрудников\n\n"
             "Сервис по поиску id - @getmyid_bot\n\n"
             "<em>Пример id: -1009284727</em>",
        parse_mode="html",
    )


@router_admin.callback_query(StateFilter(FSMAdmin.check_place), F.data == "access_place")
async def process_accept_place_command(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await AsyncOrm.add_place(
        title=data["title"],
        chat_id=data["chat_id"],
    )
    cached_places[data["title"]] = data["chat_id"]
    if data["chat_id"] not in cached_chat_ids:
        cached_chat_ids.append(data["chat_id"])

    await callback.message.answer(
        text=f'Рабочая точка "{data["title"]}" с chat_id={data["chat_id"]} <b>успешно</b> добавлена!',
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="html",
    )
    await callback.message.answer(
        text="Админская панель:",
        reply_markup=create_admin_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.in_adm)


@router_admin.callback_query(StateFilter(FSMAdmin.check_place), F.data == "rename_place")
async def process_rename_place_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите новое <b>название</b> рабочей точки\n\n"
             "<em>Например: Мега Белая Дача</em>\n\n"
             "Пожалуйста, пишите название корректно",
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.rename_place)


@router_admin.message(StateFilter(FSMAdmin.rename_place), F.text)
async def process_accept_renamed_place_command(message: Message, state: FSMContext):
    await state.update_data(title=message.text)

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"название: {data['title']}\n"
             f"chat_id: {data['chat_id']}\n\n"
             f"Всё ли корректно?",
        reply_markup=check_add_place(),
    )
    await state.set_state(FSMAdmin.check_place)


@router_admin.message(StateFilter(FSMAdmin.rename_place))
async def warning_accept_renamed_place_command(message: Message):
    await message.answer(
        text="Введите новое <b>название</b> рабочей точки\n\n"
             "<em>Например: Мега Белая Дача</em>\n\n"
             "Пожалуйста, пишите название корректно",
        parse_mode="html",
    )


@router_admin.callback_query(StateFilter(FSMAdmin.check_place), F.data == "reid_place")
async def process_reid_place_chat_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите новый <b>id чата</b> рабочей точки, куда Бот будет отправлять отчёты сотрудников\n\n"
             "Сервис по поиску chat_id - @getmyid_bot\n\n"
             "<em>Пример id чата: -1009284727</em>",
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.reid_place)


@router_admin.message(StateFilter(FSMAdmin.reid_place), F.text)
async def process_accept_reid_chat_command(message: Message, state: FSMContext):
    await state.update_data(chat_id=int(message.text))

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"название: {data['title']}\n"
             f"chat_id: {data['chat_id']}\n\n"
             f"Всё ли корректно?",
        reply_markup=check_add_place(),
    )
    await state.set_state(FSMAdmin.check_place)


@router_admin.message(StateFilter(FSMAdmin.reid_place))
async def warning_reid_place_chat_command(message: Message):
    await message.answer(
        text="Введите новый id чата <b>ЧИСЛОМ</b>\n\n"
             "Сервис по поиску chat_id - @getmyid_bot\n\n"
             "<em>Пример id чата: -1009284727</em>",
        parse_mode="html",
    )
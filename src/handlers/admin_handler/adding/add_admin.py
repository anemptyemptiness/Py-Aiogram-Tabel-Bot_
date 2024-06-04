from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.keyboards.adm_keyboard import create_admin_kb, check_add_admin
from src.keyboards.keyboard import create_cancel_kb
from src.fsm.fsm import FSMAdmin
from src.handlers.admin_handler.adding.add_employee import router_admin
from src.db.queries.dao.dao import AsyncOrm
from src.db import cached_admins, cached_admins_fullname_and_id, cached_employees, cached_employees_fullname_and_id

router_add_adm = Router()
router_admin.include_router(router_add_adm)


@router_add_adm.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "add_admin")
async def process_add_admin_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Чтобы добавить нового администратора, Вам нужно прислать мне его id телеграм\n\n"
             "Сервис по поиску id - @getmyid_bot\n\n"
             "Отправьте id одним сообщением!\n"
             "<em>Например: 293982824</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.add_admin_id)


@router_add_adm.message(StateFilter(FSMAdmin.add_admin_id), F.text.isdigit())
async def process_add_admin_id_commnad(message: Message, state: FSMContext):
    await state.update_data(admin_id=int(message.text.strip()))
    await message.answer(
        text="Теперь нужно ввести имя и фамилию администратора\n\n"
             "<em>Например: Иванов Иван</em>",
        parse_mode="html",
    )
    await state.set_state(FSMAdmin.add_admin_name)


@router_add_adm.message(StateFilter(FSMAdmin.add_admin_id))
async def warning_add_admin_id_command(message: Message):
    await message.answer(
        text="Чтобы добавить нового администратора, Вам нужно прислать мне его id телеграм\n\n"
             "Сервис по поиску id - @getmyid_bot\n\n"
             "Отправьте id одним сообщением!\n"
             "<em>Например: 293982824</em>",
        parse_mode="html",
    )


@router_add_adm.message(StateFilter(FSMAdmin.add_admin_name), F.text)
async def process_add_admin_name_command(message: Message, state: FSMContext):
    await state.update_data(admin_name=message.text.strip())
    await message.answer(
        text="А теперь введите <b>username</b> администратора\n\n"
             "Чтобы узнать юзернейм, откройте диалог с пользователем, "
             "нажмите на его имя в верхней части экрана. "
             "Откроется окно с описанием профиля. Возле фотографии крупными "
             "буквами указано публичное имя. Ниже указан телефон, "
             "за ним — уникальный юзернейм (username)\n\n"
             "Если username нет или Вам не удалось его найти, напишите "
             "номер телефона пользователя",
        parse_mode="html",
    )
    await state.set_state(FSMAdmin.add_admin_username)


@router_add_adm.message(StateFilter(FSMAdmin.add_admin_name))
async def warning_add_admin_name_command(message: Message):
    await message.answer(
        text="Нужно ввести имя и фамилию администратора\n\n"
             "<em>Например: Иванов Иван</em>",
        parse_mode="html",
    )


@router_add_adm.message(StateFilter(FSMAdmin.add_admin_username), F.text)
async def process_add_admin_phone_command(message: Message, state: FSMContext):
    await state.update_data(admin_username=message.text)

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"id: {data['admin_id']}\n"
             f"имя: {data['admin_name']}\n"
             f"username(или номер): {data['admin_username']}\n\n"
             "Всё ли корректно?",
        reply_markup=check_add_admin(),
    )
    await state.set_state(FSMAdmin.check_admin)


@router_add_adm.message(StateFilter(FSMAdmin.add_admin_username))
async def warning_add_admin_username_command(message: Message):
    await message.answer(
        text="введите <b>username</b> администратора\n\n"
             "Чтобы узнать юзернейм, откройте диалог с пользователем, "
             "нажмите на его имя в верхней части экрана. "
             "Откроется окно с описанием профиля. Возле фотографии крупными "
             "буквами указано публичное имя. Ниже указан телефон, "
             "за ним — уникальный юзернейм (username)\n\n"
             "Если username нет или Вам не удалось его найти, напишите "
             "номер телефона пользователя",
        parse_mode="html",
    )


@router_add_adm.callback_query(StateFilter(FSMAdmin.check_admin), F.data == "access_admin")
async def process_access_admin_command(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await AsyncOrm.add_admin(
        fullname=data["admin_name"],
        user_id=data["admin_id"],
        username=data["admin_username"],
    )
    if data["admin_id"] not in cached_admins:
        cached_admins.append(data["admin_id"])
        cached_admins_fullname_and_id.append((data["admin_name"], data["admin_id"]))
    if data["admin_id"] in cached_employees:
        cached_employees.remove(data["admin_id"])
        cached_employees_fullname_and_id.remove((data["admin_name"], data["admin_id"]))

    await callback.message.answer(
        text=f"Администратор <b>{data['admin_name']}</b> с id=<b>{data['admin_id']}</b> "
             f"и username=<b>{data['admin_username']}</b> успешно добавлен!",
        parse_mode="html",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.message.answer(
        text="Админская панель:",
        reply_markup=create_admin_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.in_adm)


@router_add_adm.callback_query(StateFilter(FSMAdmin.check_admin), F.data == "rename_admin")
async def process_rename_admin_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите новое <b>имя и фамилию</b> администратора\n\n"
             "<em>Например: Иван Иванов</em>",
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.rename_admin)


@router_add_adm.callback_query(StateFilter(FSMAdmin.check_admin), F.data == "reid_admin")
async def process_reid_admin_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите новый <b>id</b> администратора\n\n"
             "Сервис по поиску id - @getmyid_bot\n\n"
             "Отправьте id одним сообщением!\n"
             "<em>Например: 293982824</em>",
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.reid_admin)


@router_add_adm.callback_query(StateFilter(FSMAdmin.check_admin), F.data == "reusername_admin")
async def process_reusername_admin_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите новый <b>username</b> администратора (или номер)\n\n"
             "<em>Например: @username</em>",
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.reusername_admin)


@router_add_adm.message(StateFilter(FSMAdmin.rename_admin), F.text)
async def process_new_name_admin_command(message: Message, state: FSMContext):
    await state.update_data(admin_name=message.text.strip())

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"id: {data['admin_id']}\n"
             f"имя: {data['admin_name']}\n"
             f"username(или номер): {data['admin_username']}\n\n"
             "Всё корректно?",
        reply_markup=check_add_admin(),
    )
    await state.set_state(FSMAdmin.check_admin)


@router_add_adm.message(StateFilter(FSMAdmin.rename_admin))
async def warning_new_name_admin_command(message: Message):
    await message.answer(
        text="Введите новое <b>имя и фамилию</b> администратора\n\n"
             "<em>Например: Иван Иванов</em>",
        parse_mode="html",
    )


@router_add_adm.message(StateFilter(FSMAdmin.reid_admin), F.text.isdigit())
async def process_new_id_admin_command(message: Message, state: FSMContext):
    await state.update_data(admin_id=int(message.text))

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"id: {data['admin_id']}\n"
             f"имя: {data['admin_name']}\n"
             f"username(или номер): {data['admin_username']}\n\n"
             "Всё корректно?",
        reply_markup=check_add_admin(),
    )
    await state.set_state(FSMAdmin.check_admin)


@router_add_adm.message(StateFilter(FSMAdmin.reid_admin))
async def warning_new_id_admin_command(message: Message):
    await message.answer(
        text="Введите новый <b>id</b> администратора\n\n"
             "Сервис по поиску id - @getmyid_bot\n\n"
             "Отправьте id одним сообщением!\n"
             "<em>Например: 293982824</em>",
        parse_mode="html",
    )


@router_add_adm.message(StateFilter(FSMAdmin.reusername_admin), F.text)
async def process_new_username_admin_command(message: Message, state: FSMContext):
    await state.update_data(admin_username=message.text)

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"id: {data['admin_id']}\n"
             f"имя: {data['admin_name']}\n"
             f"username(или номер): {data['admin_username']}\n\n"
             "Всё корректно?",
        reply_markup=check_add_admin(),
    )
    await state.set_state(FSMAdmin.check_admin)


@router_add_adm.message(StateFilter(FSMAdmin.reusername_admin))
async def warning_new_username_admin_command(message: Message):
    await message.answer(
        text="Введите новый <b>username</b> администратора (или номер)\n\n"
             "<em>Например: @username</em>",
        parse_mode="html",
    )
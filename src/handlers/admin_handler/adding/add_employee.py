from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import default_state
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from src.filters.is_admin import IsAdminFilterMessage, IsNotAdminFilterCallback
from src.keyboards.adm_keyboard import create_admin_kb, check_add_employee
from src.keyboards.keyboard import create_cancel_kb
from src.fsm.fsm import FSMAdmin
from src.db.queries.dao.dao import AsyncOrm
from src.db import cached_employees, cached_employees_fullname_and_id, cached_admins, cached_admins_fullname_and_id

router_admin = Router()


@router_admin.message(Command(commands="admin"), StateFilter(default_state), IsAdminFilterMessage())
async def process_start_adm_command(message: Message, state: FSMContext):
    await message.answer(
        text="Добро пожаловать в админскую панель!",
        reply_markup=create_admin_kb(),
    )
    await state.set_state(FSMAdmin.in_adm)


@router_admin.message(Command(commands="admin"), StateFilter(default_state))
async def warning_start_adm_command(message: Message):
    await message.answer(
        text="Извините, Вас <b>нет</b> в списке администраторов\n\n"
             "Вы можете воспользоваться следующими командами:\n"
             "/start_shift - открыть смену\n"
             "/check_attractions - проверка аттракционов\n"
             "/finish_shift - закрыть смену\n"
             "/encashment - инкассация",
        parse_mode="html",
    )


@router_admin.callback_query(StateFilter(FSMAdmin.in_adm), IsNotAdminFilterCallback(), F.data)
async def process_user_is_not_admin(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="Извините, Вы больше не администратор",
    )
    await callback.message.answer(
        text="Вы вернулись в главное меню!",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()
    await state.clear()


@router_admin.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "adm_exit")
async def process_adm_exit_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Вы вернулись в главное меню!",
    )
    await callback.answer()
    await state.clear()


@router_admin.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "add_employee")
async def process_add_employee_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Чтобы добавить нового сотрудника, Вам нужно прислать мне его id телеграм\n\n"
             "Сервис по поиску id - @getmyid_bot\n\n"
             "Отправьте id одним сообщением!\n"
             "<em>Например: 293982824</em>",
        reply_markup=create_cancel_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.add_employee_id)


@router_admin.message(StateFilter(FSMAdmin.add_employee_id), F.text.isdigit())
async def process_add_emp_id_commnad(message: Message, state: FSMContext):
    await state.update_data(employee_id=int(message.text.strip()))
    await message.answer(
        text="Теперь нужно ввести имя и фамилию сотрудника\n\n"
             "<em>Например: Иванов Иван</em>",
        parse_mode="html",
    )
    await state.set_state(FSMAdmin.add_employee_name)


@router_admin.message(StateFilter(FSMAdmin.add_employee_id))
async def warning_add_emp_id_command(message: Message):
    await message.answer(
        text="Чтобы добавить нового сотрудника, Вам нужно прислать мне его id телеграм\n\n"
             "Сервис по поиску id - @getmyid_bot\n\n"
             "Отправьте id одним сообщением!\n"
             "<em>Например: 293982824</em>",
        parse_mode="html",
    )


@router_admin.message(StateFilter(FSMAdmin.add_employee_name), F.text)
async def process_add_emp_name_command(message: Message, state: FSMContext):
    await state.update_data(employee_name=message.text.strip())
    await message.answer(
        text="А теперь введите <b>username</b> сотрудника\n\n"
             "Чтобы узнать юзернейм, откройте диалог с пользователем, "
             "нажмите на его имя в верхней части экрана. "
             "Откроется окно с описанием профиля. Возле фотографии крупными "
             "буквами указано публичное имя. Ниже указан телефон, "
             "за ним — уникальный юзернейм (username)\n\n"
             "Если username нет или Вам не удалось его найти, напишите "
             "номер телефона пользователя",
        parse_mode="html",
    )
    await state.set_state(FSMAdmin.add_employee_username)


@router_admin.message(StateFilter(FSMAdmin.add_employee_name))
async def warning_add_emp_name_command(message: Message):
    await message.answer(
        text="Нужно ввести имя и фамилию сотрудника\n\n"
             "<em>Например: Иванов Иван</em>",
        parse_mode="html",
    )


@router_admin.message(StateFilter(FSMAdmin.add_employee_username), F.text)
async def process_add_emp_phone_command(message: Message, state: FSMContext):
    await state.update_data(employee_username=message.text)

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"id: {data['employee_id']}\n"
             f"имя: {data['employee_name']}\n"
             f"username(или номер): {data['employee_username']}\n\n"
             "Всё ли корректно?",
        reply_markup=check_add_employee(),
    )
    await state.set_state(FSMAdmin.check_employee)


@router_admin.message(StateFilter(FSMAdmin.add_employee_username))
async def warning_add_emp_username_command(message: Message):
    await message.answer(
        text="введите <b>username</b> сотрудника\n\n"
             "Чтобы узнать юзернейм, откройте диалог с пользователем, "
             "нажмите на его имя в верхней части экрана. "
             "Откроется окно с описанием профиля. Возле фотографии крупными "
             "буквами указано публичное имя. Ниже указан телефон, "
             "за ним — уникальный юзернейм (username)\n\n"
             "Если username нет или Вам не удалось его найти, напишите "
             "номер телефона пользователя",
        parse_mode="html",
    )


@router_admin.callback_query(StateFilter(FSMAdmin.check_employee), F.data == "access_employee")
async def process_access_emp_command(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await AsyncOrm.add_employee(
        fullname=data["employee_name"],
        user_id=data["employee_id"],
        username=data["employee_username"],
    )
    if data["employee_id"] not in cached_employees:
        cached_employees.append(data["employee_id"])
        cached_employees_fullname_and_id.append((data["employee_name"], data["employee_id"]))
    if data["employee_id"] in cached_admins:
        cached_admins.remove(data["employee_id"])
        cached_admins_fullname_and_id.remove((data["employee_name"], data["employee_id"]))

    await callback.message.answer(
        text=f"Сотрудник <b>{data['employee_name']}</b> с id=<b>{data['employee_id']}</b> "
             f"и username=<b>{data['employee_username']}</b> успешно добавлен!",
        parse_mode="html",
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.message.answer(
        text="Админская панель:",
        reply_markup=create_admin_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.in_adm)


@router_admin.callback_query(StateFilter(FSMAdmin.check_employee), F.data == "rename_employee")
async def process_rename_emp_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите новое <b>имя и фамилию</b> сотрудника\n\n"
             "<em>Например: Иван Иванов</em>",
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.rename_employee)


@router_admin.callback_query(StateFilter(FSMAdmin.check_employee), F.data == "reid_employee")
async def process_reid_emp_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите новый <b>id</b> сотрудника\n\n"
             "Сервис по поиску id - @getmyid_bot\n\n"
             "Отправьте id одним сообщением!\n"
             "<em>Например: 293982824</em>",
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.reid_employee)


@router_admin.callback_query(StateFilter(FSMAdmin.check_employee), F.data == "reusername_employee")
async def process_reusername_emp_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text="Введите новый <b>username</b> сотрудника (или номер)\n\n"
             "<em>Например: @username</em>",
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.reusername_employee)


@router_admin.message(StateFilter(FSMAdmin.rename_employee), F.text)
async def process_new_name_emp_command(message: Message, state: FSMContext):
    await state.update_data(employee_name=message.text.strip())

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"id: {data['employee_id']}\n"
             f"имя: {data['employee_name']}\n"
             f"username(или номер): {data['employee_username']}\n\n"
             "Всё корректно?",
        reply_markup=check_add_employee(),
    )
    await state.set_state(FSMAdmin.check_employee)


@router_admin.message(StateFilter(FSMAdmin.rename_employee))
async def warning_rename_emp_command(message: Message):
    await message.answer(
        text="Введите новое <b>имя и фамилию</b> сотрудника\n\n"
             "<em>Например: Иван Иванов</em>",
        parse_mode="html",
    )


@router_admin.message(StateFilter(FSMAdmin.reid_employee), F.text.isdigit())
async def process_new_id_emp_command(message: Message, state: FSMContext):
    await state.update_data(employee_id=int(message.text))

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"id: {data['employee_id']}\n"
             f"имя: {data['employee_name']}\n"
             f"username(или номер): {data['employee_username']}\n\n"
             "Всё корректно?",
        reply_markup=check_add_employee(),
    )
    await state.set_state(FSMAdmin.check_employee)


@router_admin.message(StateFilter(FSMAdmin.reid_employee))
async def warning_reid_emp_command(message: Message):
    await message.answer(
        text="Введите новый <b>id</b> сотрудника <b>ЧИСЛОМ</b>\n\n"
             "Сервис по поиску id - @getmyid_bot\n\n"
             "Отправьте id одним сообщением!\n"
             "<em>Например: 293982824</em>",
        parse_mode="html",
    )


@router_admin.message(StateFilter(FSMAdmin.reusername_employee), F.text)
async def process_new_username_emp_command(message: Message, state: FSMContext):
    await state.update_data(employee_username=message.text)

    data = await state.get_data()

    await message.answer(
        text="Данные:\n"
             f"id: {data['employee_id']}\n"
             f"имя: {data['employee_name']}\n"
             f"username(или номер): {data['employee_username']}\n\n"
             "Всё корректно?",
        reply_markup=check_add_employee(),
    )
    await state.set_state(FSMAdmin.check_employee)


@router_admin.message(StateFilter(FSMAdmin.reusername_employee))
async def warning_reusername_emp_command(message: Message):
    await message.answer(
        text="Введите новый <b>username</b> сотрудника (или номер)\n\n"
             "<em>Например: @username</em>",
        parse_mode="html",
    )
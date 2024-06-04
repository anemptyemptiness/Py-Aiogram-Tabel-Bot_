from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.keyboards.adm_keyboard import create_employee_list_kb, create_admin_kb, create_watching_employees_kb
from src.callbacks.employee import EmployeeCallbackFactory
from src.fsm.fsm import FSMAdmin
from src.handlers.admin_handler.adding.add_employee import router_admin
from src.db.queries.dao.dao import AsyncOrm

router_show_emp = Router()
router_admin.include_router(router_show_emp)


@router_show_emp.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "employee_list")
async def process_show_employees_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список сотрудников:",
        reply_markup=create_employee_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.watching_employees)


@router_show_emp.callback_query(StateFilter(FSMAdmin.watching_employees), F.data == "go_back")
async def process_go_back_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Добро пожаловать в админскую панель!",
        reply_markup=create_admin_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.in_adm)


@router_show_emp.callback_query(StateFilter(FSMAdmin.watching_employees), EmployeeCallbackFactory.filter())
async def process_watching_info_command(callback: CallbackQuery, callback_data: EmployeeCallbackFactory, state: FSMContext):
    fullname, username = await AsyncOrm.get_employee_by_id(user_id=callback_data.user_id)

    await state.update_data(fullname=fullname)
    await state.update_data(username=username)

    await callback.message.edit_text(
        text="Информация:\n\n"
             f"Имя: {fullname}\n"
             f"username: {username}",
        reply_markup=create_watching_employees_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.current_employee)


@router_show_emp.callback_query(StateFilter(FSMAdmin.current_employee), F.data == "go_back")
async def process_go_back_from_watching_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список сотрудников:",
        reply_markup=create_employee_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.watching_employees)
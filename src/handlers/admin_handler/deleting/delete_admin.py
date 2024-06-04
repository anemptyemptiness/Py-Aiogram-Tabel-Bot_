from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.keyboards.adm_keyboard import create_admin_list_kb, create_admin_kb, create_delete_kb
from src.callbacks.admin import AdminCallbackFactory
from src.fsm.fsm import FSMAdmin
from src.handlers.admin_handler.adding.add_employee import router_admin
from src.db.queries.dao.dao import AsyncOrm
from src.db import cached_admins, cached_admins_fullname_and_id

router_del_adm = Router()
router_admin.include_router(router_del_adm)


@router_del_adm.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "delete_admin")
async def process_del_admin_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список администраторов:",
        reply_markup=create_admin_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.which_admin_to_delete)


@router_del_adm.callback_query(StateFilter(FSMAdmin.which_admin_to_delete), AdminCallbackFactory.filter())
async def process_which_admin_to_del_command(callback: CallbackQuery, callback_data: AdminCallbackFactory, state: FSMContext):
    fullname, username = await AsyncOrm.get_admin_by_id(user_id=callback_data.user_id)

    await state.update_data(fullname=fullname)
    await state.update_data(username=username)
    await state.update_data(user_id=callback_data.user_id)

    await callback.message.edit_text(
        text="Информация:\n\n"
             f"Имя: {fullname}\n"
             f"username: {username}",
        reply_markup=create_delete_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.deleting_admin)


@router_del_adm.callback_query(StateFilter(FSMAdmin.which_admin_to_delete), F.data == "go_back")
async def process_go_back_which_do_admin_delete_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Добро пожаловать в админскую панель!",
        reply_markup=create_admin_kb(),
    )
    await state.set_state(FSMAdmin.in_adm)


@router_del_adm.callback_query(StateFilter(FSMAdmin.deleting_admin), F.data == "delete")
async def process_deleting_admin_command(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await AsyncOrm.delete_admin(
        fullname=data["fullname"],
        username=data["username"],
    )
    cached_admins.remove(data["user_id"])
    cached_admins_fullname_and_id.remove((data["fullname"], data["user_id"]))

    await callback.message.edit_text(
        text=f"Администратор {data['fullname']} успешно удален!\n\n"
             "Список администраторов:",
        reply_markup=create_admin_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.which_admin_to_delete)


@router_del_adm.callback_query(StateFilter(FSMAdmin.deleting_admin), F.data == "go_back")
async def process_go_back_del_admin_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список администраторов:",
        reply_markup=create_admin_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.which_admin_to_delete)
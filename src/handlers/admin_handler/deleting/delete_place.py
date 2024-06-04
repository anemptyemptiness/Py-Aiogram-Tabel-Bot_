from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.keyboards.adm_keyboard import create_places_list_kb, create_admin_kb, create_delete_kb
from src.callbacks.place import PlaceCallbackFactory
from src.fsm.fsm import FSMAdmin
from src.handlers.admin_handler.adding.add_employee import router_admin
from src.db.queries.dao.dao import AsyncOrm
from src.db import cached_places, cached_chat_ids

router_del_place = Router()
router_admin.include_router(router_del_place)


@router_del_place.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "delete_place")
async def process_del_place_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список точек:",
        reply_markup=create_places_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.which_place_to_delete)


@router_del_place.callback_query(StateFilter(FSMAdmin.which_place_to_delete), PlaceCallbackFactory.filter())
async def process_which_place_to_del_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await state.update_data(title=callback_data.title)
    await state.update_data(chat_id=callback_data.chat_id)

    await callback.message.edit_text(
        text="Информация:\n"
             f"Название точки: {callback_data.title}\n"
             f"chat id: {callback_data.chat_id}",
        reply_markup=create_delete_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.deleting_place)


@router_del_place.callback_query(StateFilter(FSMAdmin.which_place_to_delete), F.data == "go_back")
async def process_go_back_which_do_place_delete_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Добро пожаловать в админскую панель!",
        reply_markup=create_admin_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.in_adm)


@router_del_place.callback_query(StateFilter(FSMAdmin.deleting_place), F.data == "delete")
async def process_deleting_place_command(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await AsyncOrm.delete_place(
        title=data["title"],
    )
    cached_places.pop(data["title"])
    cached_chat_ids.remove(data["chat_id"])

    await callback.message.edit_text(
        text=f'Рабочая точка "{data["title"]}" <b>успешно</b> удалена!\n\n'
             "Список рабочих точек:",
        reply_markup=create_places_list_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMAdmin.which_place_to_delete)


@router_del_place.callback_query(StateFilter(FSMAdmin.deleting_place), F.data == "go_back")
async def process_go_back_del_place_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список рабочих точек:",
        reply_markup=create_places_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.which_place_to_delete)
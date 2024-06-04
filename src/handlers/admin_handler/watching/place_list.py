from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.keyboards.adm_keyboard import create_places_list_kb, create_admin_kb, create_watching_places_kb
from src.callbacks.place import PlaceCallbackFactory
from src.fsm.fsm import FSMAdmin
from src.handlers.admin_handler.adding.add_employee import router_admin

router_show_places = Router()
router_admin.include_router(router_show_places)


@router_show_places.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "places_list")
async def process_show_places_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список рабочих точек:",
        reply_markup=create_places_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.watching_place)


@router_show_places.callback_query(StateFilter(FSMAdmin.watching_place), F.data == "go_back")
async def process_go_back_places_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Добро пожаловать в админскую панель!",
        reply_markup=create_admin_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.in_adm)


@router_show_places.callback_query(StateFilter(FSMAdmin.watching_place), PlaceCallbackFactory.filter())
async def process_watching_places_info_command(callback: CallbackQuery, callback_data: PlaceCallbackFactory, state: FSMContext):
    await state.update_data(title=callback_data.title)
    await state.update_data(chat_id=callback_data.chat_id)

    await callback.message.edit_text(
        text="Информация:\n\n"
             f"Название: {callback_data.title}\n"
             f"chat id: {callback_data.chat_id}",
        reply_markup=create_watching_places_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.current_place)


@router_show_places.callback_query(StateFilter(FSMAdmin.current_place), F.data == "go_back")
async def process_go_back_from_watching_places_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Список рабочих точек:",
        reply_markup=create_places_list_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.watching_place)
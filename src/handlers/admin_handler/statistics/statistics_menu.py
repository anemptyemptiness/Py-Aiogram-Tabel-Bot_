from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from src.fsm.fsm import (
    FSMAdmin,
    FSMStatistics,
    FSMStatisticsVisitors,
    FSMStatisticsMoney,
)
from src.handlers.admin_handler import router_admin
from src.keyboards.adm_keyboard import (
    create_admin_kb,
    create_stats_kb,
    create_stats_visitors_kb,
    create_stats_money_kb,
)

router_adm_stats = Router()
router_admin.include_router(router_adm_stats)


@router_adm_stats.callback_query(StateFilter(FSMAdmin.in_adm), F.data == "adm_stats")
async def process_adm_stats_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Выберите статистику:",
        reply_markup=create_stats_kb(),
    )
    await callback.answer()
    await state.set_state(FSMStatistics.in_stats)


@router_adm_stats.callback_query(StateFilter(FSMStatistics.in_stats), F.data == "adm_stats_visitors")
async def process_adm_stats_visitors_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Статистика посетителей:",
        reply_markup=create_stats_visitors_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMStatisticsVisitors.in_stats)


@router_adm_stats.callback_query(StateFilter(FSMStatistics.in_stats), F.data == "adm_stats_money")
async def process_adm_stats_money_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Статистика выручки:",
        reply_markup=create_stats_money_kb(),
        parse_mode="html",
    )
    await callback.answer()
    await state.set_state(FSMStatisticsMoney.in_stats)


@router_adm_stats.callback_query(StateFilter(FSMStatistics.in_stats), F.data == "adm_stats_back")
async def process_adm_stats_back_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Добро пожаловать в админскую панель!",
        reply_markup=create_admin_kb(),
    )
    await callback.answer()
    await state.set_state(FSMAdmin.in_adm)


@router_adm_stats.callback_query(StateFilter(FSMStatistics.in_stats), F.data == "adm_exit")
async def process_adm_exit_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text="Вы вернулись в главное меню!",
    )
    await callback.answer()
    await state.clear()
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext

from src.filters.check_chat import CheckChatFilter
from src.filters.admin_or_employee import CheckUserFilter


router_authorise = Router()


@router_authorise.message(CheckUserFilter())
async def warning_user(message: Message):
    await message.answer(
        text="Вас нет в списке работников данной компании"
    )


@router_authorise.message(CheckChatFilter())
async def warning_chat(message: Message):
    pass


@router_authorise.message(~StateFilter(default_state), F.text.startswith("/") == True)
async def is_command_handler(message: Message):
    await message.answer(text="Вы уже находитесь в другой команде!\n\n"
                              'Если вы хотите выйти из команды, нажмите кнопку "<b>Отмена</b>"\n'
                              'или напишите "<b>Отмена</b>" в чат',
                         parse_mode="html")


@router_authorise.message(~StateFilter(default_state), F.text == "Отмена")
async def process_cancel_in_states_command(message: Message, state: FSMContext):
    await message.answer(
        text='Вы вернулись в главное меню!',
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()


@router_authorise.callback_query(~StateFilter(default_state), F.data == "cancel")
async def process_cancel_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await callback.message.edit_text(
        text="➢ Отмена"
    )
    await callback.message.answer(
        text="Вы вернулись в главное меню!",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="html",
    )
    await callback.answer()
    await state.clear()


@router_authorise.message(Command(commands="start"), StateFilter(default_state))
async def process_command_start(message: Message):
    await message.answer(
        text=f"Здравствуйте, {message.from_user.full_name}!\n\n"
             "Используйте меню в левой нижней части экрана, чтобы работать с ботом"
    )


@router_authorise.message(StateFilter(default_state), F.text.startswith("/") == False)
async def warning_default(message: Message):
    await message.answer(
        text="Выберите нужную Вам команду из выпадающего меню"
    )


@router_authorise.callback_query(StateFilter(default_state))
async def warning_any_callback_without_command(callback: CallbackQuery):
    await callback.answer(text="Вы не можете нажать на кнопку вне команды")
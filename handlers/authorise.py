from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext

from fsm.fsm import Authorise
from filters.check_chat import CheckChatFilter
from filters.admin_or_employee import CheckUserFilter
from filters.is_auth import isUserAuthFilter
from config.config import config
from db import DB


router_authorise = Router()


@router_authorise.message(CheckUserFilter(config.admins, config.employees))
async def warning_user(message: Message):
    await message.answer(text="Вас нет в списке работников данной компании")


@router_authorise.message(CheckChatFilter(config.admin_chats))
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
    await state.clear()
    await message.answer(text='Вы вернулись в главное меню',
                         reply_markup=ReplyKeyboardRemove())


@router_authorise.message(Command(commands="start"), StateFilter(default_state))
async def process_command_start(message: Message, state: FSMContext):
    if not DB.user_exists(message.from_user.id):
        await message.answer(text=f"Добро пожаловать, {message.from_user.full_name}!\n\n"
                                  "Используйте меню в левой нижней части экрана, чтобы работать с ботом")
        await message.answer(text="Пожалуйста, введите Ваше имя и фамилию!")
        await state.set_state(Authorise.fullname)
    else:
        await message.answer(text="Вы уже зарегистрированы в боте!")


@router_authorise.message(StateFilter(default_state), isUserAuthFilter())
async def user_not_auth(message: Message):
    await message.answer(text="Похоже, пока что Вас нет в базе данных\n\n"
                              "Нажмите на /start, чтобы авторизоваться")


@router_authorise.message(StateFilter(Authorise.fullname), F.text)
async def process_authorise_command(message: Message, state: FSMContext):
    if len(message.text.split()) == 2:
        try:
            DB.add_users(
                user_id=message.from_user.id,
                fullname=message.text
            )
            await message.answer(text="Ваши данные <b>успешно сохранены</b>, спасибо!\n\n"
                                      "Повторной авторизации делать не нужно!",
                                 parse_mode="html")
        except Exception as e:
            await message.answer(text="Что-то пошло не так при авторизации, сообщите руководству!")
            await message.bot.send_message(chat_id=config.admins[0],
                                           text=f"{e}")
        finally:
            await state.clear()
    else:
        await message.answer(text="Пожалуйста, введите Ваше имя и фамилию!")


@router_authorise.message(StateFilter(Authorise.fullname))
async def warning_authorise_command(message: Message):
    await message.answer(text="Пожалуйста, введите Ваше имя и фамилию!")


@router_authorise.message(StateFilter(default_state), F.text.startswith("/") == False)
async def warning_default(message: Message):
    await message.answer(text="Выберите нужную Вам команду из выпадающего меню")

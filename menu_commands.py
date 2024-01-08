from aiogram import types


async def set_default_commands(bot):
    await bot.set_my_commands([
        types.BotCommand(command="start_shift", description="Открыть смену"),
        types.BotCommand(command="encashment", description="Инкассация"),
        types.BotCommand(command="check_attractions", description="Проверка аттракционов"),
        types.BotCommand(command="finish_shift", description="Закрыть смену"),
    ])

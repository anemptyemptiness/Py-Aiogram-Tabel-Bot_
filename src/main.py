import asyncio
import logging
import sys
from threading import Thread

from src.config import settings, redis
from src.handlers import (
    router_authorise,
    router_attractions,
    router_encashment,
    router_start_shift,
    router_finish,
    router_admin,
)
from menu_commands import set_default_commands

from aiogram.fsm.storage.redis import RedisStorage
from aiogram import Bot, Dispatcher

from src.autoposting.send_notification import creating_new_loop_for_notification
from src.autoposting.check_for_revenue import creating_new_loop_for_checking_revenue


async def main() -> None:

    bot = Bot(token=settings.TOKEN)
    storage = RedisStorage(redis=redis)
    dp = Dispatcher(storage=storage)

    logging.basicConfig(
        format='[{asctime}] #{levelname:8} {filename}: '
               '{lineno} - {name} - {message}',
        style="{",
        level=logging.WARNING,
        filename="logs.log",
        filemode="w",
    )

    # Подключаем роутеры к корневому роутеру (диспетчеру)
    dp.include_router(router_authorise)
    dp.include_router(router_start_shift)
    dp.include_router(router_encashment)
    dp.include_router(router_attractions)
    dp.include_router(router_finish)
    dp.include_router(router_admin)

    await set_default_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    global_loop = asyncio.get_event_loop()
    auto_posting_thread = Thread(target=creating_new_loop_for_notification, args=(global_loop, bot))
    auto_checking_revenue_thread = Thread(target=creating_new_loop_for_checking_revenue, args=(global_loop, bot))
    auto_posting_thread.start()
    auto_checking_revenue_thread.start()

    print("Бот успешно запущен!", file=sys.stderr)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

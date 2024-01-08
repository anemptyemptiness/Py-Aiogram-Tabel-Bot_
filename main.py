import asyncio
import logging
from threading import Thread
from datetime import datetime, timedelta, timezone

import db
from config.config import config
from handlers import start_shift, encashment, check_attractions, finish_shift, adm_get_stats, authorise
from menu_commands import set_default_commands
from lexicon.lexicon_ru import warning

from aiogram.fsm.storage.redis import RedisStorage
from aiogram import Bot, Dispatcher

logging.basicConfig(level=logging.DEBUG)

bot = Bot(token=config.tg_bot.token)
storage = RedisStorage(redis=config.redis)
dp = Dispatcher(storage=storage)
DB = db.db.DataBase(config=config)


async def auto_posting():
    last_message = None

    while True:
        if (datetime.now(tz=timezone(timedelta(hours=3.0))).hour >= 10) \
                and (datetime.now(tz=timezone(timedelta(hours=3.0))).hour <= 20):
            await asyncio.sleep(60 * 30)

            user_ids = DB.get_users()

            for user_id in user_ids:
                if user_id[0] in config.employees:
                    try:
                        message = await bot.send_message(
                            chat_id=user_id[0],
                            text=warning
                        )

                        if last_message is not None:
                            await bot.delete_message(chat_id=last_message.chat.id,
                                                     message_id=last_message.message_id)

                        last_message = message
                    except Exception as e:
                        print("main.py: The user has blocked the bot:", e)
        else:
            await asyncio.sleep(60)


def creating_new_loop(global_loop):
    asyncio.run_coroutine_threadsafe(auto_posting(), global_loop)


async def main() -> None:
    # Подключаем роутеры к корневому роутеру (диспетчеру)
    dp.include_router(authorise.router_authorise)
    dp.include_router(start_shift.router_start_shift)
    dp.include_router(encashment.router_encashment)
    dp.include_router(check_attractions.router_attractions)
    dp.include_router(finish_shift.router_finish)
    dp.include_router(adm_get_stats.router_adm)

    await set_default_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    global_loop = asyncio.get_event_loop()
    auto_posting_thread = Thread(target=creating_new_loop, args=(global_loop,))
    auto_posting_thread.start()

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

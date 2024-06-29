import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from src.db import cached_employees
from src.lexicon.lexicon_ru import warning
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


def creating_new_loop_for_notification(global_loop, bot: Bot):
    asyncio.run_coroutine_threadsafe(auto_posting(bot), global_loop)


async def auto_posting(bot: Bot):
    last_message = None

    while True:
        if (datetime.now(tz=timezone(timedelta(hours=3.0))).hour >= 10) \
                and (datetime.now(tz=timezone(timedelta(hours=3.0))).hour <= 20):
            await asyncio.sleep(60 * 30)

            user_ids = cached_employees

            for user_id in user_ids:
                try:
                    message = await bot.send_message(
                        chat_id=user_id,
                        text=f"{warning}",
                        parse_mode="html",
                    )

                    if last_message is not None:
                        await bot.delete_message(chat_id=last_message.chat.id,
                                                 message_id=last_message.message_id)

                    last_message = message
                except (Exception, TelegramBadRequest):
                    pass
        else:
            await asyncio.sleep(60)

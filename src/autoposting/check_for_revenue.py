from datetime import datetime, timezone, timedelta
from aiogram import Bot

from src.config import settings
from src.db.queries.dao.dao import AsyncOrm
import asyncio


def creating_new_loop_for_checking_revenue(global_loop, bot: Bot):
    asyncio.run_coroutine_threadsafe(send_revenue_report_by_N_days(bot), global_loop)


async def send_revenue_report_by_N_days(bot: Bot):
    while True:
        try:
            date_now = datetime.now(tz=timezone(timedelta(hours=3.0))).date()
            how_many_days_ago_on_places = [
                (place_id, (date_now - last_update_date).days) for place_id, last_update_date in await AsyncOrm._check_data_from_finances()
            ]

            for place_id, days_difference in how_many_days_ago_on_places:
                if days_difference >= settings.DAYS_FOR_FINANCES_CHECK:
                    await AsyncOrm.set_data_to_finances_by_place(place_id=place_id)

                    data = await AsyncOrm.get_data_from_finances_by_place(place_id=place_id)

                    for title, _, last_money, updated_money, updated_at in data:
                        chat_id = settings.REVENUE_CHAT_ID  # chat-id группы, куда бот будет присылать отчеты по выручке
                        difference = updated_money - last_money
                        last_money = f"{int(last_money):,}".replace(",", " ")
                        updated_money = f"{int(updated_money):,}".replace(",", " ")

                        report: str = "📊Статистика по росту выручки\n"
                        report += f"<b>от</b> {updated_at.strftime('%d.%m.%y')} <b>до</b> {date_now.strftime('%d.%m.%y')}\n\n"

                        report += f"🏚Точка: <b>{title}</b>\n└"
                        report += f"Выручка {updated_at.strftime('%d.%m.%y')}: <em><b>{last_money}₽</b></em>\n└"
                        report += f"Выручка {date_now.strftime('%d.%m.%y')}: <em><b>{updated_money}₽</b></em>\n\n"

                        is_normal = True if difference > 0 else False

                        difference = f"{int(difference):,}".replace(",", " ")
                        report += f"Разница составила: <em><b>{difference}₽</b></em> "

                        report += f"{'🟢' if is_normal else '🔴'}\n\n"
                        report += f"Результат: <em>{'все в норме✅' if is_normal else 'нужно смотреть камеры⚠️'}</em>"

                        await bot.send_message(
                            chat_id=chat_id,
                            text=report,
                            parse_mode="html",
                        )

                    await asyncio.sleep(60 * 60 * 24)  # спим 1 день
                else:
                    await asyncio.sleep(60 * 60 * 24)  # спим 1 день
            await asyncio.sleep(60 * 60 * 24)  # спим 1 день
        except Exception:
            await asyncio.sleep(60 * 60 * 24)  # спим 1 день

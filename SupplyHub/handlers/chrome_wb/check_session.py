import logging
import asyncio
from datetime import datetime

from handlers.chrome_wb.browser import BrowserManager 
from handlers.database.connection import set_session

async def check_session(user_id):
    """Проверка, активна ли сессия пользователя."""
    page = await BrowserManager.get_active_page(user_id)

    try:
        await page.goto("https://seller.wildberries.ru/")
        await asyncio.sleep(5)
        data = await page.query_selector('.logo_Logo__PlzzM') 
        if data:
            logging.info(f"{datetime.now()} | Сессия для пользователя {user_id} активна.")
            await set_session(1, user_id)
            return True
        else:
            logging.warning(f"{datetime.now()} | Сессия для пользователя {user_id} неактивна.")
            await set_session(0, user_id)
            return False

    except Exception as e:
        logging.error(f"{datetime.now()} | Ошибка при проверке сессии пользователя {user_id}: {e}")
        return False
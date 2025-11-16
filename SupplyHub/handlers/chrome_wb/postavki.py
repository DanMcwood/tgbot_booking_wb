import logging
from datetime import datetime
import asyncio

from handlers.chrome_wb.browser import BrowserManager 
from handlers.params.settings import SUPPLIES_URL

async def update_supplies(user_id):
    """Обновление списка поставок с Wildberries для конкретного пользователя."""
    supplies = []
    page = await BrowserManager.get_active_page(user_id)

    try:
        # Переходим на страницу поставок
        await page.goto(SUPPLIES_URL, wait_until="networkidle")
        logging.info(f"{datetime.now()} | Загружен URL {SUPPLIES_URL} для пользователя {user_id}")

        floater = await page.query_selector('.__floater.__floater__open')
        if floater:
            close_button = await floater.query_selector('.Tooltip-hint-view__close-button__VRU1RdrpEJ')
            if close_button:
                await close_button.click() 
                floater = await page.query_selector('.__floater.__floater__open')
                if floater:
                    close_button = await floater.query_selector('.Tooltip-hint-view__close-button__VRU1RdrpEJ')
                    if close_button:
                        await close_button.click()  

        # Ждем загрузки таблицы
        await page.query_selector(".All-supplies-table-row__C6iU8GGIHd")
        logging.info(f"{datetime.now()} | Таблица поставок успешно загружена.")

        # Извлекаем строки таблицы
        rows = await page.query_selector_all(".All-supplies-table-row__C6iU8GGIHd")
        for row in rows:
            try:
                # Извлекаем ячейки из строки
                cells = await row.query_selector_all(".All-supplies-table-row__cell__PdZJUOpQYs")
                # Сохраняем текст из каждой ячейки
                row_data = [await cell.inner_text() for cell in cells]

                # Проверяем, что первая ячейка (например, номер заказа) не пустая
                if row_data and row_data[0] != "-":
                    supplies.append(row_data)
            except Exception as e:
                logging.warning(f"{datetime.now()} | Ошибка при обработке строки: {e}")

        logging.info(f"{datetime.now()} | Обновлено: {len(supplies)} записей для пользователя {user_id}")
    except Exception as e:
        logging.error(f"{datetime.now()} | Ошибка при обновлении поставок для пользователя {user_id}: {e}")
    return supplies
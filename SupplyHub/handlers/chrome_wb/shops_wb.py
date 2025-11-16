import logging
import asyncio
from datetime import datetime

from handlers.chrome_wb.browser import BrowserManager 
from handlers.database.connection import add_shop_wb_to_db, get_shops_wb, get_shop_wb

async def fetch_shops(user_id):
    """Получение списка магазинов и сохранение в базу данных."""
    page = await BrowserManager.get_active_page(user_id)

    try:
        await page.goto("https://seller.wildberries.ru/")
        await asyncio.sleep(1.5)

        await page.wait_for_selector(".ProfileView", timeout=15000)
        profile_button = await page.query_selector(".ProfileView")
        if not profile_button:
            logging.error(f"{datetime.now()} | Кнопка 'Меню' не найдена.")
            return False

        await profile_button.hover()
        logging.info(f"{datetime.now()} | Курсор наведен на кнопку 'Меню'.")

        await page.wait_for_selector("div.suppliers-list_SuppliersList__ZPInT", timeout=15000)
        suppliers_list = await page.query_selector("div.suppliers-list_SuppliersList__ZPInT")
        if not suppliers_list:
            logging.error(f"{datetime.now()} | Список магазинов не найден.")
            return False

        shop_items = await suppliers_list.query_selector_all(
            "ul.suppliers-list_SuppliersList__list__9lMrO > li.suppliers-list_SuppliersList__item__GPkdU"
        )

        shops = []
        for item in shop_items:
            shop_name_span = await item.query_selector(
                "div.suppliers-item_SuppliersItem__text__sLbvh > div.Portal-tooltip__text > span.text_Text--h5__Jr45n"
            )
            shop_name = (await shop_name_span.text_content()).strip()

            logging.info(f"{datetime.now()} | Найден магазин: {shop_name}")
            shops.append(shop_name)

            cur_shops = await get_shops_wb(user_id)
            if shop_name not in cur_shops:
                await add_shop_wb_to_db(user_id, shop_name)

        logging.info(f"{datetime.now()} | Всего найдено {len(shops)} магазинов.")
        return True
    except Exception as e:
        logging.error(f"{datetime.now()} | Ошибка при получении списка магазинов: {e}")
        return False

async def select_shop(user_id, shop_name, max_retries=3):
    """Выбор магазина из списка с перезапуском в случае ошибки."""
    retries = 0
    page = await BrowserManager.get_active_page(user_id)

    while retries < max_retries:
        logging.info(f"{datetime.now()} | Попытка {retries + 1}/{max_retries} выбрать магазин '{shop_name}'.")

        try:
            await page.goto("https://seller.wildberries.ru/")
            await asyncio.sleep(1.5)
            await page.wait_for_selector(".ProfileView", timeout=15000)
            profile_button = await page.query_selector(".ProfileView")
            if not profile_button:
                logging.error(f"{datetime.now()} | Кнопка 'Меню' не найдена.")
                retries += 1
                continue

            await profile_button.hover()
            logging.info(f"{datetime.now()} | Курсор наведен на кнопку 'Меню'.")

            await page.wait_for_selector("div.suppliers-list_SuppliersList__ZPInT", timeout=15000)
            suppliers_list = await page.query_selector("div.suppliers-list_SuppliersList__ZPInT")
            if not suppliers_list:
                logging.error(f"{datetime.now()} | Список магазинов не найден.")
                retries += 1
                continue

            shop_items = await suppliers_list.query_selector_all(
                "ul.suppliers-list_SuppliersList__list__9lMrO > li.suppliers-list_SuppliersList__item__GPkdU"
            )

            if not shop_items:
                logging.error(f"{datetime.now()} | Список магазинов пуст.")
                retries += 1
                continue

            for item in shop_items:
                try:
                    shop_name_span = await item.query_selector(
                        "div.suppliers-item_SuppliersItem__text__sLbvh > div.Portal-tooltip__text > span.text_Text--h5__Jr45n"
                    )
                    if not shop_name_span:
                        logging.warning(f"{datetime.now()} | Не удалось найти span с именем магазина.")
                        continue

                    current_shop_name = (await shop_name_span.text_content()).strip()
                    if current_shop_name == shop_name:
                        checkbox = await item.query_selector("div.SuppliersItem__checkbox > label.checkbox_Checkbox__kpbr4")
                        if checkbox:
                            await checkbox.click()
                            logging.info(f"{datetime.now()} | Магазин '{shop_name}' выбран.")
                            return True
                except Exception as inner_ex:
                    logging.error(f"{datetime.now()} | Ошибка при обработке магазина: {inner_ex}")
                    continue

            logging.error(f"{datetime.now()} | Магазин '{shop_name}' не найден.")
            retries += 1
            continue

        except Exception as e:
            logging.error(f"{datetime.now()} | Ошибка при выборе магазина: {e}")
            retries += 1

    logging.error(f"{datetime.now()} | Не удалось выбрать магазин после {max_retries} попыток.")
    return None

async def select_shop_bron(user_id, shop_id, request_id, max_retries=3):
    """Выбор магазина из списка для бронирования."""
    shop_name = await get_shop_wb(shop_id)
    retries = 0
    page = await BrowserManager.get_active_request_page(user_id, request_id)

    while retries < max_retries:
        await page.goto("https://seller.wildberries.ru/")
        await asyncio.sleep(1.5)
        try:
            await page.wait_for_selector(".ProfileView", timeout=15000)
            profile_button = await page.query_selector(".ProfileView")
            if not profile_button:
                logging.error(f"{datetime.now()} | Кнопка 'Меню' не найдена.")
                retries += 1
                continue

            await profile_button.hover()
            logging.info(f"{datetime.now()} | Курсор наведен на кнопку 'Меню'.")

            await page.wait_for_selector("div.suppliers-list_SuppliersList__ZPInT", timeout=15000)
            suppliers_list = await page.query_selector("div.suppliers-list_SuppliersList__ZPInT")
            if not suppliers_list:
                logging.error(f"{datetime.now()} | Список магазинов не найден.")
                retries += 1
                continue

            shop_items = await suppliers_list.query_selector_all(
                "ul.suppliers-list_SuppliersList__list__9lMrO > li.suppliers-list_SuppliersList__item__GPkdU"
            )

            for item in shop_items:
                shop_name_span = await item.query_selector(
                    "div.suppliers-item_SuppliersItem__text__sLbvh > div.Portal-tooltip__text > span.text_Text--h5__Jr45n"
                )
                current_shop_name = (await shop_name_span.text_content()).strip()

                if current_shop_name == shop_name:
                    checkbox = await item.query_selector("div.SuppliersItem__checkbox > label.checkbox_Checkbox__kpbr4")
                    if checkbox:
                        await checkbox.click()
                        logging.info(f"{datetime.now()} | Магазин '{shop_name}' выбран.")
                        return True

            logging.error(f"{datetime.now()} | Магазин '{shop_name}' не найден.")
            retries += 1 
            continue

        except Exception as e:
            logging.error(f"{datetime.now()} | Ошибка при выборе магазина: {e}")
            retries += 1 
            continue

    logging.error(f"{datetime.now()} | Не удалось выбрать магазин после {max_retries} попыток.")
    return None
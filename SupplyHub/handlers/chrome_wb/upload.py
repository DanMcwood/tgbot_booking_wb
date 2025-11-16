import logging
import tempfile
from datetime import datetime
import asyncio

from handlers.chrome_wb.browser import BrowserManager 
from handlers.database.connection import get_db_connection, get_warehouse_name
from handlers.tasks.utils import filter_supply_text_type

async def upload_supply(request_id: int, user_id):
    """Создание новой поставки на Wildberries."""
    try:
        conn = await get_db_connection()

        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT warehouse_ids, supply_type, file FROM supply_requests WHERE request_id = ?
            """, (request_id,))
            request = await cursor.fetchone()

        if not request:
            logging.warning(f"{datetime.now()} | Запрос с request_id={request_id} не найден.")
            return False

        warehouse_id = request['warehouse_ids']
        supply_type = request['supply_type']
        file_data = request['file'] 
        supply_type = await filter_supply_text_type(supply_type)
        warehouse_name = await get_warehouse_name(warehouse_id)
        if not file_data:
            logging.error(f"{datetime.now()} | Файл отсутствует в базе данных для request_id={request_id}.")
            return False

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(file_data)
        logging.info(f"{datetime.now()} | Временный файл создан: {temp_file_path}")

        page = await BrowserManager.get_active_page(user_id)
        await page.goto("https://seller.wildberries.ru/supplies-management/all-supplies", wait_until="networkidle")
        logging.info(f"{datetime.now()} | Открыта страница управления поставками для request_id={request_id}.")

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
                        
        await page.wait_for_selector("button[data-testid='main-layout-create-supply-button-primary']", timeout=15000)
        logging.info(f"{datetime.now()} | Кнопка 'Создать поставку' успешно найдена.")

        create_button = await page.query_selector("button[data-testid='main-layout-create-supply-button-primary']")
        if not create_button:
            logging.error(f"{datetime.now()} | Кнопка 'Создать поставку' не найдена.")
            return False
        await create_button.click()
        logging.info(f"{datetime.now()} | Кнопка 'Создать поставку' нажата.")

        await page.wait_for_selector("button[data-testid='control-card-download-file-button-secondary']", timeout=15000)
        upload_button = await page.query_selector("button[data-testid='control-card-download-file-button-secondary']")
        if not upload_button:
            logging.error(f"{datetime.now()} | Кнопка загрузки файла не найдена.")
            return False

        file_input = await page.query_selector("input[type='file']")
        if not file_input:
            logging.error(f"{datetime.now()} | Элемент <input type='file'> для загрузки файла не найден.")
            return False

        await file_input.set_input_files(temp_file_path)
        logging.info(f"{datetime.now()} | Файл {temp_file_path} успешно загружен.")

        await page.wait_for_selector("button[data-testid='steps-next-button-desktop-button-primary']", timeout=15000)
        next_button = await page.query_selector("button[data-testid='steps-next-button-desktop-button-primary']")
        if not next_button:
            logging.error(f"{datetime.now()} | Кнопка 'Дальше' не найдена.")
            return False
        await next_button.click()
        logging.info(f"{datetime.now()} | Кнопка 'Дальше' нажата.")
        await asyncio.sleep(2)
        modal = await page.query_selector('.Modal__tbHWWxPrcR')
        if modal:
            close_button = await modal.query_selector('.button__ymbakhzRxO')
            if close_button:
                await close_button.click()

        await page.wait_for_selector("#warehouse")
        warehouse_dropdown = await page.query_selector("#warehouse")
        await warehouse_dropdown.click()
        logging.info(f"{datetime.now()} | Выпадающий список складов открыт.")

        await page.wait_for_selector(".Select__options__szIlvVfsGy", timeout=15000)
        await page.wait_for_selector("ul.Dropdown-list__OOmE0KcqVt", timeout=15000)
        logging.info(f"{datetime.now()} | Родительский элемент выпадающего списка загружен.")
        warehouse_options = await page.query_selector_all(
            "ul.Dropdown-list__OOmE0KcqVt > li.Dropdown-list__item__Gpe4bccUdB:not(.Dropdown-list__item--search__sRlryCVxVW) button:not(.Dropdown-option--disabled__NRMNOpovp4)"
        )

        if not warehouse_options:
            logging.error(f"{datetime.now()} | Опции в выпадающем списке складов не найдены.")
            return False

        logging.info(f"{datetime.now()} | Найдено складов: {len(warehouse_options)}")

        warehouse_found = False
        for option in warehouse_options:
            span_element = await option.query_selector("span.Text__jKJsQramuu.Text--textDecoration-none__rkxLphaqR0")
            warehouse_text = (await span_element.text_content()).strip()
            if warehouse_text == warehouse_name.strip():
                await option.click()
                logging.info(f"{datetime.now()} | Склад '{warehouse_name}' успешно выбран.")
                warehouse_found = True
                break

        if not warehouse_found:
            logging.error(f"{datetime.now()} | Склад '{warehouse_name}' не найден в списке.")

        await page.wait_for_selector(".Min-supplies-types__supplies-container__51JyJyrdb5", timeout=15000)
        supply_type_options = await page.query_selector_all(".Supplies-card__container__cKd843Fwnx")
        supply_type_found = False

        for option in supply_type_options:
            span_element = await option.query_selector("span.Text__jKJsQramuu")
            supply_type_text = (await span_element.text_content()).strip()
            if supply_type_text == supply_type:
                checkbox = await option.query_selector(".Checkbox__fo7N2aOxu-")

                await checkbox.click()
                supply_type_found = True
                logging.info(f"{datetime.now()} | Чекбокс для '{supply_type}' выбран.")
                break

        if not supply_type_found:
            logging.error(f"{datetime.now()} | Тип поставки '{supply_type}' не найден.")
            return False

        next_button = await page.query_selector("button[data-testid='steps-next-button-desktop-button-primary']")
        if not next_button:
            logging.error(f"{datetime.now()} | Кнопка 'Дальше' не найдена.")
            return False
        await next_button.click()
        logging.info(f"{datetime.now()} | Кнопка 'Дальше' нажата.")

        await page.wait_for_selector(".Header-block__IGY7hZsRx9 span.Text--body-m__s84\\+1\\+NX2a", timeout=15000)
        await page.wait_for_timeout(2000)  
        order_number_element = await page.query_selector(".Header-block__IGY7hZsRx9 span.Text--body-m__s84\\+1\\+NX2a")

        order_text = await order_number_element.text_content()
        if not order_text:
            logging.error(f"{datetime.now()} | Номер заказа не найден.")
            return False

        print(order_text)
        order_number = order_text.split("№")[-1].strip()
        logging.info(f"{datetime.now()} | Получен номер заказа: {order_number}.")

        async with conn.cursor() as cursor:
            await cursor.execute(
                "UPDATE supply_requests SET supply_number = ? WHERE request_id = ?",
                (order_number, request_id)
            )
            await conn.commit()
        logging.info(f"{datetime.now()} | Номер заказа {order_number} записан в базу для request_id={request_id}.")
        return True
    except Exception as e:
        logging.error(f"{datetime.now()} | Ошибка при загрузке поставки для request_id={request_id}: {e}")
        return False

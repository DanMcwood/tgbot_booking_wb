import logging
import random
import asyncio
from datetime import datetime

from handlers.params.custom_logging import info_booking
from handlers.chrome_wb.shops_wb import select_shop_bron
from handlers.chrome_wb.config import random_scroll
from handlers.database.connection import get_request_data_bron, set_new_value, set_cool_bron, get_status, get_data_request_just_searching
from handlers.tasks.notification import send_notif
from handlers.params.settings import month_translation, day_translation, stay_api, second_api, time_to_sleep
from handlers.api_wb.functions import get_supply_coef
from handlers.chrome_wb.browser import BrowserManager 

future_data = {}
box_type_mapping = {
    2: 1,
    5: 2,
    6: 3
}

async def book_supply(request_id, shop_id):
    """Бронирование поставки на Wildberries для конкретного пользователя."""
    supply_found = False
    page = None

    # Этап 1: Получение данных для бронирования поставки
    try:
        request = await get_request_data_bron(request_id)
        if not request:
            logging.warning(f"Запрос с request_id={request_id} не найден.")
            await set_new_value(2, request_id)
            return

        if int(request['is_processing']) != 0:
            info_booking(f"{datetime.now()} | Задача для request_id={request_id} уже находится в обработке / закончила обработку.")
            return

        coefficient = int(request['coefficient'])
        supply_number = int(request['supply_number'])
        user_id = int(request['user_id'])
        custom_dates = request['custom_dates'].split(', ')
        date_start = datetime.strptime(request['date_start'], '%Y-%m-%d')
        date_end = datetime.strptime(request['date_end'], '%Y-%m-%d')
        today = datetime.now()

        if today > date_end:
            await set_new_value(3, request_id)
            info_booking(f"{datetime.now()} | Время истекло для request_id={request_id}.")
            return

    except ValueError as ve:
        logging.error(f"{datetime.now()} | Ошибка данных в преобразовании для request_id={request_id}: {ve}")
        await set_new_value(7, request_id)
        return

    await set_new_value(1, request_id) 

    # Этап 2: Получение страницы с выбранным магазином
    try:
        page = await select_shop_bron(user_id, shop_id, request_id)
        if not page:
            logging.error(f"{datetime.now()} | Не удалось открыть магазин для request_id={request_id}.")
            await set_new_value(7, request_id)
            return
    except Exception as e:
        logging.error(f"{datetime.now()} | Ошибка при открытии магазина для request_id={request_id}: {e}")
        await set_new_value(7, request_id)
        return
    # Этап 3: Поиск поставки
    page = await BrowserManager.get_active_request_page(user_id, request_id)
    try:
        await page.goto("https://seller.wildberries.ru/supplies-management/all-supplies")

        await asyncio.sleep(2)
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

        await random_scroll(page)
        await page.wait_for_selector(".All-supplies-table-row__C6iU8GGIHd", timeout=15000)
        info_booking(f"{datetime.now()} | Загружена страница управления поставками для request_id={request_id}.")

        rows = await page.query_selector_all(".All-supplies-table-row__C6iU8GGIHd")
        for row in rows:
            await asyncio.sleep(random.uniform(0.5, 2))
            try:
                cells = await row.query_selector_all(".All-supplies-table-row__cell__PdZJUOpQYs")
                for cell in cells:
                    supply_text = await cell.inner_text()
                    if supply_text.isdigit() and int(supply_text) == supply_number:
                        supply_found = True
                        await row.hover()
                        await asyncio.sleep(random.uniform(0.5, 1.5))
                        await row.click()
                        info_booking(f"{datetime.now()} | Поставка с номером {supply_number} открыта для request_id={request_id}.")
                        break
            except Exception as e:
                logging.warning(f"{datetime.now()} | Ошибка при обработке строки для request_id={request_id}: {e}")
            if supply_found:
                break

        if not supply_found:
            await set_new_value(5, request_id)
            info_booking(f"{datetime.now()} | Поставка с номером {supply_number} не найдена для request_id={request_id}.")
            return
    except Exception as e:
        logging.error(f"{datetime.now()} | Ошибка при поиске поставки для request_id={request_id}: {e}")
        return

    # Этап 4: Бронирование даты
    try:
        while True:
            status = await get_status(request_id)
            if status == "ready":
                return
            try:
                modal_button = await page.query_selector(".Modal__button__ErQBFMuV6x button")
                if modal_button:
                    await modal_button.click()
                    await asyncio.sleep(0.3)
            except Exception:
                pass
        
            if request_id not in future_data:
                future_data[request_id] = asyncio.Future()
            data = await future_data[request_id]  
            
            info_booking(f"{datetime.now()} | Открываю календарь для выбора даты.")
            try:
                await page.wait_for_selector(".Supply-detail-options__plan-desktop-button__-N407e2FDC", timeout=8000)
                plan_button = await page.query_selector(".Supply-detail-options__plan-desktop-button__-N407e2FDC")
                await plan_button.hover()
                await plan_button.click()

                await page.wait_for_selector(".Calendar-plan-table-view__calendar-row", timeout=10000)
                date_rows = await page.query_selector_all(".Calendar-plan-table-view__calendar-row")

                possible_dates = []
                for date_row in date_rows:
                    cells = await date_row.query_selector_all(".Calendar-cell__3yrLIkkTHO")
                    for cell in cells:
                        try:
                            date_text_elem = await cell.query_selector(".Calendar-cell__date-container__2TUSaIwaeG")
                            coef_elem = await cell.query_selector(".Coefficient-table-cell__EqV0w0Bye8")

                            if not date_text_elem or not coef_elem:
                                continue

                            date_status = await date_text_elem.inner_text()
                            coef_text = await coef_elem.inner_text()
                            if coef_text == "Пока недоступно":
                                continue

                            day, month = date_status.split()[:2]
                            english_month = month_translation.get(month.strip(','), month)
                            date_curr = datetime.strptime(f"{day} {english_month} {datetime.now().year}", "%d %B %Y")
                            weekday = date_curr.strftime('%a')
                            weekday_english = day_translation.get(weekday, weekday)

                            if date_start < date_curr <= date_end and weekday_english in custom_dates:
                                coef_value = 0 if coef_text == "Бесплатно" else int(coef_text[1:])
                                possible_dates.append({"cell": cell, "date": date_curr, "coef": coef_value})
                    
                        except Exception as e:
                            logging.warning(f"{datetime.now()} | Ошибка обработки ячейки для request_id={request_id}: {e}")

                if not possible_dates:
                    future_data[request_id] = asyncio.Future()
                    info_booking(f"{datetime.now()} | Обновляю страницу, пытаюсь снова.")
                    await page.reload()
                    await asyncio.sleep(random.uniform(0.5, 2))
                    continue
            
                best_date_info = min(possible_dates, key=lambda x: x["coef"])
                best_date_cell, fact_date, best_coef = best_date_info["cell"], best_date_info["date"], best_date_info['coef']

            except Exception as e:
                logging.warning(f"{datetime.now()} | Ошибка обработки календаря для request_id={request_id}: {e}")
                future_data[request_id] = asyncio.Future()
                await page.reload()
                continue
            info_booking(f"{datetime.now()} | Запланированная дата: {fact_date}, коэффициент: {best_coef}.")
            await best_date_cell.hover()
            plan_confirm_button = await page.query_selector("xpath=//button[.//span[text()='Выбрать']]")
            await plan_confirm_button.click()
            await page.wait_for_selector("xpath=//button[span[normalize-space(text()) = 'Запланировать']]", timeout=10000)
            button = await page.query_selector("xpath=//button[span[normalize-space(text()) = 'Запланировать']]")
            await button.click()
            await page.wait_for_selector(".Badge--lightBlue__GoNBA1KdKR", timeout=100000)
            badge_text = await page.inner_text(".Badge--lightBlue__GoNBA1KdKR")
            future_data[request_id] = asyncio.Future()

            if "Запланировано" in badge_text:
                fact_date_str = fact_date.strftime('%Y-%m-%d')
                await set_cool_bron(fact_date_str, best_coef, request_id)
                info_booking(f"{datetime.now()} | Поставка запланирована для request_id={request_id}.")
                await send_notif(8, request_id)
                return
                
    except Exception as e:
        logging.error(f"{datetime.now()} | Ошибка при бронировании даты для request_id={request_id}: {e}")
    finally:
        await page.close()

async def cicle_coef(requests):
    """Функция циклически обрабатывает запросы."""
    i = 1
    while requests: 
        if i == 1:
            api = stay_api
        else:
            api = second_api
        # Получение идентификаторов складов и типов поставки
        warehouse_ids = ",".join({str(item["warehouse_ids"]) for item in requests}) + "," + ",".join({str(item["supply_type"]) for item in requests})

        try:
            # Получение данных через API
            data = await get_supply_coef(warehouse_ids, api)  # Функция API-запроса
        except Exception as e:
            logging.error(f"{datetime.now()} | Ошибка при запросе коэффициентов: {e}")

        # Обработка каждого запроса
        for request in requests:
            try:
                request_id = int(request["request_id"])
                coefficient = int(request["coefficient"])
                date_start = datetime.strptime(request["date_start"], "%Y-%m-%d")
                date_end = datetime.strptime(request["date_end"], "%Y-%m-%d")
                custom_dates = request["custom_dates"].split(", ")
                warehouse_id = int(request["warehouse_ids"])
                supply_type = int(request["supply_type"])

                # Поиск подходящих данных
                filtred_data = []
                for entry in data:
                    curr_warehouse = entry["warehouseID"]
                    curr_supply_type = int(box_type_mapping.get(entry["boxTypeID"], entry["boxTypeID"]))
                    curr_coef = int(entry["coefficient"])
                    curr_date = entry["date"].split("T")[0]
                    date_obj = datetime.strptime(curr_date, "%Y-%m-%d")  # Преобразуем в объект datetime
                    weekday = date_obj.strftime("%a")
                    weekday_english = day_translation.get(weekday, weekday)
                    # Условие фильтрации
                    if (
                        curr_warehouse == warehouse_id
                        and curr_supply_type == supply_type
                        and 0 <= curr_coef <= coefficient
                        and date_start <= date_obj <= date_end
                        and weekday_english in custom_dates
                    ):
                        filtred_data.append(entry)

                # Если найдено подходящее
                if filtred_data:
                    info_booking(f"{datetime.now()} | Данные найдены для request_id={request_id}: НАЙДЕНЫ!")
                    if request_id in future_data and not future_data[request_id].done():
                        future_data[request_id].set_result(filtred_data)
                else:
                    info_booking(f"{datetime.now()} | Нет подходящих данных для request_id={request_id}.")

            except Exception as e:
                logging.error(f"{datetime.now()} | Ошибка обработки запроса request_id={request['request_id']}: {e}")

        # Обновляем запросы
        requests = await get_data_request_just_searching() 
        if i == 1:
            i = 2
        else:
            i = 1
        await asyncio.sleep(time_to_sleep)  
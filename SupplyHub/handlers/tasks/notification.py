import logging

from bot import bot, dp
from handlers.buttons import notif_send_btn
from handlers.database.connection import get_all_is_process, set_is_processing_and_status, get_user_id, get_request_data, get_warehouse_name
from handlers.tasks.utils import filter_supply_type, format_date_md, escape_markdown_v2

"""Обработка уведомлений"""
async def send_notif(value, request_id):
    value = int(value)
    request_data = await get_request_data(request_id)
    if request_data:
        for row in request_data:
            shop_id, warehouse_id, supply_type, supply_sum, date_start, date_end, supply_number, fact_coefficient, fact_date = row[1], row[2], row[3], row[4], row[11], row[12], row[16], row[17], row[18]
    warehouse_name = await get_warehouse_name(warehouse_id)
    mess = await filter_supply_type(supply_type)
    date_start = await format_date_md(date_start)
    date_end = await format_date_md(date_end)
    fact_date = await format_date_md(fact_date)

    user_id = await get_user_id(shop_id)

    if value == 8:
        mes = (
            f"🤖 *Бронирование поставки {request_id} успешно выполнено!*\n\n"
            f"• *Поставка* {supply_number} > *{supply_sum} шт.* загружена:\n"
            f"• *Тип поставки:* {mess}\n"
            f"• *Склад:* {warehouse_name}\n"
            f"• *Коэффициент:* {fact_coefficient}\n"          
            f"• *Дата поставки:* {fact_date}\n"
        )
        status = "done"
        is_processing = 0

    elif value == 5:
        mes = (
            "🤖 *Бронирование поставки приостановлено!*\n\n"
            f"Не смог найти поставку с номером {supply_number} в кабинете продавца.\n"
        )
        status = "lost_supply"
        is_processing = 0

    elif value in (4, 6, 7):
        mes = (
            "🤖 *Бронирование поставки приостановлено!*\n\n"
            "WildBerries поменял структуру страницы, обновите код.\n"
        )
        status = "lost_supply"
        is_processing = 0

    elif value == 3:
        mes = (
            "🤖 *Бронирование поставки приостановлено!*\n\n"
            "Время для бронирования поставки вышло.\n"
            f"Измените {date_start} и {date_end}"
        )
        status = "timeout"
        is_processing = 0

    elif value == 2:
        mes = (
            "🤖 *Бронирование поставки приостановлено!*\n\n"
            "Проверьте заполнение всех данных запроса."
        )
        status = "lost_supply"
        is_processing = 0

    await set_is_processing_and_status(is_processing, status, request_id)
    mes = await escape_markdown_v2(mes)
    await bot.send_message(chat_id=user_id, text=mes, parse_mode="MarkdownV2", reply_markup=notif_send_btn(request_id))

async def check_and_send_message():
    logging.info("Запуск задачи: check_and_send_message")
    rows = await get_all_is_process()
    for row in rows:
        if int(row["is_processing"]) > 1:
            request_id = int(row["request_id"])
            is_processing = int(row["is_processing"])
            await send_notif(is_processing, request_id)
            logging.info(f"Отправляю сообщение по запросу {request_id}")
import asyncio
import logging
from datetime import datetime

from handlers.params.custom_logging import info_booking
from handlers.database.connection import get_request_searching, get_request_by_status, get_data_request_just_searching
from handlers.chrome_wb.bronirovanie import book_supply, cicle_coef

"""Запуск для бронирования"""
async def process_multiple_requests():
    """Обработка нескольких запросов одновременно."""
    info_booking(f"{datetime.now()} |Запуск задачи: process_multiple_requests. Запускаю бронирование")
    requests = await get_request_searching()
    tasks = [book_supply(request['request_id'], request['shop_id']) for request in requests]
    await asyncio.gather(*tasks)

async def has_searching_requests() -> bool:
    """Проверяет, есть ли в базе записи со статусом 'searching'."""
    info_booking(f"{datetime.now()} | Запуск задачи: has_searching_requests. Проверяю записи")
    result = await get_request_by_status()
    return result is not None

async def check_and_process_requests():
    """Проверяет записи в базе и запускает обработку, если они есть."""
    if await has_searching_requests():
        await process_multiple_requests()

async def check_supplies():
    """Проверяет записи в базе и запускает поиск коэффициентов."""
    requests = await get_data_request_just_searching()
    if requests:
        await cicle_coef(requests)
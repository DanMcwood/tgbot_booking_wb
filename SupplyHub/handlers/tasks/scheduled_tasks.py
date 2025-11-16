import asyncio
import logging
from datetime import datetime

from handlers.params.custom_logging import info_scheduled
from handlers.api_wb.functions import update_all_warehouses
from handlers.tasks.utils import minus_quantities
from handlers.tasks.notification import check_and_send_message
from handlers.tasks.start_bron import check_and_process_requests, check_supplies
from handlers.database.connection import update_active_requests

async def scheduled_update():
    while True:
        info_scheduled(f"{datetime.now()} | Запуск задачи: scheduled_update")
        await update_all_warehouses()
        await asyncio.sleep(6 * 60 * 60)  

async def scheduled_task():
    while True:
        info_scheduled(f"{datetime.now()} | Запуск задачи: scheduled_task")
        await minus_quantities()
        await asyncio.sleep(24 * 60 * 60) 

async def scheduled_supply_booking():
    info_scheduled(f"{datetime.now()} | Запуск задачи: scheduled_supply_booking")
    await check_and_process_requests()

async def scheduled_message():
    while True:
        info_scheduled(f"{datetime.now()} | Запуск задачи: scheduled_message")
        await check_and_send_message()
        await asyncio.sleep(180)

async def scheduled_active_requests():
    while True:
        info_scheduled(f"{datetime.now()} | Запуск задачи: scheduled_active_requests")
        await update_active_requests()
        await asyncio.sleep(60)

async def schedule_task_every_minute(task):
    """Запускает указанную задачу каждую минуту независимо от её завершения."""
    while True:
        asyncio.create_task(task())
        await asyncio.sleep(60)

async def schedule_request():
    """Запускает указанную задачу каждую минуту независимо от её завершения."""
    while True:
        await check_supplies()
        await asyncio.sleep(60)
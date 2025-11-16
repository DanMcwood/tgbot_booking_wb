import asyncio
import logging
from datetime import datetime

from handlers.params.custom_logging import info_scheduled
from handlers.params.settings import API_TOKEN
from handlers.__init__ import register_all_handlers
from handlers.tasks.scheduled_tasks import scheduled_message, scheduled_supply_booking, scheduled_update, scheduled_task, scheduled_active_requests, schedule_task_every_minute, schedule_request
from bot import bot, dp

async def run_cron_tasks():
    """Запуск задач на основе asyncio."""
    tasks = [
    asyncio.create_task(scheduled_update()),
    asyncio.create_task(scheduled_task()),
    asyncio.create_task(scheduled_active_requests()),
    asyncio.create_task(scheduled_message()),
    asyncio.create_task(schedule_task_every_minute(scheduled_supply_booking)),
    asyncio.create_task(schedule_request()),
    ]
    info_scheduled(f"{datetime.now()} | CRON-задачи (через asyncio) запущены")
    await asyncio.gather(*tasks)
    
async def run_bot():
    """Функция для запуска бота"""
    register_all_handlers(dp)
    logging.info(f"{datetime.now()} | Бот и CRON-задачи запущены")
    await dp.start_polling(bot)

async def main():
    """Основная функция"""
    await asyncio.gather(run_cron_tasks(), run_bot())

if __name__ == "__main__":
    asyncio.run(main())


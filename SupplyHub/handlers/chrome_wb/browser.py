import os
import logging
from playwright.async_api import async_playwright
import shutil
import psutil
import asyncio
from datetime import datetime

from handlers.chrome_wb.config import configure_page_for_stealth

class BrowserManager:
    """Singleton для управления браузерами."""
    _browsers = {}
    _active_pages = {}
    _locks = {}

    @classmethod
    async def get_browser(cls, user_id):
        """Инициализация браузера с уникальным профилем."""
        user_id = int(user_id)
        if user_id not in cls._locks:
            cls._locks[user_id] = asyncio.Lock() 

        async with cls._locks[user_id]: 
            if user_id not in cls._browsers:
                logging.info(f"{datetime.now()} | Инициализация браузера для пользователя {user_id}")
                try:
                    os.makedirs(f"C:/Users/huawei/desktop/SupplyHub/profiles/{user_id}", exist_ok=True)
                    playwright = await async_playwright().start()
                    browser = await playwright.chromium.launch_persistent_context(
                        user_data_dir=f"C:/Users/huawei/desktop/SupplyHub/profiles/{user_id}",
                        headless=False,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--disable-extensions",
                            "--disable-infobars",
                            "--enable-automation",
                            "--no-first-run",
                            "--enable-webgl",
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-background-timer-throttling",
                            "--disable-renderer-backgrounding"
                        ]
                    )
                    cls._browsers[user_id] = browser
                    logging.info(f"{datetime.now()} | Браузер для пользователя {user_id} успешно запущен.")
                except Exception as e:
                    logging.error(f"{datetime.now()} | Ошибка инициализации браузера для пользователя {user_id}: {e}")
                    raise
            return cls._browsers[user_id]

    @classmethod
    async def close_browser(cls, user_id):
        """Закрытие браузера для конкретного пользователя."""
        user_id = int(user_id)
        if user_id in cls._browsers:
            logging.info(f"{datetime.now()} | Закрытие браузера для пользователя {user_id}")
            try:
                await cls._browsers[user_id].close()
                del cls._browsers[user_id]
                if user_id in cls._active_pages:
                    del cls._active_pages[user_id]
            except Exception as e:
                logging.error(f"{datetime.now()} | Ошибка при закрытии браузера для пользователя {user_id}: {e}")
            finally:
                if user_id in cls._locks:
                    del cls._locks[user_id]

    @classmethod
    async def get_active_page(cls, user_id):
        """Получение активной страницы браузера."""
        user_id = int(user_id)
        if user_id in cls._active_pages:
            logging.info(f"{datetime.now()} | Активная страница для пользователя {user_id} уже существует.")
            return cls._active_pages[user_id]

        logging.info(f"{datetime.now()} | Создаем новую страницу для пользователя {user_id}")
        browser = await cls.get_browser(user_id)
        page = await browser.new_page()
        await configure_page_for_stealth(page)
        cls._active_pages[user_id] = page
        return cls._active_pages[user_id]

    @classmethod
    async def get_active_request_page(cls, user_id, request_id):
        """Получение активной страницы браузера."""
        user_id = int(user_id)
        request_id = int(request_id)
        if request_id in cls._active_pages:
            logging.info(f"{datetime.now()} | Активная страница для пользователя {user_id} уже существует.")
            return cls._active_pages[request_id]

        logging.info(f"{datetime.now()} | Создаем новую страницу для пользователя {user_id}")
        browser = await cls.get_browser(user_id)
        page = await browser.new_page()
        await configure_page_for_stealth(page)
        cls._active_pages[request_id] = page
        return cls._active_pages[request_id]
    
    @classmethod
    async def logout(cls, user_id):
        """Явный выход пользователя и удаление данных сессии."""
        user_id = int(user_id)
        logging.info(f"Начало выхода пользователя {user_id}.")

        try:
            page = await cls.get_active_page(user_id)
            await page.goto("https://seller.wildberries.ru/logout") 
            logging.info(f"{datetime.now()} | Выполнен явный выход из учётной записи для пользователя {user_id}.")
        except Exception as e:
            logging.warning(f"{datetime.now()} | Не удалось выполнить выход из учётной записи для пользователя {user_id}: {e}")

        try:
            await page.context.clear_cookies()  
            logging.info(f"{datetime.now()} | Куки и локальное хранилище очищены для пользователя {user_id}.")
        except Exception as e:
            logging.warning(f"{datetime.now()} | Не удалось очистить куки или локальное хранилище для пользователя {user_id}: {e}")

        await cls.close_browser(user_id)

        profile_path = f"C:/Users/huawei/desktop/SupplyHub/profiles/{user_id}"
        if os.path.exists(profile_path):
            try:
                cls._kill_playwright_processes() 
                shutil.rmtree(profile_path, ignore_errors=False)
                logging.info(f"{datetime.now()} | Профиль пользователя {user_id} успешно удалён.")
            except Exception as e:
                logging.error(f"{datetime.now()} | Ошибка при удалении профиля пользователя {user_id}: {e}")
        else:
            logging.warning(f"{datetime.now()} | Профиль пользователя {user_id} отсутствует.")

    @classmethod
    def _kill_playwright_processes(cls):
        """Принудительно завершаем процессы Playwright."""
        logging.info(f"{datetime.now()} | Проверяем активные процессы Playwright.")
        for process in psutil.process_iter(['name']):
            try:
                if process.info['name'] in ('playwright-cli', 'chrome', 'chromium', 'msedge'):
                    logging.info(f"{datetime.now()} | Завершаем процесс: {process.info['name']} (PID: {process.pid})")
                    process.terminate() 
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logging.error(f"{datetime.now()} | Ошибка при завершении процесса: {e}")
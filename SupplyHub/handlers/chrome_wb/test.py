import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import os
import logging
import asyncio
import uuid
from datetime import datetime
from playwright.async_api import async_playwright, Error

class BrowserManager:
    _playwright = None
    _page_ids = {}
    _locks = {}

    @classmethod
    async def _get_playwright(cls):
        """Инициализация Playwright как singleton."""
        if cls._playwright is None:
            cls._playwright = await async_playwright().start()
        return cls._playwright

    @classmethod
    async def _create_new_tab(cls, user_id):
        """Создание новой вкладки для пользователя."""
        logging.info(f"{datetime.now()} | Создается новая вкладка для пользователя {user_id}.")
        
        if user_id not in cls._locks:
            cls._locks[user_id] = asyncio.Lock()

        async with cls._locks[user_id]:
            try:
                # Проверяем наличие активных вкладок
                if user_id in cls._page_ids:
                    open_pages = [page_id for page_id, page in cls._page_ids[user_id].items() if not page.is_closed()]
                    if open_pages:
                        # Используем первую открытую вкладку
                        existing_page_id = open_pages[0]
                        logging.info(f"{datetime.now()} | Используется существующая вкладка {existing_page_id} для пользователя {user_id}.")
                        return cls._page_ids[user_id][existing_page_id], existing_page_id

                # Создаем новый контекст, если нет активных вкладок
                playwright = await cls._get_playwright()
                profile_path = f"C:/Users/huawei/Desktop/SupplyHub/profiles/{user_id}"
                os.makedirs(profile_path, exist_ok=True)
                playwright = await async_playwright().start()
                if playwright is None:
                    raise Exception("Playwright не был инициализирован.")

                # Создаем контекст браузера
                context = await playwright.chromium.launch_persistent_context(
                    user_data_dir=profile_path,
                    headless=False,
                    args=[]
                )
                pages = context.pages
                if pages:
                    logging.error(f"{datetime.now()} | Ошибка: Контекст для пользователя {user_id} был закрыт.")
                    raise Error("Контекст закрыт после создания.")

                # Проверяем активные страницы в новом контексте
                if context.pages:
                    for page in context.pages:
                        if not page.is_closed():
                            page_id = next((pid for pid, p in cls._page_ids.get(user_id, {}).items() if p == page), str(uuid.uuid4()))
                            cls._page_ids.setdefault(user_id, {})[page_id] = page
                            logging.info(f"{datetime.now()} | Используется существующая вкладка с ID {page_id} из нового контекста.")
                            return page, page_id

                # Создаем новую вкладку
                page = await context.new_page()

                # Сохраняем новую вкладку
                page_id = str(uuid.uuid4())
                cls._page_ids.setdefault(user_id, {})[page_id] = page

                logging.info(f"{datetime.now()} | Новая вкладка создана с ID {page_id} для пользователя {user_id}.")
                return page, page_id
            except Error as e:
                logging.error(f"{datetime.now()} | Ошибка Playwright для пользователя {user_id}: {e}")
                cls._page_ids.pop(user_id, None)  # Очистка данных о вкладках
                raise
            except Exception as e:
                logging.error(f"{datetime.now()} | Неизвестная ошибка при создании вкладки для пользователя {user_id}: {e}")
                raise

@pytest.mark.asyncio
async def test_create_new_tab():
    """
    Проверка создания новой вкладки для пользователя.
    """
    user_id = "test_user_1"

    # Создаем новую вкладку
    page, page_id = await BrowserManager._create_new_tab(user_id)

    # Проверяем, что вкладка создана
    assert page is not None, "Вкладка должна быть создана"
    assert page_id is not None, "Идентификатор вкладки должен быть создан"
    assert user_id in BrowserManager._page_ids, "Должен быть записан пользователь"
    assert page_id in BrowserManager._page_ids[user_id], "Должна быть сохранена вкладка пользователя"

    # Закрываем вкладку
    await page.close()
    assert page.is_closed(), "Вкладка должна быть закрыта"


@pytest.mark.asyncio
async def test_reuse_existing_tab():
    """
    Проверка повторного использования существующей вкладки.
    """
    user_id = "test_user_2"

    # Создаем первую вкладку
    page1, page_id1 = await BrowserManager._create_new_tab(user_id)

    # Повторно вызываем создание вкладки
    page2, page_id2 = await BrowserManager._create_new_tab(user_id)

    # Проверяем, что вкладка не создается заново, а используется существующая
    assert page1 == page2, "Должна быть использована существующая вкладка"
    assert page_id1 == page_id2, "Идентификатор вкладки должен совпадать"

    # Закрываем вкладку
    await page1.close()


@pytest.mark.asyncio
async def test_create_tab_after_closing_context():
    """
    Проверка создания новой вкладки после закрытия контекста.
    """
    user_id = "test_user_3"

    # Создаем новую вкладку
    page1, page_id1 = await BrowserManager._create_new_tab(user_id)

    # Закрываем контекст вручную
    context = page1.context
    await context.close()

    # Проверяем, что контекст закрыт
    assert context.is_closed(), "Контекст должен быть закрыт"

    # Создаем новую вкладку после закрытия контекста
    page2, page_id2 = await BrowserManager._create_new_tab(user_id)

    # Проверяем, что создана новая вкладка
    assert page2 is not None, "Новая вкладка должна быть создана"
    assert page_id1 != page_id2, "Идентификаторы вкладок должны различаться"


@pytest.mark.asyncio
async def test_error_handling():
    """
    Проверка обработки ошибок при создании вкладки.
    """
    user_id = "test_user_4"

    # Мокаем метод создания контекста, чтобы выбрасывать ошибку
    with patch("playwright.async_api.async_playwright") as mock_playwright:
        mock_playwright.return_value.chromium.launch_persistent_context = AsyncMock(side_effect=Exception("Ошибка браузера"))
        
        # Проверяем, что ошибка обрабатывается
        with pytest.raises(Exception, match="Ошибка браузера"):
            await BrowserManager._create_new_tab(user_id)

    # Проверяем, что вкладка для пользователя не была создана
    assert user_id not in BrowserManager._page_ids, "Не должно быть записей для пользователя после ошибки"

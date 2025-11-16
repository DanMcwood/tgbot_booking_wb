import logging
from datetime import datetime

from handlers.chrome_wb.browser import BrowserManager 
from handlers.database.connection import set_session

async def send_phone_number(user_id, phone_number: str):
    """Ввод номера телефона на сайте Wildberries."""
    logging.info(f"{datetime.now()} | Ввод номера телефона для пользователя {user_id}")
    page = await BrowserManager.get_active_page(user_id)
    
    try:
        await page.goto("https://seller-auth.wildberries.ru/")
        logging.info(f"{datetime.now()} | Текущий URL: {page.url}")
        logging.info("Открыта страница авторизации Wildberries")

        phone_input_selector = "input[data-testid='phone-input']"
        await page.wait_for_selector(phone_input_selector)

        if phone_number.startswith('+7'):
            phone_number = phone_number[2:]
        elif phone_number.startswith('8'):
            phone_number = phone_number[1:]
        elif phone_number.startswith('7'):
            phone_number = phone_number[1:]

        phone_input = await page.query_selector(phone_input_selector)
        await phone_input.fill(phone_number)

        submit_button_selector = "button[data-testid='submit-phone-button']"
        await page.wait_for_selector(submit_button_selector)
        submit_button = await page.query_selector(submit_button_selector)
        await submit_button.click()
        logging.info(f"{datetime.now()} | Номер телефона {phone_number} отправлен.")

        sms_input_selector = '[data-testid="sms-code-input"]'
        logging.info("Ожидаем появления поля для ввода SMS-кода...")

        try:
            await page.wait_for_selector(sms_input_selector, timeout=60000)  
            logging.info("Поле для ввода SMS-кода найдено. Ожидаем ввода кода.")
            return True
        except Exception:
            logging.warning("Поле для ввода SMS-кода так и не появилось.")
            await page.screenshot(path="screenshot_sms_error.png")
            logging.info("Скриншот страницы сохранён.")
            return False
    except Exception as e:
        logging.error(f"{datetime.now()} | Ошибка при вводе номера телефона для пользователя {user_id}: {e}")
        return False

async def send_sms_code(user_id, sms_code: str):
    """Ввод SMS-кода на сайте Wildberries."""
    logging.info(f"{datetime.now()} | Ввод SMS-кода для пользователя {user_id}")
    page = await BrowserManager.get_active_page(user_id)

    try:
        sms_input_selector = '[data-testid="sms-code-input"]'
        await page.wait_for_selector(sms_input_selector, timeout=60000)

        code_inputs = await page.query_selector_all(sms_input_selector)
        for i, code_input in enumerate(code_inputs):
            await code_input.fill(sms_code[i])

        logging.info(f"{datetime.now()} | SMS-код {sms_code} отправлен.")

        await page.wait_for_url("https://seller.wildberries.ru/", timeout=15000)
        logging.info(f"{datetime.now()} | Авторизация для пользователя {user_id} завершена успешно.")
        await set_session(1, user_id)
        return True
    except Exception as e:
        logging.error(f"{datetime.now()} | Ошибка при вводе SMS-кода для пользователя {user_id}: {e}")
        return False
from aiogram import Dispatcher
import asyncio
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

# Импортируем функции
from handlers.database.connection import get_notification, get_selected_shop, get_shop_name, set_notification, get_user_urls, insert_urls, get_url_data, set_url, set_url_name, set_session, get_session, del_url, set_start_date, delete_dates_start_end
from handlers.buttons import settings_buttons, notification_buttons, urls_buttons, urls_ext_buttons, choose_url_btn, next_step_go, exit_btn, coef_btn, create_days_keyboard, create_delivery_keyboard, create_search_period_keyboard, create_calendar_keyboard, last_keayboard, bron_start_btn
from handlers.params.fsmGroups import Form
from handlers.chrome_wb.postavki import update_supplies
from handlers.tasks.utils import start_searching, escape_markdown_v2, format_date_md, filter_supply_type, minus_quantities, look_google, look_excel, select_day, set_dates_period
from handlers.params.settings import days_of_week
from handlers.chrome_wb.auth import BrowserManager
from handlers.params.fsmGroups import RegisterStates
from handlers.lists.registration import process_name
from bot import bot, dp

###### Настройки   #############################################################################################################

async def settings_menu(callback_query: CallbackQuery = None, source_message: Message = None, state: FSMContext = None):
    if callback_query:
        user_id = callback_query.from_user.id
        messs = ""
        _, id = callback_query.data.split(":")
        id = int(id)
        if id != 0:
            await del_url(id)
    elif source_message:
        user_data = await state.get_data()
        mes_id = user_data.get("mes_id")
        chat_id = user_data.get("chat_id")
        await state.clear()
        user_id = source_message.from_user.id
        messs = "*Ссылка успешно добавлена/изменена!*"
    else:
        raise ValueError("Either 'callback_query' or 'source_message' must be provided")
    selected_shop = await get_selected_shop(user_id)
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    current_state = await get_notification(user_id)
    if current_state == 1:
        mess = "🔔"
    else:
        mess = "🔕"

    value = await get_session(user_id)
    value = int(value)
    mes = (
        "⚙️ *Настройки*\n\n"
        f"👤 Пользователь: {user_id}\n"
        f"🛒 Выбранный магазин: {shop_name}\n"
        f"{messs}"
    )
    mes = await escape_markdown_v2(mes)
    if callback_query:
        await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=settings_buttons(mess, value))
    elif source_message:
        await bot.edit_message_text(text=mes, parse_mode="MarkdownV2",  chat_id=chat_id, message_id=mes_id, reply_markup=settings_buttons(mess, value))


async def settings_notifications(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    _, value = callback_query.data.split(":")
    current_state = await get_notification(user_id)
    print(current_state)
    value, current_state = int(value), int(current_state)
    selected_shop = await get_selected_shop(user_id)
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    mess = "Уведомления используются для оповещения пользователя об успешном бронировании поставки."
    if value == 1:
        if current_state == 1:
            current_state -= 1
            mess = "🔕 Уведомления выключены"
        else:
            current_state += 1
            mess = "🔔 Уведомления включены"
        await set_notification(user_id, current_state)
    
    mes = (
        "⚙️ *Настройки*\n\n"
        f"👤 Пользователь: {user_id} • {shop_name}\n\n"
        f"{mess}"
    )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=notification_buttons(current_state))

async def settings_urls(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    _, page = callback_query.data.split(":")
    page = int(page)
    selected_shop = await get_selected_shop(user_id)
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    urls = await get_user_urls(selected_shop)
    
    mes = (
        "⚙️ *Настройки*\n\n"
        f"👤 Пользователь: {user_id} • {shop_name}\n\n"
        "🔗 *Ваши ссылки:*"
    )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=urls_buttons(urls, page))

async def add_name_urls(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    selected_shop = await get_selected_shop(user_id)
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    mes = (
        "⚙️ *Настройки*\n\n"
        f"👤 Пользователь: {user_id} • {shop_name}\n\n"
        "🔗 Введите *название* для ссылки:"
    )
    mes = await escape_markdown_v2(mes)
    new_mes = await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=urls_ext_buttons())
    await state.set_state(Form.waiting_for_name_url)
    await state.update_data(mes_id=new_mes.message_id, chat_id=callback_query.message.chat.id)

async def add_urls(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await state.get_data()
    mes_id = user_data.get("mes_id")
    chat_id = user_data.get("chat_id")
    selected_shop = await get_selected_shop(user_id)
    url_name = message.text
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    mes = (
        "⚙️ *Настройки*\n\n"
        f"👤 Пользователь: {user_id} • {shop_name}\n\n"
        "🔗 Пришли *ссылку* на таблицу:\n"
        "Она должна быть в открытом доступе"
    )
    mes = await escape_markdown_v2(mes)
    await message.delete()
    new_mes = await bot.edit_message_text(text=mes, parse_mode="MarkdownV2", chat_id=chat_id, message_id=mes_id, reply_markup=urls_ext_buttons())
    await state.clear()
    await state.set_state(Form.waiting_for_url)
    await state.update_data(url_name=url_name, mes_id=new_mes.message_id, chat_id=message.chat.id)

async def finish_add_urls(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    url_name = data.get('url_name')
    mes_id = data.get("mes_id")
    chat_id = data.get("chat_id")
    url = message.text
    selected_shop = await get_selected_shop(user_id)
    await insert_urls(selected_shop, url_name, url) 
    await message.delete()
    await state.update_data(url_name=url_name, mes_id=mes_id, chat_id=chat_id)
    await settings_menu(source_message=message, state=state)

async def look_urls(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    _, url_id = callback_query.data.split(":")
    url_id = int(url_id)
    selected_shop = await get_selected_shop(user_id)
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    url_name, url = await get_url_data(url_id)
    mes = (
        "⚙️ *Настройки*\n\n"
        f"👤 Пользователь: {user_id} • {shop_name}\n"
        f"🔗 *Название*: {url_name}\n"
        f"*Ссылка*: {url}"
    )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=choose_url_btn(url_id))

async def relook_uerls(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    _, value, url_id = callback_query.data.split(":")
    value, url_id = int(value), int(url_id) 
    user_id = callback_query.from_user.id
    selected_shop = await get_selected_shop(user_id)
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    
    if value == 1 or value == 3:
        messs = "🔗 Введите новое название для ссылки:"
    elif value == 2:
        messs = ("🔗 Пришли ссылку на таблицу:\nОна должна быть в открытом доступе")

    mes = (
        "⚙️ *Настройки*\n\n"
        f"👤 Пользователь: {user_id} • {shop_name}\n\n"
        f"{messs}"
    )
    mes = await escape_markdown_v2(mes)
    new_mes = await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=urls_ext_buttons())
    await state.set_state(Form.waiting_for_change)
    await state.update_data(url_id=url_id, value=value, mes_id=new_mes.message_id, chat_id=callback_query.message.chat.id)

async def changing_url(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    mes_id = data.get("mes_id")
    chat_id = data.get("chat_id")
    selected_shop = await get_selected_shop(user_id)
    time_value = message.text
    data = await state.get_data()
    url_id = data.get('url_id')
    value = data.get('value')
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    if int(value) == 1: 
        await set_url_name(url_id, time_value)
        await message.delete()
        await state.clear()
        await state.update_data(mes_id=mes_id, chat_id=message.chat.id)
        await settings_menu(source_message=message, state=state)
    elif int(value) == 3:
        await set_url_name(url_id, time_value)
        value = 4
        await message.delete()
        mes = (
            "⚙️ *Настройки*\n\n"
            f"👤 Пользователь: {user_id} • {shop_name}\n\n"
            "🔗 Пришли новую *ссылку* на таблицу:\n"
            "Она должна быть в открытом доступе"
        )
        mes = await escape_markdown_v2(mes) 
        new_mes = await bot.edit_message_text(text=mes, parse_mode="MarkdownV2", chat_id=chat_id, message_id=mes_id, reply_markup=urls_ext_buttons())
        await state.clear()
        await state.set_state(Form.waiting_for_change)
        await state.update_data(url_id=url_id, value=value, mes_id=new_mes.message_id, chat_id=message.chat.id)
    elif int(value) == 2 or int(value) == 4:
        await set_url(url_id, time_value)
        await message.delete()
        await state.clear()
        await state.update_data(url_id=url_id, value=value, mes_id=mes_id, chat_id=message.chat.id)
        await settings_menu(source_message=message, state=state)

async def handle_exit_button(callback_query: CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    _, value = callback_query.data.split(":")
    value = int(value)
    if value == 1:
        await callback_query.message.edit_text("🚀 Выполняется загрузка...")
        await BrowserManager.logout(user_id)
        await callback_query.message.edit_text("Вы успешно вышли из системы.")
        value = 0
        await set_session(value, user_id)
        await asyncio.sleep(1)
        await settings_menu(callback_query)
    else:
        new_mes = await callback_query.message.edit_text("Проверяю сессии...")
        await asyncio.sleep(1)
        await state.set_state(RegisterStates.waiting_for_name)
        await state.update_data(hello_message_id=new_mes.message_id, chat_id=callback_query.message.chat.id, value = 1, user_id=user_id)
        await process_name(Message, state)

# Регистрация команд
def menu_settings_commands(dp: Dispatcher):
    dp.callback_query.register(settings_menu, lambda c: c.data.startswith('keysettings'))
    dp.callback_query.register(settings_notifications, lambda c: c.data.startswith('notifications'))
    dp.callback_query.register(settings_urls, lambda c: c.data.startswith('urls_update'))
    dp.callback_query.register(add_name_urls, lambda c: c.data.startswith('loopingurlname'))
    dp.message.register(add_urls, Form.waiting_for_name_url)
    dp.message.register(finish_add_urls, Form.waiting_for_url)
    dp.callback_query.register(look_urls, lambda c: c.data.startswith('plookurls'))
    dp.callback_query.register(relook_uerls, lambda c: c.data.startswith('kjeay'))
    dp.message.register(changing_url, Form.waiting_for_change)
    dp.callback_query.register(handle_exit_button, lambda c: c.data.startswith('exitfromuser'))
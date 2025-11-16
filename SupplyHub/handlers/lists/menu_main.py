from aiogram import Dispatcher
from aiogram.types import CallbackQuery
import asyncio
from aiogram import types
from aiogram.fsm.context import FSMContext

# Импортируем функции
from handlers.database.connection import get_active_requests, get_selected_shop, get_shop_name, check_user_exists
from handlers.buttons import main_menu_btn
from handlers.tasks.utils import escape_markdown_v2
#Главное меню
async def main_menu_callback(callback_query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    selected_shop = await get_selected_shop(callback_query.from_user.id)
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    user = await check_user_exists(callback_query.from_user.id)

    # Получаем количество активных запросов
    active_requests = await get_active_requests(callback_query.from_user.id)
    nickname = user['nickname'] if user['nickname'] else callback_query.from_user.first_name

    # Формируем текст для личного кабинета
    user_info_text = (
        f"Приветствую, {nickname}!\n\n"
        "*👤 Личный кабинет*\n\n"
        f"🆔 {callback_query.from_user.id}\n"
        f"🛒 Выбранный магазин: {shop_name}\n"
        f"📋 Активные запросы: {active_requests}"
    )
    mes = await escape_markdown_v2(user_info_text)
    await callback_query.message.edit_text(mes, parse_mode="MarkdownV2",reply_markup=main_menu_btn())  # Отправляем информацию о пользователе

# Регистрация команд
def menu_main_commands(dp: Dispatcher):
    dp.callback_query.register(main_menu_callback, lambda c: c.data.startswith("main_menu"))

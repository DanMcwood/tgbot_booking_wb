from aiogram import Dispatcher, types, F
from datetime import datetime
import asyncio
from aiogram import types 

# Импортируем функции
from handlers.params.settings import last_update_time
from handlers.database.connection import get_selected_shop, set_favorite_warehouses, get_warehouses_and_favorite, get_shop_name
from handlers.api_wb.functions import update_warehouses
from handlers.buttons import warehouses_btn, is_supply_btn
from handlers.tasks.utils import escape_markdown_v2

###### Избранные склады   #############################################################################################################

async def handle_warehouse_buttons(callback_query: types.CallbackQuery, page=None, request=None):
    _, unknown, page, request = callback_query.data.split(":")
    user_id = callback_query.from_user.id

    user_data = await get_selected_shop(user_id)
    shop_name = await get_shop_name(user_data) if user_data else "Не выбран"
    selected_shop = user_data
    warehouses, favorite_warehouses = await get_warehouses_and_favorite(selected_shop)

    page, request = int(page.strip()), int(request.strip())

    # Формируем текст для личного кабинета
    user_info_text = (
        "📦 *Избранные склады*\n\n"
        f"🆔 {user_id}\n"
        f"🛒 Выбранный магазин: {shop_name}"
    )
    mes = await escape_markdown_v2(user_info_text)
    await callback_query.message.edit_text(mes, parse_mode="MarkdownV2", reply_markup=warehouses_btn(warehouses, favorite_warehouses, page, request))

# Обработчик кнопки выбрать склад
async def handle_update_bron(callback_query: types.CallbackQuery):
    data = callback_query.data.split(":")
    warehouse_id = int(data[1])
    await callback_query.message.edit_text("Хотите создать новое бронирование?", reply_markup=is_supply_btn(warehouse_id))

# Обработчик кнопки выбрать склад любимым
async def toggle_favorite_warehouse(callback_query: types.CallbackQuery):
    _, warehouse_id, page, request = callback_query.data.split(":")
    warehouse_id, page, request = int(warehouse_id.strip()), int(page.strip()), int(request.strip())
    
    user_id = callback_query.from_user.id
    
    selected_shop = await get_selected_shop(user_id)
    warehouses, favorite_warehouses = await get_warehouses_and_favorite(selected_shop)

    # Добавляем или удаляем склад из избранного
    if warehouse_id in favorite_warehouses:
        favorite_warehouses.remove(warehouse_id)
    else:
        favorite_warehouses.append(warehouse_id)
    # Обновляем список избранных складов в базе данных
    updated_favorites = ",".join(map(str, favorite_warehouses))

    await set_favorite_warehouses(updated_favorites, selected_shop)
    await callback_query.answer("Избранный склад обновлён!")
    await handle_warehouse_buttons(callback_query, page=page, request=request)

# Обработчик кнопки обновить склады
async def handle_update_button(callback_query: types.CallbackQuery):
    global last_update_time
    current_time = datetime.now()
    user_id = callback_query.from_user.id
    _, unknown, page, request = callback_query.data.split(":")
    page, request = int(page.strip()), int(request.strip())

    # Проверка, прошло ли достаточно времени (1 минута)
    if (current_time - last_update_time).total_seconds() < 60:
        await callback_query.answer("Обновлять склады можно не чаще одного раза в минуту.", show_alert=True)
        return

    last_update_time = current_time
    await update_warehouses(user_id)
    await callback_query.answer("Склады успешно обновлены!")
    await handle_warehouse_buttons(callback_query, page=0, request=request)

##########################################################################################################################################

# Регистрация команд
def menu_warehouses_commands(dp: Dispatcher):
    dp.callback_query.register(handle_warehouse_buttons, lambda c: c.data.startswith('favorite_warehouses'))
    dp.callback_query.register(toggle_favorite_warehouse, lambda c: c.data.startswith('toggle_favorite'))
    dp.callback_query.register(handle_update_button, lambda c: c.data.startswith('update_warehouses'))
    dp.callback_query.register(handle_update_bron, lambda c: c.data.startswith('is_supply'))
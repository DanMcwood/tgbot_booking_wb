from aiogram import Dispatcher, types
from datetime import datetime
from datetime import timedelta

from handlers.database.connection import get_warehouses_and_selected, get_selected_shop, update_selected, get_warehouses_and_favorite, set_null_selected
from handlers.api_wb.functions import update_warehouses, first_get_coef, get_cached_coefficients
from handlers.buttons import select_warehouses_coef, show_history_coef, mistake_btn
from handlers.params.settings import last_update_time
from handlers.tasks.limiter import MultiUserLimiter
from handlers.tasks.utils import filter_data, escape_markdown_v2
user_limiter = MultiUserLimiter(call_limit=6, time_frame=timedelta(minutes=1))

###### Коэффициенты приемки   #############################################################################################################

# Обработчик кнопки "выбор складов для Коэффициенты приемки"
async def show_history(callback_query: types.CallbackQuery, page=None, request=None):
    _, unknown, page, request = callback_query.data.split(":")
    page, request = int(page.strip()), int(request.strip())
    user_id = callback_query.from_user.id

    shop_id = await get_selected_shop(user_id)

    if request == 0:
        selected_warehouses = []
        await set_null_selected(shop_id)
    elif request == 1:
        warehouses, selected_warehouses = await get_warehouses_and_selected(shop_id)
    warehouses, favorite_warehouses = await get_warehouses_and_favorite(shop_id)

    mes = (
        "📈 *Коэффициенты*\n\n"
        "📍 Выбери склады, чтобы посмотреть коэффициенты:"
    )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(mes, parse_mode="MarkdownV2", reply_markup=select_warehouses_coef(warehouses, favorite_warehouses, selected_warehouses, page, request))

# Обработчик кнопки "Коэффициенты приемки складов"
async def show_warehouses_history(callback_query: types.CallbackQuery):
    _, types, data, page, request = callback_query.data.split(":")
    data, page, request = int(data), int(page), int(request)
    user_id = callback_query.from_user.id    
    
    shop_id = await get_selected_shop(user_id)
    warehouses, selected_warehouses = await get_warehouses_and_selected(shop_id)

    if data == 1:
        if await user_limiter.can_user_call(user_id):
            data = await first_get_coef(user_id, selected_warehouses)
            if data == None:
                await callback_query.message.edit_text(text=f"❌ Выбранный склад не принимает поставки", reply_markup=mistake_btn())
                return
            filtred_data = await filter_data(data, types)
        else:
            await callback_query.message.edit_text(text=f"❌ Выполнять запрос можно не более 6 раз в минуту!", reply_markup=mistake_btn())
            return
    else:
        data = await get_cached_coefficients(user_id, selected_warehouses, user_limiter)

    mes = (
        "📈 *Коэффициенты*\n\n"
        "📍 Коэффициенты для выбранных складов:\n"
    )
    filtred_data = await filter_data(data, types)
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(mes, parse_mode="MarkdownV2", reply_markup=show_history_coef(filtred_data, page, request, types))
    
async def handle_got_type(callback_query: types.CallbackQuery):
    _, warehouse_id, page, request = callback_query.data.split(":")
    warehouse_id, page, request = int(warehouse_id), int(page), int(request)
    await callback_query.answer("Выбери тип/типы поставок")
    await show_history(callback_query, page=page, request=request)
    
# Обработчик кнопки выбрать склад 
async def toggle_select_warehouse(callback_query: types.CallbackQuery):
    _, warehouse_id, page, request = callback_query.data.split(":")
    warehouse_id, page, request = int(warehouse_id), int(page), int(request)
        
    user_id = callback_query.from_user.id

    selected_shop = await get_selected_shop(user_id)
    warehouses, selected_warehouses = await get_warehouses_and_selected(selected_shop)

    # Добавляем или удаляем склад из избранного
    if warehouse_id in selected_warehouses:
        selected_warehouses.remove(warehouse_id)
        if warehouse_id == 1 or warehouse_id == 2 or warehouse_id == 3:
            await callback_query.answer("Тип поставки удален!")
        else:
            await callback_query.answer("Cклад удален!")
    else:
        selected_warehouses.append(warehouse_id)
        if warehouse_id == 1 or warehouse_id == 2 or warehouse_id == 3:
            await callback_query.answer("Тип поставки выбран!")
        else:
            await callback_query.answer("Cклад выбран!")

    # Обновляем список избранных складов в базе данных
    updated_favorites = ",".join(map(str, selected_warehouses))

    await update_selected(updated_favorites, selected_shop)
    await show_history(callback_query, page=page, request=request)

# Обработчик кнопки обновить склады
async def handle_update_btn (callback_query: types.CallbackQuery):
    global last_update_time
    current_time = datetime.now()
    user_id = callback_query.from_user.id
    _, unknown, page, request = callback_query.data.split(":")

    # Проверка, прошло ли достаточно времени (1 минута)
    if (current_time - last_update_time).total_seconds() < 60:
        await callback_query.answer("Обновлять склады можно не чаще одного раза в минуту.", show_alert=True)
        return

    last_update_time = current_time
    await update_warehouses(user_id)
    await callback_query.answer("Склады успешно обновлены!")
    await show_history(callback_query, page=page, request=request)
    
##########################################################################################################################################

# Регистрация команд
def menu_coef_commands(dp: Dispatcher):
    dp.callback_query.register(show_history, lambda c: c.data.startswith('history_coefficients'))
    dp.callback_query.register(show_warehouses_history, lambda c: c.data.startswith('show_history_coefficients'))
    dp.callback_query.register(handle_update_btn, lambda c: c.data.startswith('reload_history'))
    dp.callback_query.register(toggle_select_warehouse, lambda c: c.data.startswith('tap_select'))
    dp.callback_query.register(handle_got_type, lambda c: c.data.startswith('aint_got_type'))

    
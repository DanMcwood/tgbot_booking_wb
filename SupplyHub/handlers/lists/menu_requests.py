from aiogram import Dispatcher
from aiogram.types import CallbackQuery

from handlers.database.connection import get_active_requests, get_selected_shop, get_shop_name, get_all_request_data, get_warehouse_name, set_warehouse_id, set_supply_type, get_request_data, set_update_requests_2, set_coef, set_quantities, set_selected_days, get_url_data, get_supply_number, delete_request
from handlers.buttons import requests_btn, request_one_btn, request_choose_edit_btn
from handlers.tasks.utils import start_searching, escape_markdown_v2, format_date_md, filter_supply_type, look_google, set_dates_period
from handlers.params.settings import days_of_week
from handlers.chrome_wb.upload  import upload_supply

######   Запросы    ##################################################################################################################
async def requests_menu(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    _, page, value, request_id, is_active, is_ready, is_done, is_null, is_processing = callback_query.data.split(":")
    page, value, request_id, is_active, is_ready, is_done, is_null, is_processing = int(page), int(value), int(request_id), int(is_active), int(is_ready), int(is_done), int(is_null), int(is_processing)

    selected_shop = await get_selected_shop(user_id)
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    active_requests = await get_active_requests(user_id)
    requests = await get_all_request_data(selected_shop)
    
    #if value == 0: первый запуск
    #elif value == 1: пагинация, переключение актив 
    if value == 2: #кнопки активации поиска
        await start_searching(request_id)
    if value == 9:
        await delete_request(request_id)
    mes = (
        "🤖 *Запросы на бронирование*\n\n"
        f"🆔 {user_id}\n"
        f"🛒 Выбранный магазин: {shop_name}\n"
        f"📋 Активные запросы: {active_requests}"
    )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text = mes, parse_mode="MarkdownV2", reply_markup = await requests_btn(requests, page, is_active, is_ready, is_done, is_null, is_processing))

async def one_request_menu(callback_query: CallbackQuery, callback_data: str = None):
    _, request_id, value, edit_data, edit2_data = callback_query.data.split(":")
    request_id, value = int(request_id), int(value)
    user_id = callback_query.from_user.id

    if value == 2:
        warehouse_id = int(edit_data)
        await set_warehouse_id(warehouse_id, request_id)
    elif value == 3:
        supply_type = edit_data
        await set_supply_type(supply_type, request_id)
    elif value == 4:
        supply_sum = int(edit_data)
        supply_number = int(edit2_data)
        if supply_number != 0:
            await set_update_requests_2(supply_sum, supply_number, request_id)
    elif value == 5:
        coef = int(edit_data)
        await set_coef(coef, request_id)
    elif value == 6:
        quantities = int(edit_data)
        await set_quantities(quantities, request_id)
    elif value == 7:
        serialized_days = edit_data
        selected_days_list = serialized_days.split(",")
        selected_days = {day: (day in selected_days_list) for day in days_of_week}
        selected_days_str = ", ".join([d for d, selected in selected_days.items() if selected])
        await set_selected_days(selected_days_str, request_id)
    elif value == 8:
        period = edit_data
        await set_dates_period(period, request_id)
    elif value == 9:
        url_id = edit_data
        await callback_query.message.edit_text("Выполняется загрузка...")
        url_name, url = await get_url_data(url_id)
        value, supply_sum = await look_google(url, request_id)
        supply_number = await get_supply_number(request_id)
        await upload_supply(request_id, user_id)
        if supply_number != 0:
            await set_update_requests_2(supply_sum, supply_number, request_id)

    request_data = await get_request_data(request_id)
    if request_data:
        for row in request_data:
            shop_id, warehouse_id, supply_type, supply_sum, coefficient, quantities, date_start, date_end, selected_days, edit_date, status, state = row[1], row[2], row[3], row[4], row[7], row[9], row[11], row[12], row[13], row[14], row[15], row[23]
    warehouse_name = await get_warehouse_name(warehouse_id)
    mess = await filter_supply_type(supply_type)
    date_start = await format_date_md(date_start)
    date_end = await format_date_md(date_end)

    if value == 1:
        mes = (
            f"🤖 *Бронирование:* {request_id}         • {edit_date}\n\n"
            "Выбери, что хочешь изменить"
        )
        mes = await escape_markdown_v2(mes)
        await callback_query.message.edit_text(text = mes, parse_mode="MarkdownV2", reply_markup = request_choose_edit_btn(request_id, request_data, warehouse_name, mess))
    else:
        mes = (
            f"🤖 *Бронирование:* {request_id}         • {edit_date}\n\n"
            f"• *Склад:* {warehouse_name}\n"
            f"• *Макс. коэф.:* x{coefficient}\n"       
            f"• *Тип поставки:* {mess}\n"
            f"• *Кол-во:* {supply_sum} шт.\n"
            f"• *Дни недели:* {selected_days}\n"
            f"• *Поиск на дни:* {date_start}:{date_end}\n"
            f"• *Запас дней:* {quantities}"
        )
        mes = await escape_markdown_v2(mes)
        await callback_query.message.edit_text(text = mes, parse_mode="MarkdownV2", reply_markup = request_one_btn(request_id, status, state, supply_type, warehouse_id, supply_sum))

def menu_requests_commands(dp: Dispatcher):
    dp.callback_query.register(requests_menu, lambda c: c.data.startswith('requests_menu'))
    dp.callback_query.register(one_request_menu, lambda c: c.data.startswith('ssselected_request'))

    
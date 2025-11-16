from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from handlers.database.connection import get_active_requests, get_selected_shop, get_shop_name, get_warehouse_name, get_warehouses_and_favorite, delete_request, add_request_to_db, get_request_data, set_update_requests_2, set_quantities, set_selected_days, get_supply_number, set_start_date, delete_dates_start_end, set_status, set_coef, get_user_urls, get_url_data, set_state_request, set_is_processing_and_status
from handlers.buttons import bron_menu_btn, warehouses_btn, supply_type_btn, upload_type_btn, upload_supply_btn, next_step_go, exit_btn, coef_btn, create_days_keyboard, create_delivery_keyboard, create_search_period_keyboard, create_calendar_keyboard, last_keayboard, bron_start_btn, back_btn
from handlers.params.fsmGroups import Form
from handlers.chrome_wb.postavki import update_supplies
from handlers.tasks.utils import filter_supply_async, filter_request_type, filter_supply_text_type, filter_supply_type, look_chat, look_google, look_excel, select_day, set_dates_period, escape_markdown_v2, format_date_md
from handlers.params.settings import days_of_week
from handlers.chrome_wb.upload import upload_supply

######   Автобронирование    ##################################################################################################################
async def auto_booking_menu(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    selected_shop = await get_selected_shop(user_id)
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    active_requests = await get_active_requests(user_id)

    mes = (
        "🤖 *Автобронирование*\n\n"
        f"🆔 {user_id}\n"
        f"🛒 Выбранный магазин: {shop_name}\n"
        f"📋 Активные запросы: {active_requests}"
    )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text = mes, parse_mode="MarkdownV2", reply_markup=bron_menu_btn())

###### Этап 1 - Выбор склада
async def handle_warehouse_id(callback_query: CallbackQuery):
    _, page, request = callback_query.data.split(":")
    page, request = int(page.strip()), int(request.strip())
    
    user_id = callback_query.from_user.id
    user_data = await get_selected_shop(user_id)
    shop_name = await get_shop_name(user_data) if user_data else "Не выбран"
    selected_shop = user_data
    warehouses, favorite_warehouses = await get_warehouses_and_favorite(selected_shop)

    try:
        page = int(page)  
    except (ValueError, IndexError):
        page = 0  

    if request != 1 or request != 2:
        mes = f"*🤖 Бронирование* {request}\n\nВыберите новый склад для поставки:"
    else:
        mes = (
            "*🤖 Новое бронирование*\n\n"
            f"🆔 {user_id}\n"
            f"🛒 Выбранный магазин: {shop_name}\n\n"
            "Выберите склад для поставки:"
        )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(mes, parse_mode="MarkdownV2", reply_markup=warehouses_btn(warehouses, favorite_warehouses, page, request))

###### Этап 2 - Тип поставки
async def handle_supply_file(callback_query: CallbackQuery):
    _, warehouse_id, value = callback_query.data.split(":")
    warehouse_id, value = int(warehouse_id), int(value)
    request_id = "new"
    if value == 1:
        mes = f"*🤖 Бронирование* {warehouse_id}\n\nВыберите новый тип поставки:"
    else:
        warehouse_name = await get_warehouse_name(warehouse_id)

        user_id = callback_query.from_user.id
        user_data = await get_selected_shop(user_id)
        shop_name = await get_shop_name(user_data) if user_data else "Не выбран"

        mes = (
            "*🤖 Новое бронирование*\n\n"
            f"📍 {warehouse_name}\n\n"
            f"🆔 {user_id}\n"
            f"🛒 Выбранный магазин: {shop_name}\n\n"
            "Выбери тип поставки:"
        )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(mes, parse_mode="MarkdownV2", reply_markup=supply_type_btn(warehouse_id, request_id, value))    

###### Этап 3 - Загурзка файла
async def upload_metod_selection(callback_query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    _, supply_type, warehouse_id, request_id, edit  = callback_query.data.split(":")
    supply_type, warehouse_id, edit = int(supply_type.strip()), int(warehouse_id.strip()), int(edit.strip())
    user_id = callback_query.from_user.id

    if edit == 1:
        request_id = int(request_id)
        mes = f"*🤖 Бронирование* {warehouse_id}\n\nВыберите тип загрузки:"
    else:
        if  request_id != "new":  
            request_id = int(request_id.strip())
            await delete_request(request_id)
        
        mess = await filter_supply_type(supply_type)

        user_data = await get_selected_shop(user_id)
        shop_name = await get_shop_name(user_data) if user_data else "Не выбран"
        warehouse_name = await get_warehouse_name(warehouse_id)

        mes = (
            "🤖 *Новое бронирование*\n\n"
            f"📍 {warehouse_name} > {mess}\n\n"
            f"🆔 {user_id}\n"
            f"🛒 Выбранный магазин: {shop_name}\n\n"
            "Выберите метод загрузки:"
        )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(mes, parse_mode="MarkdownV2", reply_markup=upload_type_btn(warehouse_id, supply_type, edit, request_id))

#Ожидание получения поставки
async def handle_upload_selection(callback_query: CallbackQuery, state: FSMContext):
    _, request_type, supply_type, warehouse_id, edit, request_id  = callback_query.data.split(":")
    supply_type, warehouse_id, edit = int(supply_type.strip()), int(warehouse_id.strip()), int(edit.strip())
    user_id = callback_query.from_user.id
    user_data = await get_selected_shop(user_id)

    messs = await filter_request_type(request_type)

    if edit == 1:
        request_id = int(request_id)
        mes = f"*🤖 Бронирование* {request_id}\n{messs}"
        warehouse_name = await get_warehouse_name(warehouse_id)
    else:
        mess = await filter_supply_type(supply_type)        
        shop_name = await get_shop_name(user_data) if user_data else "Не выбран"
        warehouse_name = await get_warehouse_name(warehouse_id)
        
        request_id = await add_request_to_db(user_data, warehouse_id, supply_type, user_id)
        
        mes = (
            "🤖 *Новое бронирование*\n\n"
            f"📍 {warehouse_name} > {mess}\n\n"
            f"🆔 {user_id}\n"
            f"🛒 Выбранный магазин: {shop_name}\n\n"
            f"{messs}"
        )

    if request_type == "draft":
        my_urls = None
        supplies = await update_supplies(user_id)
        supply_text_type = await filter_supply_text_type(supply_type)  
        filtred_supplies = await filter_supply_async(supplies, supply_text_type, warehouse_name)
    elif request_type == "my_google":
        filtred_supplies = None
        my_urls = await get_user_urls(user_data)
    else:
        filtred_supplies = None
        my_urls = None
        await state.update_data(request_id=request_id, request_type=request_type, edit=edit)
        await state.set_state(Form.waiting_for_supply)
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=upload_supply_btn(filtred_supplies, supply_type, warehouse_id, warehouse_name, request_id, edit, my_urls))

###### Этап 4 - Проверка поставки
async def handle_step_4(message: Message, state: FSMContext):    
    user_id = message.from_user.id
    data = await state.get_data()
    request_id = int(data.get('request_id'))
    request_type = data.get('request_type')
    edit = int(data.get('edit'))

    request_data = await get_request_data(request_id)
    if request_data:
        for row in request_data:
            shop_name, warehouse_id, supply_type = row[1], row[2], row[3]
        
    mess = await filter_supply_type(supply_type)

    handler = {"chat": look_chat, "table": look_excel, "google": look_google}.get(request_type)
    value, supply_sum = await handler(message, request_id)
    
    selected_shop = await get_selected_shop(user_id)
    shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"
    warehouse_name = await get_warehouse_name(warehouse_id)
    await message.delete()
    await message.answer("Выполняется загрузка...")
    sucsess = await upload_supply(request_id, user_id)
    if not sucsess:
        value = 4
    supply_number = await get_supply_number(request_id)
    if value in {1, 3, 5}:
        if edit == 1:
            mes = f"*🤖 Бронирование* {request_id}\n*Новое количество:* {supply_sum} шт."
        else:
            if supply_number != 0:
                mes = (
                    "🤖 *Новое бронирование*\n\n"
                    f"📍 {warehouse_name} > {mess}\n\n"
                    f"🆔 {user_id}\n"
                    f"🛒 Выбранный магазин: {shop_name}\n\n"
                    f"Поставка загружена. Количество: {supply_sum} шт."
                )
            else:
                mes = "Ошибка загрузки, повторите попытку."
        mes = await escape_markdown_v2(mes)
        supply_number = 0
        await message.answer(mes, parse_mode="MarkdownV2", reply_markup=next_step_go(supply_type, warehouse_id, supply_sum, request_id, supply_number, edit))        
    else:
        mes = {0: "Неверный формат данных. Ожидается: 'ШК количество' построчно. Попробуйте снова.",
            2: "Неверный формат таблицы. Ожидаются колонки 'Баркод' и 'Количество'.",
            4: "Неверный формат ссылки или доступ ограничен."}.get(value)
        mes = await escape_markdown_v2(mes)
        await message.answer(mes, parse_mode="MarkdownV2", reply_markup=exit_btn(supply_type, warehouse_id, request_id, edit))
        await state.clear()
        await state.update_data(request_id=request_id, request_type=request_type, edit=edit)
        await state.set_state(Form.waiting_for_supply)

###### Этап 5 - Коэффициент приемки
async def handle_step_5(callback_query: CallbackQuery, state: FSMContext, callback_data: str = None):
    user_id = callback_query.from_user.id
    _, supply_type, warehouse_id, supply_sum, request_id, supply_number, edit = callback_query.data.split(":")
    supply_type, warehouse_id, supply_sum, request_id, supply_number, edit = int(supply_type), int(warehouse_id), int(supply_sum), int(request_id), int(supply_number), int(edit)
    sucsess = True
    if edit == 1:
        mes = f"*🤖 Бронирование* {request_id}\nВыберите максимальный коэффициент:"
        serialized_days = 1
        mes = await escape_markdown_v2(mes)
        btns = coef_btn(supply_type, warehouse_id, request_id, serialized_days, edit)
        await callback_query.message.edit_text(text = mes, parse_mode="MarkdownV2", reply_markup=btns)
    else:
        if edit == 2:
            url_id = supply_type
            await callback_query.message.edit_text("Выполняется загрузка...")
            url_name, url = await get_url_data(url_id)
            value, supply_sum = await look_google(url, request_id)
            supply_number = await get_supply_number(request_id)
            sucsess = await upload_supply(request_id, user_id)
            edit = 0

        if not sucsess:
            mes = "*Ошибка загрузки поставки.*\n Вернитесь назад"
            btns = back_btn(supply_type, warehouse_id, request_id, edit)
            mes = await escape_markdown_v2(mes)
            await callback_query.message.edit_text(text = mes, parse_mode="MarkdownV2", reply_markup=btns)
        else:
            selected_days = {day: True for day in days_of_week}
            serialized_days = ",".join(day for day, selected in selected_days.items() if selected)
            if supply_number != 0:
                await set_update_requests_2(supply_sum, supply_number, request_id)
            await set_state_request(2, request_id)
            request_data = await get_request_data(request_id)
            if request_data:
                for row in request_data:
                    shop_name, warehouse_id, supply_type = row[21], row[2], row[3]

            warehouse_name = await get_warehouse_name(warehouse_id)

            mess = await filter_supply_type(supply_type)

            mes = (
                "🤖 *Новое бронирование*\n\n"
                f"📍 {warehouse_name} > {mess} > {supply_sum} шт.\n\n"
                f"🆔 {user_id}\n"
                f"🛒 Выбранный магазин: {shop_name}\n\n"
                "Выберите максимальный коэффициент:"
            )
            btns = coef_btn(supply_type, warehouse_id, request_id, serialized_days, edit)
            mes = await escape_markdown_v2(mes)
            await callback_query.message.edit_text(text = mes, parse_mode="MarkdownV2", reply_markup=btns)

###### Этап 6 - Выбор дней недели
# Обработчик выбора коэффициента
async def handle_coefficient(callback_query: CallbackQuery, state: FSMContext):
    _, value, coefficient, request_id, serialized_days, edit = callback_query.data.split(":")
    coefficient, request_id, edit = int(coefficient), int(request_id), int(edit)
    if isinstance(value, int):
        int(value)
    user_id = callback_query.from_user.id
    selected_days_list = [day.strip() for day in serialized_days.split(",")]
    await set_coef(coefficient, request_id)
    selected_days = {day: (day in selected_days_list) for day in days_of_week}
    selected_days = await select_day(value, selected_days)
    serialized_days = ",".join(day for day, selected in selected_days.items() if selected)
    if edit == 1:
        supply_type, warehouse_id, supply_sum, supply_number = 1, 1, 1, 1
        mes = f"*🤖 Бронирование* {request_id}\nВыберите дни недели отгрузки:"
    else:
        request_data = await get_request_data(request_id)
        if request_data:
            for row in request_data:
                shop_name, warehouse_id, supply_type, supply_sum, supply_number = row[21], row[2], row[3], row[4], row[16]

        warehouse_name = await get_warehouse_name(warehouse_id)
        mess = await filter_supply_type(supply_type)
        mes = (
            "🤖 *Новое бронирование*\n\n"
            f"📍 {warehouse_name} > {mess} > {supply_sum} шт. > x{coefficient}\n\n"
            f"🆔 {user_id}\n"
            f"🛒 Выбранный магазин: {shop_name}\n\n"
            "Выберите дни недели отгрузки:"
        )
    await set_state_request(3, request_id)
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text = mes, parse_mode="MarkdownV2", reply_markup=create_days_keyboard(request_id, selected_days, serialized_days, supply_type, warehouse_id, supply_sum, supply_number, edit, coefficient))

###### Этап 7 - Выбор срока отгрузки
# Обработчик выбора дней недели
async def days_callback_handler(callback_query: CallbackQuery):
    _, request_id, serialized_days, value, edit = callback_query.data.split(":")
    request_id, value, edit = int(request_id), int(value), int(edit)
    if edit == 1:
        mes = f"*🤖 Бронирование* {request_id}\nУкажите срок, необходимый вам для отгрузки товара на склад WB:"

    else:
        selected_days_list = serialized_days.split(",")
        selected_days = {day: (day in selected_days_list) for day in days_of_week}
        selected_days = await select_day(value, selected_days)
        if value == 1:
            selected_days_str = ", ".join([d for d, selected in selected_days.items() if selected])
            await set_selected_days(selected_days_str, request_id)
            
        user_id = callback_query.from_user.id

        request_data = await get_request_data(request_id)
        if request_data:
            for row in request_data:
                shop_name, warehouse_id, supply_type, supply_sum, coefficient, selected_days = row[21], row[2], row[3], row[4], row[7], row[13]

        warehouse_name = await get_warehouse_name(warehouse_id)
        mess = await filter_supply_type(supply_type)

        mes = (
            "🤖 *Новое бронирование*\n\n"
            f"📍 {warehouse_name} > {mess} > {supply_sum} шт. > x{coefficient} >\n"
            f"> {selected_days}\n\n"
            f"🆔 {user_id}\n"
            f"🛒 Выбранный магазин: {shop_name}\n\n"
            "Укажите срок, необходимый вам для отгрузки товара на склад WB:"
        )
        await set_state_request(4, request_id)
        selected_days = {day: True for day in days_of_week}
    mes = await escape_markdown_v2(mes)
    # Перерисовываем клавиатуру с обновленными днями
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=create_delivery_keyboard(request_id, serialized_days, edit, coefficient))
    await callback_query.answer()

###### Этап 8 - Выбор срока отгрузки
# Обработчик выбора срока отгрузки
async def delivery_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    _, quantities, request_id, value, edit = callback_query.data.split(":")
    quantities, request_id, value, edit = int(quantities), int(request_id), int(value), int(edit)
    user_id = callback_query.from_user.id

    if edit == 1:
        mes = f"*🤖 Бронирование* {request_id}\nУкажите период отгрузки:"
        selected_days = 1
    else:

        if value == 1:
            await set_quantities(quantities, request_id)
        elif value == 2:
            await set_quantities(100, request_id)

        request_data = await get_request_data(request_id)
        if request_data:
            for row in request_data:
                shop_name, warehouse_id, supply_type, supply_sum, coefficient, selected_days = row[21], row[2], row[3], row[4], row[7], row[13]

        warehouse_name = await get_warehouse_name(warehouse_id)
        mess = await filter_supply_type(supply_type)

        mes = (
            "🤖 *Новое бронирование*\n\n"
            f"📍 {warehouse_name} > {mess} > {supply_sum} шт. > x{coefficient} >\n"
            f"> {selected_days} > {quantities}\n\n"
            f"🆔 {user_id}\n"
            f"🛒 Выбранный магазин: {shop_name}\n\n"
            "Укажите период отгрузки:"
        )
    await set_state_request(5, request_id)
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=create_search_period_keyboard(request_id, selected_days, edit))

###### Этап 8,5 - Выбор периода поиска
async def calendar_start_last(callback_query: CallbackQuery, state: FSMContext):
    _, request_id, day, value, month_offset, edit = callback_query.data.split(":")
    request_id, month_offset, value, edit = int(request_id), int(month_offset), int(value), int(edit)
    user_id = callback_query.from_user.id

    if value == 0:
        messs = "Укажите начальную дату отгрузки:" 
    elif value == 1:
        await set_start_date(day, request_id)
        messs = "Укажите конечную дату отгрузки:"
        value = 2
    else:
        await delete_dates_start_end(request_id)
        messs = "Укажите начальную дату отгрузки:"

    if edit == 1:
        mes = f"*🤖 Бронирование* {request_id}\nУкажите период отгрузки:"
    else:
        request_data = await get_request_data(request_id)
        if request_data:
            for row in request_data:
                shop_name, warehouse_id, supply_type, supply_sum, coefficient, quantities, date_start, date_end, selected_days = row[21], row[2], row[3], row[4], row[7], row[9], row[11], row[12], row[13]

        warehouse_name = await get_warehouse_name(warehouse_id)
        mess = await filter_supply_type(supply_type)

        mes = (
            "🤖 *Новое бронирование*\n\n"
            f"📍 {warehouse_name} > {mess} > {supply_sum} шт. > x{coefficient} >\n"
            f"> {selected_days} > {quantities} > \n"
            f"> Поиск с {date_start} по {date_end}> \n\n"
            f"🆔 {user_id}\n"
            f"🛒 Выбранный магазин: {shop_name}\n\n"
            f"{messs}"
        )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=create_calendar_keyboard(request_id, month_offset, value, edit))

###### Этап 9 - Выбор периода поиска
# Обработчик выбора периода поиска
async def period_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    _, request_id, period, value = callback_query.data.split(":")
    request_id, value = int(request_id), int(value)
    user_id = callback_query.from_user.id

    if value == 1 or value == 4:
        await set_dates_period(period, request_id)

    request_data = await get_request_data(request_id)
    if request_data:
        for row in request_data:
            shop_id, warehouse_id, supply_type, supply_sum, coefficient, quantities, date_start, date_end, selected_days = row[1], row[2], row[3], row[4], row[7], row[9], row[11], row[12], row[13]
    if all([warehouse_id != 0, supply_type != 0, supply_sum != 0, quantities != 0, date_start != "0", date_end != "0", selected_days != 0]):
        status = "ready"
        await set_status(status, request_id)
        messs = "Включить автобронирование?"
        data = 1
    else:
        messs = "Нужно изменить нулевые данные"
        data = 0
    warehouse_name = await get_warehouse_name(warehouse_id)
    mess = await filter_supply_type(supply_type)
    date_start = await format_date_md(date_start)
    date_end = await format_date_md(date_end)
    mes = (
        f"🤖 *Новое бронирование:* {request_id}\n\n"
        f"📍 *Склад:* {warehouse_name}\n"
        f"• *Макс. коэф.:* x{coefficient}\n"       
        f"• *Тип поставки:* {mess}\n"
        f"• *Кол-во:* {supply_sum} шт.\n"
        f"• *Дни недели:* {selected_days}\n"
        f"• *Поиск на дни:* {date_start}:{date_end}\n"
        f"• *Запас дней:* {quantities}\n"
        f"{messs}"
    )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=last_keayboard(request_id, data))

async def starting_bronirovanie(callback_query: CallbackQuery, state: FSMContext):
    _, request_id, value = callback_query.data.split(":")
    request_id, value = int(request_id), int(value)
    user_id = callback_query.from_user.id
    request_data = await get_request_data(request_id)
    if request_data:
        for row in request_data:
            warehouse_id, supply_type, supply_sum, coefficient, quantities, date_start, date_end, selected_days = row[2], row[3], row[4], row[7], row[9], row[11], row[12], row[13]
    if value == 1:
        status = "searching"
        messs = "🚀 Оперативно сообщим о бронировании, если свободная приёмка появится на WB."
        messag = "*Автобронирование успешно запущено!*"
        await set_status(status, request_id)
    else:
        status = "ready"
        messs = "💤 Бронирование отключено."
        messag = "*Запрос*"
        is_processing = 0
        await set_is_processing_and_status(is_processing, status, request_id)
        
    warehouse_name = await get_warehouse_name(warehouse_id)
    mess = await filter_supply_type(supply_type)
    date_start = await format_date_md(date_start)
    date_end = await format_date_md(date_end)
    mes = (
        f"🤖 {messag}\n\n"
        f"📍 *Склад:* {warehouse_name}\n"
        f"• *Макс. коэф.:* x{coefficient}\n"       
        f"• *Тип поставки:* {mess}\n"
        f"• *Кол-во:* {supply_sum} шт.\n"
        f"• *Дни недели:* {selected_days}\n"
        f"• *Поиск на дни:* {date_start}:{date_end}\n"
        f"• *Запас дней:* {quantities}\n\n"
        f"{messs}"
    )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=bron_start_btn(request_id, value))

# Регистрация команд
def menu_bron_commands(dp: Dispatcher):
    dp.callback_query.register(auto_booking_menu, lambda c: c.data.startswith('auto_booking'))
    dp.callback_query.register(handle_warehouse_id, lambda c: c.data.startswith('select_type'))
    dp.callback_query.register(handle_supply_file, lambda c: c.data.startswith('choose_warehouse'))
    dp.callback_query.register(upload_metod_selection, lambda c: c.data.startswith('metod_upload'))
    dp.callback_query.register(handle_upload_selection, lambda c: c.data.startswith('upload'))
    dp.message.register(handle_step_4, Form.waiting_for_supply)
    dp.callback_query.register(handle_step_5, lambda c: c.data.startswith('next_step'))
    dp.callback_query.register(handle_coefficient, lambda c: c.data.startswith("qwer"))
    dp.callback_query.register(days_callback_handler, lambda c: c.data.startswith("step_seven"))
    dp.callback_query.register(delivery_callback_handler, lambda c: c.data.startswith("eight_step"))
    dp.callback_query.register(calendar_start_last, lambda c: c.data.startswith("half_eight_step"))
    dp.callback_query.register(period_callback_handler, lambda c: c.data.startswith("nine_step"))
    dp.callback_query.register(starting_bronirovanie, lambda c: c.data.startswith("bron_starting"))
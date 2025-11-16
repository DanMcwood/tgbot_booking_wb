from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from datetime import datetime, timedelta
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta

from handlers.params.settings import days_of_week, ITEMS_PER_PAGE, COEFFICIENTS
from handlers.tasks.utils import format_date, filter_supply_type
from handlers.database.connection import get_warehouse_name

ITEMS_PER_PAGE = int(ITEMS_PER_PAGE)
#Кнопки главного меню ////main_menu_callback////
def main_menu_btn():
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Коэффициенты", callback_data="history_coefficients:0:0:0"),
        InlineKeyboardButton(text="📦 Избранные склады", callback_data="favorite_warehouses:0:0:2")],
        [InlineKeyboardButton(text="🤖 Автобронирование", callback_data="auto_booking"),
        InlineKeyboardButton(text="🗂 Запросы", callback_data="requests_menu:0:0:0:0:0:0:0:0")],
        [InlineKeyboardButton(text="🛒 Мои магазины", callback_data="shops_menu:0:0"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="keysettings:0")]
    ])
    return markup

#Кнопки создания бронирования ////handle_update_bron////
def is_supply_btn(warehouse_id):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📝 Новое бронирование', callback_data=f'choose_warehouse:{warehouse_id}:0')],
        [InlineKeyboardButton(text='🏠 Личный кабинет', callback_data='main_menu')]
    ])
    return markup

#Кнопки меню бронирования ////auto_booking_menu////
def bron_menu_btn():
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📝 Новое бронирование', callback_data='select_type:0:1')],
        [InlineKeyboardButton(text='📂 Активные бронирования', callback_data='requests_menu:0:0:0:1:0:0:0:0')],
        [InlineKeyboardButton(text='🗂 Все бронирования', callback_data='requests_menu:0:0:0:0:0:0:0:0')],
        [InlineKeyboardButton(text='🏠 Личный кабинет', callback_data='main_menu')]
    ])
    return markup

#Кнопки меню складов ////handle_warehouse_id////handle_warehouse_buttons////
def warehouses_btn(warehouses, favorite_warehouses, page, request: int):
    
    favorite_list = [w for w in warehouses if w[0] in favorite_warehouses]
    other_list = [w for w in warehouses if w[0] not in favorite_warehouses]
    sorted_warehouses = favorite_list + other_list

    keyboard_buttons = []
    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    for warehouse in sorted_warehouses[start_index:end_index]:
 
        warehouse_id, warehouse_name = warehouse
        is_favorite = "❤️" if warehouse_id in favorite_warehouses else "➖"
        favorite_button = InlineKeyboardButton(
            text=is_favorite,
            callback_data=f"toggle_favorite:{warehouse_id}:{page}:{request}"
        )
        if request == 1:
            name_button = InlineKeyboardButton(
                text=warehouse_name,
                callback_data=f"choose_warehouse:{warehouse_id}:0"
            )
        elif request == 2:
            name_button = InlineKeyboardButton(
                text=warehouse_name,
                callback_data=f"is_supply:{warehouse_id}"
            )
        else:
            name_button = InlineKeyboardButton(
                text=warehouse_name,
                callback_data=f"ssselected_request:{request}:2:{warehouse_id}:0"
            )
        keyboard_buttons.append([name_button, favorite_button])
    
    # Кнопки навигации 
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="< Назад", callback_data=f"favorite_warehouses:0:{page - 1}:{request}"))
    if end_index < len(sorted_warehouses):
        navigation_buttons.append(InlineKeyboardButton(text="Далее >", callback_data=f"favorite_warehouses:0:{page + 1}:{request}"))
    if navigation_buttons:
        keyboard_buttons.append(navigation_buttons)

    # Кнопка обновления складов
    keyboard_buttons.append([InlineKeyboardButton(text="🔄 Обновить склады", callback_data=f"update_warehouses:0:0:{request}")])
    keyboard_buttons.append([InlineKeyboardButton(text="🏠 Личный кабинет", callback_data=f"main_menu")])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return markup

#Кнопки выбора типа поставки ////handle_supply_file////
def supply_type_btn(warehouse_id, request_id, value):
    if value == 1:
        data1 = f"ssselected_request:{warehouse_id}:3:1:0"
        data2 = f"ssselected_request:{warehouse_id}:3:2:0"
        data3 = f"ssselected_request:{warehouse_id}:3:3:0"
        data4 = f"ssselected_request:{warehouse_id}:3:4:0"
        data5 = f"ssselected_request:{warehouse_id}:1:1:0"
    else:
        data1 = f'metod_upload:{1}:{warehouse_id}:{request_id}:0'
        data2 = f'metod_upload:{2}:{warehouse_id}:{request_id}:0'
        data3 = f'metod_upload:{3}:{warehouse_id}:{request_id}:0'
        data4 = f'metod_upload:{4}:{warehouse_id}:{request_id}:0'
        data5 = f'select_type:0:1'

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔸 Короба', callback_data=data1)],
        [InlineKeyboardButton(text='🔹 Монопаллеты', callback_data=data2)],
        [InlineKeyboardButton(text='🔸 Суперсейф', callback_data=data3)],
        [InlineKeyboardButton(text='🔹 QR-поставка с коробами', callback_data=data4)],
        [InlineKeyboardButton(text='< Назад', callback_data=data5),
        InlineKeyboardButton(text='🏠 Личный кабинет', callback_data='main_menu')]
    ])
    return markup

#Кнопки выбора типа загрузки ////upload_metod_selection////
def upload_type_btn(warehouse_id, supply_type, edit, request_id):
    if edit == 1:
        data5 = f"ssselected_request:{request_id}:1:1:0"
    else:
        data5 = f'choose_warehouse:{warehouse_id}:0'
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='💬 Чат', callback_data=f'upload:chat:{supply_type}:{warehouse_id}:{edit}:{request_id}'),
            InlineKeyboardButton(text='📗 Excel', callback_data=f'upload:table:{supply_type}:{warehouse_id}:{edit}:{request_id}')
        ],
        [
            InlineKeyboardButton(text='🔗 Google', callback_data=f'upload:google:{supply_type}:{warehouse_id}:{edit}:{request_id}'),
            InlineKeyboardButton(text='🖇 My Google', callback_data=f'upload:my_google:{supply_type}:{warehouse_id}:{edit}:{request_id}')],
            [InlineKeyboardButton(text='📍 Выбрать поставку на WB', callback_data=f'upload:draft:{supply_type}:{warehouse_id}:{edit}:{request_id}')],
        [
            InlineKeyboardButton(text='< Назад', callback_data=data5),
            InlineKeyboardButton(text='🏠 Личный кабинет', callback_data='main_menu')
        ]
    ])
    
    return markup

#Кнопки загрузки поставки ////handle_upload_selection////
def upload_supply_btn(filtred_supplies, supply_type, warehouse_id, warehouse_name, request_id, edit, my_urls):
    if filtred_supplies is not None:
        keyboard_buttons = []

        for supply in filtred_supplies: 
            supply_number = supply[0]
            creation_date = supply[2]
            supply_sum = supply[4]

            formatted_date = " ".join(creation_date.split()[:2])

            if edit == 1:
                data1 = f"ssselected_request:{request_id}:4:{supply_sum}:{supply_number}"
            else:
                data1 = f"next_step:{supply_type}:{warehouse_id}:{supply_sum}:{request_id}:{supply_number}:0"
            button_text = f"№ {supply_number} > {supply_type} > Поставка: {formatted_date} > {supply_sum} шт. > {warehouse_name}"
            button = ([InlineKeyboardButton(text=button_text, callback_data=data1)])
            keyboard_buttons.append(button)

        keyboard_buttons.append([InlineKeyboardButton(text="< Назад", callback_data=f"metod_upload:{supply_type}:{warehouse_id}:{request_id}:{edit}")])
        keyboard_buttons.append([InlineKeyboardButton(text="🏠 Личный кабинет", callback_data=f"main_menu")])

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    elif my_urls is not None:
        url_buttons = []

        for url in my_urls:
            if edit == 1:
                data1 = f"ssselected_request:{request_id}:9:{url['url_id']}:0"
            else:
                data1 = f"next_step:{url['url_id']}:{warehouse_id}:0:{request_id}:0:2"
            
            # Добавление кнопки в список
            url_buttons.append([InlineKeyboardButton(text=url["url_name"], callback_data=data1)])

        url_buttons.append([InlineKeyboardButton(text="< Назад", callback_data=f"metod_upload:{supply_type}:{warehouse_id}:{request_id}:{edit}")])
        url_buttons.append([InlineKeyboardButton(text="🏠 Личный кабинет", callback_data=f"main_menu")])
        markup = InlineKeyboardMarkup(inline_keyboard=url_buttons)

    else:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='< Выбрать другой метод', callback_data=f'metod_upload:{supply_type}:{warehouse_id}:{request_id}:{edit}')],
            [InlineKeyboardButton(text='🏠 Личный кабинет', callback_data='main_menu')]
        ])
    return markup

#Кнопки проверки поставки ////handle_step_4////
def next_step_go(supply_type, warehouse_id, supply_sum, request_id, supply_number, edit):
    if edit == 1:
        data1 = f"ssselected_request:{request_id}:4:{supply_sum}:0"
    else:
        data1 = f'next_step:{supply_type}:{warehouse_id}:{supply_sum}:{request_id}:{supply_number}:0'
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='< Изменить файл', callback_data=f'metod_upload:{supply_type}:{warehouse_id}:{request_id}:{edit}'),
            InlineKeyboardButton(text='Далее >', callback_data=data1)
        ],  # Первые две кнопки в одном ряду
        [InlineKeyboardButton(text='🏠 Личный кабинет', callback_data='main_menu')]  # Отдельный ряд для третьей кнопки
    ])
    return markup

#Кнопки выхода ////handle_step_4////
def exit_btn(supply_type, warehouse_id, request_id, edit):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='< Назад', callback_data=f'metod_upload:{supply_type}:{warehouse_id}:{request_id}:{edit}')],
        [InlineKeyboardButton(text='🏠 Личный кабинет', callback_data='main_menu')]
    ])   
    return markup


def back_btn(supply_type, warehouse_id, request_id, edit):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='< Назад', callback_data=f'metod_upload:{supply_type}:{warehouse_id}:{request_id}:0'),
        InlineKeyboardButton(text='🏠 Личный кабинет', callback_data='main_menu')]
    ])
    return markup

#Кнопки выбора коэффициентов ////handle_step_5////
def coef_btn(supply_type, warehouse_id, request_id, serialized_days, edit):
    keyboard = []
    if edit == 1:
        data1 = f"ssselected_request:{request_id}:5:0:0"
        data3 = f"ssselected_request:{request_id}:1:0:0"
    else:
        data1 = f"qwer:9:0:{request_id}:{serialized_days}:0"
        data3  = f'metod_upload:{supply_type}:{warehouse_id}:{request_id}:0'
    # Добавляем кнопку "Бесплатная приемка" в самый верх
    keyboard.append([InlineKeyboardButton(text="Бесплатная приемка", callback_data=data1)])

    # Создаем кнопки коэффициентов (x1, x2, ..., x20) по 4 в строке
    row = []
    for i in range(1, COEFFICIENTS + 1):
        if edit == 1:
            data2 = f"ssselected_request:{request_id}:5:{i}:0"
        else:
            data2 = f"qwer:9:{i}:{request_id}:{serialized_days}:0"
        button = InlineKeyboardButton(
            text=f"⪢x{i}",
            callback_data=data2
        )
        row.append(button)
        if len(row) == 4:
            keyboard.append(row)
            row = []

    # Добавляем последнюю строку, если остались кнопки
    if row:
        keyboard.append(row)

    # Добавляем кнопки "История коэффициентов" и "Назад"
    keyboard.append([InlineKeyboardButton(text="📈 Коэффициенты", callback_data=f"history_coefficients:0:0")])
    keyboard.append([InlineKeyboardButton(text="< Назад", callback_data=data3)])
    keyboard.append([InlineKeyboardButton(text="🏠 Личный кабинет", callback_data=f"main_menu")])

    # Преобразуем список в объект InlineKeyboardMarkup
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Функция для создания клавиатуры дней недели ///handle_coefficient/////
def create_days_keyboard(request_id, selected_days, serialized_days, supply_type, warehouse_id, supply_sum, supply_number, edit, coefficient):
    keyboard = InlineKeyboardBuilder()

    # Первый ряд (Пн-Пт)
    for day in days_of_week[:5]:
        text = f"✅ {day}" if selected_days[day] else day
        keyboard.button(text=text, callback_data=f"qwer:{day}:{coefficient}:{request_id}:{serialized_days}:{edit}")

    keyboard.adjust(5)

    # Второй ряд (Сб, Вс и три пустых кнопки)
    for day in days_of_week[5:]:
        text = f"✅ {day}" if selected_days[day] else day
        keyboard.button(text=text, callback_data=f"qwer:{day}:{coefficient}:{request_id}:{serialized_days}:{edit}")

    for _ in range(3):
        keyboard.button(text=" ", callback_data="none")

    keyboard.adjust(5)

    # Кнопки "Назад" и "Пропустить"/"Далее"
    if all(selected_days.values()):  # Проверка, что все дни выбраны
        next_text = "Пропустить >"
    else:
        next_text = "Далее >"
    if edit == 1:
        data1 = f"ssselected_request:{request_id}:0:0:0"
        data2 = f"ssselected_request:{request_id}:7:{serialized_days}:0"
    else:
        data1 = f"next_step:{supply_type}:{warehouse_id}:{supply_sum}:{request_id}:{supply_number}:0"
        data2 = f"step_seven:{request_id}:{serialized_days}:1:0"
    keyboard.row(
        InlineKeyboardButton(text="< Назад", callback_data=data1),
        InlineKeyboardButton(text=next_text, callback_data=data2)
    )

    return keyboard.as_markup()

# Функция для создания клавиатуры сроков отгрузки ////days_callback_handler////
def create_delivery_keyboard(request_id, serialized_days, edit, coefficient):
    keyboard = InlineKeyboardBuilder()
    if edit == 1:
        data1 = f"ssselected_request:{request_id}:1:0:0"
        data4 = f"ssselected_request:{request_id}:100:0:0"
    else:
        data1 = f"qwer:10:{coefficient}:{request_id}:{serialized_days}:0"
        data4 = f"eight_step:20:{request_id}:2:0"
    # Первые три кнопки (0, 1, 2 дня)
    for i in range(3):
        if edit == 1:
            data2 = f"ssselected_request:{request_id}:6:{i}:0"
        else:
            data2 = f"eight_step:{i}:{request_id}:1:0"
        keyboard.button(text=f"{i} дней", callback_data=data2)

    keyboard.adjust(3)

    # Кнопки от 3 до 14 дней
    for i in range(3, 15):
        if edit == 1:
            data3 = f"ssselected_request:{request_id}:6:{i}:0"
        else:
            data3 = f"eight_step:{i}:{request_id}:1:0"
        keyboard.button(text=f"{i} дней", callback_data=data3)

    keyboard.adjust(3)

    # Кнопки "Назад" и "Пропустить"
    keyboard.row(
        InlineKeyboardButton(text="< Назад", callback_data=data1),
        InlineKeyboardButton(text="Пропустить >", callback_data=data4)
    )
    keyboard.row(InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu"))

    return keyboard.as_markup()

# Клавиатура для выбора периода поиска ////delivery_callback_handler////
def create_search_period_keyboard(request_id, selected_days, edit):
    keyboard = InlineKeyboardBuilder()
    if edit == 1:
        data1 = f"ssselected_request:{request_id}:8:1:0"
        data2 = f"ssselected_request:{request_id}:8:2:0"
        data3 = f"ssselected_request:{request_id}:8:3:0"
        data4 = f"ssselected_request:{request_id}:1:0:0"
    else:
        data1 = f"nine_step:{request_id}:1:1"
        data2 = f"nine_step:{request_id}:2:1"
        data3 = f"nine_step:{request_id}:3:1"
        data4 = f"step_seven:{request_id}:{selected_days}:0:0"

    keyboard.button(text="🔸 Завтра", callback_data=data1)
    keyboard.button(text="🔹 7 дн", callback_data=data2)
    keyboard.button(text="🔸 Искать, пока не найдется", callback_data=data3)
    keyboard.button(text="♦️ Выбрать период", callback_data=f"half_eight_step:{request_id}:0:0:0:{edit}")
    keyboard.adjust(1)  

    keyboard.row(
        InlineKeyboardButton(text="< Назад", callback_data=data4),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")
    )

    return keyboard.as_markup()

# Функция для создания календаря ////calendar_last////
def create_calendar_keyboard(request_id, month_offset, value, edit):
    today = datetime.today()
    # Смещаем текущий месяц на month_offset
    first_day_of_month = today.replace(day=1) + timedelta(days=30 * month_offset)
    month_start = first_day_of_month.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Название месяца и года
    month_name = month_start.strftime("%B %Y")

    # Получаем список всех дней месяца
    days = [month_start + timedelta(days=i) for i in range((month_end - month_start).days + 1)]

    # Первая строка с кнопками (Назад, Название месяца, Далее)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="<-", callback_data=f"half_eight_step:{request_id}:0:{value}:{month_offset - 1}:{edit}"),
                InlineKeyboardButton(text=month_name, callback_data="ignore"),
                InlineKeyboardButton(text="->", callback_data=f"half_eight_step:{request_id}:0:{value}:{month_offset + 1}:{edit}")
            ],
            # Вторая строка с днями недели
            [
                InlineKeyboardButton(text="Пн", callback_data="ignore"),
                InlineKeyboardButton(text="Вт", callback_data="ignore"),
                InlineKeyboardButton(text="Ср", callback_data="ignore"),
                InlineKeyboardButton(text="Чт", callback_data="ignore"),
                InlineKeyboardButton(text="Пт", callback_data="ignore"),
                InlineKeyboardButton(text="Сб", callback_data="ignore"),
                InlineKeyboardButton(text="Вс", callback_data="ignore")
            ]
        ]
    )

    # Начало месяца — это день недели, с которого начинается месяц (например, если 1-е число — это пятница)
    start_day_of_week = month_start.weekday()  # Понедельник = 0, Воскресенье = 6

    # Заполняем календарь
    row = []

    # Добавляем пустые кнопки для дней предыдущего месяца
    if start_day_of_week > 0:
        previous_month_end = (month_start - timedelta(days=1)).replace(day=1)  # Последний день предыдущего месяца
        for i in range(start_day_of_week):
            # Пустые кнопки из предыдущего месяца
            button = InlineKeyboardButton(text=" ", callback_data="ignore")
            row.append(button)

    # Добавляем кнопки для дней текущего месяца
    for day in days:
        if value == 2:
            if edit == 1:
                time_mes = f"ssselected_request:{request_id}:8:{day.strftime('%Y-%m-%d')}:0"
            else:
                time_mes = f"nine_step:{request_id}:{day.strftime('%Y-%m-%d')}:4"
        else:
            time_mes = f"half_eight_step:{request_id}:{day.strftime('%Y-%m-%d')}:1:{month_offset + 1}:{edit}"
        button = InlineKeyboardButton(text=str(day.day), callback_data=f"{time_mes}")
        row.append(button)

        # Когда строка заполнилась до 7 кнопок (неделя), добавляем ее в клавиатуру
        if len(row) == 7:
            keyboard.inline_keyboard.append(row)
            row = []  # Сбрасываем строку

    # Если есть оставшиеся дни в неполной неделе, добавляем их
    if row:
        keyboard.inline_keyboard.append(row)

    # Добавляем пустые кнопки для дней следующего месяца, если последний день месяца не воскресенье
    if len(row) < 7:
        next_month_start = month_end + timedelta(days=1)
        for i in range(7 - len(row)):
            button = InlineKeyboardButton(text=" ", callback_data="ignore")
            row.append(button)
        
    # Кнопка "Назад" внизу на весь размер
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="< Выбрать из предложенного списка", callback_data=f"eight_step:0:{request_id}:0:{edit}")])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")])
    return keyboard

# Кнопки коэффициентов ////show_warehouses_history////
def show_history_coef(data, page, request, types):
    # Вычисляем индекс для среза списка данных для текущей страницы
    start_index = page * ITEMS_PER_PAGE
    end_index = int(start_index) + ITEMS_PER_PAGE
    data_page = data[start_index:end_index]

    keyboard_buttons = []
    for item in data_page:
        date = item.get("date", "Не указана").split("T")[0]  
        warehouse = item.get("warehouseName", "Неизвестный склад")
        box_type = item.get("boxTypeName", "Неизвестный тип")
        coefficient = item.get("coefficient", "Нет данных")
        if coefficient == -1 or coefficient == "-1":
            coefficient = "Не принимается"
        elif coefficient == 0 or coefficient == "0":
            coefficient = "Бесплатно"
        button_text = f"{date.strip()} > {warehouse.strip()} > {box_type.strip()} > {coefficient}"
        button = InlineKeyboardButton(text=button_text, callback_data="none")
        keyboard_buttons.append([button])

    # Кнопки навигации
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="< Назад", callback_data=f"show_history_coefficients:{types}:0:{page - 1}:{request}"))
    navigation_buttons.append(InlineKeyboardButton(text=f"{page + 1}", callback_data="none"))  
    if end_index < len(data):
        navigation_buttons.append(InlineKeyboardButton(text="Далее >", callback_data=f"show_history_coefficients:{types}:0:{page + 1}:{request}"))
    if navigation_buttons:
        keyboard_buttons.append(navigation_buttons)

    keyboard_buttons.append([InlineKeyboardButton(text="🔄 Выбрать другие склады", callback_data="history_coefficients:0:0:0")])
    keyboard_buttons.append([InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return markup

# Кнопки выбора коэффициентов для складов ////show_history////
def select_warehouses_coef(warehouses, favorite_warehouses, selected_warehouses, page, request, ):
    # Сортировка складов
    type1, box_is_selected = "1", "▪️" if 1 in selected_warehouses else "▫️"
    type2, pal_is_selected = "2", "▪️" if 2 in selected_warehouses else "▫️"
    type3, safe_is_selected = "3", "▪️" if 3 in selected_warehouses else "▫️"

    types = ""

    if 1 in selected_warehouses:
        types += "1"
    if 2 in selected_warehouses:
        types += "2"
    if 3 in selected_warehouses:
        types += "3"
        
    if any(x in selected_warehouses for x in [1, 2, 3]):
        selected_warehouses = [w for w in selected_warehouses if w not in [1, 2, 3]]
        typecallback = f"show_history_coefficients:{types}"
    else:
        typecallback = f"show_history_coefficients:{types}"
    
    favorite_list = [w for w in warehouses if w[0] in favorite_warehouses]
    other_list = [w for w in warehouses if w[0] not in favorite_warehouses]
    sorted_warehouses = favorite_list + other_list

    if request == 0:
        selected_warehouses = []
        resorted_warehouses = sorted_warehouses
    elif request == 1:
        selected_list = [w for w in sorted_warehouses if w[0] in selected_warehouses]
        another_list = [w for w in sorted_warehouses if w[0] not in selected_warehouses]
        resorted_warehouses = selected_list + another_list
        
    # Разметка для кнопок
    keyboard_buttons = []
    start_index = page * ITEMS_PER_PAGE
    end_index = int(start_index) + ITEMS_PER_PAGE

    # Создание кнопок для складов
    row = []
    for idx, warehouse in enumerate(resorted_warehouses[start_index:end_index], start=1):
        warehouse_id, warehouse_name = warehouse
        is_favorite = "❤️" if warehouse_id in favorite_warehouses else ""
        is_selected = "▪️" if warehouse_id in selected_warehouses else "▫️"
        button = InlineKeyboardButton(
            text=f"{is_selected} {warehouse_name} {is_favorite}",
            callback_data=f"tap_select:{warehouse_id}:{page}:1"
        )
        row.append(button)

        # Каждые 2 склада добавляем строку
        if idx % 2 == 0 or idx == len(sorted_warehouses[start_index:end_index]):
            keyboard_buttons.append(row)
            row = []

    # Кнопки навигации
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="< Назад", callback_data=f"history_coefficients:0:{page - 1}:{request}"))
    navigation_buttons.append(InlineKeyboardButton(text=f"{page + 1}", callback_data="none"))
    if end_index < len(sorted_warehouses):
        navigation_buttons.append(InlineKeyboardButton(text="Далее >", callback_data=f"history_coefficients:0:{page + 1}:{request}"))
    if navigation_buttons:
        keyboard_buttons.append(navigation_buttons)

    supply_type_buttons = []
    supply_type_buttons.append(InlineKeyboardButton(text=f"{box_is_selected} Короба", callback_data=f"tap_select:1:{page}:1"))
    supply_type_buttons.append(InlineKeyboardButton(text=f"{pal_is_selected} Монопаллеты", callback_data=f"tap_select:2:{page}:1"))
    supply_type_buttons.append(InlineKeyboardButton(text=f"{safe_is_selected} Суперсейф", callback_data=f"tap_select:3:{page}:1"))
    if supply_type_buttons:
        keyboard_buttons.append(supply_type_buttons)
    # Дополнительные кнопки
    if selected_warehouses == []:
        call_text = "Выбрать все склады"
        call_data = f"{typecallback}:1:0:0"
    else:
        call_text = "Показать коэффициенты"
        call_data = f"{typecallback}:1:0:0"

    keyboard_buttons.append([
        InlineKeyboardButton(text=call_text, callback_data=call_data),
        InlineKeyboardButton(text="🔄 Обновить склады", callback_data=f"reload_history:0:{page}:{request}")])
    keyboard_buttons.append([InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")])

    # Создание разметки
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return markup

def mistake_btn(): 
    markup = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="history_coefficients:0:0:0")],
    [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
    ])

    return markup

# Функция для создания клавиатуры магазинов ////my_shops_callback////
def shops_menu_btn(shops): 
    inline_keyboard = []

    # Строка выбора магазина
    select_row = [InlineKeyboardButton(text="🟣", callback_data="none")]
    for i, shop in enumerate(shops, start=1):
        select_row.append(InlineKeyboardButton(text=f"{i}", callback_data=f"shops_menu:1:{i}"))
    inline_keyboard.append(select_row)

    # Строка редактирования магазина ////////
    edit_row = [InlineKeyboardButton(text="✏️", callback_data="none")]
    for i, shop in enumerate(shops, start=1):
        edit_row.append(InlineKeyboardButton(text=f"{i}", callback_data=f"edit_shop:2:{i}"))
    inline_keyboard.append(edit_row)

    # Строка удаления магазина ////////
    delete_row = [InlineKeyboardButton(text="🗑️", callback_data="none")]
    for i, shop in enumerate(shops, start=1):
        delete_row.append(InlineKeyboardButton(text=f"{i}", callback_data=f"shops_menu:3:{i}"))
    inline_keyboard.append(delete_row)

    # Дополнительные кнопки ////////
    inline_keyboard.append([InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu"),
                            InlineKeyboardButton(text="➕ Добавить магазин", callback_data=f"additing_shop")])

    markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    return markup

def get_shop_wb_reg_btn(shops):
    keyboard = InlineKeyboardBuilder()

    if shops:  
        for shop in shops:
            if not shop['shop_name']:
                button_text = f"{shop['shop_wb']}"
                keyboard.button(
                    text=button_text,
                    callback_data=f"popupshop:{shop['shop_id']}"
                )
        keyboard.adjust(len(shops))  
    else:
        keyboard.button(text="Магазины не найдены", callback_data="none")

    keyboard.row(
        InlineKeyboardButton(text="🛒 Мои магазины", callback_data="shops_menu:0:0"),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu"),
    )
    return keyboard.as_markup()

def get_shop_wb_btn(shops):
    keyboard = InlineKeyboardBuilder()

    if shops: 
        for shop in shops:
            if not shop['shop_name']:
                button_text = f"{shop['shop_wb']}"
                keyboard.button(
                    text=button_text,
                    callback_data=f"type_edit_shop:5:{shop['shop_id']}"
                )
        keyboard.adjust(len(shops))  
    else:
        keyboard.button(text="Магазины не найдены", callback_data="none")

    keyboard.row(
        InlineKeyboardButton(text="🛒 Мои магазины", callback_data="shops_menu:0:0"),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu"),
    )
    return keyboard.as_markup()

def editing_shops(shop_id):
    # Создаем клавиатуру с кнопками
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Изменить название", callback_data=f"type_edit_shop:1:{shop_id}"),
            InlineKeyboardButton(text="Изменить API", callback_data=f"type_edit_shop:2:{shop_id}"),
        ],
        [InlineKeyboardButton(text="✏️ Изменить все", callback_data=f"type_edit_shop:3:{shop_id}")],
        [
            InlineKeyboardButton(text="🛒 Назад в мои магазины", callback_data="shops_menu:0:0"),
            InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")
        ]

    ])
    return markup

#Кнопки добавления имени магазина ////choose_type_edit_shop////
def back_to_shops_menu(shop_id, state):
    buttons = [
        [InlineKeyboardButton(text="🛒 Назад в мои магазины", callback_data="shops_menu:0:0")],
        [InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")]
    ]
    
    # Если state == 1, добавляем кнопку "✏️ Выбрать другое действие"
    if state == 1:
        buttons.insert(0, [InlineKeyboardButton(text="✏️ Выбрать другое действие", callback_data=f"edit_shop:4:{shop_id}")])
    
    # Создаем клавиатуру из списка
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    return markup

# Функция для клавиатуры бронирования ////period_callback_handler////
def last_keayboard(request_id, data):
    keyboard = InlineKeyboardBuilder()
    if data == 1:
        text1 = "🤖 Запустить авотбронирование"
        data1 = f"bron_starting:{request_id}:1"
    else:
        text1 = "✏️ Редактировать запрос"
        data1 = f"ssselected_request:{request_id}:0:0:0"
    # Кнопки выбора
    keyboard.button(text=text1, callback_data=data1)
    keyboard.button(text="🗂 Все запросы", callback_data=f"requests_menu:0:0:0:0:0:0:0:0")
    keyboard.adjust(1)  

    keyboard.row(
        InlineKeyboardButton(text="< Назад", callback_data=f"eight_step:0:{request_id}:3:0"),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")
    )
    return keyboard.as_markup()

# Функция для клавиатуры бронирования ////period_callback_handler////
def bron_start_btn(request_id, value):
    keyboard = InlineKeyboardBuilder()
    if value == 1:
        text1 = "🤖 Новый запрос"
        data1 = "auto_booking"
    else:
        text1 = "🤖 Возобновить бронирование"
        data1 = f"bron_starting:{request_id}:1"
    keyboard.row(
        InlineKeyboardButton(text=text1, callback_data=data1),
        InlineKeyboardButton(text="🗂 Все запросы", callback_data=f"requests_menu:0:0:0:0:0:0:0:0")
    )
    keyboard.adjust(1)  
    keyboard.button(text="🏠 Личный кабинет", callback_data="main_menu")

    return keyboard.as_markup()

async def requests_btn(requests, page, is_active, is_ready, is_done, is_null, is_process):
    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE

    # Фильтруем запросы по статусу
    filtered_requests = [
        request for request in requests
        if (not is_active or request["status"] == "searching")
        and (not is_ready or request["status"] == "ready")
        and (not is_done or request["status"] == "done")
        and (not is_null or request["status"] in ["timeout", "lost_supply"])
        and (not is_process or request["status"] == "in process")
    ]

    # Получаем элементы для текущей страницы
    page_requests = filtered_requests[start_index:end_index]

    keyboard_buttons = []

    if page_requests:
        for request in page_requests:
            # Извлечение данных из строки
            request_id = request["request_id"]
            edit_date = format_date(request["edit_date"])
            warehouse_id = request["warehouse_ids"]
            supply_type = request["supply_type"]
            supply_sum = request["supply_sum"]
            coefficient = request["coefficient"]
            date_start = request["date_start"]
            date_end = request["date_end"]

            if date_start and date_start != "0":
                date_start = datetime.strptime(date_start, "%Y-%m-%d").strftime("%d.%m")
                date_end = datetime.strptime(date_end, "%Y-%m-%d").strftime("%d.%m") if date_end != "0" else "не заполнено"
            else:
                date_start = "не заполнено"

            status = request["status"]
            warehouse_name = await get_warehouse_name(warehouse_id)
            mess = await filter_supply_type(supply_type)

            # Форматирование текста кнопки
            button_text = (
                f"{edit_date} | {warehouse_name} • {mess} • {supply_sum} шт. "
                f"• x{coefficient} > {date_start}:{date_end} | {status}"
            )

            request_button = InlineKeyboardButton(
                text=button_text,
                callback_data=f"ssselected_request:{request_id}:0:0:0"
            )
            keyboard_buttons.append([request_button])
    else:
        # Пустая страница
        keyboard_buttons.append([
            InlineKeyboardButton(text="Нет данных для отображения", callback_data="none")
        ])

    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="<", callback_data=f"requests_menu:{page - 1}:1:0:{is_active}:{is_ready}:{is_done}:{is_null}:{is_process}"))
    else:
        navigation_buttons.append(InlineKeyboardButton(text=" ", callback_data=f"none"))
    navigation_buttons.append(InlineKeyboardButton(text=f"{page + 1}", callback_data=f"none"))
    if end_index < len(filtered_requests):
        navigation_buttons.append(InlineKeyboardButton(text=">", callback_data=f"requests_menu:{page + 1}:1:0:{is_active}:{is_ready}:{is_done}:{is_null}:{is_process}"))
    else:
        navigation_buttons.append(InlineKeyboardButton(text=" ", callback_data=f"none"))
    
    keyboard_buttons.append(navigation_buttons)
        
    type_buttons = [
        InlineKeyboardButton(text="▪️ Все" if is_active == 0 and is_ready == 0 and is_done == 0 and is_null == 0 and is_process == 0 else "Все", callback_data=f"requests_menu:0:1:0:0:0:0:0:0"),
        InlineKeyboardButton(text="▪️ Выполненные" if is_done == 1 else "Выполненные", callback_data=f"requests_menu:0:1:0:0:0:1:0:0"),
        InlineKeyboardButton(text="▪️ Ошибка" if is_null == 1 else "Ошибка", callback_data=f"requests_menu:0:1:0:0:0:0:1:0")]
    type_buttons2 = [
        InlineKeyboardButton(text="▪️ Активные" if is_active == 1 else "Активные", callback_data=f"requests_menu:0:1:0:1:0:0:0:0"),
        InlineKeyboardButton(text="▪️ Заполненные" if is_ready == 1 else "Заполненные", callback_data=f"requests_menu:0:1:0:0:1:0:0:0"),
        InlineKeyboardButton(text="▪️ В процессе" if is_process == 1 else "В процессе", callback_data=f"requests_menu:0:1:0:0:0:0:0:1")
    ]
    keyboard_buttons.append(type_buttons)   
    keyboard_buttons.append(type_buttons2)   
    
    exit_buttons = [
        InlineKeyboardButton(text="🤖 Новый запрос", callback_data="auto_booking"),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu"),
    ]
    keyboard_buttons.append(exit_buttons)
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return markup

def request_one_btn(request_id, status, state, supply_type, warehouse_id, supply_sum):
    keyboard = InlineKeyboardBuilder()
    selected_days = {day: True for day in days_of_week}
    serialized_days = ",".join(day for day, selected in selected_days.items() if selected)
    # Условия для выбора текста и данных для кнопок в зависимости от статуса
    if status == "in process":
        text1 = "Продолжить заполнение"
        if state == 1:
            data1 = f'metod_upload:{supply_type}:{warehouse_id}:{request_id}:0'
        if state == 2:
            data1 =f"next_step:0:0:{supply_sum}:{request_id}:0:1"
        elif state == 3:
            data1 = f"qwer:0:0:{request_id}:{serialized_days}:0"
        elif state == 4:
            data1 = f"step_seven:{request_id}:1:1:0"
        elif state == 5:
            data1 = f"eight_step:1:{request_id}:2:0"
    elif status == "done":
        text1 = "🤖 Бронирование выполнено!"
        data1 = f"requests_menu:0:1:0:0:0:1:0:0"
    elif status == "searching":
        text1 = "🤖 Выключить авотбронирование"
        data1 = f"bron_starting:{request_id}:0"
    elif status == "lost_supply":
        text1 = "💤 Номер поставки не был найден, поменяй поставку"
        data1 = f"choose_warehouse:{request_id}:1"
    elif status == "timeout":
        text1 = "💤 Время для поиска вышло, поменяй даты/запас дней"
        data1 = f"step_seven:{request_id}:1:1:1"
    elif status == "ready":
        text1 = "🤖 Запустить авотбронирование"
        data1 = f"bron_starting:{request_id}:1"

    # Кнопка с действиями в зависимости от статуса
    keyboard.button(text=text1, callback_data=data1)

    # Размещение кнопок "Редактировать запрос" и "Все запросы"
    keyboard.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"ssselected_request:{request_id}:1:0:0"),  # Левая кнопка
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"requests_menu:0:0:0:0:0:0:0:0")  # Правая кнопка
    )

    # Дополнительная кнопка для личного кабинета
    keyboard.row(
        InlineKeyboardButton(text="🗂 Все запросы", callback_data=f"requests_menu:0:0:0:0:0:0:0:0"),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")
    )

    # Возвращаем клавиатуру
    return keyboard.as_markup()
# Функция для клавиатуры бронирования ////period_callback_handler////
def request_choose_edit_btn(request_id, request_data, warehouse_name, mess):
    selected_days = {day: True for day in days_of_week}
    serialized_days = ",".join(day for day, selected in selected_days.items() if selected)
    keyboard_buttons = []
    if request_data:
        for row in request_data:
            warehouse_id = row[2] if row[2] not in (None, "0", 0) else "не заполнено"
            supply_type = row[3] if row[3] not in (None, "0", 0) else "не заполнено"
            supply_sum = row[4] if row[4] not in (None, "0", 0) else "не заполнено"
            coefficient = row[7] if row[7] not in (None, "0", 0) else "Бесплатно"
            quantities = row[9] if row[9] not in (None, "0", 0) else "не заполнено"
            date_start = row[11] if row[11] not in (None, "0", 0) else "не заполнено"
            date_end = row[12] if row[12] not in (None, "0", 0) else "не заполнено"
            selected_days = row[13] if row[13] not in (None, "0", 0) else "не заполнено"

            # Форматирование даты
            if date_start != "не заполнено":
                date_start = datetime.strptime(date_start, "%Y-%m-%d").strftime("%d.%m")
            else:
                date_start = "не заполнено"

            if date_end != "не заполнено":
                date_end = datetime.strptime(date_end, "%Y-%m-%d").strftime("%d.%m")
            else:
                date_end = "не заполнено"
    else:
        # Если request_data пуст, задаем все значения как "не заполнено"
        warehouse_id = "не заполнено"
        supply_type = "не заполнено"
        supply_sum = "не заполнено"
        coefficient = "не заполнено"
        quantities = "не заполнено"
        date_start = "не заполнено"
        date_end = "не заполнено"
        selected_days = "не заполнено"

    fields = [
        ("Склад", warehouse_name, f"select_type:0:{request_id}"),
        ("Тип поставки", mess, f'choose_warehouse:{request_id}:1'),
        ("Товары", f"{supply_sum} шт.", f'metod_upload:{supply_type}:{warehouse_id}:{request_id}:1'),
        ("Макс. коэф.", f"x{coefficient}", f"next_step:0:0:{supply_sum}:{request_id}:0:1"),
        ("Дни недели", selected_days, f"qwer:0:0:{request_id}:{serialized_days}:1"),
        ("Срок отгрузки", f"{quantities} дней", f"step_seven:{request_id}:1:1:1"),
        ("Начало поиска", date_start, f"eight_step:1:{request_id}:2:1"),
        ("Конец поиска", date_end, f"eight_step:1:{request_id}:2:1"),
    ]

    for field_name, field_value, field_callback in fields:
        field_button = InlineKeyboardButton(text=f"{field_name}: {field_value}", callback_data=field_callback)

        keyboard_buttons.append([field_button])

    keyboard_buttons.append([
        InlineKeyboardButton(text="< Назад", callback_data=f"ssselected_request:{request_id}:0:0:0"),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return markup

# Функция для формирования клавиатуры настроек
def settings_buttons(mess, value):
    if value == 1:
        text1 = "🌐 Выход из аккаунта вб"
    else:
        text1 = "🌐 Вход в аккаунт вб"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{mess} Уведомления", callback_data="notifications:0"),
        InlineKeyboardButton(text="🔗 Ссылки на таблицы", callback_data="urls_update:0")],
        [InlineKeyboardButton(text=text1, callback_data=f"exitfromuser:{value}")],
        [InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")]
    ])
    return keyboard

# Функция для формирования клавиатуры с ссылками и пагинацией
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def urls_buttons(urls, page, per_page=5):
    start = page * per_page
    end = start + per_page

    # Инициализация кнопок ссылок
    url_buttons = []
    if urls:
        # Список кнопок для ссылок с кнопками для удаления
        url_buttons = [
            [
                InlineKeyboardButton(text=url["url_name"], callback_data=f"plookurls:{url['url_id']}")
            ]
            for url in urls[start:end]
        ]

    # Кнопки пагинации
    pagination_buttons = []
    if urls and len(urls) > per_page:
        if start > 0:  # Если не первая страница
            pagination_buttons.append(InlineKeyboardButton(text="<", callback_data=f"urls_update:{page - 1}"))
        else:
            pagination_buttons.append(InlineKeyboardButton(text=" ", callback_data=f"none"))
        pagination_buttons.append(InlineKeyboardButton(text=f"{page + 1}", callback_data=f"none"))
        if end < len(urls):  # Если не последняя страница
            pagination_buttons.append(InlineKeyboardButton(text=">", callback_data=f"urls_update:{page + 1}"))
        else:
            pagination_buttons.append(InlineKeyboardButton(text=" ", callback_data=f"none"))
    
    # Если ссылки отсутствуют
    if not urls:
        url_buttons.append([
            InlineKeyboardButton(text="У вас пока нет сохраненных ссылок", callback_data="none")
        ])
    
    # Кнопка добавления ссылок
    add_buttons = [
        InlineKeyboardButton(text="➕ Добавить ссылку", callback_data="loopingurlname")
    ]

    # Управляющие кнопки
    control_buttons = [
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="keysettings:0"),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")
    ]

    # Формирование итоговой клавиатуры
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=url_buttons + [pagination_buttons] + [add_buttons] + [control_buttons]
    )
    return keyboard

def notification_buttons(current_state):
    if current_state == 1:
        mes = "Выключить уведомления"
    else:
        mes = "Включить уведомления"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=mes, callback_data="notifications:1")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="keysettings:0"),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")]
    ])
    return keyboard

def urls_ext_buttons():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Ссылки", callback_data="urls_update:0"),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")]
    ])
    return keyboard

def choose_url_btn(url_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Изменить название", callback_data=f"kjeay:1:{url_id}"),
        InlineKeyboardButton(text="🔗 Изменить ссылку", callback_data=f"kjeay:2:{url_id}")],
        [InlineKeyboardButton(text="✏️ Изменить все", callback_data=f"kjeay:3:{url_id}"),
         InlineKeyboardButton(text="🗑 Удалить", callback_data=f"keysettings:{url_id}")],
        [InlineKeyboardButton(text="🔗 Ссылки", callback_data="urls_update:0"),
        InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")]
    ])
    return keyboard

def notif_send_btn(request_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Открыть запрос", callback_data=f"ssselected_request:{request_id}:0:0:0")],
        [InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="main_menu")]
    ])
    return keyboard
import re
import pandas as pd
from io import BytesIO
import requests
from datetime import datetime, timedelta

from handlers.database.connection import update_request_with_file, set_period, set_end_date, get_shop_data, set_status, get_all_quantities, set_null_quantity, set_quantity

async def filter_supply_async(supplies, supply_text_type, warehouse_name):
    return [
        supply for supply in supplies
        if supply[2] == supply_text_type and supply[5] == warehouse_name
    ]

async def filter_supply_type(supply_type):
    supply_type = int(supply_type)
    return {1: "Короба", 2: "Монопаллеты", 3: "Суперсейф", 4: "QR-поставка с коробами"}.get(supply_type, "Неизвестный тип поставки")

async def filter_request_type(request_type):
    return {"chat": "Отправь сообщение с инфорацией о поставке в формате 'шк товара количество, '", "google": "Отправь ссылку на таблицу:", "draft": "Выбери один из черновиков:", "my_google": "Использую добавленную ссылку на google sheet.", "table": "Отправь таблицу:"}.get(request_type, "Неизвестный тип загрузки")

async def filter_supply_text_type(supply_type):
    supply_type = int(supply_type)
    return {1: "Короб", 2: "Монопаллета", 3: "Суперсейф", 4: "QR-поставка с коробами"}.get(supply_type, "Неизвестный тип поставки")

#Загрузка поставки через чат
async def look_chat(message, request_id):
    # Разбираем сообщение пользователя
    rows = re.findall(r'(\d+)\s+(\d+)', message.text)
    if not rows:
        value, supply_sum = 0
        return value, supply_sum
    else:
        value = 1

    # Создаём DataFrame с двумя колонками
    df = pd.DataFrame(rows, columns=["Баркод", "Количество"])
    df["Количество"] = pd.to_numeric(df["Количество"])  # Преобразуем к числовому типу

    # Считаем сумму значений во второй колонке
    supply_sum = int(df["Количество"].sum())

    # Сохраняем в Excel
    excel_file = 'data.xlsx'
    df.to_excel(excel_file, index=False)
    # Читаем Excel-файл в бинарном режиме
    with open(excel_file, 'rb') as f:
        file_data = f.read()

    await update_request_with_file(excel_file, file_data, supply_sum, request_id)

    return value, supply_sum

#Загрузка поставки через файл
async def look_excel(message, request_id):
    if message.document.mime_type != 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        return 0, 0

    try:
        # Получаем метаданные файла
        file_info = await message.bot.get_file(message.document.file_id)

        # Загружаем содержимое файла, которое возвращает BytesIO
        file_content = await message.bot.download_file(file_info.file_path)
        file_name = message.document.file_name or "uploaded_data.xlsx"

        # Проверка типа для отладки
        print(f"Тип file_content: {type(file_content)}")  # Ожидаем <class '_io.BytesIO'>

        # Если это _io.BytesIO, читаем как файл для pandas
        if isinstance(file_content, BytesIO):
            file_data = file_content  # Используем напрямую
        else:
            file_data = BytesIO(file_content)  # На случай, если вернутся байты

        # Чтение Excel в pandas
        df = pd.read_excel(file_data)

        # Приводим названия колонок к нижнему регистру и удаляем пробелы
        df.columns = [col.strip().lower() for col in df.columns]

        # Отладка: выводим обработанные названия колонок
        print(f"Обработанные названия колонок: {df.columns}")

        # Проверяем наличие колонок
        if "баркод" not in df.columns or "количество" not in df.columns:
            print("Ошибка: Требуемые колонки отсутствуют.")
            return 2, 0

        # Преобразуем колонку "количество" к числовому типу
        df["количество"] = pd.to_numeric(df["количество"], errors='coerce').fillna(0)
        supply_sum = int(df["количество"].sum())

        # Преобразуем содержимое файла в байты для сохранения в базу
        file_content_bytes = file_data.getvalue() if isinstance(file_data, BytesIO) else file_content

        # Передаем данные в базу
        await update_request_with_file(file_name, file_content_bytes, supply_sum, request_id)

        return 3, supply_sum
    except Exception as e:
        print(f"Error in look_excel during file processing: {e}")
        return 2, 0

async def look_google(message, request_id):
    try:
        url1 = message.text
    except AttributeError:
        url1 = message
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url1)
    if not match:
        print("Ошибка: Некорректная ссылка на Google Sheets.")
        return 4, 0

    try:
        # Формируем URL для экспорта Google Sheets в CSV
        sheet_id = match.group(1)
        url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

        # Загружаем данные
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Ошибка загрузки данных: HTTP {response.status_code}")
            return 4, 0

        # Проверяем содержимое CSV
        if not response.content or len(response.content.strip()) == 0:
            print("Ошибка: Получен пустой CSV-файл.")
            return 4, 0
        print(f"Загружен CSV-файл, размер: {len(response.content)} байт")

        # Загружаем данные в pandas DataFrame (без пропуска первой строки)
        csv_data = BytesIO(response.content)
        df = pd.read_csv(csv_data, on_bad_lines='skip', engine='python')

        # Логируем содержимое DataFrame после загрузки
        print(f"DataFrame загружен: {df.shape} строк, {df.columns.tolist()} колонок")
        print(df.head())  # Печатаем первые строки для проверки

        # Проверяем количество колонок
        if df.shape[1] < 2:
            print(f"Ошибка: Недостаточно колонок в Google Sheets. Найдено {df.shape[1]} колонок.")
            return 4, 0

        # Удаляем полностью пустые строки
        df.dropna(how='all', inplace=True)

        # Удаляем строки, где хотя бы одна из первых двух колонок пуста
        df.dropna(subset=[df.columns[0], df.columns[1]], inplace=True)

        # Преобразуем вторую колонку в числовой формат и округляем значения
        df.iloc[:, 1] = pd.to_numeric(df.iloc[:, 1], errors='coerce').fillna(0).round(0).astype(int)

        # Проверяем, не пуст ли DataFrame после фильтрации
        if df.empty:
            print("Ошибка: DataFrame пуст после обработки.")
            return 4, 0

        # Считаем сумму значений во второй колонке
        supply_sum = int(df.iloc[:, 1].sum())
        print(f"Сумма значений во второй колонке: {supply_sum}")

        # Сохраняем DataFrame в Excel
        file_data = BytesIO()
        df.to_excel(file_data, index=False, engine='openpyxl')
        file_data.seek(0)
        file_bytes = file_data.getvalue()

        # Логируем содержимое перед сохранением
        print(f"DataFrame сохранен в Excel, размер данных: {len(file_bytes)} байт")

        # Передаём данные в базу
        file_name = f"google_sheet_{sheet_id}.xlsx"
        await update_request_with_file(file_name, file_bytes, supply_sum, request_id)

        print(f"Файл успешно обработан: {file_name}, сумма поставки: {supply_sum}")
        return 5, supply_sum
    except Exception as e:
        print(f"Ошибка в функции look_google: {e}")
        return 4, 0


# Проверка value и изменение дня недели
async def select_day(value, selected_days):
    if value in selected_days:
            selected_days[value] = not selected_days[value]
    return selected_days

# расшифровка дат и запись в бд
async def set_dates_period(period, request_id):
    today = datetime.today()
    period = period.strip()
    try:
        if int(period) in (1, 2, 3):    
            period = int(period)
            if period == 1:
                date_start = (today + timedelta(days=1)).strftime("%Y-%m-%d")
                date_end = (today + timedelta(days=2)).strftime("%Y-%m-%d")

            elif period == 2:
                date_start = today.strftime("%Y-%m-%d")
                date_end = (today + timedelta(days=7)).strftime("%Y-%m-%d")
                
            elif period == 3:
                date_start = today.strftime("%Y-%m-%d")
                date_end = (today + timedelta(days=100)).strftime("%Y-%m-%d")

            await set_period(date_start, date_end, request_id)
    except:
        await set_end_date(period, request_id)

# Функция построение текста магазинов
async def set_shop_list(user_id):
    shops = await get_shop_data(user_id)
    shop_list = "*🏬 Мои магазины:*\n\n"
    for i, shop in enumerate(shops, start=1):
        shop_list += f"Магазин {i}: {shop['shop_name']}\n"
    if not shops:
        shop_list = "У вас пока нет добавленных магазинов."
    return shops, shop_list

async def filter_data(data, types):
    var1 = var2 = var3 = 0 
    if types:
        if '1' in types:
            var1 = "Короба"
        if '2' in types:
            var2 = "Монопаллеты"
        if '3' in types:
            var3 = "Суперсейф"
    filtered_data = []
    for item in data:
        date = item.get("date", "Не указана").split("T")[0]  
        warehouse = item.get("warehouseName", "Неизвестный склад")
        box_type = item.get("boxTypeName", "Неизвестный тип")
        coefficient = item.get("coefficient", "Нет данных")

        match_found = False  

        if var1 and var1 in box_type:
            match_found = True
        if var2 and var2 in box_type:
            match_found = True
        if var3 and var3 in box_type:
            match_found = True

        if match_found:
            filtered_data.append({
                "date": date,
                "warehouseName": warehouse,
                "boxTypeName": box_type,
                "coefficient": coefficient
            })
    return filtered_data

def format_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%H:%M %d.%m")

async def start_searching(value:int, request_id):
    if value == 1:
        status = "active"
    elif value == 2:
        status = "ready"
    await set_status(status, request_id)

async def escape_markdown_v2(text: str) -> str:
    special_chars = r"[\\\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!]"
    return re.sub(special_chars, r"\\\g<0>", text)

async def format_date_md(day):
    if day != "0":
        formatted_date = datetime.strptime(day, "%Y-%m-%d").strftime("%d.%m")
    else:
        formatted_date = "не заполнено"
    return formatted_date

async def minus_quantities():
    rows = await get_all_quantities()
    for row in rows:
        if row["quantities"] is not None:
            request_id = int(row["request_id"])
            quantity = int(row["quantities"])
            new_quantity = quantity - 1
            if new_quantity < 0:
                await set_null_quantity(request_id)
            else:
                await set_quantity(new_quantity, request_id)
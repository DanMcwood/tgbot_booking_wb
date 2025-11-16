import aiosqlite
from datetime import datetime
from collections import Counter
import uuid

from handlers.params.settings import DB_PATH

async def get_db_connection():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn

#--------- users -----------------------------------------------------------------------------------------------------------------------------------
# ДОБАВЛЕНИЕ ------

async def set_notification(user_id, notification):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE users SET notification = ? WHERE user_id = ?", (notification, user_id,))
        await conn.commit()

async def add_user_to_db(user_id: int, nickname: str):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("INSERT OR IGNORE INTO users (user_id, nickname) VALUES (?, ?)",(user_id, nickname,))
        await conn.commit()

async def set_selected_shop(shop_id, user_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE users SET selected_shop = ? WHERE user_id = ?", (shop_id, user_id,))
        await conn.commit()

async def add_nickname_to_db(text, user_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (text, user_id,))
        await conn.commit()

async def set_session(value, user_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE users SET session = ? WHERE user_id = ?", (value, user_id,))
        await conn.commit()

# УДАЛЕНИЕ ------


# ВЫБОР ------

async def get_session(user_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT session FROM users WHERE user_id = ?", (user_id,))
        session = await cursor.fetchone()
    return session['session']

async def get_notification(user_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT notification FROM users WHERE user_id = ?", (user_id,))
        notification = await cursor.fetchone()
    return notification['notification']

async def check_user_exists(user_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT user_id, nickname FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
        if user:
            return {'user_id': user[0], 'nickname': user[1]} 
        return None  

async def get_user_data(user_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
    return user

async def get_active_requests(user_id: int) -> int:
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT active_requests FROM users WHERE user_id = ?",(user_id,))
        result = await cursor.fetchone()
        return result['active_requests'] if result else 0  # Возвращаем 0, если пользователя нет в базе

async def get_nickname(user_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT nickname FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None
    
async def get_selected_shop(user_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT selected_shop FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else None
    
async def get_all_user_ids():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT user_id FROM users", ())
        result = await cursor.fetchall()
        return [row[0] for row in result] if result else None

#--------- requests -----------------------------------------------------------------------------------------------------------------------------------
# ДОБАВЛЕНИЕ ------

async def set_cool_bron(fact_date, fact_coefficient, request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET status = ?, fact_date = ?, fact_coefficient = ?, is_processing = 0 WHERE request_id = ?", ("done", fact_date, fact_coefficient, request_id))
        await conn.commit()

async def set_is_processing_and_status(is_processing, status, request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET status = ?, is_processing = ? WHERE request_id = ?", (status, is_processing, request_id))
        await conn.commit()

async def set_null_process_status(is_processing, status, request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET is_processing = ?, status = ? WHERE request_id = ?", (is_processing, status, request_id,))
        await conn.commit()

async def set_new_value(value, request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET is_processing = ? WHERE request_id = ?", (value, request_id,))
        await conn.commit()

async def set_state_request(state, request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET state = ? WHERE request_id = ?", (state, request_id,))
        await conn.commit()

async def set_supply_type(supply_type, request_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET supply_type = ?, edit_date = ? WHERE request_id = ?", (supply_type, edit_date, request_id,))
        await conn.commit()

async def set_warehouse_id(warehouse_id, request_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET warehouse_ids = ?, edit_date = ? WHERE request_id = ?", (warehouse_id, edit_date, request_id,))
        await conn.commit()

async def add_request_to_db(shop_id, warehouse_id, supply_type, user_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status = "in process"
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("INSERT OR IGNORE INTO supply_requests (shop_id, warehouse_ids, supply_type, edit_date, status, user_id) VALUES (?, ?, ?, ?, ?, ?) RETURNING request_id",(shop_id, warehouse_id, supply_type, edit_date, status, user_id))
        result = await cursor.fetchone()  # Получаем результат
        await conn.commit()
        return result['request_id'] if result else None

async def update_request_with_file(excel_file, file_data, supply_sum, request_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute('''
            UPDATE supply_requests
            SET filename = ?, file = ?, supply_sum = ?, edit_date = ?
            WHERE request_id = ?
        ''', (excel_file, file_data, supply_sum, edit_date, request_id,))
        await conn.commit()
        
async def set_coef(coefficient, request_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET coefficient = ?, edit_date = ? WHERE request_id = ?", (coefficient, edit_date, request_id,))
        await conn.commit()

async def set_quantities(quantities, request_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET quantities = ?, edit_date = ? WHERE request_id = ?", (quantities, edit_date, request_id,))
        await conn.commit()

async def set_selected_days(selected_days, request_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET custom_dates = ?, edit_date = ? WHERE request_id = ?", (selected_days, edit_date, request_id,))
        await conn.commit()

async def set_period(date_start, date_end, request_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET date_start = ?, date_end = ?, edit_date = ? WHERE request_id = ?", (date_start, date_end, edit_date, request_id,))
        await conn.commit()

async def set_start_date(value, request_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET date_start = ?, edit_date = ? WHERE request_id = ?", (value, edit_date, request_id,))
        await conn.commit()

async def set_update_requests_2(supply_sum, supply_number, request_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET supply_sum = ?, supply_number = ?, edit_date = ? WHERE request_id = ?", (supply_sum, supply_number, edit_date, request_id,))
        await conn.commit()

async def set_end_date(period, request_id):
    edit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET date_end = ?, edit_date = ? WHERE request_id = ?", (period, edit_date, request_id,))
        await conn.commit()

async def set_status(status, request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET status = ? WHERE request_id = ?", (status, request_id,))
        await conn.commit()
        
async def set_null_quantity(request_id):
    status = "timeout"
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET status = ? WHERE request_id = ?", (status, request_id,))
        await conn.commit()

async def set_quantity(new_quantity, request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE supply_requests SET quantities = ? WHERE request_id = ?", (new_quantity, request_id,))
        await conn.commit()

# УДАЛЕНИЕ ------

async def delete_request(request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("DELETE FROM supply_requests WHERE request_id = ?", (request_id,))
        await conn.commit()

async def delete_dates_start_end(request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("DELETE FROM supply_requests (date_start, date_end) VALUES (?, ?) WHERE request_id = ?", (request_id,))
        await conn.commit()

# ВЫБОР ------

async def get_request_data_bron(request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT coefficient, custom_dates, status, date_start, date_end, supply_number, is_processing, user_id FROM supply_requests WHERE request_id = ?", (request_id,))
        request = await cursor.fetchone()
    return request

async def get_request_by_status():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT 1 FROM supply_requests WHERE status = 'searching' AND is_processing = 0 LIMIT 1")
        result = await cursor.fetchone()
    return result

async def get_request_searching():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT request_id, shop_id FROM supply_requests WHERE status = 'searching' AND is_processing = 0")
        requests = await cursor.fetchall()
    return requests

async def get_data_request_searching():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM supply_requests WHERE status = 'searching' AND is_processing = 0")
        requests = await cursor.fetchall()
    return requests

async def get_data_request_just_searching():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM supply_requests WHERE status = 'searching'")
        requests = await cursor.fetchall()
    return requests

async def get_supply_number(request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT supply_number FROM supply_requests WHERE request_id = ?", (request_id,))
        result = await cursor.fetchone()
    return result[0] if result else None

async def get_all_quantities():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT request_id, quantities FROM supply_requests")
        rows = await cursor.fetchall()
    return rows

async def get_all_is_process():
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT request_id, is_processing FROM supply_requests")
        rows = await cursor.fetchall()
    return rows

async def get_selected_days(request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT custom_dates FROM supply_requests WHERE request_id = ?", (request_id,))
        selected_days = await cursor.fetchone()
    return selected_days

async def get_request_data(request_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM supply_requests WHERE request_id = ?", (request_id,))
        requests = await cursor.fetchall()
    return requests

async def get_all_request_data(shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM supply_requests WHERE shop_id = ?", (shop_id,))
        requests = await cursor.fetchall()
    return requests  

async def get_shop_id(request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT shop_id FROM supply_requests WHERE request_id = ?", (request_id,))
        result = await cursor.fetchone()
    return result[0] if result else None

async def get_status(request_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT status FROM supply_requests WHERE request_id = ?", (request_id,))
        result = await cursor.fetchone()
    return result[0] if result else None

#--------- shops -----------------------------------------------------------------------------------------------------------------------------------
# ДОБАВЛЕНИЕ ------
async def add_shop_wb_to_db(user_id, shop_name):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("""
            INSERT INTO shops (user_id, shop_wb) VALUES (?, ?)
        """, (user_id, shop_name))
        await conn.commit()

async def add_shop_to_db(user_id: int, shop_name: str):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("INSERT INTO shops (shop_name, user_id) VALUES (?, ?) RETURNING shop_id",(shop_name, user_id,))
        result = await cursor.fetchone()  
        await conn.commit()
        return result['shop_id'] if result else None
    
async def add_api_to_db(text, shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE shops SET api = ? WHERE shop_id = ?", (text, shop_id,))
        await conn.commit()

async def set_shop_name(text, shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE shops SET shop_name = ? WHERE shop_id = ?", (text, shop_id,))
        await conn.commit()

async def update_selected(selected_warehouses, shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE shops SET selected_warehouses = ? WHERE shop_id = ?", (selected_warehouses, shop_id,))
        await conn.commit()

async def set_favorite_warehouses(updated_favorites, shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE shops SET favorite_warehouses = ? WHERE shop_id = ?", (updated_favorites, shop_id,))
        await conn.commit()

async def set_null_selected(shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE shops SET selected_warehouses = NULL WHERE shop_id = ?", (shop_id,))
        await conn.commit()

async def set_shop_name(text, shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE shops SET shop_name = ? WHERE shop_id = ?", (text, shop_id,))
        await conn.commit()

        
# УДАЛЕНИЕ ------

async def delete_shop(shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("DELETE FROM shops WHERE shop_id = ?", (shop_id,))
        await conn.commit()

# ВЫБОР ------

async def get_user_id(shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT user_id FROM shops WHERE shop_id = ?", (shop_id,))
        result = await cursor.fetchone()
        return result[0] if result else None
    
async def get_shops_with_counter(user_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Выбираем shop_id и shop_wb для данного пользователя
        await cursor.execute(
            "SELECT shop_id, shop_wb, shop_name FROM shops WHERE user_id = ? AND shop_wb IS NOT NULL",
            (user_id,)
        )
        result = await cursor.fetchall()
        # Преобразуем результат в список словарей для удобства
        return [{"shop_id": row[0], "shop_wb": row[1], "shop_name": row[2]} for row in result]
    
async def get_shops_wb(user_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        # Извлекаем все магазины пользователя
        await cursor.execute("SELECT shop_wb FROM shops WHERE user_id = ?", (user_id,))
        result = await cursor.fetchall()
        return [row[0] for row in result] if result else []
    
async def get_shop_wb(shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT shop_wb FROM shops WHERE shop_id = ?", (shop_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

async def get_api_key(shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT API FROM shops WHERE shop_id = ?", (shop_id,))
        result = await cursor.fetchone()
        return result[0] if result else None
    
async def get_shop_name(shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT shop_name FROM shops WHERE shop_id = ?", (shop_id,))
        result = await cursor.fetchone()
        return result[0] if result else None
    
async def get_api_key_from_shop(selected_shop):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT API FROM shops WHERE shop_id = ?", (selected_shop,))
        result = await cursor.fetchone()
        return result[0] if result else None
    
async def get_shop_data(user_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM shops WHERE user_id = ?", (user_id,))
        shops = await cursor.fetchall()
    return shops

async def get_warehouses_and_selected(shop_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT warehouse_id, warehouse_name FROM warehouses")
        warehouses = await cursor.fetchall()
        await cursor.execute("SELECT selected_warehouses FROM shops WHERE shop_id = ?", (shop_id,))
        result = await cursor.fetchone()
        selected_warehouses = list(map(int, result[0].split(","))) if result and result[0] else []
    return warehouses, selected_warehouses

async def get_warehouses_and_favorite(shop_id: int):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT warehouse_id, warehouse_name FROM warehouses")
        warehouses = await cursor.fetchall()
        await cursor.execute("SELECT favorite_warehouses FROM shops WHERE shop_id = ?", (shop_id,))
        result = await cursor.fetchone()
        favorite_warehouses = list(map(int, result[0].split(","))) if result and result[0] else []
    return warehouses, favorite_warehouses


#--------- warehouses -----------------------------------------------------------------------------------------------------------------------------------
# ДОБАВЛЕНИЕ ------

async def save_warehouses_to_db(warehouses):
    try:
        conn = await get_db_connection()
        async with conn.cursor() as cursor:
            await cursor.execute("DELETE FROM warehouses")
            for warehouse in warehouses:
                warehouse_id = warehouse.get("ID")
                warehouse_name = warehouse.get("name")
                if warehouse_id and warehouse_name:
                    try:
                        await conn.execute("INSERT OR IGNORE INTO warehouses (warehouse_id, warehouse_name) VALUES (?, ?)",(warehouse_id, warehouse_name,))
                    except aiosqlite.Error as e:
                        print(f"Ошибка при добавлении склада {warehouse_id}: {e}")
            await conn.commit()
    except aiosqlite.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")


# УДАЛЕНИЕ ------


# ВЫБОР ------

async def get_warehouse_name(warehouse_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT warehouse_name FROM warehouses WHERE warehouse_id = ?", (warehouse_id,))
        result = await cursor.fetchone()
        return result[0] if result else None

#--------- urls -----------------------------------------------------------------------------------------------------------------------------------
# ДОБАВЛЕНИЕ ------

async def insert_urls(shop_id, url_name, url):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("""
            INSERT INTO urls (shop_id, url_name, url) VALUES (?, ?, ?)
        """, (shop_id, url_name, url))
        await conn.commit()   

async def set_url_name(url_id, url_name):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE urls SET url_name = ? WHERE url_id = ?", (url_name, url_id,))
        await conn.commit()

async def set_url(url_id, url):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("UPDATE urls SET url = ? WHERE url_id = ?", (url, url_id,))
        await conn.commit()

# УДАЛЕНИЕ ------

async def del_url(url_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("DELETE FROM urls WHERE url_id = ?", (url_id,))
        await conn.commit()

# ВЫБОР ------

async def get_user_urls(shop_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        cursor = await conn.execute("SELECT url_id, url_name, url FROM urls WHERE shop_id = ?", (shop_id,))
        urls = await cursor.fetchall()
    return [dict(url) for url in urls]
    
async def get_url_data(url_id):
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT * FROM urls WHERE url_id = ?", (url_id,))
        data = await cursor.fetchone()
    return data['url_name'], data['url']





#Активные запросы
async def update_active_requests():
    """Обновляет active_requests в таблице users на основе данных из supply_requests."""
    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT user_id FROM supply_requests WHERE status = 'searching'")
        rows = await cursor.fetchall()
        user_ids = [row["user_id"] for row in rows]

        user_request_counts = Counter(user_ids)
        for user_id, request_count in user_request_counts.items():
            await cursor.execute(
                "UPDATE users SET active_requests = ? WHERE user_id = ?",
                (request_count, user_id) 
            )

        await conn.commit()
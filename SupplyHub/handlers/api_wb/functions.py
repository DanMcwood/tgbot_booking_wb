from handlers.database.connection import get_api_key_from_shop, get_selected_shop, save_warehouses_to_db, get_all_user_ids
from handlers.params.settings import BASE_URL, CACHE_LIFETIME, TIME_FRAME, CALL_LIMIT
import aiohttp
from datetime import datetime

cached_data = {}
last_updated = {}

# Функция для получения списка складов с Wildberries
async def get_warehouses(user_id):
    selected_shop = await get_selected_shop(user_id)
    API_KEY = await get_api_key_from_shop(selected_shop)
    
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    url = f"{BASE_URL}/api/v1/warehouses"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        return data
                    else:
                        return None
                else:
                    return None
    except aiohttp.ClientError as e:
        return None
    
# Функция для обновления складов
async def update_warehouses(user_id):
    warehouses = await get_warehouses(user_id)
    if warehouses:
        await save_warehouses_to_db(warehouses)

async def update_all_warehouses():
    user_ids = await get_all_user_ids()  
    
    for user_id in user_ids:
        warehouses = await get_warehouses(user_id)
        if warehouses:
            await save_warehouses_to_db(warehouses)

# Функция для получения коэффициентов складов
async def first_get_coef(user_id, selected_warehouses):
    data = await get_coef(user_id, selected_warehouses)
    now = datetime.now()
    if data:
        cached_data[user_id] = data
        last_updated[user_id] = now
    
    return data

# Функция для получения коэффициентов складов
async def get_coef(user_id, selected_warehouses):
    if set(selected_warehouses) <= {1, 2, 3}:  
        selected_warehouses = None
    if selected_warehouses is not None:
        warehouse_ids = ",".join(map(str, selected_warehouses))
        url = f"{BASE_URL}/api/v1/acceptance/coefficients?warehouseIDs={warehouse_ids}"
    else:
        url = f"{BASE_URL}/api/v1/acceptance/coefficients"
    selected_shop = await get_selected_shop(user_id)
    API_KEY = await get_api_key_from_shop(selected_shop)
    headers = {"Authorization": f"Bearer {API_KEY}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        return data
                    else:
                        return None
                else:
                    return None
    except aiohttp.ClientError:
        return None

# Функция для получения коэффициентов складов для бронирования
async def get_supply_coef(warehouse_ids, api):
    url = f"{BASE_URL}/api/v1/acceptance/coefficients?warehouseIDs={warehouse_ids}"
    headers = {"Authorization": f"Bearer {api}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        return data
                    else:
                        return None
                else:
                    return None
    except aiohttp.ClientError:
        return None
    
# Функция получения кешированных коэффициентов
async def get_cached_coefficients(user_id, selected_warehouses, limiter):
    # Проверяем актуальность кеша
    now = datetime.now()
    if user_id in cached_data and user_id in last_updated:
        if now - last_updated[user_id] < CACHE_LIFETIME:
            return cached_data[user_id]
        # Проверяем лимит вызовов
    if not await limiter.can_user_call(user_id):
        raise Exception("Превышен лимит запросов к API. Повторите попытку позже.")
    # Если кеш устарел или данных нет, запрашиваем новые данные
    data = await get_coef(user_id, selected_warehouses)
    if data:
        cached_data[user_id] = data
        last_updated[user_id] = now
    return data
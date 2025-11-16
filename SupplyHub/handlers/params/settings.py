from datetime import datetime, timedelta

API_TOKEN = '7703064254:AAEanvpBWj15YCTpGGuRgelwk0FuVtP8wiU'
BASE_URL = "https://supplies-api.wildberries.ru"
DB_PATH = 'C:/Users/huawei/desktop/SupplyHub/handlers/database/database.db'
SUPPLIES_URL = 'https://seller.wildberries.ru/supplies-management/all-supplies'
stay_api = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQxMTE4djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc0ODUyNjM2OCwiaWQiOiIwMTkzNzA3Mi03MWFjLTcxNzctOTg2My0xZDAyODFmNWEyOTEiLCJpaWQiOjU5OTM4Njk0LCJvaWQiOjY2MzQ4NCwicyI6MTAyNCwic2lkIjoiOTdhZjIxN2ItY2RiZC00YzY0LWI0NzctOTc0MTA3YzM3YjcxIiwidCI6ZmFsc2UsInVpZCI6NTk5Mzg2OTR9.H1WAKnsWFaJzfJs9Yq3aH4fmpZbIL-evGireE_sDweaThupHXUa15gwK3lWglUySj8_xSgLHUdoW9COnaj4c_Q"
second_api = "eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjQxMTE4djEiLCJ0eXAiOiJKV1QifQ.eyJlbnQiOjEsImV4cCI6MTc0ODUyNjM2OCwiaWQiOiIwMTkzNzA3Mi03MWFjLTcxNzctOTg2My0xZDAyODFmNWEyOTEiLCJpaWQiOjU5OTM4Njk0LCJvaWQiOjY2MzQ4NCwicyI6MTAyNCwic2lkIjoiOTdhZjIxN2ItY2RiZC00YzY0LWI0NzctOTc0MTA3YzM3YjcxIiwidCI6ZmFsc2UsInVpZCI6NTk5Mzg2OTR9.H1WAKnsWFaJzfJs9Yq3aH4fmpZbIL-evGireE_sDweaThupHXUa15gwK3lWglUySj8_xSgLHUdoW9COnaj4c_Q"
if stay_api == second_api:
    time_to_sleep = 10
else:
    time_to_sleep = 5
# Количество коэффициентов
COEFFICIENTS = 20

# Переменные для пагинации
ITEMS_PER_PAGE = 10

# Создаем клавиатуру выбора дней недели (все дни выбраны по умолчанию)
days_of_week = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

day_translation = {
    "Mon": "Пн", "Tue": "Вт", "Wed": "Ср", "Thu": "Чт", "Fri": "Пт", "Sat": "Сб", "Sun": "Вс"
}

# Месяц и год для отображения
current_month = datetime.today().month
current_year = datetime.today().year

# Переменная для хранения времени последнего вызова по кнопке
last_update_time = datetime.now() - timedelta(minutes=1)

# Маппинг русских месяцев на английские
month_translation = {
    "января": "January", "февраля": "February", "марта": "March", "апреля": "April", "мая": "May", "июня": "June",
    "июля": "July", "августа": "August", "сентября": "September", "октября": "October", "ноября": "November", "декабря": "December"
}

CACHE_LIFETIME = timedelta(minutes=5)  # Время жизни кеша
TIME_FRAME = timedelta(minutes=1)  # Окно времени для лимита запросов
CALL_LIMIT = 6  # Лимит вызовов за TIME_FRAME
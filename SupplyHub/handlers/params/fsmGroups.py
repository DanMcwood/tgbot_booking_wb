from aiogram.fsm.state import StatesGroup, State

# Состояния для FSM
class Form(StatesGroup):
    waiting_for_new_name = State()  # Ожидаем нового имени магазина
    waiting_for_supply = State() # Ожидаем данные для поставок
    choosing_days = State()
    choosing_delivery_days = State()
    choosing_start_date = State()
    choosing_end_date = State()
    choosing_search_period = State() 
    waiting_for_name_url = State()
    waiting_for_url = State()
    waiting_for_change = State()

#Классы
class RegisterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_shop_name = State()
    waiting_for_api = State()
    waiting_for_phone_number = State()
    waiting_for_phone = State()
    waiting_for_sms_code = State()
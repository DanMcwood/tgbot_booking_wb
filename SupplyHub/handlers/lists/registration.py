from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import Dispatcher, types
import asyncio
from aiogram import types


from handlers.database.connection import add_nickname_to_db, set_selected_shop, add_api_to_db, get_nickname, get_shop_name, get_shop_wb, set_shop_name, get_shops_with_counter
from handlers.tasks.utils import escape_markdown_v2
from handlers.params.fsmGroups import RegisterStates
from handlers.chrome_wb.auth import send_phone_number, send_sms_code 
from handlers.chrome_wb.check_session import check_session
from handlers.chrome_wb.shops_wb import fetch_shops
from handlers.buttons import main_menu_btn, get_shop_wb_reg_btn
from bot import bot, dp

user_sessions = {}

async def process_name(message: Message, state: FSMContext):
    data = await state.get_data()
    hello_message_id = data.get("hello_message_id")
    chat_id = data.get("chat_id")
    value = data.get("value")
    user_id = data.get("user_id")
    value = int(value)
    if value != 1:
        text = message.text
        await message.delete()
        await add_nickname_to_db(text, user_id)
        chat_id = message.chat.id

    if hello_message_id and chat_id:
        try:
            loading_message = await bot.edit_message_text("🚀 Выполняется загрузка...", chat_id=chat_id, message_id=hello_message_id)
        except Exception:
            loading_message = await message.answer("🚀 Выполняется загрузка...")

    session_active = await check_session(user_id)
    if session_active:
        await loading_message.edit_text("✅ Вы уже авторизованы и можете продолжать работать!\n Повторно введите коамнду /start")
        return
    await state.clear()
    user_sessions[user_id] = {'stage': 'phone'}
    mes_id = await loading_message.edit_text(
        "Авторизация\n(необходима всего 1 раз)\n\n"
        "📱 Отправьте номер телефона, привязанный к личному кабинету WB Партнёры:\n"
        "Формат: +7**********"
    )
    await state.set_state(RegisterStates.waiting_for_phone)
    await state.update_data(mes_id=mes_id.message_id, chat_id=chat_id)

async def handle_auth(message: Message, state: FSMContext):
    """Обработка процесса авторизации пользователя."""
    user_id = str(message.from_user.id)
    data = await state.get_data()
    mes_id = data.get("mes_id")
    chat_id = data.get("chat_id")
    await message.delete()
    current_state = await state.get_state()

    if current_state == RegisterStates.waiting_for_phone.state:
        phone_number = message.text.strip()
        if not (phone_number.startswith("+7") and phone_number[2:].isdigit() and len(phone_number) == 12):
            new_mes = await bot.edit_message_text("Введи корректный номер телефона в формате: +7**********", chat_id=chat_id, message_id=mes_id)
            await state.update_data(mes_id=new_mes.message_id, chat_id=message.chat.id)
            return

        loading_message = await bot.edit_message_text("🚀 Выполняется загрузка...", chat_id=chat_id, message_id=mes_id)

        page_id = await send_phone_number(user_id, phone_number)
        if page_id:
            if user_id not in user_sessions:
                user_sessions[user_id] = {}
            user_sessions[user_id]['phone_number'] = phone_number

            new_mes = await loading_message.edit_text("📱 Отправьте код из SMS:")
            await state.clear()
            await state.set_state(RegisterStates.waiting_for_sms_code)
        else:
            new_mes = await loading_message.edit_text("❌ Ошибка при отправке номера телефона. Попробуйте снова.")
        await state.update_data(mes_id=new_mes.message_id, chat_id=message.chat.id)

    elif current_state == RegisterStates.waiting_for_sms_code.state:
        sms_code = message.text.strip()
        data = await state.get_data()

        if not (sms_code.isdigit() and len(sms_code) == 6):
            new_mes = await bot.edit_message_text("Введи корректный 6-значный SMS-код.", chat_id=chat_id, message_id=mes_id)
            await state.update_data(mes_id=new_mes.message_id, chat_id=message.chat.id)
            return
        
        loading_message = await bot.edit_message_text("🚀 Выполняется загрузка...", chat_id=chat_id, message_id=mes_id)

        success = await send_sms_code(user_id, sms_code)
        if success:
            user_sessions[user_id]['authenticated'] = True
            shops = False
            sucsess2 = await fetch_shops(user_id)
            if sucsess2:
                shops = await get_shops_with_counter(user_id)

            new_mes = await loading_message.edit_text("✅ Авторизация успешна!\nТеперь выбери магазин:", reply_markup=get_shop_wb_reg_btn(shops))
            await state.clear()
            await state.update_data(mes_id=new_mes.message_id, chat_id=message.chat.id)
        else:
            new_mes = await loading_message.edit_text("❌ Ошибка при вводе SMS-кода. Попробуйте снова.")
            await state.update_data(mes_id=new_mes.message_id, chat_id=message.chat.id)

async def process_get_shop_name(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id   
    _, shop_id =  callback_query.data.split(":")
    await set_selected_shop(shop_id, user_id)
    shop_wb = await get_shop_wb(shop_id)
    new_mes = await callback_query.message.edit_text(f"Введи название магазина для работы.\n Текущее название: {shop_wb}")
    await state.update_data(shop_id=shop_id)
    await state.set_state(RegisterStates.waiting_for_shop_name)
    await state.update_data(mes_id=new_mes.message_id, chat_id=callback_query.message.chat.id)

async def process_shop_name(message: Message, state: FSMContext):
    user_data = await state.get_data()
    shop_id = user_data.get('shop_id')
    mes_id = user_data.get("mes_id")
    chat_id = user_data.get("chat_id")
    shop_id = int(shop_id)
    text = message.text
    await message.delete()
    await set_shop_name(text, shop_id)
    new_mes = await bot.edit_message_text("Укажи API-ключ для магазина.\n\n Его можно найти в настройках профиля лк селлера (Доступ к API)", chat_id=chat_id, message_id=mes_id)
    await state.clear()
    await state.set_state(RegisterStates.waiting_for_api)
    await state.update_data(mes_id=new_mes.message_id, chat_id=message.chat.id, shop_id=shop_id)

async def process_api(message: Message, state: FSMContext):
    text = message.text
    user_id = message.from_user.id

    user_data = await state.get_data()
    shop_id = user_data['shop_id']
    mes_id = user_data.get("mes_id")
    chat_id = user_data.get("chat_id")
    await message.delete()

    await add_api_to_db(text, shop_id)

    nickname = await get_nickname(user_id)
    shop_name = await get_shop_name(shop_id)

    active_requests = 0
    go_mes = await bot.edit_message_text("Ты успешно зарегистрировался!", chat_id=chat_id, message_id=mes_id)
    await asyncio.sleep(1)
    load_mes = await go_mes.edit_text("Открываю меню...")
    await asyncio.sleep(1)
    mes = (
        f"Приветствую, *{nickname}*!\n\n"
        "👤 *Личный кабинет*\n\n" 
        f"🆔 {message.from_user.id}\n"
        f"🛒 Выбранный магазин: {shop_name}\n"
        f"📋 Активные запросы: {active_requests}"
    )
    mes = await escape_markdown_v2(mes)
    await load_mes.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=main_menu_btn())
    await state.clear()

def register_commands(dp: Dispatcher):
    dp.message.register(handle_auth, RegisterStates.waiting_for_phone)
    dp.message.register(handle_auth, RegisterStates.waiting_for_sms_code)
    dp.message.register(process_name, RegisterStates.waiting_for_name)
    dp.message.register(process_shop_name, RegisterStates.waiting_for_shop_name)
    dp.message.register(process_api, RegisterStates.waiting_for_api)
    dp.message.register(handle_auth, lambda message: str(message.from_user.id) in user_sessions)
    dp.callback_query.register(process_get_shop_name, lambda c: c.data.startswith('popupshop'))
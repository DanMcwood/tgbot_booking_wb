from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram import Dispatcher

from handlers.database.connection import add_user_to_db, get_active_requests, check_user_exists, get_selected_shop, get_shop_name
from handlers.buttons import main_menu_btn
from handlers.params.fsmGroups import RegisterStates
from handlers.tasks.utils import escape_markdown_v2

async def start_command(message: Message, state: FSMContext):
    await state.clear()
    await message.delete()
    user_id = message.from_user.id
    user = await check_user_exists(user_id)

    if not user:
        await add_user_to_db(message.from_user.id, message.from_user.username)
        hello_message = await message.answer("Привет! Введите имя.")
        await state.set_state(RegisterStates.waiting_for_name)  
        await state.update_data(hello_message_id=hello_message.message_id, chat_id=message.chat.id, value = 0, user_id=user_id)
    else:
        selected_shop = await get_selected_shop(message.from_user.id)
        shop_name = await get_shop_name(selected_shop) if selected_shop else "Не выбран"

        active_requests = await get_active_requests(message.from_user.id)
        nickname = user['nickname'] if user['nickname'] else message.from_user.first_name  
        mes = (f"Приветствую, {nickname}!\n\n"
            "👤 *Личный кабинет*\n\n"
            f"🆔 {message.from_user.id}\n"
            f"🛒 Выбранный магазин: {shop_name}\n"
            f"📋 Активные запросы: {active_requests}")
        mes = await escape_markdown_v2(mes)       
        await message.answer(text=mes, parse_mode="MarkdownV2", reply_markup=main_menu_btn())

def tg_commands(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
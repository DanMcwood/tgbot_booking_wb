from aiogram import Dispatcher
from aiogram.types import CallbackQuery
from aiogram import types
from aiogram.fsm.context import FSMContext

from handlers.database.connection import set_selected_shop, get_selected_shop, get_shop_name, delete_shop, get_shop_data, add_api_to_db, set_shop_name, get_shops_with_counter, get_shop_wb
from handlers.buttons import shops_menu_btn, editing_shops, back_to_shops_menu, get_shop_wb_btn
from handlers.params.fsmGroups import Form
from handlers.tasks.utils import set_shop_list, escape_markdown_v2
from handlers.chrome_wb.shops_wb import fetch_shops, select_shop
from bot import bot, dp

#Меню магазинов
async def my_shops_callback(callback_query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    _, value, shop_index = callback_query.data.split(":")
    value, shop_index = int(value.strip()), int(shop_index.strip()) - 1
    user_id = callback_query.from_user.id    
    shops, shop_list = await set_shop_list(user_id)
    shop_id = await get_selected_shop(user_id)
    shop_name = await get_shop_name(shop_id)
    
    if value == 1:
        shop_id, _, shop_name, *other_values = shops[shop_index]
        new_shop_id, new_shop_name = shop_id, shop_name
        await set_selected_shop(new_shop_id, user_id)
        shop_wb = await get_shop_wb(shop_id)
        new_page_id = await select_shop(user_id, shop_wb)
        shops, shop_list = await set_shop_list(user_id)
        await callback_query.answer(f"Магазин '{shop_name}' успешно выбран!")
    elif value == 3:
        shop_id, _, shop_name, *other_values = shops[shop_index]
        del_shop_id, del_shop_name, new_shop_name = int(shop_id), shop_name, shop_name
        shop_id = await get_selected_shop(user_id)
        shop_id = int(shop_id)
        if shop_id == del_shop_id:
            shop_data = await get_shop_data(user_id)
            new_shop_id, new_shop_name = shop_data[0][0], shop_data[0][2]
            await set_selected_shop(new_shop_id, user_id)
        await delete_shop(del_shop_id)
        shops, shop_list = await set_shop_list(user_id)
        await callback_query.answer(f"Магазин '{del_shop_name}' успешно удален!")
    else:
        new_shop_name = shop_name
    
    if shop_name == None:
        shop_name = "Не выбран"

    mes = (
        f"👤 *{user_id}* > *{new_shop_name}*\n\n"
        f"{shop_list}\n"
        "Выберите номер магазина для действия:\n"
        "🟣 - Выбор магазина, ✏️ - Изменение, 🗑️ - Удаление"
    )
    mes = await escape_markdown_v2(mes)

    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=shops_menu_btn(shops))

# Обработчик редактирования магазина  
async def handle_edit_shop(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id   
    _, value, shop_index = callback_query.data.split(":")
    value, shop_index = int(value.strip()), int(shop_index.strip())
    
    if value == 2:
        shop_index -= 1
        shops, shop_list = await set_shop_list(user_id)
        shop_id, _, shop_name, *other_values = shops[shop_index]
    elif value == 4:
        await state.clear()
        shop_id = shop_index
        shop_name = await get_shop_name(shop_id)
    else:
        shop_id = await get_selected_shop(user_id)
        shop_name = await get_shop_name(shop_id)

    if shop_name == None:
        shop_name = "Не выбран"

    mes = (
        f"🏬 *Мои магазины*\n\n"
        f"Магазин, который Вы хотите отредактировать: *{shop_name}*\n\n"
        "Выберите действие:"
    )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=editing_shops(shop_id))

# Обработчик выбора действия редактирования магазина  
async def choose_type_edit_shop(callback_query: types.CallbackQuery, state: FSMContext):
    _, value, shop_id = callback_query.data.split(":")
    value, shop_id = int(value.strip()), int(shop_id.strip())
    user_id = callback_query.from_user.id   
    if value in (1, 3):
        new_mes = await callback_query.message.edit_text("Введите новое название:", reply_markup=back_to_shops_menu(shop_id, 1))
    elif value in (2, 6):
        new_mes = await callback_query.message.edit_text("Введите API-ключ:", reply_markup=back_to_shops_menu(shop_id, 1))
    elif value == 5:
        new_mes = await callback_query.message.edit_text("Введите название магазина:", reply_markup=back_to_shops_menu(shop_id, 1))
    
    await state.set_state(Form.waiting_for_new_name)
    await state.update_data(mes_id=new_mes.message_id, chat_id=callback_query.message.chat.id, shop_id=shop_id, value=value)

# Ожидаем ответ пользователя с новым именем
async def process_new_name(message: types.Message, state: FSMContext):
    print(1)
    new_value = message.text
    user_data = await state.get_data()
    value = user_data.get('value')
    mes_id = user_data.get("mes_id")
    chat_id = user_data.get("chat_id")
    value = int(value)
    shop_id = user_data.get('shop_id')
    shop_id = int(shop_id)
    user_id = message.from_user.id
    await message.delete()
    print(2)
    if value == 2:
        print(3)
        await add_api_to_db(new_value, shop_id)
        await bot.edit_message_text("API-ключ успешно изменен.", reply_markup=back_to_shops_menu(shop_id, 2), chat_id=chat_id, message_id=mes_id)
        await state.clear()
    elif value in (1, 3):
        print(3)
        await set_shop_name(new_value, shop_id)
        if value == 1:
            await bot.edit_message_text("Название успешно изменено", reply_markup=back_to_shops_menu(shop_id, 2), chat_id=chat_id, message_id=mes_id)
            await state.clear() 
        elif value == 3:
            new_mes = await bot.edit_message_text("Название успешно изменено.\n\nПришли новый API:", reply_markup=back_to_shops_menu(shop_id, 1), chat_id=chat_id, message_id=mes_id)
            value = 2
            await state.clear()  
            await state.set_state(Form.waiting_for_new_name)
            await state.update_data(mes_id=new_mes.message_id, chat_id=message.chat.id, shop_id=shop_id, value=value)
    elif value == 5:
        print(3)
        await set_shop_name(new_value, shop_id)
        new_mes = await bot.edit_message_text("Магазин успешно создан.\n\nПришли API-ключ:", reply_markup=back_to_shops_menu(shop_id, 2), chat_id=chat_id, message_id=mes_id)
        value = 6
        await state.clear()
        await state.set_state(Form.waiting_for_new_name)
        await state.update_data(mes_id=new_mes.message_id, chat_id=message.chat.id, shop_id=shop_id, value=value)
    elif value == 6:
        print(3)
        await add_api_to_db(new_value, shop_id)
        await bot.edit_message_text("API-ключ успешно добавлен.", reply_markup=back_to_shops_menu(shop_id, 2), chat_id=chat_id, message_id=mes_id)
        await state.clear()

async def add_new_shop(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id   
    page_id = await fetch_shops(user_id)
    shops = await get_shops_with_counter(user_id)
    mes = (
        f" 🏬 *Магазины*\n"
        "Выберите магазин для добавления api:\n"
    )
    mes = await escape_markdown_v2(mes)
    await callback_query.message.edit_text(text=mes, parse_mode="MarkdownV2", reply_markup=get_shop_wb_btn(shops))
    
# Регистрация команд
def menu_shop_commands(dp: Dispatcher):
    dp.callback_query.register(add_new_shop, lambda c: c.data.startswith('additing_shop'))
    dp.callback_query.register(my_shops_callback, lambda c: c.data.startswith('shops_menu'))
    dp.callback_query.register(handle_edit_shop, lambda c: c.data.startswith('edit_shop'))
    dp.callback_query.register(choose_type_edit_shop, lambda c: c.data.startswith('type_edit_shop'))
    dp.message.register(process_new_name, Form.waiting_for_new_name)



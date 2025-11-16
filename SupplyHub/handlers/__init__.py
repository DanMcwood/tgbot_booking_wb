from handlers.commands import tg_commands
from handlers.lists.registration import register_commands
from handlers.lists.menu_main import menu_main_commands
from handlers.lists.menu_bron import menu_bron_commands
from handlers.lists.menu_warehouses import menu_warehouses_commands
from handlers.lists.menu_coef import menu_coef_commands
from handlers.lists.menu_shop import menu_shop_commands
from handlers.lists.menu_requests import menu_requests_commands
from handlers.lists.menu_settings import menu_settings_commands

def register_all_handlers(dp):
    tg_commands(dp)
    register_commands(dp)
    menu_main_commands(dp)
    menu_bron_commands(dp)
    menu_warehouses_commands(dp)
    menu_coef_commands(dp)
    menu_shop_commands(dp)
    menu_requests_commands(dp)
    menu_settings_commands(dp)
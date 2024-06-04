from src.handlers.admin_handler.adding.add_employee import router_admin
from src.handlers.admin_handler.adding.add_admin import router_add_adm
from src.handlers.admin_handler.adding.add_place import router_add_place
from src.handlers.admin_handler.deleting.delete_employee import router_del_emp
from src.handlers.admin_handler.deleting.delete_admin import router_del_adm
from src.handlers.admin_handler.deleting.delete_place import router_del_place
from src.handlers.admin_handler.watching.employee_list import router_show_emp
from src.handlers.admin_handler.watching.admin_list import router_show_admins
from src.handlers.admin_handler.watching.place_list import router_show_places
from src.handlers.admin_handler.statistics.statistics_menu import router_adm_stats
from src.handlers.admin_handler.statistics.visitors_statistics import router_adm_visitors
from src.handlers.admin_handler.statistics.money_statistics import router_adm_money

__all__ = [
    "router_admin",
]
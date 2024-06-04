from src.config import settings
from src.db.db import DataBase

DB = DataBase(settings=settings)

cached_places: dict = {title: chat_id for title, chat_id in DB.get_places()}
cached_employees: list = DB.get_employees_user_ids()
cached_admins: list = DB.get_admins_user_ids()
cached_chat_ids: list = DB.get_chat_ids()
cached_employees_fullname_and_id: list = DB.get_employees_fullname_and_id(role="employee")
cached_admins_fullname_and_id: list = DB.get_employees_fullname_and_id(role="admin")
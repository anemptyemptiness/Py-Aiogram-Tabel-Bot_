from src.config import Settings
import psycopg2
import logging


class DataBase:
    def __init__(self, settings: Settings) -> None:
        self._user = settings.DB_USER
        self._password = settings.DB_PASS
        self._database = settings.DB_NAME
        self._host = settings.DB_HOST
        self._port = settings.DB_PORT
        self._logger = logging.getLogger(__name__)

    def _connect_to_db(self):
        connect = psycopg2.connect(
            dbname=self._database,
            user=self._user,
            password=self._password,
            host=self._host,
            port=self._port
        )

        return connect

    def get_admins_user_ids(self):
        connect = self._connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                """
                SELECT e.user_id
                FROM employees AS e
                WHERE e.role = 'admin';
                """
            )
            return [int(x[0]) for x in cursor.fetchall()]
        except Exception as e:
            self._logger.exception("Ошибка в get_admins_user_ids()")
        finally:
            cursor.close()
            connect.close()

    def get_employees_user_ids(self):
        connect = self._connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                """
                SELECT e.user_id 
                FROM employees AS e 
                WHERE e.role = 'employee';
                """
            )
            return [int(x[0]) for x in cursor.fetchall()]
        except Exception as e:
            self._logger.exception("Ошибка в get_employees_user_ids()")
        finally:
            cursor.close()
            connect.close()

    def get_places(self):
        connect = self._connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                """
                SELECT p.title, p.chat_id 
                FROM places AS p;
                """
            )
            return [(x[0], x[1]) for x in cursor.fetchall()]
        except Exception as e:
            self._logger.exception("Ошибка в get_places()")
        finally:
            cursor.close()
            connect.close()

    def get_chat_ids(self):
        connect = self._connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                """
                SELECT p.chat_id 
                FROM places AS p;
                """
            )
            return [x[0] for x in cursor.fetchall()]
        except Exception as e:
            self._logger.exception("Ошибка в get_chat_ids()")
        finally:
            cursor.close()
            connect.close()

    def get_employees_fullname_and_id(self, role: str):
        connect = self._connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(
                f"""
                SELECT e.fullname, e.user_id 
                FROM employees AS e 
                WHERE role = '{role}';
                """
            )
            return [(x[0], x[1]) for x in cursor.fetchall()]
        except Exception as e:
            self._logger.exception("Ошибка в get_employees_fullname_and_id()")
        finally:
            cursor.close()
            connect.close()

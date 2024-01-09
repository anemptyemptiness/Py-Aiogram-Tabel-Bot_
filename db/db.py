from config.config import Config
from aiogram import Bot
import psycopg2


class DataBase:
    def __init__(self, config: Config) -> None:
        self.user = config.user_db
        self.password = config.password_db
        self.database = config.database
        self.host = config.host_db

    def connect_to_db(self):
        connect = psycopg2.connect(
            dbname=self.database,
            user=self.user,
            password=self.password,
            host=self.host,
            port=5432
        )

        return connect

    def get_users(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute("SELECT user_id FROM users;")
            user_ids = cursor.fetchall()
            return user_ids
        except Exception as e:
            print("Error with SELECT:", e)
        finally:
            cursor.close()
            connect.close()

    def get_names(self):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute("SELECT fullname FROM users;")
            names = cursor.fetchall()
            return names
        except Exception as e:
            print("Error with get_names() func:", e)
        finally:
            cursor.close()
            connect.close()

    def add_users(self, user_id: int, fullname: str) -> None:
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(f"INSERT INTO users (user_id, fullname) VALUES ({user_id}, '{fullname}');")
            connect.commit()
        except Exception as e:
            print("Error with INSERT:", e)
        finally:
            cursor.close()
            connect.close()

    def user_exists(self, user_id) -> bool:
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute(f"SELECT user_id FROM users WHERE user_id = {user_id};")
            user_id = cursor.fetchone()
            return True if user_id else False
        except Exception as e:
            print("Error with CHECK EXISTS:", e)
        finally:
            cursor.close()
            connect.close()

    def set_data(self, user_id: int, date: str, place: str, count: int, cash) -> None:
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute("INSERT INTO visitors (user_id, date, place, count, cash) "
                           f"VALUES ({user_id}, '{date}', '{place}', {count}, {cash});")
            connect.commit()
        except Exception as e:
            print("Error with INSERT:", e)
        finally:
            cursor.close()
            connect.close()

    def get_statistics_visitors(self, date_from: str, date_to: str):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute("SELECT v.place, u.fullname, v.user_id, SUM(v.count) "
                           "FROM visitors AS v, users AS u "
                           f"WHERE v.date BETWEEN '{date_from}' AND '{date_to}' "
                           "AND u.user_id = v.user_id "
                           "GROUP BY v.user_id, v.place, u.fullname "
                           "ORDER BY 1;")
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print("Error with statistics:", e)
            return ["----"]
        finally:
            cursor.close()
            connect.close()

    def get_statistics_money(self, date_from: str, date_to: str):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute("SELECT v.place, u.fullname, v.user_id, concat(SUM(v.cash::numeric)) "
                           "FROM visitors AS v, users AS u "
                           f"WHERE v.date BETWEEN '{date_from}' AND '{date_to}' "
                           "AND u.user_id = v.user_id "
                           "GROUP BY v.user_id, v.place, u.fullname "
                           "ORDER BY 1;")
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            print("Error with money statistics:", e)
            return ["----"]
        finally:
            cursor.close()
            connect.close()

    def get_total_money(self, date_from: str, date_to: str):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute("SELECT concat(SUM(v.cash::numeric)) "
                           "FROM visitors AS v "
                           f"WHERE v.date BETWEEN '{date_from}' AND '{date_to}';")
            money = cursor.fetchone()
            return money[0]
        except Exception as e:
            print("Error with total money statistics:", e)
            return ["-"]
        finally:
            cursor.close()
            connect.close()

    def get_current_name(self, user_id: int):
        connect = self.connect_to_db()
        cursor = connect.cursor()

        try:
            cursor.execute("SELECT u.fullname "
                           "FROM users AS u "
                           f"WHERE u.user_id = {user_id};")
            name = cursor.fetchone()
            return name[0]
        except Exception as e:
            print("Error with get_current_name():", e)
        finally:
            cursor.close()
            connect.close()

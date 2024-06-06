from sqlalchemy import select, and_, func, delete
from sqlalchemy import Numeric
from sqlalchemy.orm import joinedload
from sqlalchemy.dialects.postgresql import insert
from src.database import async_engine, async_session, Base
from src.db.queries.models.models import Employees, Places, Reports, Finances

from datetime import datetime, timedelta, timezone, date


class AsyncOrm:
    @staticmethod
    async def create_tables():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    @staticmethod
    async def get_current_name(user_id: int):
        async with async_session() as session:
            query = (
                select(
                    Employees.fullname
                )
                .select_from(Employees)
                .filter_by(user_id=user_id)
            )

            res = await session.execute(query)
            result = res.scalars().one()  # тут будет записано имя

            await session.commit()
            return result

    @staticmethod
    async def add_employee(fullname: str, user_id: int, username: str):
        async with async_session() as session:
            stmt = (
                insert(Employees)
                .values(fullname=fullname, user_id=user_id, username=username, role="employee")
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[Employees.user_id],
                set_=dict(fullname=fullname, username=username, role="employee")
            )
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def add_admin(fullname: str, user_id: int, username: str):
        async with async_session() as session:
            stmt = (
                insert(Employees)
                .values(fullname=fullname, user_id=user_id, username=username, role="admin")
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[Employees.user_id],
                set_=dict(fullname=fullname, username=username, role="admin")
            )
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def add_place(title: str, chat_id: int):
        async with async_session() as session:
            stmt = (
                insert(Places)
                .values(title=title, chat_id=chat_id)
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[Places.chat_id],
                set_=dict(title=title)
            )
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def get_employees():
        async with async_session() as session:
            query = (
                select(
                    Employees.fullname,
                    Employees.username
                )
                .select_from(Employees)
                .filter_by(role="employee")
            )
            res = await session.execute(query)
            result = [(data[0], data[1]) for data in res.all()]

            await session.commit()
            return result

    @staticmethod
    async def get_employee_by_id(user_id: int):
        async with async_session() as session:
            query = (
                select(
                    Employees.fullname,
                    Employees.username
                )
                .select_from(Employees)
                .filter(and_(
                    Employees.user_id == user_id,
                    Employees.role == "employee"
                ))
            )
            res = await session.execute(query)
            result = [data for data in res.one()]

            await session.commit()
            return result

    @staticmethod
    async def get_admins():
        async with async_session() as session:
            query = (
                select(
                    Employees.fullname,
                    Employees.username
                )
                .select_from(Employees)
                .filter_by(role="admin")
            )
            res = await session.execute(query)
            result = [(data[0], data[1]) for data in res.all()]

            await session.commit()
            return result

    @staticmethod
    async def get_admin_by_id(user_id: int):
        async with async_session() as session:
            query = (
                select(
                    Employees.fullname,
                    Employees.username
                )
                .select_from(Employees)
                .filter(and_(
                    Employees.user_id == user_id,
                    Employees.role == "admin"
                ))
            )
            res = await session.execute(query)
            result = [data for data in res.one()]

            await session.commit()
            return result

    @staticmethod
    async def delete_employee(fullname: str, username: str):
        async with async_session() as session:
            employee_query = (
                delete(Employees)
                .filter_by(
                    fullname=fullname,
                    username=username,
                    role="employee",
                )
            )
            await session.execute(employee_query)
            await session.commit()

    @staticmethod
    async def delete_admin(fullname: str, username: str):
        async with async_session() as session:
            admin_query = (
                delete(Employees)
                .filter_by(
                    fullname=fullname,
                    username=username,
                    role="admin",
                )
            )
            await session.execute(admin_query)
            await session.commit()

    @staticmethod
    async def delete_place(title: str):
        async with async_session() as session:
            place_query = (
                delete(Places)
                .filter_by(title=title)
            )
            await session.execute(place_query)
            await session.commit()

    @staticmethod
    async def set_data_to_reports(user_id: int, place: str, visitors: int, revenue: float):
        async with async_session() as session:
            employee_query = (
                select(Employees.id).
                filter_by(user_id=user_id)
            )

            place_query = (
                select(Places.id).
                filter_by(title=place.strip())
            )

            stmt = (
                insert(Reports).
                values(
                    {
                        "revenue": revenue,
                        "place_id": place_query,
                        "user_id": employee_query,
                        "visitors": visitors,
                    }
                )
            )

            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def get_visitors_data_from_reports_by_date(date_from: date, date_to: date):
        async with async_session() as session:
            query = (
                select(
                    Places.title,
                    Employees.fullname,
                    Reports.user_id,
                    func.sum(Reports.visitors),
                )
                .select_from(Reports)
                .join(Reports.place)
                .join(Reports.employee)
                .filter(
                    Reports.report_date.between(date_from, date_to)
                )
                .group_by(
                    Places.title,
                    Employees.fullname,
                    Reports.user_id,
                )
                .order_by(Places.title)
            )
            res = await session.execute(query)
            await session.commit()

            # returns List[places.title, employees.fullname, reports.user_id, sum of visitors]
            return res.all()

    @staticmethod
    async def get_revenue_data_from_reports_by_date(date_from: date, date_to: date):
        async with async_session() as session:
            query = (
                select(
                    func.coalesce(Places.title, 'удаленная точка'),
                    func.coalesce(Employees.fullname, 'удаленный сотр.'),
                    Reports.user_id,
                    func.concat(func.sum(func.cast(Reports.revenue, Numeric))),
                )
                .select_from(Reports)
                .join(Reports.place, isouter=True)
                .join(Reports.employee, isouter=True)
                .filter(
                    Reports.report_date.between(date_from, date_to),
                )
                .group_by(
                    Places.title,
                    Employees.fullname,
                    Reports.user_id,
                )
                .order_by(Reports.user_id)
            )
            res = await session.execute(query)
            await session.commit()

            # returns List[places.title, employees.fullname, reports.user_id, sum of revenue]
            return res.all()

    @staticmethod
    async def set_data_to_finances():
        async with async_session() as session:
            time_now = datetime.now(tz=timezone(timedelta(hours=3.0))).date()
            time_14_days_ago = time_now - timedelta(days=14) + timedelta(days=1)

            sum_of_revenue_query = (
                select(
                    Reports.place_id,
                    func.sum(Reports.revenue)
                )
                .select_from(Reports)
                .filter(
                    Reports.report_date.between(time_14_days_ago, time_now)
                )
                .group_by(Reports.place_id)
            )

            res = await session.execute(sum_of_revenue_query)
            data_from_reports = {int(place_id): float(summary) for place_id, summary in res.all()}

            # На этом этапе я получил новые выручки
            # за прошлые 2 недели
            await session.flush()

            # Если не пришло никакого результата из Reports,
            # то просто заполняю Finances дефолтными значениями
            if not data_from_reports:
                # Если Reports еще пустая, то ничего не делаем
                if not await AsyncOrm._check_reports_for_null():
                    await session.commit()
                    return

                place_ids_query = (
                    select(Reports.place_id)
                )
                res = await session.execute(place_ids_query)
                place_ids_dict = {"place_id": int(place_id) for place_id in res.scalars().all()}

                await session.flush()

                stmt = (
                    insert(Finances)
                    .values(place_ids_dict)
                )
                await session.execute(stmt)
                await session.commit()
                return

            # Если таблица Finances была пустая, то я вставлю в
            # last_money и updated_money одинаковые значения,
            # так как еще не было суммы новее, поэтому они должны быть равны
            if not await AsyncOrm._check_finances_for_null():
                stmt = (
                    insert(Finances)
                    .values(
                        [
                            {"place_id": place_id, "last_money": updated_money, "updated_money": updated_money}
                            for place_id, updated_money in data_from_reports.items()
                        ]
                    )
                )

                await session.execute(stmt)
                await session.commit()

                # Выхожу из метода, так как нет смысла делать что-либо дальше
                # Я обновил всё, что можно на данный момент
                return

            # Если таблица Finances не пустая, то нужно в
            # старое значение last_money поставить
            # старое значение updated_money
            else:
                last_updated_money_query = (
                    select(
                        Finances.place_id,
                        Finances.updated_money
                    )
                    .select_from(Finances)
                )
                res = await session.execute(last_updated_money_query)
                data_from_finances = {int(place_id): float(last_updated_money) for place_id, last_updated_money in res.all()}

                # На данном этапе я получил старые
                # значения updated_money, чтобы
                # вставить их в last_money
                await session.flush()

                stmt = (
                    insert(Finances)
                    .values(
                        [
                            {"place_id": place_id, "last_money": last_updated_money}
                            for place_id, last_updated_money in data_from_finances.items()
                        ]
                    )
                    .on_conflict_do_update(
                        index_elements=[Finances.place_id],
                        set_={
                            "last_money": insert(Finances).excluded.last_money,
                        }
                    )
                )
                await session.execute(stmt)

            # На этом этапе last_money содержат
            # старые значения updated_money
            #
            # Теперь мне нужно в updated_money
            # вставить новые значения, которые пришли
            # из таблицы Reports (новые выручки точек за 2 прошлые недели)
            await session.flush()

            stmt = (
                insert(Finances)
                .values(
                    [
                        {"place_id": place_id, "updated_money": updated_money}
                        for place_id, updated_money in data_from_reports.items()
                    ]
                )
                .on_conflict_do_update(
                    index_elements=[Finances.place_id],
                    set_={
                        "updated_money": insert(Finances).excluded.updated_money,
                    },
                )
            )

            # Я обновил updated_money новыми значениями,
            # и теперь можно спокойно выходить из функции
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def get_data_from_finances():
        async with async_session() as session:
            query = (
                select(
                    Finances,
                )
                .select_from(Finances)
                .options(joinedload(Finances.place))
            )

            res = await session.execute(query)
            result = [
                (
                    data.place.title,
                    data.place.chat_id,
                    data.last_money,
                    data.updated_money,
                    data.updated_at,
                ) for data in res.scalars().all()
            ]

            return result

    @staticmethod
    async def _check_data_from_finances():
        async with async_session() as session:
            if not await AsyncOrm._check_finances_for_null():
                await AsyncOrm.set_data_to_finances()

            query = (
                select(
                    Finances.updated_at
                )
                .select_from(Finances)
                .limit(1)
            )
            res = await session.execute(query)
            result = res.scalars().one()

            await session.commit()
            return result

    @staticmethod
    async def _check_finances_for_null():
        async with async_session() as session:
            query = (
                select(Finances)
            )
            res = await session.execute(query)
            await session.commit()

            return res.scalars().all()

    @staticmethod
    async def _check_reports_for_null():
        async with async_session() as session:
            query = (
                select(Reports)
            )
            res = await session.execute(query)
            await session.commit()

            return res.scalars().all()
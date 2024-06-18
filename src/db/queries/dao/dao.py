from sqlalchemy import select, update, and_, func, delete
from sqlalchemy import Numeric
from sqlalchemy.orm import joinedload
from sqlalchemy.dialects.postgresql import insert

from src.config import settings
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
    async def set_data_to_finances_default():
        async with async_session() as session:
            time_now = datetime.now(tz=timezone(timedelta(hours=3.0))).date()
            time_N_days_ago = time_now - timedelta(days=settings.DAYS_FOR_FINANCES_CHECK) + timedelta(days=1)

            sum_of_revenue_query = (
                select(
                    Reports.place_id,
                    func.sum(Reports.revenue)
                )
                .select_from(Reports)
                .filter(
                    Reports.report_date.between(time_N_days_ago, time_now)
                )
                .group_by(Reports.place_id)
            )

            res = await session.execute(sum_of_revenue_query)
            data_from_reports = {int(place_id): float(summary) for place_id, summary in res.all()}

            # На этом этапе я получил новые выручки
            # за прошлые N дней
            await session.flush()

            # Если не пришло никакого результата из Reports,
            # то Reports пустая, а это значит, что ничего делать не будем
            # и выйдем из функции
            if not data_from_reports:
                return

            # Если таблица Finances была пустая, то я вставлю в
            # last_money и updated_money одинаковые значения,
            # так как еще не было суммы новее, поэтому они должны быть равны
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
            await session.commit()
            return

    @staticmethod
    async def set_data_to_finances_by_place(place_id: int):
        async with async_session() as session:
            time_now = datetime.now(tz=timezone(timedelta(hours=3.0))).date()
            time_N_days_ago = time_now - timedelta(days=settings.DAYS_FOR_FINANCES_CHECK) + timedelta(days=1)

            sum_of_revenue_query = (
                select(
                    Reports.place_id,
                    func.sum(Reports.revenue)
                )
                .select_from(Reports)
                .filter(
                    and_(Reports.report_date.between(time_N_days_ago, time_now), Reports.place_id == place_id)
                )
                .group_by(Reports.place_id)
            )

            res = await session.execute(sum_of_revenue_query)
            data_from_reports = {int(place_id): float(summary) for place_id, summary in res.all()}

            # если такой точки еще не было в Finances,
            # то ее нужно там создать, а далее выйти из функции
            if not await AsyncOrm._check_finances_for_null_by_place(place_id=place_id):
                stmt = (
                    insert(Finances)
                    .values(
                        [
                            {"place_id": place_id, "updated_money": updated_money, "last_money": 0}
                            for place_id, updated_money in data_from_reports.items()
                        ]
                    )
                )
                await session.execute(stmt)
                await session.commit()
                return

            last_updated_money_query = (
                select(
                    Finances.updated_money
                )
                .select_from(Finances)
                .filter_by(place_id=place_id)
            )
            res = await session.execute(last_updated_money_query)
            data_from_finances_for_place = {
                "place_id": place_id, "last_money": float(res.scalar()),
            }

            # На данном этапе я получил старое
            # значение updated_money для конкретной точки, чтобы
            # вставить их в last_money для этой же точки
            await session.flush()

            stmt = (
                insert(Finances)
                .values(data_from_finances_for_place)
                .on_conflict_do_update(
                    index_elements=[Finances.place_id],
                    set_={
                        "last_money": insert(Finances).excluded.last_money,
                    }
                )
            )
            await session.execute(stmt)

            # На этом этапе last_money содержит
            # старое значение updated_money
            #
            # Теперь мне нужно в updated_money
            # вставить новое значение, которые пришло
            # из таблицы Reports (новые выручки точки за прошлые N дней)
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

            # Я обновил updated_money новым значением,
            # и теперь можно спокойно выходить из функции
            await session.execute(stmt)
            await session.commit()

    @staticmethod
    async def get_data_from_finances_by_place(place_id: int):
        async with async_session() as session:
            time_now = datetime.now(tz=timezone(timedelta(hours=3.0))).date()

            query = (
                select(
                    Finances,
                )
                .select_from(Finances)
                .filter_by(place_id=place_id)
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

            # обновлю дату updated_at в Finances, так как я получил
            # и вывел всю старую нужную информацию в этой функции

            stmt = (
                update(Finances).values(updated_at=time_now).filter_by(place_id=place_id)
            )
            await session.execute(stmt)
            await session.commit()

            return result

    @staticmethod
    async def _check_data_from_finances():
        async with async_session() as session:
            # если таблица Finances пустая, то заполняю ее дефолтными значениями
            if not await AsyncOrm._check_finances_for_null():
                await AsyncOrm.set_data_to_finances_default()

            query = (
                select(
                    Places.id,
                    Finances.updated_at,
                )
                .select_from(Finances)
                .join(Places, Finances.place_id == Places.id)
            )
            res = await session.execute(query)
            result = res.all()

            await session.commit()
            return result

    @staticmethod
    async def _check_finances_for_null_by_place(place_id: int):
        async with async_session() as session:
            query = (
                select(Finances)
                .select_from(Finances)
                .filter_by(place_id=place_id)
            )
            res = await session.execute(query)
            await session.commit()

            return res.scalars().all()

    @staticmethod
    async def _check_finances_for_null():
        async with async_session() as session:
            query = (
                select("*")
                .select_from(Finances)
            )
            res = await session.execute(query)

            return res.all()

    @staticmethod
    async def _check_reports_for_null():
        async with async_session() as session:
            query = (
                select(Reports)
            )
            res = await session.execute(query)
            await session.commit()

            return res.scalars().all()
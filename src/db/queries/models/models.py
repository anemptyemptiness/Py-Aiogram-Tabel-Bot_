from sqlalchemy.dialects.postgresql import BIGINT, INTEGER, DATE
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import text, ForeignKey

from src.database import Base

from typing import Annotated
from datetime import datetime, timezone, timedelta

created_at = Annotated[datetime, mapped_column(
    DATE,
    server_default=text("CAST(DATE_TRUNC('day', TIMEZONE('utc-3', now())) AS DATE)")
)]
updated_at = Annotated[datetime, mapped_column(
        DATE,
        server_default=text("CAST(DATE_TRUNC('day', TIMEZONE('utc-3', now())) AS DATE)"),
        onupdate=datetime.now(tz=timezone(timedelta(hours=3.0))).date(),
)]


class Employees(Base):
    __tablename__ = "employees"

    id = mapped_column(INTEGER, primary_key=True)
    fullname: Mapped[str]
    username: Mapped[str]
    role: Mapped[str]
    user_id = mapped_column(BIGINT, unique=True)
    created_at: Mapped[created_at]

    # one-2-many bound (one employee -> many reports)
    reports: Mapped["Reports"] = relationship(back_populates="employee", uselist=False)


class Finances(Base):
    __tablename__ = "finances"

    id = mapped_column(INTEGER, primary_key=True)
    place_id: Mapped[int] = mapped_column(ForeignKey("places.id"), unique=True)
    updated_at: Mapped[updated_at]
    last_money: Mapped[float] = mapped_column(default=0.0)
    updated_money: Mapped[float] = mapped_column(default=0.0)

    # one-2-one bound with Places-table
    place: Mapped["Places"] = relationship(back_populates="finance", uselist=False)


class Places(Base):
    __tablename__ = "places"

    id = mapped_column(INTEGER, primary_key=True)
    title: Mapped[str]
    chat_id = mapped_column(BIGINT, unique=True)

    # one-2-one bound with Finances-table (one place -> one finance-report)
    finance: Mapped["Finances"] = relationship(back_populates="place", uselist=False)

    # one-2-many bound (one place -> many reports)
    reports: Mapped["Reports"] = relationship(back_populates="place", uselist=False)


class Reports(Base):
    __tablename__ = "reports"

    id = mapped_column(INTEGER, primary_key=True)
    report_date: Mapped[created_at]
    visitors: Mapped[int]
    revenue: Mapped[float]

    # one-2-many bound (one place -> many reports)
    place_id: Mapped[int] = mapped_column(ForeignKey("places.id"))  # Настроить ON DELETE
    place: Mapped["Places"] = relationship(back_populates="reports", uselist=False)

    # one-2-many bound (one employee -> many reports)
    user_id: Mapped[int] = mapped_column(ForeignKey("employees.id"))  # что делать на ON DELETE?
    employee: Mapped["Employees"] = relationship(back_populates="reports", uselist=False)
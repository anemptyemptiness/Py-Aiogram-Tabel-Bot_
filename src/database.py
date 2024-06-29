from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

async_engine = create_async_engine(
    settings.get_url_asyncpg,
    # echo=True,
)

async_session = async_sessionmaker(bind=async_engine)


class Base(DeclarativeBase):

    def __repr__(self):
        cols = []

        for col in self.__table__.columns.keys():
            cols.append(f"{col}={repr(getattr(self, col))}")

        return f"class={self.__class__.__name__}, {', '.join(cols)}"
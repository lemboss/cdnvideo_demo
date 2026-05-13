from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self) -> None:
        self.engine = create_async_engine(self.database_url, pool_pre_ping=True)
        if self.database_url.startswith("sqlite"):
            event.listen(self.engine.sync_engine, "connect", _configure_sqlite)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_schema(self) -> None:
        from app.repositories.models import CityORM  # noqa: F401

        if self.engine is None:
            raise RuntimeError("Database is not connected.")
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def healthcheck(self) -> None:
        if self.engine is None:
            raise RuntimeError("Database is not connected.")
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self.session_factory is None:
            raise RuntimeError("Database is not connected.")
        async with self.session_factory() as session:
            yield session

    async def close(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()


def _configure_sqlite(dbapi_connection: object, _connection_record: object) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()

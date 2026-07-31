from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class DatabaseManager:
    """Owns SQLAlchemy engine lifecycle and low-cost readiness checks."""

    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=1_800,
        )
        self._sessions = async_sessionmaker(self._engine, expire_on_commit=False)

    async def ping(self) -> None:
        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def close(self) -> None:
        await self._engine.dispose()

    async def create_schema(self, base: type[DeclarativeBase]) -> None:
        async with self._engine.begin() as connection:
            await connection.run_sync(base.metadata.create_all)

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._sessions() as session:
            yield session

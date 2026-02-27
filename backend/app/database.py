from collections.abc import AsyncGenerator

from sqlalchemy import pool as sa_pool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

_db_url = settings.active_database_url or "sqlite+aiosqlite:///:memory:"

# NullPool for PostgreSQL/asyncpg: each serverless invocation opens its own
# connection and closes it immediately.  No connection leaks on Vercel.
# StaticPool for SQLite in-memory (local dev without a DB configured).
if _db_url.startswith("sqlite"):
    _pool_kwargs: dict = {
        "poolclass": sa_pool.StaticPool,
        "connect_args": {"check_same_thread": False},
    }
else:
    _pool_kwargs = {"poolclass": sa_pool.NullPool}

engine = create_async_engine(
    _db_url,
    echo=settings.debug,
    **_pool_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

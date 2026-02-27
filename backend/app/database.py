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

# In production (Vercel serverless) use NullPool – each request opens and
# closes its own connection. nhost does not provide a built-in PgBouncer
# pooler, so NullPool prevents connection exhaustion on serverless.
# In local development a regular pool is used for better performance.
_pool_kwargs: dict = (
    {"poolclass": sa_pool.NullPool}
    if settings.is_production
    else {"pool_size": 5, "max_overflow": 10, "pool_pre_ping": True}
)

engine = create_async_engine(
    settings.active_database_url or "sqlite+aiosqlite:///:memory:",
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

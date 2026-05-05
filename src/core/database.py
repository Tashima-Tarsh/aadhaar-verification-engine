from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.config.settings import settings

# SQLite (used in tests) does not support pool_size/max_overflow
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")
_pool_kwargs = {} if _is_sqlite else {"pool_size": 20, "max_overflow": 10}

engine = create_async_engine(settings.DATABASE_URL, echo=False, **_pool_kwargs)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Alias used by health endpoint and workers
async_session_factory = AsyncSessionLocal


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

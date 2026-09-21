from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from bot.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Create all tables (use alembic in production)."""
    from bot.models import participant, volunteer, region  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

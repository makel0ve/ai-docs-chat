from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()
engine = create_async_engine(url=settings.database_url, echo=False)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
redis_client = Redis.from_url(url=settings.redis_url)


class Base(DeclarativeBase):
    pass


async def get_session():
    async with async_session() as session:
        yield session

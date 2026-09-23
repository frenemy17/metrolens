from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
import os

raw_url = os.environ.get("DATABASE_URL")
if raw_url:
    if raw_url.startswith("postgres://"):
        DATABASE_URL = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw_url.startswith("postgresql://") and not raw_url.startswith("postgresql+asyncpg://"):
        DATABASE_URL = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        DATABASE_URL = raw_url
    engine = create_async_engine(DATABASE_URL, echo=False)
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "metrolens.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
    engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with async_session_maker() as session:
        yield session

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from src.models import Base
from src.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME
import logging

logger = logging.getLogger(__name__)

# Формируем URL подключения для asyncpg
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Создаем асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Установите True для отладки SQL-запросов
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=10,
    max_overflow=20
)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Создает все таблицы в базе данных"""
    logger.info("Инициализация базы данных...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных инициализирована успешно")


async def drop_db():
    """Удаляет все таблицы (для тестирования)"""
    logger.warning("Удаление всех таблиц из базы данных...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.info("Все таблицы удалены")


async def get_session() -> AsyncSession:
    """Возвращает новую асинхронную сессию"""
    async with AsyncSessionLocal() as session:
        yield session

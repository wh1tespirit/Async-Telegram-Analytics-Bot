"""
Тестовый скрипт для проверки подключения к БД и моделей
"""
import asyncio
import logging
from sqlalchemy import select, func
from src.db import init_db, AsyncSessionLocal
from src.models import Video, VideoSnapshot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_db():
    """Тестирует подключение к БД и выполняет простые запросы"""
    
    # Инициализируем БД
    await init_db()
    logger.info("✓ База данных инициализирована")
    
    # Создаем сессию
    async with AsyncSessionLocal() as session:
        # Проверяем количество видео
        result = await session.execute(select(func.count(Video.id)))
        video_count = result.scalar()
        logger.info(f"✓ Количество видео в БД: {video_count}")
        
        # Проверяем количество снапшотов
        result = await session.execute(select(func.count(VideoSnapshot.id)))
        snapshot_count = result.scalar()
        logger.info(f"✓ Количество снапшотов в БД: {snapshot_count}")
        
        # Получаем одно видео для примера
        if video_count > 0:
            result = await session.execute(select(Video).limit(1))
            video = result.scalar_one_or_none()
            if video:
                logger.info(f"✓ Пример видео: {video}")
        
        logger.info("✅ Все тесты пройдены!")


if __name__ == '__main__':
    asyncio.run(test_db())

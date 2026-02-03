import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from sqlalchemy import insert
from src.db import engine, init_db
from src.models import Video, VideoSnapshot

logger = logging.getLogger(__name__)


def parse_datetime(dt_str: str) -> datetime:
    """Парсит строку даты в datetime объект"""
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))


async def load_data(json_path: str = "data/videos.json"):
    """
    Загружает данные из JSON файла в базу данных.
    Использует bulk insert для максимальной производительности.
    """
    logger.info(f"Начинаем загрузку данных из {json_path}")
    
    # Проверяем существование файла
    file_path = Path(json_path)
    if not file_path.exists():
        logger.error(f"Файл {json_path} не найден!")
        return
    
    # Читаем JSON файл
    logger.info("Чтение JSON файла...")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    videos_data = data.get('videos', [])
    logger.info(f"Найдено {len(videos_data)} видео")
    
    # Подготавливаем данные для bulk insert
    videos_to_insert: List[Dict[str, Any]] = []
    snapshots_to_insert: List[Dict[str, Any]] = []
    
    logger.info("Подготовка данных для вставки...")
    for video_raw in videos_data:
        # Подготавливаем данные видео
        video_dict = {
            'id': video_raw['id'],
            'creator_id': video_raw['creator_id'],
            'video_created_at': parse_datetime(video_raw['video_created_at']),
            'views_count': video_raw['views_count'],
            'likes_count': video_raw['likes_count'],
            'comments_count': video_raw['comments_count'],
            'reports_count': video_raw['reports_count'],
            'created_at': parse_datetime(video_raw['created_at']),
            'updated_at': parse_datetime(video_raw['updated_at']),
        }
        videos_to_insert.append(video_dict)
        
        # Подготавливаем данные снапшотов
        for snapshot_raw in video_raw.get('snapshots', []):
            snapshot_dict = {
                'id': snapshot_raw['id'],
                'video_id': snapshot_raw['video_id'],
                'views_count': snapshot_raw['views_count'],
                'likes_count': snapshot_raw['likes_count'],
                'comments_count': snapshot_raw['comments_count'],
                'reports_count': snapshot_raw['reports_count'],
                'delta_views_count': snapshot_raw['delta_views_count'],
                'delta_likes_count': snapshot_raw['delta_likes_count'],
                'delta_comments_count': snapshot_raw['delta_comments_count'],
                'delta_reports_count': snapshot_raw['delta_reports_count'],
                'created_at': parse_datetime(snapshot_raw['created_at']),
                'updated_at': parse_datetime(snapshot_raw['updated_at']),
            }
            snapshots_to_insert.append(snapshot_dict)
    
    logger.info(f"Подготовлено {len(videos_to_insert)} видео и {len(snapshots_to_insert)} снапшотов")
    
    # Вставляем данные в БД
    logger.info("Вставка данных в базу данных...")
    async with engine.begin() as conn:
        # Сначала вставляем видео
        logger.info("Вставка видео...")
        await conn.execute(insert(Video), videos_to_insert)
        logger.info(f"✓ Вставлено {len(videos_to_insert)} видео")
        
        # Затем вставляем снапшоты (батчами для больших объемов)
        logger.info("Вставка снапшотов...")
        batch_size = 5000
        for i in range(0, len(snapshots_to_insert), batch_size):
            batch = snapshots_to_insert[i:i + batch_size]
            await conn.execute(insert(VideoSnapshot), batch)
            logger.info(f"  Вставлено {min(i + batch_size, len(snapshots_to_insert))}/{len(snapshots_to_insert)} снапшотов")
        
        logger.info(f"✓ Вставлено {len(snapshots_to_insert)} снапшотов")
    
    logger.info("✅ Загрузка данных завершена успешно!")


async def main():
    """Основная функция для запуска загрузки данных"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Инициализируем БД (создаем таблицы)
    await init_db()
    
    # Загружаем данные
    await load_data()


if __name__ == '__main__':
    asyncio.run(main())

"""
SQL Executor - выполняет SQL-запросы и возвращает результаты
"""
import logging
from sqlalchemy import text
from app.database.db import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def execute_sql_query(sql_query: str) -> int:
    """
    Выполняет SQL-запрос и возвращает числовой результат.
    
    Args:
        sql_query: SQL-запрос, который должен вернуть одно число
        
    Returns:
        Числовой результат запроса
        
    Raises:
        Exception: Если запрос невалидный или вернул не число
    """
    try:
        logger.info(f"Выполняем SQL: {sql_query}")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(sql_query))
            value = result.scalar()
            
            # Преобразуем в int (на случай если вернулся float, Decimal или None)
            if value is None:
                return 0
            
            # PostgreSQL может вернуть Decimal, int, float
            try:
                return int(value)
            except (ValueError, TypeError):
                logger.warning(f"Не удалось преобразовать значение {value} (тип: {type(value)}) в int, возвращаем 0")
                return 0
            
    except Exception as e:
        logger.error(f"Ошибка при выполнении SQL: {e}")
        raise Exception(f"Не удалось выполнить запрос: {e}")

"""
Query Service - главный сервис для обработки запросов пользователя
"""
import logging
from app.services.llm_service import ask_llm
from app.services.sql_executor import execute_sql_query

logger = logging.getLogger(__name__)


async def process_user_query(user_query: str) -> int:
    """
    Обрабатывает запрос пользователя на естественном языке.
    
    Workflow:
    1. Отправляет запрос в LLM для генерации SQL
    2. Выполняет полученный SQL в базе данных
    3. Возвращает числовой результат
    
    Args:
        user_query: Вопрос пользователя на русском языке
        
    Returns:
        Числовой ответ на вопрос
        
    Raises:
        Exception: Если не удалось обработать запрос
    """
    try:
        logger.info(f"Обработка запроса: {user_query}")
        
        # Шаг 1: Генерируем SQL через LLM
        sql_query = await ask_llm(user_query)
        
        # Шаг 2: Выполняем SQL
        result = await execute_sql_query(sql_query)
        
        logger.info(f"Результат: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        raise

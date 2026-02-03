"""
Тестовый скрипт для проверки LLM-сервиса и генерации SQL
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from app.services.query_service import process_user_query

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_queries():
    """Тестирует различные типы запросов"""
    
    # Проверяем наличие API ключа
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY не установлен в .env файле!")
        return
    
    test_cases = [
        "Сколько всего видео есть в системе?",
        "Сколько видео набрало больше 100000 просмотров за всё время?",
        "На сколько просмотров в сумме выросли все видео 28 ноября 2025?",
        "Сколько разных видео получали новые просмотры 27 ноября 2025?",
        "Сколько видео было опубликовано с 1 по 5 ноября 2025?",
    ]
    
    logger.info("=" * 80)
    logger.info("Начинаем тестирование LLM-сервиса")
    logger.info("=" * 80)
    
    for i, query in enumerate(test_cases, 1):
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Тест {i}/{len(test_cases)}")
        logger.info(f"Вопрос: {query}")
        logger.info("-" * 80)
        
        try:
            result = await process_user_query(query)
            logger.info(f"Ответ: {result}")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        
        # Небольшая пауза между запросами
        await asyncio.sleep(1)
    
    logger.info(f"\n{'=' * 80}")
    logger.info("Тестирование завершено!")
    logger.info("=" * 80)


async def interactive_mode():
    """Интерактивный режим для тестирования запросов"""
    
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY не установлен в .env файле!")
        return
    
    logger.info("=" * 80)
    logger.info("Интерактивный режим тестирования")
    logger.info("Введите 'exit' для выхода")
    logger.info("=" * 80)
    
    while True:
        try:
            query = input("\nВаш вопрос: ").strip()
            
            if query.lower() in ['exit', 'quit', 'выход']:
                logger.info("До свидания!")
                break
            
            if not query:
                continue
            
            result = await process_user_query(query)
            print(f"Ответ: {result}")
            
        except KeyboardInterrupt:
            logger.info("\nДо свидания!")
            break
        except Exception as e:
            logger.error(f"Ошибка: {e}")


async def main():
    """Главная функция"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        await interactive_mode()
    else:
        await test_queries()


if __name__ == '__main__':
    asyncio.run(main())

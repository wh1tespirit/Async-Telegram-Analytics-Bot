"""
LLM Service для преобразования естественного языка в SQL-запросы
"""
import os
import logging
from datetime import datetime
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Инициализация клиента OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Системный промпт для Text-to-SQL
SYSTEM_PROMPT = """Ты эксперт по PostgreSQL. Твоя задача — генерировать ТОЛЬКО SQL-код на основе вопроса пользователя.

## Схема базы данных

### Таблица `videos` (итоговая статистика по видео)
- id (String) - идентификатор видео
- creator_id (String) - идентификатор креатора
- video_created_at (TIMESTAMP WITH TIME ZONE) - дата и время публикации видео
- views_count (BIGINT) - финальное количество просмотров
- likes_count (INTEGER) - финальное количество лайков
- comments_count (INTEGER) - финальное количество комментариев
- reports_count (INTEGER) - финальное количество жалоб
- created_at (TIMESTAMP WITH TIME ZONE) - дата создания записи
- updated_at (TIMESTAMP WITH TIME ZONE) - дата обновления записи

### Таблица `video_snapshots` (почасовые замеры статистики)
- id (String) - идентификатор снапшота
- video_id (String) - ссылка на видео (FK -> videos.id)
- views_count (BIGINT) - просмотры на момент замера
- likes_count (INTEGER) - лайки на момент замера
- comments_count (INTEGER) - комментарии на момент замера
- reports_count (INTEGER) - жалобы на момент замера
- delta_views_count (BIGINT) - прирост просмотров с прошлого замера
- delta_likes_count (INTEGER) - прирост лайков с прошлого замера
- delta_comments_count (INTEGER) - прирост комментариев с прошлого замера
- delta_reports_count (INTEGER) - прирост жалоб с прошлого замера
- created_at (TIMESTAMP WITH TIME ZONE) - время замера (раз в час)
- updated_at (TIMESTAMP WITH TIME ZONE) - дата обновления записи

## КРИТИЧЕСКИЕ ПРАВИЛА

1. **Ответ должен содержать ТОЛЬКО SQL-запрос** - без markdown, без кавычек, без объяснений
2. **Запрос ОБЯЗАН возвращать РОВНО ОДНО ЧИСЛО** - используй COUNT, SUM, AVG и т.д.
3. **Для подсчета количества видео** → используй таблицу `videos`
4. **Для подсчета динамики/прироста за конкретную дату** → используй таблицу `video_snapshots` и суммируй `delta_*`
5. **Для фильтрации по датам**:
   - Используй `::date` для приведения timestamp к дате
   - Формат дат: 'YYYY-MM-DD'
   - Для диапазона используй `BETWEEN` или `>=` и `<=`
6. **Если год не указан** - используй 2025 год (данные из ноября-декабря 2025)
7. **Текущая дата**: {current_date}

## Примеры запросов

Вопрос: "Сколько всего видео есть в системе?"
SQL: SELECT COUNT(id) FROM videos

Вопрос: "Сколько видео у креатора с id abc123 вышло с 1 ноября 2025 по 5 ноября 2025 включительно?"
SQL: SELECT COUNT(id) FROM videos WHERE creator_id = 'abc123' AND video_created_at::date BETWEEN '2025-11-01' AND '2025-11-05'

Вопрос: "Сколько видео набрало больше 100000 просмотров за всё время?"
SQL: SELECT COUNT(id) FROM videos WHERE views_count > 100000

Вопрос: "На сколько просмотров в сумме выросли все видео 28 ноября 2025?"
SQL: SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE created_at::date = '2025-11-28'

Вопрос: "Сколько разных видео получали новые просмотры 27 ноября 2025?"
SQL: SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE created_at::date = '2025-11-27' AND delta_views_count > 0

Вопрос: "Сколько лайков набрали все видео за период с 26 по 28 ноября?"
SQL: SELECT COALESCE(SUM(delta_likes_count), 0) FROM video_snapshots WHERE created_at::date BETWEEN '2025-11-26' AND '2025-11-28'

## ВАЖНО
- Всегда используй COALESCE для SUM, чтобы вернуть 0 вместо NULL
- Для подсчета уникальных видео используй COUNT(DISTINCT video_id)
- Для фильтрации "больше N" используй оператор >
- Для фильтрации "меньше N" используй оператор <
"""


async def ask_llm(query: str) -> str:
    """
    Преобразует естественный запрос в SQL.
    
    Args:
        query: Вопрос пользователя на русском языке
        
    Returns:
        SQL-запрос в виде строки
        
    Raises:
        Exception: Если не удалось получить ответ от LLM
    """
    try:
        # Формируем промпт с текущей датой
        current_date = datetime.now().strftime("%Y-%m-%d")
        system_prompt = SYSTEM_PROMPT.format(current_date=current_date)
        
        logger.info(f"Отправляем запрос в LLM: {query}")
        
        # Вызываем OpenAI API
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Можно использовать gpt-3.5-turbo для экономии
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0,  # Детерминированный вывод
            max_tokens=200,  # SQL запросы обычно короткие
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Очищаем от возможных markdown блоков
        if sql_query.startswith("```"):
            # Убираем ```sql и ```
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        logger.info(f"Получен SQL: {sql_query}")
        return sql_query
        
    except Exception as e:
        logger.error(f"Ошибка при обращении к LLM: {e}")
        raise Exception(f"Не удалось сгенерировать SQL-запрос: {e}")

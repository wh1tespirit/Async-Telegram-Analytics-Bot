# LLM Service - Text-to-SQL

## Описание

LLM-сервис преобразует вопросы на естественном языке (русском) в SQL-запросы к PostgreSQL.

## Архитектура

```
User Query (RU) 
    ↓
[LLM Service] → OpenAI GPT-4o-mini → SQL Query
    ↓
[SQL Executor] → PostgreSQL → Result (число)
    ↓
User Answer
```

## Компоненты

### 1. `llm_service.py`
- **Функция**: `ask_llm(query: str) -> str`
- **Задача**: Генерирует SQL-запрос из текста
- **Модель**: GPT-4o-mini (можно заменить на gpt-3.5-turbo)
- **Промпт**: Детальное описание схемы БД + примеры + правила

### 2. `sql_executor.py`
- **Функция**: `execute_sql_query(sql: str) -> int`
- **Задача**: Выполняет SQL и возвращает число
- **Безопасность**: Использует SQLAlchemy text() для защиты

### 3. `query_service.py`
- **Функция**: `process_user_query(query: str) -> int`
- **Задача**: Главный интерфейс (LLM + SQL)

## Системный промпт

Ты эксперт по PostgreSQL. Твоя задача — генерировать ТОЛЬКО SQL-код на основе вопроса пользователя.

### Схема базы данных

#### Таблица `videos` (итоговая статистика по видео)
- id (String) - идентификатор видео
- creator_id (String) - идентификатор креатора
- video_created_at (TIMESTAMP WITH TIME ZONE) - дата и время публикации видео
- views_count (BIGINT) - финальное количество просмотров
- likes_count (INTEGER) - финальное количество лайков
- comments_count (INTEGER) - финальное количество комментариев
- reports_count (INTEGER) - финальное количество жалоб
- created_at (TIMESTAMP WITH TIME ZONE) - дата создания записи
- updated_at (TIMESTAMP WITH TIME ZONE) - дата обновления записи

#### Таблица `video_snapshots` (почасовые замеры статистики)
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

### КРИТИЧЕСКИЕ ПРАВИЛА

1. **Ответ должен содержать ТОЛЬКО SQL-запрос** - без markdown, без кавычек, без объяснений
2. **Запрос ОБЯЗАН возвращать РОВНО ОДНО ЧИСЛО** - используй COUNT, SUM, AVG и т.д.
3. **Для подсчета количества видео** → используй таблицу `videos`
4. **Для подсчета динамики/прироста за конкретную дату** → используй таблицу `video_snapshots` и суммируй `delta_*`
5. **Для фильтрации по датам**:
   - Используй `::date` для приведения timestamp к дате
   - Формат дат: 'YYYY-MM-DD'
   - Для диапазона используй `BETWEEN` или `>=` и `<=`
   - **Для фильтрации по времени (часам)** используй сравнение timestamp с указанием часового пояса UTC: `created_at >= 'YYYY-MM-DD HH:00:00+00:00'::timestamptz`
6. **Если год не указан** - используй 2025 год (данные из ноября-декабря 2025)
7. **Текущая дата**: {current_date}
8. **Все строковые значения (ID, ссылки) ОБЯЗАТЕЛЬНО оборачивай в одинарные кавычки** - например: `creator_id = 'abc123'`
9. **Для фильтрации video_snapshots по creator_id** → используй JOIN с таблицей videos
10. **Время в базе данных хранится в UTC** - всегда указывай `+00:00` при фильтрации по времени

### Примеры запросов

Вопрос: "Сколько всего видео есть в системе?"
SQL: SELECT COUNT(id) FROM videos

Вопрос: "Сколько видео у креатора с id abc123 вышло с 1 ноября 2025 по 5 ноября 2025 включительно?"
SQL: SELECT COUNT(id) FROM videos WHERE creator_id = 'abc123' AND video_created_at::date BETWEEN '2025-11-01' AND '2025-11-05'

Вопрос: "Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63 набрали больше 10000 просмотров по итоговой статистике?"
SQL: SELECT COUNT(id) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63' AND views_count > 10000

Вопрос: "На сколько просмотров в сумме выросли все видео 28 ноября 2025?"
SQL: SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE created_at::date = '2025-11-28'

Вопрос: "Сколько разных видео получали новые просмотры 27 ноября 2025?"
SQL: SELECT COUNT(DISTINCT video_id) FROM video_snapshots WHERE created_at::date = '2025-11-27' AND delta_views_count > 0

Вопрос: "Сколько лайков набрали все видео за период с 26 по 28 ноября?"
SQL: SELECT COALESCE(SUM(delta_likes_count), 0) FROM video_snapshots WHERE created_at::date BETWEEN '2025-11-26' AND '2025-11-28'

Вопрос: "На сколько просмотров суммарно выросли все видео креатора с id cd87be38b50b4fdd8342bb3c383f3c7d в промежутке с 10:00 до 15:00 28 ноября 2025 года?"
SQL: SELECT COALESCE(SUM(vs.delta_views_count), 0) FROM video_snapshots vs JOIN videos v ON vs.video_id = v.id WHERE v.creator_id = 'cd87be38b50b4fdd8342bb3c383f3c7d' AND vs.created_at >= '2025-11-28 10:00:00+00:00'::timestamptz AND vs.created_at < '2025-11-28 15:00:00+00:00'::timestamptz

### ВАЖНО
- Всегда используй COALESCE для SUM, чтобы вернуть 0 вместо NULL
- Для подсчета уникальных видео используй COUNT(DISTINCT video_id)
- Для фильтрации "больше N" используй оператор >
- Для фильтрации "меньше N" используй оператор <
- При фильтрации video_snapshots по creator_id используй JOIN: `FROM video_snapshots vs JOIN videos v ON vs.video_id = v.id WHERE v.creator_id = '...'`
- Для временных диапазонов "с X:00 до Y:00" используй `>= 'YYYY-MM-DD X:00:00+00:00'::timestamptz AND < 'YYYY-MM-DD Y:00:00+00:00'::timestamptz` (не включая конечное время)

## Примеры

### Вопрос 1
**Запрос**: "Сколько всего видео?"  
**SQL**: `SELECT COUNT(id) FROM videos`

### Вопрос 2
**Запрос**: "На сколько выросли просмотры 28 ноября?"  
**SQL**: `SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE created_at::date = '2025-11-28'`

### Вопрос 3
**Запрос**: "Сколько видео набрало больше 100k просмотров?"  
**SQL**: `SELECT COUNT(id) FROM videos WHERE views_count > 100000`

## Тестирование

### Автоматические тесты
```bash
python test_llm.py
```

### Интерактивный режим
```bash
python test_llm.py --interactive
```

## Настройка

1. Добавьте `OPENAI_API_KEY` в `.env`
2. Убедитесь, что БД запущена и данные загружены
3. Запустите тесты

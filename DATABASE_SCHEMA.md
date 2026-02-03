# Схема базы данных

## Таблица `videos`

Хранит итоговую статистику по каждому видео.

| Поле | Тип | Описание | Индекс |
|------|-----|----------|--------|
| `id` | String (UUID) | Идентификатор видео (PK) | ✓ |
| `creator_id` | String | Идентификатор креатора | |
| `video_created_at` | DateTime(TZ) | Дата и время публикации видео | ✓ |
| `views_count` | BigInteger | Финальное количество просмотров | |
| `likes_count` | Integer | Финальное количество лайков | |
| `comments_count` | Integer | Финальное количество комментариев | |
| `reports_count` | Integer | Финальное количество жалоб | |
| `created_at` | DateTime(TZ) | Дата создания записи | |
| `updated_at` | DateTime(TZ) | Дата обновления записи | |

## Таблица `video_snapshots`

Хранит почасовые замеры статистики по каждому видео.

| Поле | Тип | Описание | Индекс |
|------|-----|----------|--------|
| `id` | String (UUID) | Идентификатор снапшота (PK) | ✓ |
| `video_id` | String (FK) | Ссылка на видео | ✓ |
| `views_count` | BigInteger | Просмотры на момент замера | |
| `likes_count` | Integer | Лайки на момент замера | |
| `comments_count` | Integer | Комментарии на момент замера | |
| `reports_count` | Integer | Жалобы на момент замера | |
| `delta_views_count` | BigInteger | Прирост просмотров | |
| `delta_likes_count` | Integer | Прирост лайков | |
| `delta_comments_count` | Integer | Прирост комментариев | |
| `delta_reports_count` | Integer | Прирост жалоб | |
| `created_at` | DateTime(TZ) | Время замера | ✓ |
| `updated_at` | DateTime(TZ) | Дата обновления записи | |

## Связи

- `video_snapshots.video_id` → `videos.id` (CASCADE DELETE)

## Индексы

- `videos.id` - Primary Key
- `videos.video_created_at` - Для фильтрации по дате публикации
- `video_snapshots.id` - Primary Key
- `video_snapshots.video_id` - Foreign Key
- `video_snapshots.created_at` - **КРИТИЧНО** для запросов по датам замеров

## Примеры SQL-запросов

### Сколько всего видео?
```sql
SELECT COUNT(id) FROM videos;
```

### Сколько видео у креатора за период?
```sql
SELECT COUNT(id) FROM videos 
WHERE creator_id = 'xxx' 
AND video_created_at BETWEEN '2025-11-01' AND '2025-11-05';
```

### Сколько видео набрало больше N просмотров?
```sql
SELECT COUNT(id) FROM videos 
WHERE views_count > 100000;
```

### На сколько выросли просмотры в конкретный день?
```sql
SELECT SUM(delta_views_count) FROM video_snapshots 
WHERE created_at::date = '2025-11-28';
```

### Сколько видео получали просмотры в конкретный день?
```sql
SELECT COUNT(DISTINCT video_id) FROM video_snapshots 
WHERE created_at::date = '2025-11-27' 
AND delta_views_count > 0;
```

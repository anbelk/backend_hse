# Ad Moderation Service

Асинхронная модерация объявлений через Kafka.

## Запуск

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

1. `docker compose up -d`
2. `python -m pgmigrate -c "postgresql://postgres:postgres@127.0.0.1:5433/ad_moderation" -d . migrate -t latest`
3. `uvicorn src.main:app --reload --host 0.0.0.0 --port 8000` — в одном терминале
4. `python -m src.workers.moderation_worker` — в другом терминале

## Переменные окружения

Скопировать `.env.example` в `.env` при необходимости.

## API

- `POST /async_predict` — запрос на модерацию, возвращает `task_id`
- `GET /moderation_result/{task_id}` — статус задачи

Kafka Console: http://localhost:8081

# City Geo Service

FastAPI-микросервис для хранения городов, получения координат через Яндекс Геокодер и поиска двух ближайших городов по формуле Haversine.

## Локальный запуск

```bash
python3.13 -m venv venv
./venv/bin/pip install -e ".[dev]"
cp .env.example .env
```

Заполните `.env`, затем:

```bash
set -a
source .env
set +a
./venv/bin/alembic upgrade head
RATE_LIMIT_ENABLED=false ./venv/bin/uvicorn app.main:app --reload
```

Для локального запуска без Docker rate limiting можно отключить через `RATE_LIMIT_ENABLED=false`. Если нужен rate limiting локально, поднимите Redis и задайте `REDIS_URL`.

Healthcheck:

```bash
curl http://localhost:8000/health
```

Пример добавления города:

```bash
curl -X POST http://localhost:8000/cities \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"name":"Москва"}'
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Контейнер стартует через gunicorn с uvicorn worker. Если `RUN_MIGRATIONS=true`, entrypoint выполнит `alembic upgrade head`.

## Production

Обязательные переменные:

- `API_KEY`
- `YANDEX_GEOCODER_API_KEY`
- `DATABASE_URL`
- `REDIS_URL`
- `CORS_ORIGINS`

Рекомендуемая команда уже задана в `Dockerfile`:

```bash
gunicorn app.main:create_app --factory -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000
```

Для production задайте `ENVIRONMENT=production`, надежный `API_KEY`,
реальный `YANDEX_GEOCODER_API_KEY` и не включайте `DEBUG`.

## Тесты

```bash
./venv/bin/pytest
```

Contract-тест сравнивает текущую OpenAPI-схему со snapshot в `tests/contract/openapi_snapshot.json`.

## Миграции

```bash
./venv/bin/alembic revision --autogenerate -m "change description"
./venv/bin/alembic upgrade head
```

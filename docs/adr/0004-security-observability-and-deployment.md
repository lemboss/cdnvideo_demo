# ADR 0004: Безопасность, наблюдаемость и деплой

## Статус
Принято

## Контекст
Сервис должен иметь минимальный production baseline: API key, CORS allowlist, rate limiting, JSON-логи, graceful shutdown и Docker-деплой.

## Решение
Используем `X-API-Key`, Redis-backed rate limiting, allowlist CORS, middleware ограничения request body, структурированные JSON-логи с `X-Request-ID`, единый формат ошибок и запуск через gunicorn + uvicorn worker.

CI запускает Ruff и тесты, затем собирает Docker image и публикует его в GHCR после прохождения проверок.

CD выполняется отдельным GitHub Actions job на push в `main`: workflow подключается к production-серверу по SSH, подтягивает опубликованный image, перезапускает сервис через `docker compose` и проверяет `/health`.

Redis используется только как распределенное хранилище счетчиков rate limiting, а не как основное хранилище данных. Это нужно, потому что production-запуск через gunicorn предполагает несколько workers, а позднее сервис может быть запущен в нескольких инстансах. In-memory limiter в такой схеме считал бы лимиты отдельно в каждом worker или инстансе и позволял бы обходить ограничение.

## Последствия
Сервис готов к запуску несколькими workers. Redis становится обязательной зависимостью, если rate limiting включен.

# ADR 0004: Безопасность, наблюдаемость и деплой

## Статус
Принято

## Контекст
Сервис должен иметь минимальный production baseline: API key, CORS allowlist, rate limiting, JSON-логи, graceful shutdown и Docker-деплой.

## Решение
Используем `X-API-Key`, Redis-backed rate limiting, allowlist CORS, middleware ограничения request body, структурированные JSON-логи с `X-Request-ID`, единый формат ошибок и запуск через gunicorn + uvicorn worker.

CI собирает Docker image и публикует его в GHCR после прохождения тестов и contract check.

## Последствия
Сервис готов к запуску несколькими workers. Redis становится обязательной зависимостью, если rate limiting включен.

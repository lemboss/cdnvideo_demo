# TODO

## Done
- [x] FastAPI-сервис с async SQLite, Alembic и Docker.
- [x] CRUD API для городов и поиск 2 ближайших городов по Haversine.
- [x] Интеграция с Яндекс Геокодером через отдельный интерфейс.
- [x] API key, CORS allowlist, Redis-backed rate limiting и body size limit.
- [x] JSON-логи, request id, единый error handling и graceful shutdown.
- [x] Unit/API/integration/contract tests.
- [x] Ruff для PEP8/lint/format.
- [x] ADR для ключевых архитектурных решений.
- [x] GitHub Actions CI/CD: Ruff, tests, Docker image build/push и SSH autodeploy.

## Backlog
- [ ] Подключить Prometheus metrics endpoint.
- [ ] Подключить Grafana dashboards.
- [ ] Описать и внедрить SLI/SLO для availability, error rate и latency.
- [ ] Добавить мониторинг latency по HTTP endpoints.
- [ ] Добавить мониторинг SQLite/БД: health, время запросов, ошибки операций.
- [ ] Добавить мониторинг диска для SQLite volume.
- [ ] Добавить алертинг по 5xx/error rate.
- [ ] Добавить алертинг по превышению latency SLO.
- [ ] Добавить алертинг по деградации БД и заполнению диска.
- [ ] Подготовить Kubernetes manifests или Helm chart.
- [ ] Настроить горизонтальное масштабирование сервиса в Kubernetes.
- [ ] Описать production runbook для мониторинга, алертов и инцидентов.

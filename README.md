# Система потокового анализа новостей

Микросервисный пайплайн для сбора публикаций из ВКонтакте и Telegram, NLP‑обработки (NER, Entity Linking, анализ тональности) и построения графа знаний.

Работа выполнена в рамках ВКР магистратуры ОП «Инженерия данных», ФКН НИУ ВШЭ, 2026.

## Архитектура

```
VK / Telegram  →  collectors  →  Redis Streams  →  processor (dedup + normalize)
                                                          ↓
                                                    nlp_worker (NER + sentiment + EL)
                                                          ↓
                                              ┌───────────┴───────────┐
                                              ↓                       ↓
                                        OpenSearch              graph_builder → Neo4j
                                              ↑                       ↑
                                              └─── api_gateway ────────┘
                                                       ↑
                                                   dashboard (Streamlit)
```

Восемь сервисов, общающихся через Redis Streams. Состояние — в OpenSearch (документы, поиск, агрегации) и Neo4j (граф).

## Стек

- Python 3.11, uv (workspace‑монорепо)
- aiohttp, Telethon — сбор
- datasketch (MinHash + Redis‑backed LSH) — устойчивая дедупликация между перезапусками
- razdel, pymorphy3 — токенизация и нормализация
- Natasha — NER, RuBERT (опционально, через `NLP_MODE=full`) — тональность
- Wikidata `wbsearchentities` (Entity Linking) с кешем в Redis
- OpenSearch 2.15, Neo4j 5.22 community, Redis 7.4
- FastAPI — API, Streamlit + Plotly — UI
- Prometheus + Grafana — метрики и дашборды
- Caddy — reverse proxy + автоматический HTTPS (Let's Encrypt)
- Docker Compose, GitHub Actions → GHCR, деплой на Yandex Cloud

## Быстрый старт

```bash
cp .env.example .env
make install            # uv sync для всех воркспейсов
make up                 # поднимает инфраструктуру и сервисы
make migrate            # применяет миграции OpenSearch и Neo4j
make seed               # генерирует синтетические посты (mock‑режим)
```

После запуска:

- OpenSearch Dashboards — http://localhost:5601
- Neo4j Browser — http://localhost:7474 (neo4j / neopassword123)
- API — http://localhost:8000/docs
- Streamlit UI — http://localhost:8501
- Prometheus — http://localhost:9090
- Grafana — http://localhost:3000 (admin / admin)

## Режим работы без ключей

По умолчанию `COLLECTOR_MODE=mock` — коллекторы генерируют синтетические посты. Чтобы переключиться на реальные источники, заполните ключи в `.env` и поставьте `COLLECTOR_MODE=real`.

### Получение ключа VK

1. Зайти на https://dev.vk.com под своим аккаунтом.
2. «Мои приложения» → «Создать приложение» → выбрать **Standalone‑приложение**.
3. После создания → «Настройки» → раздел **«Сервисный ключ доступа»** → скопировать.
4. В `.env`:
   ```
   COLLECTOR_MODE=real
   VK_TOKEN=<сервисный ключ>
   VK_COMMUNITIES=ria,tassagency,rbc_news,lentaru,meduzaproject
   ```
5. Перезапустить коллектор: `docker compose restart vk-collector`.

Лимиты: 5 запросов/сек, 5000/день. Коллектор использует rate limiter (3 req/сек) и экспоненциальный backoff (`tenacity`) на временные ошибки. Параметры опроса в `.env`: `VK_POLL_INTERVAL` (секунды между обходами всех сообществ).

Возможные ошибки в логах:
- `VKAuthError` (коды 5/17/27/28) — токен невалиден или истёк, коллектор остановится;
- `VKCaptchaError` (код 14) — VK требует капчу, коллектор подождёт минуту и продолжит со следующего сообщества;
- `VKRateLimitError` (код 6) — превышен RPS, retry с backoff (до 5 попыток);
- `VKTransientError` (коды 1/10, HTTP 5xx) — временная ошибка сервера, retry.

### Telegram

1. Зарегистрировать приложение на https://my.telegram.org → API development tools — получить `api_id` и `api_hash`.
2. В `.env`:
   ```
   COLLECTOR_MODE=real
   TG_API_ID=<id>
   TG_API_HASH=<hash>
   TG_CHANNELS=ria,tass,bbcrussian
   ```
3. При первом запуске Telethon попросит код из SMS — авторизоваться интерактивно, файл сессии сохранится в томе. Дальше коллектор работает в фоне.

## Метрики и мониторинг

В каждом сервисе доступен `/metrics` (для воркеров — на отдельном порту 9100). Prometheus собирает с api_gateway и всех воркеров. В Grafana заведён дашборд из 9 панелей: пропускная способность по этапам, p50/p95 латентности API, заполненность буфера графа, hit‑rate Wikidata‑кеша, доли тональности и т.п.

## NLP на CPU

По умолчанию `NLP_MODE=lite`: NER через Natasha (быстро, без GPU), тональность — лексиконный классификатор. Для полного режима с RuBERT (~700 МБ, медленнее на CPU) поставьте `NLP_MODE=full`.

## Миграции

Схема OpenSearch и Neo4j версионируется как `infra/migrations/{opensearch,neo4j}/V###__name.{json,cypher}`. Раннер `scripts/migrate.py` идемпотентен: применённые версии регистрируются в индексе `news_migrations` и узлах `(:Migration)`, повторный запуск пропускает их.

## Бенчмарки

В `scripts/` лежат скрипты оценки:

- `eval_ner.py` — NER на factRuEval‑2016 (P/R/F1 по PER/ORG/LOC);
- `eval_sentiment.py` — тональность на встроенном hand‑labelled датасете либо HF;
- `eval_throughput.py` — end‑to‑end пропускная способность пайплайна;
- `eval_latency.py` — p50/p95/p99 эндпоинтов API.

Результаты сохраняются в `docs/metrics/`.

## Разработка

```bash
make lint               # ruff + mypy
make format             # автоформат
make test               # pytest (unit + integration через testcontainers)
make logs               # docker compose logs -f
make down               # остановить
make clean              # сбросить тома
```

## Структура

```
libs/common/            — общие схемы, клиенты Redis/OpenSearch/Neo4j, метрики, логирование
services/               — 7 микросервисов (vk_collector, telegram_collector, processor,
                          nlp_worker, graph_builder, api_gateway, dashboard)
infra/                  — миграции OpenSearch/Neo4j, конфиги Prometheus/Grafana/Caddy
scripts/                — миграции, генератор моков, бенчмарки
tests/                  — unit + integration
docs/                   — описание архитектуры и результаты бенчмарков
```

## Деплой

CI: GitHub Actions с матричной сборкой образов и публикацией в GHCR. Деплой по SSH на Yandex Cloud (4 vCPU / 8 ГБ): тянутся свежие теги, `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`. Caddy на хосте проксирует HTTPS на api_gateway/dashboard и автоматически обновляет сертификаты Let's Encrypt по `*.nip.io`.

## Лицензия

Apache 2.0.

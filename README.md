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
- datasketch (MinHash), razdel, pymorphy3 — обработка
- Natasha — NER, RuBERT (опционально, через `NLP_MODE=full`) — тональность
- OpenSearch 2.15, Neo4j 5.22 community, Redis 7.4
- FastAPI — API, Streamlit + Plotly — UI
- Docker Compose, GitHub Actions

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

Документация по подключению будет добавлена позже. Сейчас Telegram‑коллектор работает только в `mock`‑режиме.

## NLP на CPU

По умолчанию `NLP_MODE=lite`: NER через Natasha (быстро, без GPU), тональность — лексиконный классификатор. Для полного режима с RuBERT (~700 МБ, медленнее на CPU) поставьте `NLP_MODE=full`.

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
libs/common/            — общие схемы, клиенты Redis/OpenSearch, логирование
services/               — 7 микросервисов
infra/                  — маппинги OpenSearch, init‑скрипт Neo4j
scripts/                — bootstrap и генератор моков
tests/                  — unit + integration
```

## Лицензия

Apache 2.0.

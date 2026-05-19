# redis-mtusi

Учебный Redis для проекта «ДЗ 2.4: кеширование LLM».

Контейнер слушает **localhost:6379** — так же, как ожидает `demo.py`.

## Требования

- [Docker](https://docs.docker.com/get-docker/) и Docker Compose (входит в Docker Desktop)

## Команды

```bash
cd redis-mtusi

# Запустить Redis в фоне
docker compose up -d

# Проверить, что живой (ответ: PONG)
docker compose exec redis-mtusi redis-cli ping

# Статус контейнера
docker compose ps

# Логи
docker compose logs -f redis-mtusi

# Остановить (данные в volume сохранятся)
docker compose down

# Остановить и удалить данные кеша в Redis
docker compose down -v
```

## Проверка с проектом

Из корня репозитория:

```bash
uv run python demo.py
```

Должен появиться блок `=== RedisLLMCache ===` и hit rate 40%.

## Полезно для отладки

```bash
# Посмотреть ключи кеша (префикс llm:)
docker compose exec redis-mtusi redis-cli KEYS 'llm:*'

# Очистить только ключи демо
docker compose exec redis-mtusi redis-cli FLUSHDB
```

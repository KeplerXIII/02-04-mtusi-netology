# ДЗ 2.4: Кеширование LLM

## Запуск

```bash
cp .env.example .env
uv sync
uv run python demo.py
```

Для уровня 2 (Redis): см. папку [`redis-mtusi/`](redis-mtusi/README.md)

```bash
cd redis-mtusi && docker compose up -d
cd .. && uv run python demo.py
```

## Файлы

- `llm_cache.py` — классы `LLMCache` и `RedisLLMCache`
- `demo.py` — 5 запросов (2 повтора), вывод `stats()`
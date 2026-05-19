import os

from dotenv import load_dotenv
from openai import OpenAI

from llm_cache import LLMCache, RedisLLMCache, make_cache_key

load_dotenv()

MODEL = "deepseek-chat"
TEMPERATURE = 0.7


def ask_llm(client: OpenAI, messages: list) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE,
    )
    return resp.choices[0].message.content or ""


def cached_request(cache, client: OpenAI, messages: list) -> str:
    cached = cache.get(MODEL, messages, TEMPERATURE)
    if cached is not None:
        print("  -> из кеша")
        return cached

    print("  -> запрос к API")
    answer = ask_llm(client, messages)
    cache.set(MODEL, messages, TEMPERATURE, answer)
    return answer


def run_demo(cache, title: str) -> None:
    print(f"\n=== {title} ===")
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Нет DEEPSEEK_API_KEY в .env")
        return

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    prompts = [
        [{"role": "user", "content": "Скажи одно слово: яблоко"}],
        [{"role": "user", "content": "Скажи одно слово: груша"}],
        [{"role": "user", "content": "Скажи одно слово: яблоко"}],  # повтор 1
        [{"role": "user", "content": "Скажи одно слово: слива"}],
        [{"role": "user", "content": "Скажи одно слово: груша"}],  # повтор 2
    ]

    for i, messages in enumerate(prompts, 1):
        print(f"Запрос {i}: {messages[0]['content']}")
        text = cached_request(cache, client, messages)
        print(f"  Ответ: {text[:80]}{'...' if len(text) > 80 else ''}")

    print(f"\nСтатистика: hits={cache.hits}, misses={cache.misses}")
    print(f"Hit rate: {cache.stats()}%")


def check_criteria(cache: LLMCache) -> None:
    print("\n=== Проверка критериев ===")

    messages = [{"role": "user", "content": "тест"}]
    key1 = make_cache_key(MODEL, messages, TEMPERATURE)
    key2 = make_cache_key(MODEL, messages, TEMPERATURE)
    ok_key = key1 == key2 and "timestamp" not in key1 and "request_id" not in key1
    print(f"Ключ детерминированный (без timestamp/request_id): {'OK' if ok_key else 'FAIL'}")

    short_cache = LLMCache(ttl_seconds=1)
    short_cache.set(MODEL, messages, TEMPERATURE, "old")
    import time

    time.sleep(1.1)
    expired = short_cache.get(MODEL, messages, TEMPERATURE)
    ok_ttl = expired is None
    print(f"TTL (просроченная запись не возвращается): {'OK' if ok_ttl else 'FAIL'}")

    # hit rate: 5 запросов, 3 уникальных -> 2 hits, 3 misses -> 40%
    expected_rate = round(2 / 5 * 100, 2)
    ok_rate = cache.stats() == expected_rate
    print(f"Hit rate {cache.stats()}% (ожидается {expected_rate}%): {'OK' if ok_rate else 'FAIL'}")

    ok_demo = cache.hits == 2 and cache.misses == 3
    print(f"5 запросов, 2 повтора (hits=2, misses=3): {'OK' if ok_demo else 'FAIL'}")


def main() -> None:
    print("ДЗ 2.4: демонстрация кеширования LLM")
    print(f"Модель: {MODEL}")

    memory_cache = LLMCache()
    run_demo(memory_cache, "LLMCache (память)")
    check_criteria(memory_cache)

    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        r.ping()
        redis_cache = RedisLLMCache(r)
        run_demo(redis_cache, "RedisLLMCache")
        print(f"\nRedis hit rate: {redis_cache.stats()}%")
    except Exception as e:
        print(f"\nRedis недоступен ({e}), уровень 2 пропущен в демо")


if __name__ == "__main__":
    main()

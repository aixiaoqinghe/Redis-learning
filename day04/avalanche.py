"""
缓存雪崩解决方案：过期时间加随机值
问题：大量 key 同一时间过期 -> 请求全打 DB
方案： TTL 加随机偏移，打散过期时间
"""

import redis
import random

r = redis.Redis(
    host = "localhost", 
    port = 6379,
    db = 0,
    decode_responses = True,
    socket_connect_timeout = 3
)

def set_with_random_ttl(key, value, base_ttl = 300, jitter = 60):
    """
    基础过期时间 + 随机偏移
    base_ttl = 300, jitter = 60 -> 实际 TTL 在300~360秒之间
    """
    ttl = base_ttl + random.randint(0, jitter)
    r.setex(key, ttl, value)
    return ttl

if __name__ == "__main__":
    print("=== 缓存雪崩：随机 TTL ===")
    ttls = []
    for i in range(5):
        ttl = set_with_random_ttl(f"demo:avalanche:{i}", f"value{i}")
        ttls.append(ttl)
        print(f" key{i} TTL = {ttl}s")

    print(f"\n5 个 key 的 TTL：{ttls}")
    print("→ 过期时间被打散，不会同一时刻全失效")

# 清理
for i in range(5):
    r.delete(f"demo:avalanche:{i}")
print("[OK] 已清理")
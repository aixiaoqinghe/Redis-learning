"""
分布式锁版本2: SET key value NX EX seconds
一条命令搞定"抢锁 + 设过期"， 原子， 避免 v1 的死锁
"""

import redis
import uuid

r = redis.Redis(
    host = "localhost", 
    port = 6379,
    db = 0,
    decode_responses = True,
    socket_connect_timeout = 3
)

def acquire_lock(lock_key, expire = 10):
    """正确加锁: SET NX EX, value 用唯一标识"""
    value = str(uuid.uuid4())       # 唯一标识，用于释放时校验
    got = r.set(lock_key, value, nx = True, ex = expire)
    if got:
        print(f"  [成功] 拿到锁，value={value[:8]}...，过期 {expire}s")
        return value
    print("  [失败] 锁已被占用")
    return None

if __name__ == "__main__":
    print("=== 分布式锁 v2: SET NX EX ===")
    lock_key = "demo:lock:v2"
    value = acquire_lock(lock_key)
    print(f"  TTL: {r.ttl(lock_key)}")

    # 再抢一次，应该失败
    print(" 尝试再抢一次：")
    acquire_lock(lock_key)

    r.delete(lock_key)
    print("[OK] 已清理")
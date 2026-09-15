"""
分布式锁版本3: Lua 脚本释放(校验 value)
+ 模拟误删场景： A 超时锁释放 -> B 抢到 -> A 用普通的 DEL 误删 B 的锁
"""

import redis
import uuid
import time

r = redis.Redis(
    host = "localhost", 
    port = 6379,
    db = 0,
    decode_responses = True,
    socket_connect_timeout = 3
)

# Lua 脚本：只有 value 是自己的才删
UNLOCK_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

def acquire(lock_key, expire = 10):
    value = str(uuid.uuid4())
    got = r.set(lock_key, value, nx = True, ex = expire)
    return value if got else None

def unlock_safe(lock_key, value):
    """安全释放：Lua 校验 value"""
    result = r.eval(UNLOCK_LUA, 1, lock_key, value)
    if result:
        print(f"  [安全释放] 锁 {lock_key} 已释放")
    else:
        print(f"  [安全释放] 锁 {lock_key} 不是自己的，不删")

def unlock_bad(lock_key):
    """错误释放：直接 DEL (会误删)"""
    r.delete(lock_key)
    print(f"  [错误释放] 直接 DEL {lock_key}")

def simulate_misdelete():
    """模拟误删场景"""
    print("\n=== 模拟误删场景 ===")
    lock_key = "demo:lock:misdelete"

    # A 抢到锁，过期设2s
    value_a = acquire(lock_key, expire = 2)
    print(f"  A 拿到锁，value={value_a[:8]}...，过期 2s")

    # A 业务执行超时（模拟 3s > 2s）,锁自动过期
    print("  A 业务执行中（超过锁过期时间）...")
    time.sleep(3)

    # B 抢到锁（因为 A 的锁已过期）
    value_b = acquire(lock_key, expire = 10)
    print(f"  B 拿到锁，value={value_b[:8]}...")

    # A 执行完，用普通 DEL 释放 -> 误删 B 的锁
    unlock_bad(lock_key)

    # 检查：B的锁被误删了吗？
    current = r.get(lock_key)
    if current is None:
        print("  [结果] B 的锁被 A 误删了！这就是误删问题")
    else:
        print(f"  [结果] 锁还在，value={current[:8]}...")

    r.delete(lock_key)

def demo_safe_unlock():
    """演示安全的 Lua 释放"""
    print("\n=== 安全释放演示 ===")
    lock_key = "demo:lock:safe"

    value_a = acquire(lock_key)
    print(f" A 拿到锁")

    # 用一个错误的 value 释放 -> 不会删
    unlock_safe(lock_key, "wrong_value")

    # 用自己的 value 释放 -> 删成功
    unlock_safe(lock_key, value_a)

if __name__ == "__main__":
    print("=== 分布锁 v3: Lua 释放 ===")
    demo_safe_unlock()
    simulate_misdelete()
    print("[OK] 演示完毕")
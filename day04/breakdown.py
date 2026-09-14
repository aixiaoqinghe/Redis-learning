"""
缓存击穿解决方案：互斥锁
问题：热点Key过期，大量并发同时打 DB
方案：只让一个线程抢锁重建缓存，其他线程等待
"""

import redis
import time

r = redis.Redis(
    host = 'localhost',
    port = 6379,
    db = 0,
    decode_responses = True,
    socket_connect_timeout = 3
)

def get_from_db(product_id):
    """模拟慢查询"""
    time.sleep(1)   # 模拟 DB 耗时，把[重建缓存]的窗口拉长
    return f"Product-{product_id}-Data"

def get_hot_product(product_id):
    """带互斥锁保护的热点查询"""
    cache_key = f"demo:hot:{product_id}"    # 存热点商品数据的
    lock_key = f"demo:lock:{product_id}"    # 互斥锁，独立命名空间，避免和业务key冲突

    # 1.查缓存
    cached = r.get(cache_key)
    # Redis 是空的 -> cached = None 
    if cached is not None:
        print(f"[缓存命中] {cached}")
        return cached

    # 2. 缓存失效，抢锁重建
    # SET NX EX: 原子操作，避免 SETNX + EXPIRE 两步之间的死锁窗口
    # 抢锁，互斥锁的核心
    # nx = True : 只有当 lock_key 不存在时才设置成功（返回True）
    # ex = 10 ，锁的自动过期时间为10s
    # value = "1", 锁的值
    got_lock = r.set(lock_key, "1", nx = True, ex = 10)

    if got_lock:   # got_lock 是 True,抢到锁了
        try:
            print("[抢到锁] 查 DB 重建缓存")
            data = get_from_db(product_id)
            r.setex(cache_key, 300, data)
            return data
        finally:
            # 释放锁 (Day5 会用 Lua 优化，这里简化)
            r.delete(lock_key)
    else:
        # 3. 没有抢到锁，等待后重试
        print("[没抢到锁] 等待重试...")
        time.sleep(0.5)
        return get_hot_product(product_id)

if __name__ == "__main__":
    print("=== 缓存击穿：互斥锁 ===")
    print("第1次查（缓存空，抢锁查 DB）:")
    get_hot_product(1001)

    # 清理
    r.delete("demo:hot:1001", "demo:lock:1001")
    print("[OK] 已清理")
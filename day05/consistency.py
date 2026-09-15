"""
缓存一致性：先更新 DB 再删缓存 + 延迟双删
最常用方案：更新 DB -> 删缓存 -> 延迟再删一次
"""

import redis
import time
import threading
r = redis.Redis(
    host = "localhost", 
    port = 6379,
    db = 0,
    decode_responses = True,
    socket_connect_timeout = 3
)

# 模拟 DB
fake_db = {"product:1001": "iPhone"}

def update_db(key, value):
    """模拟更新 DB """
    fake_db[key] = value
    print(f"  [DB] 更新 {key} = {value}")

def delete_cache(key):
    """删缓存"""
    r.delete(key)
    print(f"  [Cache] 删除 {key}")


def delayed_double_delete(key, value, delay = 0.5):
    """
    延迟双删(核心)：
    1. 先删缓存
    2. 更新 DB
    3. 延迟再删缓存（删掉并发读时写进去的旧值）
    """
    # 第一次删
    delete_cache(key)
    # 更新 DB
    update_db(key, value)
    # 延迟再删， 第二次删缓存————把那个并发读写进去的旧值干掉！
    time.sleep(delay)
    delete_cache(key)
    print("  [完成] 延迟双删结束")

def read_with_cache(key):
    """读：先查缓存， miss 则查 DB 并重建缓存"""
    cache = r.get(key)
    if cache:
        print(f"  [Cache 命中] {key} = {cache}")
        return cache
    # 缓存 miss, 查 DB
    db_value = fake_db.get(key)
    if db_value:
        r.setex(key, 300, db_value)    # 重建缓存， TTL=300秒（这个过期时间是最终一致性的最后兜底）
        print(f"  [Cache 重建] {key} = {db_value}")
    return db_value

if __name__ == "__main__":
    # 读-写-读
    print("=== 缓存一致性：延迟双删 ===")
    key = "demo:product:1001"
    read_with_cache(key)       # 第一次读，重建缓存
    delayed_double_delete(key, "iPhone 16")
    read_with_cache(key)       # 再读，应拿到新值

    r.delete(key)
    print("[OK] 已清理")

# 记住一个原则：缓存是 DB 的衍生品，DB才是老大
# 所以先动 DB ,再动小弟（删缓存）————这也是 Cache Aside 模式的核心思想
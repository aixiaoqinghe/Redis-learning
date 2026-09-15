"""
分布式锁版本1：SETNX + EXPIRE (有死锁风险，仅演示问题)
问题：两步不原子，SETNX后进程挂了，EXPIRE没执行 -> 锁永不过期
"""

import redis

r = redis.Redis(
    host = "localhost", 
    port = 6379,
    db = 0,
    decode_responses = True,
    socket_connect_timeout = 3
)

def bad_lock(lock_key, expire = 10):
    """错误示范：两步操作，不原子"""
    # 第1步：抢锁
    got = r.setnx(lock_key, "1")
    if not got:
        print("  [失败] 锁已被占用")
        return False

    # 假设这里进程挂了（模拟：中间抛异常）-> 下面的 EXPIRE 不执行
    # raise Exception("模拟进程崩溃")

    # 第2步：设过期
    r.expire(lock_key, expire)
    print(f"  [成功] 拿到锁，过期 {expire}s")
    return True

if __name__ == "__main__":
    print("=== 分布式锁 v1: SETNX + EXPIRE (有坑) ===")
    lock_key = "demo:lock:v1"
    bad_lock(lock_key)
    print(f" TTL: {r.ttl(lock_key)}")

    # 如果中间挂了，TTL 会是 -1(永不过期) -> 死锁
    r.delete(lock_key)
    print("[OK] 已清理")
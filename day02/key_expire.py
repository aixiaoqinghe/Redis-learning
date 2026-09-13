"""
Redis Key 过期管理 + 内存淘汰策略查看
环境： 本地 Redis (localhost:6379, db=0)
依赖：pip install redis
"""

import redis
import time

try:
    r = redis.Redis(
        host = "localhost",
        port = 6379,
        db = 0,
        decode_responses = True,
        socket_connect_timeout = 3,
    )
    r.ping()        # 发个ping,测试能不能连上
    print("[OK] Redis 连接成功\n")
except redis.ConnectionError as e:
    print(f"[ERROR] Redis 连接失败：{e}")
    raise SystemExit(1)   # 退出程序

def demo_expire():
    """Key 过期管理： SETEX / EXPIRE / TTL / PERSIST"""
    print("=" * 45)

    # 1. SETEX = SET + EXPIRE: 设值 + 过期时间，原子操作
    # 业务操作：缓存验证码， 5分钟过期
    r.setex("demo:code:1001", 5, "8888")
    print(f"SETEX后TTL:{r.ttl('demo:code:1001')}秒")   # 返回5

    # 2. EXPIRE: 给已存在的key加过期
    # 业务场景：用户登录后，给session续期
    # 先存一个值（不带过期）
    r.set("demo:session:1001", "token_abc")
    # 再给它加过期时间
    r.expire("demo:session:1001", 60)
    print(f"EXPIRE 后 TTL:{r.ttl('demo:session:1001')}秒")  # 返回60

    # 3. TTL 的三种返回值
    # 正数 = 剩余秒数， -1 = 永不过期， -2 = key不存在
    # 存一个永不过期的 key
    r.set("demo:permanent", "never_expire")
    print(f"永不过期的 key TTL: {r.ttl('demo:permanent')}")   # -1
    print(f"不存在的 key TTL: {r.ttl('demo:not_exist')}")     # -2

    # 4. REPSIST: 去掉过期时间，变永久
    r.persist("demo:session:1001")
    # 之前这个key是60秒过期，persist之后，变成永不过期
    print(f"PERSIST 后 TTL: {r.ttl('demo:session:1001')}")    # -1

    # 5.等key真正过期
    print("等待6秒，观察demo:code:1001是否过期...")
    time.sleep(6)
    print(f"6 秒后 demo:code:1001: {r.get('demo:code:1001')}")  # None（已过期）
    print(f"6 秒后 TTL: {r.ttl('demo:code:1001')}")             # -2（不存在了）

    r.delete("demo:code:1001", "demo:session:1001", "demo:permanent")

def demo_eviction_policy():
    """查看内存淘汰策略和内存上限"""
    print("=" * 45)

    # 当前淘汰策略(默认noeviction)
    # config_get() 读取Redis配置
    policy = r.config_get("maxmemory-policy")
    print(f"当前淘汰策略：{policy['maxmemory-policy']}")

    # 内存上限（默认0，表示不限制，物理内存用完为止）
    maxmem = r.config_get("maxmemory")
    print(f"内存上限:{maxmem['maxmemory']} 字节 （0 = 不限制）")

    # 已用内存
    info = r.info("memory")
    print(f"已用内存：{info['used_memory_human']}")

if __name__ == "__main__":
    demo_expire()
    demo_eviction_policy()
    print("=" * 45)
    print("[OK] Day2 演示完毕，测试数据已清理")
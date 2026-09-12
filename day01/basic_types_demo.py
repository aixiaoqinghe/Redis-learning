"""
Redis 5种基本数据类型演示
环境：本地 Redis (localhost:6379, db=0)
依赖: pip install redis
"""

import redis

# ---------- 连接配置 ----------
# decode_responses = True: 让返回值是str而不是bytes,方便阅读
# socket_connect_timeout: 避免连不上时卡死,默认5秒
try:
    r = redis.Redis(
        host = 'localhost',
        port = 6379,
        db = 0,
        decode_responses = True,
        socket_connect_timeout = 3
    )
    r.ping()   # 主动探测，连不上会立刻抛异常
    print("[OK] Redis 连接成功\n")
except redis.ConnectionError as e:
    print(f"[ERROR] Redis 连接失败：{e}")
    print("请检查: 1) redis-server 是否启动 2) 端口 6379 是否被占用")
    raise SystemExit(1)

def demo_string():
    """String:最基础类型，适合计数器、缓存单值、分布式锁的value"""
    key = "demo:user:1001:name"
    r.set(key, "Alice")                 # 写入
    print("String读取：", r.get(key))   # 读取

    # 业务场景：文章阅读量自增
    view_key = "demo:article:2001:views"
    r.set(view_key, 0)
    r.incr(view_key)            # +1
    r.incrby(view_key, 10)      # +10
    print("String 计数器:", r.get(view_key))

    r.delete(key, view_key)     # 清理

def demo_hash():
    """Hash:适合存对象（如用户信息、订单详情），可单独更新某字段"""
    key = "demo:user:1001"
    r.hset(key, mapping={"name": "Alice", "age": 20, "city": "Beijing"})    # 批量写入

    print("Hash 读取 name:", r.hget(key, "name"))   # 读单字段
    print("Hash 读取全部：", r.hgetall(key))        # 读全部

    # 业务场景：只更新年龄，不用重写整个对象
    r.hset(key, "age", 21)
    print("Hash 更新后 age:", r.hget(key, "age"))

    r.delete(key)

def demo_list():
    """List:有序可重复，适合消息队列、最新动态列表、栈/队列"""
    key = "demo:msg:queue"
    r.rpush(key, "msg1", "msg2", "msg3")       # 从右侧入队
    print("List 全部：", r.lrange(key, 0, -1))

    # 业务场景：模拟队列消费（左侧出队 = FIFO）
    msg = r.lpop(key)
    print("List 出队：", msg)
    print("List 剩余：", r.lrange(key, 0, -1))

    r.delete(key)

def demo_set():
    """Set:无序不重复，适合去重、标签、共同好友、抽奖"""
    key = "demo:article:3001:tags"
    r.sadd(key, "python", "redis", "backend", "python")   # 重复的 python 只会存一个
    print("Set 全部：", r.smembers(key))
    print("Set 是否含 redis:", r.sismember(key, "redis"))

    # 业务场景：两个用户的共同关注
    a_key, b_key = "demo:user:A:follow", "demo:user:B:follow"
    r.sadd(a_key, "u1", "u2", "u3")
    r.sadd(b_key, "u2", "u3", "u4")
    print("Set 交集（共同关注）：", r.sinter(a_key, b_key))

    r.delete(key, a_key, b_key)

def demo_zset():
    """ZSet: 有序不重复，按score排序，适合排行榜、延时队列"""
    key = "demo:rank:game"
    r.zadd(key, {"Alice": 95, "Bob": 88, "Cindy": 99})    # 写入带分数
    # 业务场景：排行榜按分数从高到低
    print("ZSet Top3:", r.zrevrange(key, 0, 2, withscores=True))
    print("ZSet Alice 排名：", r.zrevrank(key, "Alice"))    # 0 表示第一名

    r.delete(key)

if __name__ == "__main__":
    print("=" * 40)
    demo_string()
    print("=" * 40)
    demo_hash()
    print("=" * 40)
    demo_list()
    print("=" * 40)
    demo_set()
    print("=" * 40)
    demo_zset()
    print("=" * 40)
    print("\n[OK] 5 种类型演示完毕，测试数据已清理")


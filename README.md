# Redis Learning

阶段2：Redis 深度学习 —— 5 天实战代码记录。

## 阶段2 学了什么

| 主题 | 具体内容 |
|------|---------|
| 五大数据结构业务场景 | String(计数器/分布式锁value)、Hash(对象存储)、List(消息队列)、Set(去重/共同关注)、ZSet(排行榜/延时队列) |
| Key 过期与内存淘汰 | SETEX / EXPIRE / TTL / PERSIST 过期管理；maxmemory-policy 淘汰策略查看 |
| RDB / AOF 持久化 | save 触发规则、BGSAVE 手动快照、appendfsync 刷盘策略、RDB 文件检查 |
| 缓存三大问题 | 穿透（缓存空值）、击穿（互斥锁 SET NX EX）、雪崩（TTL 随机打散） |
| 缓存一致性 | Cache Aside 模式 + 延迟双删 |
| 分布式锁完整演进 | v1 两步死锁 → v2 SET NX EX 原子 → v3 Lua 安全释放(防误删) → v4 看门狗续期(防超时) |

## 每天的代码索引

### Day 1 —— 五大数据结构业务演示

| 文件 | 内容 |
|------|------|
| `day01/basic_types_demo.py` | String 计数器、Hash 对象存储、List 消息队列、Set 共同关注、ZSet 排行榜 |

### Day 2 —— Key 过期 + 内存淘汰

| 文件 | 内容 |
|------|------|
| `day02/key_expire.py` | SETEX / EXPIRE / TTL / PERSIST 过期管理；查看 maxmemory-policy 和已用内存 |

### Day 3 —— 持久化 RDB / AOF

| 文件 | 内容 |
|------|------|
| `day03/persistence_demo.py` | 查看 RDB save 规则、AOF appendonly / appendfsync 配置、手动触发 BGSAVE、检查 dump.rdb |

### Day 4 —— 缓存三大问题 + 一致性

| 文件 | 内容 |
|------|------|
| `day04/penetration.py` | 缓存穿透：缓存空值（NULL_FLAG + 短过期） |
| `day04/breakdown.py` | 缓存击穿：互斥锁 SET NX EX + 等待重试 |
| `day04/avalanche.py` | 缓存雪崩：基础 TTL + 随机偏移打散过期时间 |
| `day05/consistency.py` | 缓存一致性：Cache Aside + 延迟双删 |

### Day 5 —— 分布式锁完整 Demo

| 文件 | 内容 | 问题 / 亮点 |
|------|------|------------|
| `day05/lock_v1_bad.py` | SETNX + EXPIRE | ⚠️ 两步非原子，进程挂了 → 死锁 |
| `day05/lock_v2_correct.py` | SET NX EX | ✅ 一条命令原子抢锁 + 设过期 |
| `day05/lock_v3_lua.py` | Lua 脚本安全释放 | ✅ 校验 value，防止 A 误删 B 的锁 |
| `day05/lock_v4_watchdog.py` | 看门狗续期 | ✅ 后台守护线程，业务没结束就自动续期 |

## 相关项目

学完 Redis 阶段2 后做的订单系统实战项目（包含 Redis 在真实业务中的使用）：

👉 [order-system](https://github.com/aixiaoqinghe/order-system)

## 环境

- Python 3
- redis-py (`pip install redis`)
- 本地 Redis 服务 (localhost:6379)
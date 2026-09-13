"""
Redis 持久化配置查看 + 手动触发 RDB
环境： 本地 Redis (localhost:6379, db=0), Windows移植版
依赖： pip install redis
"""

import os
import redis

try:
    r = redis.Redis(
        host = "localhost",
        port = 6379,
        db = 0,
        decode_responses = True,
        socket_connect_timeout = 3
    )
    r.ping()
    print("[OK] Redis 连接成功\n")
except redis.ConnectionError as e:
    print(f"[ERROR] Redis 连接失败: {e}")
    raise SystemExit(1)

def show_rdb_config():
    """查看RDB自动触发规则"""
    print("=" * 45)
    # save 格式：“900 1 300 10 60 10000”
    # 含义：900秒内1个key变化 / 300秒内10个 / 60秒内10000个 -> 触发 BGSAVE
    save_cfg = r.config_get("save")
    # save 就是 RDB 的自动触发条件
    # config_get查Redis配置项，返回字典
    print(f"RDB 自动触发规则 save: {save_cfg.get('save', '(空)')}")
    # 空字符串表示自动 RDB 关闭， 只能手动触发

def show_aof_config():
    """查看AOF相关配置"""
    print("=" * 45)
    appendonly = r.config_get("appendonly")
    # appendonly 查看 AOF 是否开启
    print(f"AOF 是否开启 appendonly: {appendonly['appendonly']}")

    # everysec = 每秒刷盘（默认，最多丢1秒）/ always = 每条刷 / no = 交给OS
    # appendfsync 刷盘策略（多久把日志写到硬盘一次）
    appendfsync = r.config_get("appendfsync")
    print(f"AOF 刷盘策略 appendfsync: {appendfsync['appendfsync']}")

def trigger_bgsave():
    """手动触发 RDB 快照"""
    print("=" * 45)
    # 先写点数据，确保有内容可持久化
    r.set("demo:persist:key1", "value1")

    try:
        # BGSAVE(Background Save): 后台生成 RDB
        # Windows坑：Windows移植版没有真正的fork
        # BGSAVE 行为与 linux 不同，可能阻塞主进程或表现异常
        # 生产环境都是 Linux, 面试按Linux处理
        result = r.bgsave()   # 触发 RDB 快照 <=> 对应 Linux 上的 fork() 机制
        print(f"BGSAVE 返回: {result}")   # True 表示触发成功
    except redis.ResponseError as e:
        # Windows 上可能直接报错（不支持 fork）
        print(f"BGSAVE 失败 (Windows 不支持 fork): {e}")

def check_rdb_file():
    """检查 dump.rdb 文件是否生成"""
    print("=" * 45)
    # 查看 Redis 的工作目录
    dir_cfg = r.config_get("dir")
    work_dir = dir_cfg["dir"]
    print(f"Redis 工作目录 dir: {work_dir}")

    # 查看 RDB 文件名，默认 dump.rdb
    dbfilename = r.config_get("dbfilename")
    rdb_name = dbfilename["dbfilename"]
    print(f"RDB 文件名 dbfilename: {rdb_name}")

    # 拼接完整路径并检查是否存在
    rdb_path = os.path.join(work_dir, rdb_name)
    if os.path.exists(rdb_path):
        size = os.path.getsize(rdb_path)
        print(f"[OK] RDB 文件存在：{rdb_path} ({size}字节)")
    else:
        print(f"[WARN] RDB 文件不存在: {rdb_path}")

def cleanup():
    """清理测试数据"""
    r.delete("demo:persist:key1")

if __name__ == "__main__":
    show_rdb_config()
    show_aof_config()
    trigger_bgsave()
    check_rdb_file()
    cleanup()
    print("=" * 45)
    print("[OK] Day3 持久化演示完毕，测试数据已清理")

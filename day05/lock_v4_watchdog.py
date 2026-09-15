"""
分布式锁 v4:加看门狗续期
解决：业务执行时间 > 锁过期时间 -> 锁提前释放 -> 并发问题
思路：后台线程定期给锁续期，业务没结束就一直续
"""

import redis
import uuid
import time
import threading

r = redis.Redis(host="localhost", port=6379, db=0,
                decode_responses=True, socket_connect_timeout=3)

UNLOCK_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

# 锁的生命周期：抢到锁 -> 看门狗启动 -> 业务跑 -> 看门狗自动续期（业务没结束就一直续） -> 业务结束 -> 停看门狗 -> lua 释放锁

class WatchdogLock:
    """带看门狗的分布式锁"""
    def __init__(self, lock_key, expire = 10):
        self.lock_key = lock_key
        self.expire = expire       # 锁的基础过期时间
        self.value = str(uuid.uuid4())   # 唯一标识
        self.stop_event = threading.Event()   # 通知后台线程停止
        self.watchdog_thread = None

    def acquire(self):
        """抢锁：SET NX EX"""
        got = r.set(self.lock_key, self.value, nx=True, ex=self.expire)
        if got:
            print(f"  [抢锁成功] value={self.value[:8]}...，过期 {self.expire}s")
            self._start_watchdog()
            return True
        print("  [抢锁失败] 锁已被占用")
        return False

    def _start_watchdog(self):
        """启动后台续期线程"""
        self.watchdog_thread = threading.Thread(
            target = self._renew_loop, 
            daemon = True
        )
        # daemon = True 守护线程————如果主程序崩了/退出了，守护线程自动跟着死，不会一直挂再后台续期（不然主程序没了锁还续着，成死锁了）
        self.watchdog_thread.start()
        print("  [看门狗] 已启动")

    def _renew_loop(self):
        """后台循环：每 expire/3 秒续期一次"""
        interval = self.expire / 3
        while not self.stop_event.is_set():
            time.sleep(interval)
            # 只有还是自己的锁才续
            current = r.get(self.lock_key)
            if current == self.value:
                r.expire(self.lock_key, self.expire)
                print(f"  [看门狗] 续期到 {self.expire}s")
            else:
                # 锁已经不是自己的了，停止续期
                print("  [看门狗] 锁已不属于自己，停止续期")
                break

    def release(self):
        """释放锁：先停看门狗，再 Lua 删除"""
        self.stop_event.set()    # 通知后台线程停止
        if self.watchdog_thread:
            self.watchdog_thread.join(timeout=1)
        result = r.eval(UNLOCK_LUA, 1, self.lock_key, self.value)
        if result:
            print("  [释放成功] Lua 校验通过，锁已删")
        else:
            print("  [释放失败] 锁不是自己的")

def simulate_long_task():
    """模拟业务执行时间 > 锁过期时间"""
    print("\n=== 看门狗演示：业务执行 7s，锁只设 3s ===")
    lock = WatchdogLock("demo:lock:watchdog", expire=3)

    if not lock.acquire():
        return

    print("  业务开始执行（模拟 7s）...")
    for i in range(7):
        time.sleep(1)
        # 每秒钟看一眼锁还在不在
        ttl = r.ttl("demo:lock:watchdog")
        print(f"    第{i+1}s，锁剩余 TTL = {ttl}s")

    lock.release()
    print("[OK] 演示完毕")

if __name__ == "__main__":
    simulate_long_task()
    r.delete("demo:lock:watchdog")
    print("已清理")

# 把看门狗想象成一个“保姆线程”
# 三个关键动作：定时续、校验归属、优雅停
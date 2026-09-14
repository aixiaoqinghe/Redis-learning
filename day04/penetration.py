"""
缓存穿透解决方案：缓存空值
问题：查不存在的数据，缓存和 DB 都没有 -> 每次都打 DB
方案：查 DB 没有，也往缓存写null(短过期)，下次直接命中
"""
import redis

r = redis.Redis(
    host='localhost', 
    port=6379, 
    db = 0,
    decode_responses = True,
    socket_connect_timeout = 3
)

# 用特殊标记表示“空值”，避免和真实数据混淆
NULL_FLAG = "__NULL__"


def get_from_db(product_id):
    """模拟 DB 查询：id 不存在返回 None"""
    fake_db = {"1001": "iPhone", "1002": "iPad"}
    # 用假字典 fake_db 模拟 DB
    return fake_db.get(str(product_id))

def get_product(product_id):
    """带缓存空值保护的查询"""
    cache_key = f"demo:product:{product_id}"

    # 1.先查缓存
    cached = r.get(cache_key)
    if cached == NULL_FLAG:    # 分支1：命中空值标记 -> 直接返回None,不打 DB
        # 命中空值标记 -> 直接返回None,不打DB
        print(f"[缓存命中空值] {product_id} 不存在")
        return None
    if cached is not None:     # 分支2：命中真实数据 -> 直接返回
        print(f"[缓存命中] {product_id} = {cached}")
        return cached
    # 分支3： cached是None -> 缓存没命中(key不存在)，继续查 DB

    # 2.缓存没有，查 DB
    db_value = get_from_db(product_id)

    if db_value is None:
        # 3. DB 也没有 -> 缓存空值，设短过期（防大量不同 key 撑爆缓存）
        r.setex(cache_key, 60, NULL_FLAG)
        print(f"[查 DB 无] {product_id}, 已缓存空值 60s")
        return None

    # 4. DB 有 -> 正常缓存
    r.setex(cache_key, 300, db_value)
    print(f"[查 DB 有] {product_id} = {db_value}, 已缓存 300s")
    return db_value 

if __name__ == "__main__":
    print("=== 缓存穿透：缓存空值 ===")
    print("第1次查 9999（不存在）:")
    get_product(9999)
    print("第2次查 9999（应命中空值，不打 DB）")
    get_product(9999)

    # 清理
    r.delete("demo:product:1001", "demo:product:1002")
    print("[OK] 已清理")
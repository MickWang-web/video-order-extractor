"""
数据去重模块
"""


def deduplicate_orders(orders: list[dict]) -> list[dict]:
    """
    去重：同一订单号可能出现多次（在多帧中），只保留信息最完整的那条

    Args:
        orders: 原始订单列表（含重复）

    Returns:
        去重后的订单列表，按时间倒序排列
    """
    seen = {}

    for o in orders:
        oid = str(o.get("order_id", "")).replace(" ", "").strip()
        if not oid or len(oid) < 10:
            continue

        if oid in seen:
            existing = seen[oid]
            existing_score = sum(1 for v in existing.values() if v is not None and v != "" and v != 0)
            new_score = sum(1 for k, v in o.items() if v is not None and v != "" and v != 0)
            if new_score > existing_score:
                seen[oid] = o
        else:
            seen[oid] = o

    deduped = list(seen.values())
    deduped.sort(key=lambda x: x.get("datetime", ""), reverse=True)

    return deduped

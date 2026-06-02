"""
数据汇总模块
"""

from collections import defaultdict
from typing import Optional


def generate_summary(orders: list[dict]) -> dict:
    """
    生成汇总统计

    Args:
        orders: 订单列表

    Returns:
        汇总统计字典
    """
    completed = [o for o in orders if o.get("status") == "已完成"]
    refunded = [o for o in orders if o.get("status") == "已退款"]
    qyk_orders = [o for o in orders if "亲友卡" in (o.get("tags", ""))]

    completed_amount = sum(float(o.get("amount", 0)) for o in completed)
    refund_amount = sum(float(o.get("amount", 0)) for o in refunded)
    qyk_amount = sum(float(o.get("amount", 0)) for o in qyk_orders if o.get("status") == "已完成")

    monthly = defaultdict(lambda: {
        "count": 0, "completed": 0, "refund": 0,
        "completed_amount": 0.0, "refund_amount": 0.0
    })

    for o in orders:
        month = o.get("datetime", "")[:7]
        if not month or len(month) < 7:
            continue
        monthly[month]["count"] += 1
        if o.get("status") == "已完成":
            monthly[month]["completed"] += 1
            monthly[month]["completed_amount"] += float(o.get("amount", 0))
        elif o.get("status") == "已退款":
            monthly[month]["refund"] += 1
            monthly[month]["refund_amount"] += float(o.get("amount", 0))

    monthly_summary = {}
    for month, data in sorted(monthly.items(), reverse=True):
        monthly_summary[month] = {
            "count": data["count"],
            "completed": data["completed"],
            "refund": data["refund"],
            "completed_amount": round(data["completed_amount"], 2),
            "refund_amount": round(data["refund_amount"], 2),
            "net_amount": round(data["completed_amount"] + data["refund_amount"], 2)
        }

    return {
        "total_orders": len(orders),
        "completed_count": len(completed),
        "refund_count": len(refunded),
        "completed_amount": round(completed_amount, 2),
        "refund_amount": round(refund_amount, 2),
        "net_amount": round(completed_amount + refund_amount, 2),
        "qyk_count": len(qyk_orders),
        "qyk_completed_amount": round(qyk_amount, 2),
        "monthly_summary": monthly_summary
    }

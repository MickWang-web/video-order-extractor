#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试日期过滤逻辑"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

# 复制 MainWindow._parse_date 方法用于测试
def parse_date(date_str):
    """解析日期字符串，支持多种格式"""
    if not date_str:
        return None
    formats = [
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y.%m.%d'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

# 创建应用实例（不显示窗口）
from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)
from gui_app import MainWindow
window = MainWindow()

# 模拟一些测试订单数据
test_orders = [
    {
        'order_id': '1001',
        'status': '已完成',
        'datetime': '2026/04/15 10:30:00',
        'amount': 100.00,
        'tags': ''
    },
    {
        'order_id': '1002',
        'status': '已完成',
        'datetime': '2026/05/10 14:20:00',
        'amount': 200.00,
        'tags': ''
    },
    {
        'order_id': '1003',
        'status': '已退款',
        'datetime': '2026/05/20 09:15:00',
        'amount': -50.00,
        'tags': ''
    },
    {
        'order_id': '1004',
        'status': '已完成',
        'datetime': '2026/05/28 16:45:00',
        'amount': 150.00,
        'tags': '亲友卡'
    },
]

print("=" * 60)
print("测试订单数据:")
for order in test_orders:
    print(f"  {order['order_id']}: {order['datetime']} - ¥{order['amount']}")

# 加载测试数据
window.orders = test_orders
summary = window._calculate_summary(test_orders)

print("\n原始汇总统计:")
print(f"  总订单数: {summary['total_orders']}")
print(f"  已完成金额: ¥{summary['completed_amount']}")
print(f"  退款金额: ¥{summary['refund_amount']}")
print(f"  净消费: ¥{summary['net_amount']}")
print(f"  月度汇总: {list(summary['monthly_summary'].keys())}")

# 测试解析日期
print("\n" + "=" * 60)
print("测试日期解析:")
test_dates = [
    '2026/05/01',
    '2026/05/30',
    '2026/04/15 10:30:00',
    '2026/05/10 14:20:00',
]

for date_str in test_dates:
    parsed = parse_date(date_str)
    print(f"  '{date_str}' -> {parsed}")

# 模拟日期过滤: 2026/05/01 - 2026/05/30
print("\n" + "=" * 60)
print("模拟日期过滤: 2026/05/01 - 2026/05/30")

# 设置过滤参数
window.filter_widget.date_start.setText('2026/05/01')
window.filter_widget.date_end.setText('2026/05/30')

# 获取过滤参数
filter_params = window.filter_widget.get_filter()
print(f"过滤参数: {filter_params}")

# 执行过滤
filtered = test_orders.copy()
if filter_params['date_start']:
    start_date = parse_date(filter_params['date_start'])
    if start_date:
        print(f"\n开始日期解析: '{filter_params['date_start']}' -> {start_date}")
        before_count = len(filtered)
        filtered = [o for o in filtered if parse_date(o.get('datetime', '')) is not None and parse_date(o.get('datetime', '')) >= start_date]
        print(f"开始日期过滤: {before_count} -> {len(filtered)} 条订单")

if filter_params['date_end']:
    end_date = parse_date(filter_params['date_end'])
    if end_date:
        original_end_date = end_date
        end_date = end_date + timedelta(days=1) - timedelta(seconds=1)
        print(f"\n结束日期解析: '{filter_params['date_end']}' -> {original_end_date} -> {end_date}")
        before_count = len(filtered)
        filtered = [o for o in filtered if parse_date(o.get('datetime', '')) is not None and parse_date(o.get('datetime', '')) <= end_date]
        print(f"结束日期过滤: {before_count} -> {len(filtered)} 条订单")

print("\n过滤后的订单:")
for order in filtered:
    print(f"  {order['order_id']}: {order['datetime']} - ¥{order['amount']}")

# 计算过滤后的汇总
filtered_summary = window._calculate_summary(filtered)
print("\n过滤后汇总统计:")
print(f"  总订单数: {filtered_summary['total_orders']}")
print(f"  已完成金额: ¥{filtered_summary['completed_amount']}")
print(f"  退款金额: ¥{filtered_summary['refund_amount']}")
print(f"  净消费: ¥{filtered_summary['net_amount']}")
print(f"  月度汇总: {list(filtered_summary['monthly_summary'].keys())}")

if filtered_summary['monthly_summary']:
    print("\n月度详情:")
    for month, data in filtered_summary['monthly_summary'].items():
        print(f"  {month}:")
        print(f"    订单数: {data['count']}")
        print(f"    已完成: {data['completed']}, 金额: ¥{data['completed_amount']}")
        print(f"    退款: {data['refund']}, 金额: ¥{data['refund_amount']}")
        print(f"    净消费: ¥{data['net_amount']}")

print("\n" + "=" * 60)

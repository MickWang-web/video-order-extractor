#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试图表更新逻辑"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt
from gui_app import DashboardView

app = QApplication(sys.argv)

# 创建看板视图
dashboard = DashboardView()

# 模拟过滤后的汇总数据（5月份）
filtered_summary = {
    'total_orders': 3,
    'completed_count': 2,
    'refund_count': 1,
    'completed_amount': 350.0,
    'refund_amount': -50.0,
    'net_amount': 300.0,
    'qyk_count': 1,
    'qyk_completed_amount': 150.0,
    'monthly_summary': {
        '2026/05': {
            'count': 3,
            'completed': 2,
            'refund': 1,
            'completed_amount': 350.0,
            'refund_amount': -50.0,
            'net_amount': 300.0
        }
    }
}

print("=" * 60)
print("模拟图表更新")
print("=" * 60)
print(f"汇总数据: {filtered_summary}")
print(f"月度汇总: {filtered_summary['monthly_summary']}")

# 模拟日期过滤后的数据范围显示
date_range = "2026/05/01 - 2026/05/30"

print(f"\n调用 update_dashboard 方法...")
print(f"  date_range: {date_range}")

# 调用 update_dashboard
dashboard.update_dashboard(filtered_summary, date_range)

# 检查 date_range_label 是否正确更新
print(f"\n检查结果:")
print(f"  date_range_label 文本: {dashboard.date_range_label.text()}")

# 检查趋势图的月份数据
monthly = filtered_summary.get('monthly_summary', {})
months = sorted(monthly.keys())
print(f"  月份列表: {months}")
print(f"  月份数量: {len(months)}")

if months:
    print(f"\n  各月份数据:")
    for month in months:
        data = monthly[month]
        print(f"    {month}:")
        print(f"      已完成金额: ¥{data['completed_amount']}")
        print(f"      退款金额: ¥{data['refund_amount']}")
        print(f"      净消费: ¥{data['net_amount']}")
else:
    print("\n  警告: 没有月份数据!")

print("\n" + "=" * 60)
print("测试完成")

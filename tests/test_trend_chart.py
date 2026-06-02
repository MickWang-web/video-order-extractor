#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""详细测试 update_trend_chart 方法"""
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
monthly = {
    '2026/05': {
        'count': 3,
        'completed': 2,
        'refund': 1,
        'completed_amount': 350.0,
        'refund_amount': -50.0,
        'net_amount': 300.0
    }
}

months = sorted(monthly.keys())

print("=" * 60)
print("详细测试 update_trend_chart")
print("=" * 60)
print(f"monthly: {monthly}")
print(f"months: {months}")
print(f"月份数量: {len(months)}")

if months:
    print("\n检查月份数据:")
    for month in months:
        data = monthly[month]
        print(f"\n{month}:")
        print(f"  completed_amount: {data['completed_amount']} (类型: {type(data['completed_amount']).__name__})")
        print(f"  refund_amount: {data['refund_amount']} (类型: {type(data['refund_amount']).__name__})")
        print(f"  net_amount: {data['net_amount']} (类型: {type(data['net_amount']).__name__})")
        
        # 测试计算
        print(f"  abs(refund_amount): {abs(data['refund_amount'])}")
        
        # 计算Y轴最大值
        max_amount = max(
            max([monthly[m]['completed_amount'] for m in months]) if months else 0,
            max([abs(monthly[m]['net_amount']) for m in months]) if months else 0
        )
        print(f"\nY轴最大值计算:")
        print(f"  max(completed_amount): {max([monthly[m]['completed_amount'] for m in months])}")
        print(f"  max(abs(net_amount)): {max([abs(monthly[m]['net_amount']) for m in months])}")
        print(f"  max_amount: {max_amount}")
        print(f"  top (max * 1.2): {max_amount * 1.2 if max_amount > 0 else 1000}")

print("\n" + "=" * 60)
print("调用 update_trend_chart...")
print("=" * 60)

try:
    dashboard.update_trend_chart(monthly, months)
    print("✓ update_trend_chart 调用成功，没有异常")
    
    # 检查图表是否创建
    chart_view = dashboard.trend_chart_view.findChild(
        __import__('PyQt5.QtChart', fromlist=['QChartView']).QChartView
    )
    if chart_view:
        chart = chart_view.chart()
        if chart:
            print(f"✓ 图表已创建")
            print(f"  系列数量: {len(chart.series())}")
            for series in chart.series():
                print(f"    - {series.name()}: {series.count()} 个数据点")
        else:
            print("✗ 图表未创建")
    else:
        print("✗ 未找到 chart_view")
        
except Exception as e:
    print(f"✗ update_trend_chart 调用失败:")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试真实订单数据格式"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from gui_app import MainWindow

app = QApplication(sys.argv)
window = MainWindow()

# 尝试读取一个真实的订单数据文件
import glob
json_files = glob.glob("*.json")
xlsx_files = glob.glob("*.xlsx")

print("=" * 60)
print("查找订单数据文件")
print("=" * 60)

sample_orders = None

if json_files:
    print(f"找到 JSON 文件: {json_files}")
    import json
    with open(json_files[0], 'r', encoding='utf-8') as f:
        data = json.load(f)
        if 'data' in data:
            data = data['data']
        sample_orders = data.get('orders', [])
        
elif xlsx_files:
    print(f"找到 Excel 文件: {xlsx_files}")
    import openpyxl
    wb = openpyxl.load_workbook(xlsx_files[0])
    ws = wb.active
    sample_orders = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            break
        try:
            order = {
                'order_id': str(row[1]) if row[1] else '',
                'status': str(row[2]) if row[2] else '',
                'datetime': str(row[3]) if row[3] else '',
                'amount': float(row[4]) if row[4] else 0.0,
                'tags': str(row[5]) if row[5] else ''
            }
            sample_orders.append(order)
        except (ValueError, TypeError, IndexError):
            continue

if sample_orders:
    print(f"\n找到 {len(sample_orders)} 条订单")
    print("\n前5条订单的 datetime 字段:")
    for i, order in enumerate(sample_orders[:5], 1):
        datetime_str = order.get('datetime', '')
        parsed = window._parse_date(datetime_str)
        print(f"  {i}. '{datetime_str}' -> {parsed}")
        
        # 尝试提取月份
        if parsed:
            month = parsed.strftime('%Y/%m')
            print(f"     月份: {month}")
        else:
            # 尝试使用旧方法提取
            month_old = datetime_str[:7]
            print(f"     旧方法月份: {month_old}")
    
    # 测试日期过滤
    print("\n" + "=" * 60)
    print("测试日期过滤: 2026/05/01 - 2026/05/30")
    print("=" * 60)
    
    window.orders = sample_orders
    summary_before = window._calculate_summary(sample_orders)
    
    print(f"\n过滤前:")
    print(f"  总订单数: {summary_before['total_orders']}")
    print(f"  月度汇总: {list(summary_before['monthly_summary'].keys())}")
    
    # 设置过滤参数
    window.filter_widget.date_start.setText('2026/05/01')
    window.filter_widget.date_end.setText('2026/05/30')
    
    # 手动执行过滤
    filtered = sample_orders.copy()
    from datetime import timedelta
    
    filter_params = window.filter_widget.get_filter()
    
    if filter_params['date_start']:
        start_date = window._parse_date(filter_params['date_start'])
        if start_date:
            before = len(filtered)
            filtered = [o for o in filtered 
                       if window._parse_date(o.get('datetime', '')) is not None 
                       and window._parse_date(o.get('datetime', '')) >= start_date]
            print(f"\n开始日期过滤: {before} -> {len(filtered)} 条")
            
            # 显示被过滤掉的订单
            removed = [o for o in sample_orders if o not in filtered]
            if removed[:3]:
                print("  被过滤掉的订单（前3条）:")
                for o in removed[:3]:
                    print(f"    {o.get('order_id')}: {o.get('datetime')}")
    
    if filter_params['date_end']:
        end_date = window._parse_date(filter_params['date_end'])
        if end_date:
            end_date = end_date + timedelta(days=1) - timedelta(seconds=1)
            before = len(filtered)
            filtered = [o for o in filtered 
                       if window._parse_date(o.get('datetime', '')) is not None 
                       and window._parse_date(o.get('datetime', '')) <= end_date]
            print(f"\n结束日期过滤: {before} -> {len(filtered)} 条")
    
    # 计算过滤后的汇总
    summary_after = window._calculate_summary(filtered)
    
    print(f"\n过滤后:")
    print(f"  总订单数: {summary_after['total_orders']}")
    print(f"  已完成金额: ¥{summary_after['completed_amount']}")
    print(f"  退款金额: ¥{summary_after['refund_amount']}")
    print(f"  净消费: ¥{summary_after['net_amount']}")
    print(f"  月度汇总: {list(summary_after['monthly_summary'].keys())}")
    
    if summary_after['monthly_summary']:
        print("\n月度详情:")
        for month, data in summary_after['monthly_summary'].items():
            print(f"  {month}:")
            print(f"    订单数: {data['count']}")
            print(f"    已完成: {data['completed']}, 金额: ¥{data['completed_amount']}")
            print(f"    退款: {data['refund']}, 金额: ¥{data['refund_amount']}")
            print(f"    净消费: ¥{data['net_amount']}")
else:
    print("未找到订单数据文件")
    
print("\n" + "=" * 60)

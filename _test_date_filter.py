"""
临时测试 - 验证日期范围过滤功能
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

import gui_app
window = gui_app.MainWindow()

print(f"总共 {len(window.orders)} 条订单")

# 模拟设置日期范围
filter_widget = window.filter_widget

# 设置日期范围: 2025/01/01 - 2025/12/31
filter_widget.date_start.setText("2025/01/01")
filter_widget.date_end.setText("2025/12/31")

print(f"date_start text: '{filter_widget.date_start.text()}'")
print(f"date_end text: '{filter_widget.date_end.text()}'")

# 获取 filter params
fp = filter_widget.get_filter()
print(f"filter params date_start: '{fp['date_start']}'")
print(f"filter params date_end: '{fp['date_end']}'")

# 手动调用 apply_filter
window.apply_filter()

# 检查过滤结果
from gui_app import OrderFilterWidget
from src.database import get_session
from src.services import ImportService

# 手动测试解析
print("\n--- 测试 _parse_date ---")
test_dates = ["2025/01/01", "2025/12/31", "2026/06/02"]
for d in test_dates:
    result = window._parse_date(d)
    print(f"  解析 '{d}' -> {result}")

# 测试订单日期解析
print("\n--- 测试订单日期解析 ---")
for i, order in enumerate(window.orders[:5]):
    dt_str = order.get('datetime', '')
    parsed = window._parse_date(dt_str)
    print(f"  订单 {i}: '{dt_str}' -> {parsed}")

# 检查过滤后的 orders 数量
print(f"\n过滤后 orders 数量: {len(window.orders_table._data) if hasattr(window.orders_table, '_data') else 'N/A'}")

# 尝试手动过滤
fp = filter_widget.get_filter()
filtered = window.orders.copy()
start_str = fp['date_start']
end_str = fp['date_end']

if start_str:
    start_date = window._parse_date(start_str)
    print(f"\n开始日期: {start_date}")
    if start_date:
        filtered = [o for o in filtered if window._parse_date(o.get('datetime', '')) is not None and window._parse_date(o.get('datetime', '')) >= start_date]
        print(f"  after start filter: {len(filtered)}")

if end_str:
    end_date = window._parse_date(end_str)
    print(f"结束日期: {end_date}")
    if end_date:
        from datetime import timedelta
        end_date_adj = end_date + timedelta(days=1) - timedelta(seconds=1)
        print(f"  adjusted end date: {end_date_adj}")
        filtered = [o for o in filtered if window._parse_date(o.get('datetime', '')) is not None and window._parse_date(o.get('datetime', '')) <= end_date_adj]
        print(f"  after end filter: {len(filtered)}")

print(f"\n最终过滤结果: {len(filtered)} 条订单")

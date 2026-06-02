"""
全面测试 GUI 交互功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QDate
app = QApplication(sys.argv)

import gui_app
window = gui_app.MainWindow()

print("=" * 60)
print("1. 检查数据库订单数量")
print("=" * 60)
print(f"   总订单数: {len(window.orders)}")
print(f"   summary 存在: {window.summary is not None}")
if window.summary:
    print(f"   total_orders: {window.summary.get('total_orders')}")
    print(f"   monthly 月份: {list(window.summary.get('monthly_summary', {}).keys())}")

print()
print("=" * 60)
print("2. 检查表格数据")
print("=" * 60)
print(f"   orders_table 行数: {window.orders_table.rowCount()}")
print(f"   products_table 行数: {window.products_table.rowCount()}")
print(f"   dashboard_view 存在: {window.dashboard_view is not None}")

print()
print("=" * 60)
print("3. 检查日期过滤 - 日期格式测试")
print("=" * 60)
fw = window.filter_widget
test_dates = ["2025/01/01", "2025-01-01", "2025.01.01", "2025/06/30"]
for d in test_dates:
    result = window._parse_date(d)
    print(f"   解析 '{d}' -> {result}")

print()
print("=" * 60)
print("4. 测试标签过滤")
print("=" * 60)
fw.tag_all.setChecked(False)
fw.tag_qyk.setChecked(True)
fp = fw.get_filter()
print(f"   tag filter: {fp['tag']}")

# 应用过滤
window.apply_filter()
print(f"   过滤后表格行数: {window.orders_table.rowCount()}")

# 重置
fw.tag_all.setChecked(True)
window.apply_filter()
print(f"   重置后表格行数: {window.orders_table.rowCount()}")

print()
print("=" * 60)
print("5. 测试金额过滤")
print("=" * 60)
fw.amount_min.setText("100")
fw.amount_max.setText("500")
window.apply_filter()
print(f"   金额 100-500 过滤后行数: {window.orders_table.rowCount()}")

fw.amount_min.setText("")
fw.amount_max.setText("")
window.apply_filter()
print(f"   清空金额后行数: {window.orders_table.rowCount()}")

print()
print("=" * 60)
print("6. 测试订单号搜索")
print("=" * 60)
fw.search_order_id.setText("5571")
window.apply_filter()
print(f"   搜索 '5571' 后行数: {window.orders_table.rowCount()}")

fw.search_order_id.setText("")
window.apply_filter()
print(f"   清空搜索后行数: {window.orders_table.rowCount()}")

print()
print("=" * 60)
print("7. 测试日期范围过滤")
print("=" * 60)
fw.date_start.setText("2025/01/01")
fw.date_end.setText("2025/12/31")
window.apply_filter()
print(f"   日期 2025/01/01-2025/12/31 过滤后行数: {window.orders_table.rowCount()}")

# 检查 dashboard 更新
dv = window.dashboard_view
print(f"   dashboard date_range_label: {dv.date_range_label.text()}")
print(f"   dashboard stats cards exist: {dv.stats_widget.layout().count()}")

print()
print("=" * 60)
print("8. 测试状态过滤")
print("=" * 60)
fw.status_all.setChecked(False)
fw.status_completed.setChecked(True)
window.apply_filter()
print(f"   仅已完成过滤后行数: {window.orders_table.rowCount()}")

fw.status_completed.setChecked(False)
fw.status_refunded.setChecked(True)
window.apply_filter()
print(f"   仅已退款过滤后行数: {window.orders_table.rowCount()}")

print()
print("=" * 60)
print("9. 测试重置功能")
print("=" * 60)
# 设置一些过滤条件
fw.date_start.setText("2025/01/01")
fw.amount_min.setText("100")
window.apply_filter()
before_reset = window.orders_table.rowCount()
print(f"   重置前行数: {before_reset}")

fw.on_reset()  # 调用重置
window.apply_filter()
after_reset = window.orders_table.rowCount()
print(f"   重置后行数: {after_reset}")
print(f"   date_start after reset: '{fw.date_start.text()}'")

print()
print("=" * 60)
print("10. 测试 dashboard 月度汇总")
print("=" * 60)
# 清空所有过滤
fw.on_reset()
window.apply_filter()
print(f"   所有订单: {window.orders_table.rowCount()}")
print(f"   dashboard monthly_summary: {list(window.summary.get('monthly_summary', {}).keys())}")

# 检查 trend_chart 是否有数据
trend_cv = window.dashboard_view.trend_chart_view.findChildren(__import__('PyQt5.QtChart', fromlist=['QChartView']).QChartView)[0] if window.dashboard_view.findChildren(__import__('PyQt5.QtChart', fromlist=['QChartView']).QChartView) else None
if trend_cv and trend_cv.chart():
    print(f"   trend chart series count: {len(trend_cv.chart().series())}")
else:
    print(f"   trend chart: not found or no chart set")

print()
print("=" * 60)
print("测试完成")
print("=" * 60)

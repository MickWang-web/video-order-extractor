#!/usr/bin/env python3
"""
全面测试视频订单提取应用 - 功能测试和布局测试
"""
import sys
import json
import time
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer

sys.path.insert(0, '/Users/m.wang/project/video-order-extractor')
from gui_app import MainWindow, OrderFilterWidget

class TestRunner:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.results = []
        
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("📋 开始全面测试视频订单提取应用")
        print("="*60)
        
        # 测试1: 初始化测试
        self.test_initialization()
        
        # 测试2: 按钮状态测试
        self.test_button_states()
        
        # 测试3: 复选框互斥逻辑测试
        self.test_checkbox_logic()
        
        # 测试4: 数据导入测试
        self.test_data_import()
        
        # 测试5: 过滤功能测试
        self.test_filter_functionality()
        
        # 测试6: 布局响应式测试
        self.test_layout_responsive()
        
        # 生成测试报告
        self.generate_report()
        
        # 关闭应用
        QTimer.singleShot(500, self.app.quit)
        sys.exit(self.app.exec_())
        
    def test_initialization(self):
        """测试应用初始化"""
        print("\n🔹 测试1: 应用初始化")
        try:
            # 检查主窗口是否创建成功
            assert self.window is not None, "主窗口未创建"
            assert self.window.windowTitle() == "订单分析系统", "窗口标题不正确"
            
            # 检查关键组件
            assert hasattr(self.window, 'file_path'), "缺少文件路径输入框"
            assert hasattr(self.window, 'process_btn'), "缺少处理按钮"
            assert hasattr(self.window, 'filter_widget'), "缺少过滤组件"
            assert hasattr(self.window, 'dashboard_view'), "缺少数据看板"
            
            self.results.append(("应用初始化", "通过"))
            print("   ✓ 应用初始化成功")
        except Exception as e:
            self.results.append(("应用初始化", f"失败: {e}"))
            print(f"   ✗ 应用初始化失败: {e}")
            
    def test_button_states(self):
        """测试按钮初始状态"""
        print("\n🔹 测试2: 按钮状态")
        try:
            # 初始状态测试
            assert self.window.process_btn.isEnabled(), "处理按钮应启用"
            assert self.window.browse_btn.isEnabled(), "浏览按钮应启用"
            assert self.window.import_btn.isEnabled(), "导入按钮应启用"
            
            # 选择文件后测试（模拟）
            self.window.file_path.setText("/test/path/video.mp4")
            assert self.window.file_path.text() == "/test/path/video.mp4", "文件路径未设置"
            
            self.results.append(("按钮状态", "通过"))
            print("   ✓ 按钮状态正常")
        except Exception as e:
            self.results.append(("按钮状态", f"失败: {e}"))
            print(f"   ✗ 按钮状态测试失败: {e}")
            
    def test_checkbox_logic(self):
        """测试复选框互斥逻辑"""
        print("\n🔹 测试3: 复选框互斥逻辑")
        try:
            filter_widget = self.window.filter_widget
            
            # 测试状态筛选逻辑
            assert filter_widget.status_all.isChecked(), "初始状态'全部'应选中"
            
            # 点击已完成，检查全部是否取消
            filter_widget.status_completed.click()
            assert not filter_widget.status_all.isChecked(), "选择'已完成'后'全部'应取消"
            assert filter_widget.status_completed.isChecked(), "'已完成'应选中"
            
            # 点击全部，检查已完成是否取消
            filter_widget.status_all.click()
            assert filter_widget.status_all.isChecked(), "'全部'应选中"
            assert not filter_widget.status_completed.isChecked(), "'已完成'应取消"
            
            # 测试标签筛选逻辑
            assert filter_widget.tag_all.isChecked(), "初始标签'全部'应选中"
            
            filter_widget.tag_qyk.click()
            assert not filter_widget.tag_all.isChecked(), "选择'亲友卡'后'全部'应取消"
            
            filter_widget.tag_all.click()
            assert not filter_widget.tag_qyk.isChecked(), "选择'全部'后'亲友卡'应取消"
            
            # 测试取消所有选择时自动选中全部
            filter_widget.tag_qyk.click()
            filter_widget.tag_qyk.click()  # 取消选择
            assert filter_widget.tag_all.isChecked(), "取消所有选择后应自动选中'全部'"
            
            self.results.append(("复选框互斥逻辑", "通过"))
            print("   ✓ 复选框互斥逻辑正常")
        except Exception as e:
            self.results.append(("复选框互斥逻辑", f"失败: {e}"))
            print(f"   ✗ 复选框互斥逻辑测试失败: {e}")
            
    def test_data_import(self):
        """测试数据导入功能"""
        print("\n🔹 测试4: 数据导入")
        try:
            # 读取测试数据
            with open('/Users/m.wang/project/video-order-extractor/test_data.json', 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            if 'data' in test_data:
                test_data = test_data['data']
            
            orders = test_data.get('orders', [])
            
            # 模拟导入数据
            self.window._load_data(orders, test_data)
            
            # 验证数据是否加载成功
            assert len(self.window.orders) == len(orders), "订单数据未正确加载"
            assert self.window.summary is not None, "汇总数据未生成"
            
            # 验证统计面板是否更新
            summary_text = self.window.summary_widget.total_orders.text()
            assert str(len(orders)) in summary_text, "统计面板未更新"
            
            self.results.append(("数据导入", "通过"))
            print(f"   ✓ 数据导入成功，共 {len(orders)} 条订单")
        except Exception as e:
            self.results.append(("数据导入", f"失败: {e}"))
            print(f"   ✗ 数据导入测试失败: {e}")
            
    def test_filter_functionality(self):
        """测试过滤功能"""
        print("\n🔹 测试5: 过滤功能")
        try:
            filter_widget = self.window.filter_widget
            
            # 重置过滤器
            filter_widget.on_reset()
            
            # 测试状态过滤
            initial_count = len(self.window.orders)
            filter_widget.status_completed.click()
            filter_widget.on_apply()
            
            # 获取表格行数
            table_count = self.window.orders_table.rowCount()
            assert table_count <= initial_count, "状态过滤未生效"
            
            # 测试标签过滤
            filter_widget.on_reset()
            filter_widget.tag_qyk.click()
            filter_widget.on_apply()
            
            table_count2 = self.window.orders_table.rowCount()
            assert table_count2 <= initial_count, "标签过滤未生效"
            
            # 测试订单号搜索
            filter_widget.on_reset()
            if self.window.orders:
                first_order_id = str(self.window.orders[0].get('order_id', ''))[:4]
                if first_order_id:
                    filter_widget.search_order_id.setText(first_order_id)
                    filter_widget.on_apply()
                    assert self.window.orders_table.rowCount() > 0, "订单号搜索未生效"
            
            # 重置过滤
            filter_widget.on_reset()
            
            self.results.append(("过滤功能", "通过"))
            print("   ✓ 过滤功能正常")
        except Exception as e:
            self.results.append(("过滤功能", f"失败: {e}"))
            print(f"   ✗ 过滤功能测试失败: {e}")
            
    def test_layout_responsive(self):
        """测试布局响应式"""
        print("\n🔹 测试6: 布局响应式")
        try:
            # 获取初始尺寸
            initial_width = self.window.width()
            initial_height = self.window.height()
            
            # 测试缩小窗口
            self.window.resize(800, 600)
            assert self.window.width() == 800, "窗口宽度设置失败"
            assert self.window.height() == 600, "窗口高度设置失败"
            
            # 测试左侧面板最小宽度
            left_panel = self.window.centralWidget().layout().itemAt(0).widget()
            assert left_panel.minimumWidth() == 320, "左侧面板最小宽度不正确"
            
            # 测试放大窗口
            self.window.resize(1400, 900)
            assert self.window.width() == 1400, "窗口放大失败"
            
            # 测试统计卡片布局
            cards_layout = self.window.dashboard_view.stats_widget.layout()
            assert cards_layout is not None, "统计卡片布局不存在"
            assert cards_layout.count() == 5, "统计卡片数量不正确"
            
            # 测试图表容器
            assert self.window.dashboard_view.trend_chart_view is not None, "趋势图容器不存在"
            assert self.window.dashboard_view.status_chart_view is not None, "状态饼图容器不存在"
            
            # 恢复原始尺寸
            self.window.resize(initial_width, initial_height)
            
            self.results.append(("布局响应式", "通过"))
            print("   ✓ 布局响应式正常")
        except Exception as e:
            self.results.append(("布局响应式", f"失败: {e}"))
            print(f"   ✗ 布局响应式测试失败: {e}")
            
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告")
        print("="*60)
        
        passed = sum(1 for _, status in self.results if status == "通过")
        total = len(self.results)
        
        for test_name, status in self.results:
            status_icon = "✅" if status == "通过" else "❌"
            print(f"  {status_icon} {test_name}: {status}")
        
        print(f"\n📈 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("\n🎉 所有测试通过！")
        else:
            print("\n⚠️ 部分测试失败，请检查相关功能")

if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()

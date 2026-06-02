#!/usr/bin/env python3
"""
全面测试视频订单提取应用 - 滚动条和布局压缩测试（修复版）
重点测试：
1. 左侧面板滚动条
2. 每个图表独立的滚动条
3. 窗口缩小时的布局压缩问题
4. 图表数据项较多时的显示问题
"""
import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QScrollArea
from PyQt5.QtCore import QTimer, Qt

sys.path.insert(0, '/Users/m.wang/project/video-order-extractor')
from gui_app import MainWindow


class ScrollLayoutTestRunner:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.window.show()
        self.results = []
        self.test_details = []
        
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*70)
        print("📋 滚动条和布局压缩测试（修复版）")
        print("="*70)
        
        # 测试1: 左侧面板滚动条测试
        print("\n" + "-"*70)
        print("🎯 测试1: 左侧面板滚动条")
        print("-"*70)
        self.test_left_panel_scroll()
        
        # 测试2: 每个图表独立的滚动条
        print("\n" + "-"*70)
        print("🎯 测试2: 每个图表独立的滚动条")
        print("-"*70)
        self.test_each_chart_has_scroll()
        
        # 测试3: 窗口缩小布局测试
        print("\n" + "-"*70)
        print("🎯 测试3: 窗口缩小布局测试")
        print("-"*70)
        self.test_window_resize_layout()
        
        # 测试4: 图表数据项较多测试
        print("\n" + "-"*70)
        print("🎯 测试4: 图表数据项较多测试")
        print("-"*70)
        self.test_chart_many_items()
        
        # 生成测试报告
        self.generate_report()
        
        # 关闭应用
        QTimer.singleShot(100, self.app.quit)
        sys.exit(self.app.exec_())
        
    def test_left_panel_scroll(self):
        """测试左侧面板滚动条"""
        print("\n🔹 测试1.1: 检查左侧面板滚动区域")
        try:
            # 查找左侧面板的滚动区域
            # 左侧滚动区域应该是在 centralWidget -> layout -> first widget (QScrollArea)
            central = self.window.centralWidget()
            layout = central.layout()
            
            # 左侧面板在布局中的位置
            left_scroll = None
            for i in range(layout.count()):
                item = layout.itemAt(i)
                widget = item.widget()
                if isinstance(widget, QScrollArea):
                    # 检查这个滚动区域是否是左侧面板
                    # 左侧面板滚动区域最小宽度应该是 340
                    if widget.minimumWidth() >= 340:
                        left_scroll = widget
                        break
            
            # 如果没找到，尝试直接查找子控件
            if left_scroll is None:
                for child in central.findChildren(QScrollArea):
                    if child.minimumWidth() >= 340:
                        left_scroll = child
                        break
            
            assert left_scroll is not None, "左侧面板缺少滚动区域"
            
            # 检查滚动区域属性
            widget_resizable = left_scroll.widgetResizable()
            print(f"   ℹ widgetResizable = {widget_resizable}")
            
            # widgetResizable 为 False 时，内容保持原始大小并启用滚动
            # widgetResizable 为 True 时，内容会自适应但可能无法滚动
            # 我们需要的是 False，这样内容保持原始大小
            assert not widget_resizable, \
                f"滚动区域应设置widgetResizable为False保持内容原始大小 (当前: {widget_resizable})"
            assert left_scroll.minimumWidth() >= 320, "滚动区域最小宽度不足"
            
            # 检查垂直滚动条策略
            v_policy = left_scroll.verticalScrollBarPolicy()
            assert v_policy in [Qt.ScrollBarAsNeeded, Qt.ScrollBarAlwaysOn], \
                "垂直滚动条策略不正确"
            
            self.results.append(("左侧面板滚动区域", "通过"))
            self.test_details.append(("左侧面板滚动区域", 
                f"滚动区域存在，widgetResizable={widget_resizable}保持内容原始大小"))
            print("   ✓ 左侧面板滚动区域检查通过")
            
        except Exception as e:
            self.results.append(("左侧面板滚动区域", f"失败: {e}"))
            self.test_details.append(("左侧面板滚动区域", f"失败: {str(e)}"))
            print(f"   ✗ 左侧面板滚动区域检查失败: {e}")
            
    def test_each_chart_has_scroll(self):
        """测试每个图表都有独立的滚动条"""
        print("\n🔹 测试2.1: 检查每个图表的独立滚动区域")
        try:
            # 切换到数据分析标签页
            self.window.tab_widget.setCurrentIndex(1)
            self.app.processEvents()
            
            # 检查每个图表滚动区域
            scroll_areas = {
                'trend_scroll': self.window.dashboard_view.trend_scroll,
                'status_scroll': self.window.dashboard_view.status_scroll,
                'bar_scroll': self.window.dashboard_view.bar_scroll,
                'pie_scroll': self.window.dashboard_view.pie_scroll,
            }
            
            for name, scroll in scroll_areas.items():
                assert scroll is not None, f"{name} 不存在"
                assert isinstance(scroll, QScrollArea), f"{name} 不是 QScrollArea"
                assert not scroll.widgetResizable(), \
                    f"{name} 应设置widgetResizable为False"
                
                # 检查滚动条策略
                h_policy = scroll.horizontalScrollBarPolicy()
                v_policy = scroll.verticalScrollBarPolicy()
                assert h_policy == Qt.ScrollBarAsNeeded, \
                    f"{name} 水平滚动条策略不正确"
                
                # 检查最小尺寸
                assert scroll.minimumHeight() >= 400, \
                    f"{name} 最小高度不足"
                
            self.results.append(("每个图表独立滚动条", "通过"))
            self.test_details.append(("每个图表独立滚动条", 
                "4个图表都有自己的QScrollArea，支持独立滚动"))
            print("   ✓ 每个图表独立滚动区域检查通过")
            
        except Exception as e:
            self.results.append(("每个图表独立滚动条", f"失败: {e}"))
            self.test_details.append(("每个图表独立滚动条", f"失败: {str(e)}"))
            print(f"   ✗ 每个图表独立滚动区域检查失败: {e}")
            
    def test_window_resize_layout(self):
        """测试窗口缩小布局"""
        print("\n🔹 测试3.1: 窗口缩小到最小尺寸")
        try:
            # 记录原始尺寸
            original_size = self.window.size()
            
            # 测试缩小到最小尺寸
            self.window.resize(800, 600)
            self.app.processEvents()
            
            # 检查窗口尺寸
            assert self.window.width() >= 780, "窗口宽度应不小于780"
            assert self.window.height() >= 580, "窗口高度应不小于580"
            
            # 检查左侧面板滚动区域
            left_scroll = None
            central = self.window.centralWidget()
            if central:
                for child in central.children():
                    if isinstance(child, QScrollArea):
                        left_scroll = child
                        break
            
            assert left_scroll is not None, "左侧面板滚动区域不存在"
            
            # 检查左侧面板内容是否可见（通过滚动）
            left_widget = left_scroll.widget()
            assert left_widget is not None, "左侧面板内容不存在"
            
            # 检查左侧面板内容是否超出可视区域
            if left_widget.height() > left_scroll.height():
                # 内容超出，应该有滚动条
                v_scrollbar = left_scroll.verticalScrollBar()
                assert v_scrollbar.maximum() > 0, \
                    "左侧面板内容超出但无垂直滚动条"
                print(f"   ℹ 左侧面板内容高度: {left_widget.height()}px, "
                      f"可视高度: {left_scroll.height()}px, 滚动条已启用")
            
            # 检查图表滚动区域
            dashboard = self.window.dashboard_view
            chart_scrolls = [
                dashboard.trend_scroll,
                dashboard.status_scroll,
                dashboard.bar_scroll,
                dashboard.pie_scroll
            ]
            
            for scroll in chart_scrolls:
                chart_widget = scroll.widget()
                if chart_widget:
                    # 检查图表是否保持最小尺寸
                    assert chart_widget.minimumWidth() >= 500, \
                        f"图表最小宽度不足: {chart_widget.minimumWidth()}"
                    assert chart_widget.height() >= 400, \
                        f"图表高度被压缩: {chart_widget.height()}"
                    
                    # 如果图表内容超出可视区域，应该有滚动条
                    if chart_widget.width() > scroll.width():
                        h_scrollbar = scroll.horizontalScrollBar()
                        assert h_scrollbar.maximum() > 0, \
                            "图表内容超出但无水平滚动条"
                        print(f"   ℹ 图表宽度: {chart_widget.width()}px, "
                              f"可视宽度: {scroll.width()}px, 滚动条已启用")
            
            # 恢复原始尺寸
            self.window.resize(original_size)
            self.app.processEvents()
            
            self.results.append(("窗口缩小布局", "通过"))
            self.test_details.append(("窗口缩小布局", 
                "窗口缩小到800x600时，左侧面板和图表通过滚动条正常显示"))
            print("   ✓ 窗口缩小布局测试通过")
            
        except Exception as e:
            self.results.append(("窗口缩小布局", f"失败: {e}"))
            self.test_details.append(("窗口缩小布局", f"失败: {str(e)}"))
            print(f"   ✗ 窗口缩小布局测试失败: {e}")
            
    def test_chart_many_items(self):
        """测试图表数据项较多的情况"""
        print("\n🔹 测试4.1: 加载大量数据测试")
        try:
            # 加载测试数据
            with open('/Users/m.wang/project/video-order-extractor/test_data.json', 
                      'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            if 'data' in test_data:
                test_data = test_data['data']
            
            orders = test_data.get('orders', [])
            
            # 导入数据
            self.window._load_data(orders, test_data)
            self.app.processEvents()
            
            # 切换到数据分析标签页
            self.window.tab_widget.setCurrentIndex(1)
            self.app.processEvents()
            
            # 检查图表滚动区域
            dashboard = self.window.dashboard_view
            chart_scrolls = {
                'trend_scroll': dashboard.trend_scroll,
                'status_scroll': dashboard.status_scroll,
                'bar_scroll': dashboard.bar_scroll,
                'pie_scroll': dashboard.pie_scroll,
            }
            
            for name, scroll in chart_scrolls.items():
                chart_widget = scroll.widget()
                assert chart_widget is not None, f"{name} 图表widget不存在"
                
                # 检查图表内容尺寸
                chart_width = chart_widget.width()
                chart_height = chart_widget.height()
                
                # 检查滚动区域可视尺寸
                scroll_width = scroll.width()
                scroll_height = scroll.height()
                
                print(f"   ℹ {name}: 图表内容 {chart_width}x{chart_height}, "
                      f"可视区域 {scroll_width}x{scroll_height}")
                
                # 如果内容超出，应该有滚动条
                if chart_width > scroll_width:
                    h_scrollbar = scroll.horizontalScrollBar()
                    print(f"      → 水平滚动条已启用 (max={h_scrollbar.maximum()})")
                    assert h_scrollbar.maximum() > 0, \
                        f"{name} 图表超出但无水平滚动条"
                
                if chart_height > scroll_height:
                    v_scrollbar = scroll.verticalScrollBar()
                    print(f"      → 垂直滚动条已启用 (max={v_scrollbar.maximum()})")
                    assert v_scrollbar.maximum() > 0, \
                        f"{name} 图表超出但无垂直滚动条"
            
            self.results.append(("图表数据项较多", "通过"))
            self.test_details.append(("图表数据项较多", 
                f"加载{len(orders)}条订单数据，每个图表都有独立的滚动条"))
            print("   ✓ 图表数据项较多测试通过")
            
        except Exception as e:
            self.results.append(("图表数据项较多", f"失败: {e}"))
            self.test_details.append(("图表数据项较多", f"失败: {str(e)}"))
            print(f"   ✗ 图表数据项较多测试失败: {e}")
            
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*70)
        print("📊 测试报告")
        print("="*70)
        
        passed = sum(1 for _, status in self.results if status == "通过")
        total = len(self.results)
        
        for test_name, status in self.results:
            status_icon = "✅" if status == "通过" else "❌"
            print(f"  {status_icon} {test_name}: {status}")
            
            # 显示详细信息
            for detail_name, detail in self.test_details:
                if detail_name == test_name:
                    print(f"     └─ {detail}")
                    break
        
        print(f"\n📈 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("\n🎉 所有测试通过！")
            print("\n✅ 左侧面板滚动条正常")
            print("✅ 每个图表有独立的滚动条")
            print("✅ 窗口缩小时布局无压缩、重叠")
            print("✅ 图表数据项较多时可独立滚动查看完整内容")
        else:
            print("\n⚠️ 部分测试失败，请检查相关功能")
            
        print("\n" + "-"*70)
        print("📝 测试要点总结")
        print("-"*70)
        print("1. 左侧面板设置滚动区域，防止内容压缩或重叠")
        print("2. 每个图表容器都有自己的QScrollArea，支持独立滚动")
        print("3. 窗口缩小时，内容通过滚动条正常显示，不压缩")
        print("4. 图表数据项较多时，通过独立滚动条查看，不畸变")
        print("-"*70)


if __name__ == "__main__":
    runner = ScrollLayoutTestRunner()
    runner.run_all_tests()

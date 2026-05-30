#!/usr/bin/env python3
"""
自动导入测试数据到 GUI 应用
"""
import json
import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 导入 GUI 应用
sys.path.insert(0, '/Users/m.wang/project/video-order-extractor')
from gui_app import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # 等待窗口加载完成
    QTimer.singleShot(500, lambda: load_test_data(window))
    
    sys.exit(app.exec_())

def load_test_data(window):
    """加载测试数据"""
    try:
        # 读取测试数据
        with open('/Users/m.wang/project/video-order-extractor/test_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查数据结构
        if 'data' in data:
            data = data['data']
        
        orders = data.get('orders', [])
        summary = {k: v for k, v in data.items() if k != 'orders'}
        
        # 加载数据到窗口
        window._load_data(orders, summary)
        
        # 切换到数据分析标签页
        window.tab_widget.setCurrentIndex(1)
        
        print("✅ 测试数据已成功导入！")
        print(f"📊 共导入 {len(orders)} 条订单")
        print("📈 请查看 '数据分析' 标签页")
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

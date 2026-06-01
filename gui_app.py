"""
视频订单提取 - 图形界面应用
"""
import sys
import os
import json
import re
import time
from datetime import datetime, timedelta
from collections import defaultdict
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QProgressBar,
    QTableWidget, QTableWidgetItem, QComboBox, QCheckBox,
    QSplitter, QGroupBox, QTabWidget, QHeaderView, QScrollArea,
    QSizePolicy, QMenu, QMessageBox, QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRect, QMargins
from PyQt5.QtGui import QDoubleValidator, QPalette, QColor, QPainter, QLinearGradient, QBrush, QPen, QFont
from PyQt5.QtChart import (
    QChart, QChartView, QLineSeries, QAreaSeries, QBarSeries, QBarSet, 
    QPieSeries, QPieSlice, QValueAxis, QBarCategoryAxis, QCategoryAxis
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from video_processor import process_video, get_vision_client, image_to_base64
from config import VISION_MODEL
from app.utils.database import init_db, get_session, close_engine
from app.services.import_service import ImportService


class ProcessingThread(QThread):
    """处理视频的后台线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, video_path, fps=None):
        super().__init__()
        self.video_path = video_path
        self.fps = fps

    def run(self):
        try:
            self.progress.emit(10, "开始处理视频...")
            
            def custom_progress(step, msg):
                self.progress.emit(step, msg)
            
            result = process_video(self.video_path, self.fps)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


ORDER_LIST_PROMPT = """你是一个专业的订单信息提取助手。请仔细观察这张手机截图，这是购物App的"我的订单"列表页面。

请提取页面中每一条订单的以下信息，以JSON数组格式返回：
- order_id: 订单编号（完整数字串）
- status: 订单状态（如"已完成"、"已退款"等）
- datetime: 下单时间/交易时间（格式 YYYY/MM/DD HH:MM:SS）
- amount: 金额（数字，退款为负数）
- location: 交易地点/卖场（如"深圳"，没有则为空字符串）
- tags: 标签（如"亲友卡"，没有则为空字符串）

注意事项：
1. 只返回页面上能清晰看到的订单
2. 金额要去掉¥符号，只保留数字
3. 退款订单金额为负数
4. 订单编号尽量提取完整
5. 只返回JSON，不要其他文字

返回格式示例：
```json
[
  {"order_id": "557100000000060717202605242120", "status": "已完成", "datetime": "2026/05/24 21:19:36", "amount": 52.80, "location": "深圳", "tags": "亲友卡"},
  {"order_id": "557100000008300049202605112104", "status": "已退款", "datetime": "2026/05/11 21:06:17", "amount": -145.90, "location": "深圳", "tags": ""}
]
```
"""


ORDER_DETAIL_PROMPT = """你是一个专业的订单信息提取助手。请仔细观察这张手机截图，这是购物App的"订单详情"页面。

请提取该订单的完整信息，包括订单基本信息和商品明细列表，以JSON格式返回：

订单基本信息：
- order_id: 订单编号（完整数字串）
- status: 订单状态（如"已完成"、"已退款"等）
- datetime: 交易时间（格式 YYYY/MM/DD HH:MM:SS）
- amount: 订单金额（数字）
- location: 交易地点/卖场（如"深圳"）
- member_card: 会员卡号（没有则为空字符串）
- subtotal: 商品总计（数字）
- discount: 促销折扣（数字，没有则为0）
- rebate: 消费返利（数字，没有则为0）
- tax_excluded: 未税价格（数字，没有则为空或0）
- actual_pay: 实际支付金额（数字）

商品明细列表 products：
每个商品包含：
- product_name: 商品名称
- quantity: 数量（整数）
- unit_price: 单价
- spec: 规格描述（如"330ml*30"、"大份"等，没有则为空字符串）
- subtotal: 该商品小计金额

注意事项：
1. 金额要去掉¥符号，只保留数字
2. 退款订单金额为负数
3. 商品明细尽量全部提取，不要遗漏
4. 规格包括容量、包装方式、口味等信息
5. 只返回JSON，不要其他文字

返回格式示例：
```json
{
  "order_id": "557100000000060717202605242120",
  "status": "已完成",
  "datetime": "2026/05/24 21:19:36",
  "amount": 52.80,
  "location": "深圳",
  "member_card": "5311******4410",
  "subtotal": 50.00,
  "discount": 0,
  "rebate": 0,
  "tax_excluded": 0,
  "actual_pay": 52.80,
  "products": [
    {"product_name": "鲜牛奶", "quantity": 2, "unit_price": 25.00, "spec": "1L装", "subtotal": 50.00}
  ]
}
```
"""


def _parse_json_from_text(text):
    """从模型返回文本中解析JSON"""
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = text.strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    bracket_match = re.search(r'\[[\s\S]*\]', text)
    if bracket_match:
        try:
            result = json.loads(bracket_match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    brace_match = re.search(r'\{[\s\S]*\}', text)
    if brace_match:
        try:
            result = json.loads(brace_match.group())
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    return None


def _recognize_order_list_screenshot(image_path):
    """识别订单列表截图，返回多条订单"""
    client = get_vision_client()
    b64 = image_to_base64(image_path)

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": ORDER_LIST_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        }],
        max_tokens=2000,
        temperature=0.1
    )

    text = response.choices[0].message.content
    result = _parse_json_from_text(text)

    if isinstance(result, list):
        return result
    elif isinstance(result, dict):
        return [result]
    else:
        print(f"[截屏识别] 无法解析为订单列表: {text[:200]}")
        return []


def _recognize_order_detail_screenshot(image_path):
    """识别订单详情截图，返回单条订单（含商品明细）"""
    client = get_vision_client()
    b64 = image_to_base64(image_path)

    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": ORDER_DETAIL_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        }],
        max_tokens=3000,
        temperature=0.1
    )

    text = response.choices[0].message.content
    result = _parse_json_from_text(text)

    if isinstance(result, dict):
        return result
    elif isinstance(result, list) and len(result) > 0:
        return result[0]
    else:
        print(f"[截屏识别] 无法解析为订单详情: {text[:200]}")
        return None


def _process_screenshots(image_paths, mode="order_list"):
    """批量处理截图"""
    all_orders = []

    for i, image_path in enumerate(image_paths):
        filename = os.path.basename(image_path)
        print(f"正在识别第 {i+1}/{len(image_paths)} 张截图: {filename}")

        if mode == "order_detail":
            result = _recognize_order_detail_screenshot(image_path)
            if result:
                all_orders.append(result)
                product_count = len(result.get("products", []))
                print(f"  识别到 1 条订单（包含 {product_count} 个商品）")
            else:
                print(f"  未识别到订单")
        else:
            orders = _recognize_order_list_screenshot(image_path)
            all_orders.extend(orders)
            print(f"  识别到 {len(orders)} 条订单")

        if (i + 1) % 3 == 0 and i + 1 < len(image_paths):
            print("  等待1秒避免限流...")
            time.sleep(1)

    return all_orders


class ScreenshotProcessThread(QThread):
    """处理截屏的后台线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, image_paths, mode="order_list"):
        super().__init__()
        self.image_paths = image_paths
        self.mode = mode

    def run(self):
        try:
            total = len(self.image_paths)
            self.progress.emit(10, f"开始识别 {total} 张截图...")

            orders = _process_screenshots(self.image_paths, self.mode)

            self.progress.emit(100, f"识别完成，共提取 {len(orders)} 条订单")
            self.finished.emit(orders)
        except Exception as e:
            self.error.emit(str(e))


class OrderFilterWidget(QWidget):
    """订单过滤组件"""
    filter_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # 状态过滤
        status_group = QGroupBox("订单状态")
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        self.status_all = QCheckBox("全部")
        self.status_all.setChecked(True)
        self.status_completed = QCheckBox("已完成")
        self.status_refunded = QCheckBox("已退款")
        status_layout.addWidget(self.status_all)
        status_layout.addWidget(self.status_completed)
        status_layout.addWidget(self.status_refunded)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # 标签过滤
        tag_group = QGroupBox("标签筛选")
        tag_layout = QHBoxLayout()
        tag_layout.setSpacing(10)
        self.tag_all = QCheckBox("全部")
        self.tag_all.setChecked(True)
        self.tag_qyk = QCheckBox("亲友卡")
        self.tag_other = QCheckBox("无标签")
        tag_layout.addWidget(self.tag_all)
        tag_layout.addWidget(self.tag_qyk)
        tag_layout.addWidget(self.tag_other)
        tag_group.setLayout(tag_layout)
        layout.addWidget(tag_group)

        # 金额范围
        amount_group = QGroupBox("金额范围")
        amount_layout = QHBoxLayout()
        amount_layout.setSpacing(5)
        self.amount_min = QLineEdit()
        self.amount_min.setPlaceholderText("最小金额")
        self.amount_min.setValidator(QDoubleValidator())
        self.amount_min.setMinimumWidth(80)
        self.amount_max = QLineEdit()
        self.amount_max.setPlaceholderText("最大金额")
        self.amount_max.setValidator(QDoubleValidator())
        self.amount_max.setMinimumWidth(80)
        amount_layout.addWidget(QLabel("¥"))
        amount_layout.addWidget(self.amount_min)
        amount_layout.addWidget(QLabel("-¥"))
        amount_layout.addWidget(self.amount_max)
        amount_group.setLayout(amount_layout)
        layout.addWidget(amount_group)

        # 日期范围
        date_group = QGroupBox("日期范围")
        date_layout = QHBoxLayout()
        date_layout.setSpacing(8)
        self.date_start = QLineEdit()
        self.date_start.setPlaceholderText("开始日期 (YYYY/MM/DD)")
        self.date_end = QLineEdit()
        self.date_end.setPlaceholderText("结束日期 (YYYY/MM/DD)")
        date_layout.addWidget(self.date_start, 1)
        date_layout.addWidget(QLabel("-"))
        date_layout.addWidget(self.date_end, 1)
        date_group.setLayout(date_layout)
        layout.addWidget(date_group)

        # 订单号搜索
        search_group = QGroupBox("订单号搜索")
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        self.search_order_id = QLineEdit()
        self.search_order_id.setPlaceholderText("输入订单号")
        search_layout.addWidget(self.search_order_id)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # 应用按钮
        self.apply_btn = QPushButton("应用筛选")
        self.apply_btn.setMinimumHeight(35)
        self.apply_btn.clicked.connect(self.on_apply)
        self.reset_btn = QPushButton("重置筛选")
        self.reset_btn.setMinimumHeight(35)
        self.reset_btn.clicked.connect(self.on_reset)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self.apply_btn)
        btn_layout.addWidget(self.reset_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 连接信号
        self.status_all.stateChanged.connect(self.on_status_all)
        self.status_completed.stateChanged.connect(self.on_status_single)
        self.status_refunded.stateChanged.connect(self.on_status_single)
        self.tag_all.stateChanged.connect(self.on_tag_all)
        self.tag_qyk.stateChanged.connect(self.on_tag_single)
        self.tag_other.stateChanged.connect(self.on_tag_single)
        
        # 日期输入框文本变化时自动触发过滤
        self.date_start.textChanged.connect(self._on_date_changed)
        self.date_end.textChanged.connect(self._on_date_changed)
        self.amount_min.textChanged.connect(self._on_date_changed)
        self.amount_max.textChanged.connect(self._on_date_changed)
        self.search_order_id.textChanged.connect(self._on_date_changed)

    def _on_date_changed(self):
        """任何过滤条件变化时自动触发过滤"""
        self.filter_changed.emit()

    def on_status_all(self, state):
        if state == Qt.Checked:
            self.status_completed.setChecked(False)
            self.status_refunded.setChecked(False)

    def on_status_single(self):
        # 如果任何单个状态被选中，则取消"全部"
        if self.status_completed.isChecked() or self.status_refunded.isChecked():
            self.status_all.setChecked(False)
        # 如果没有任何单个状态被选中，则选中"全部"
        if not self.status_completed.isChecked() and not self.status_refunded.isChecked():
            self.status_all.setChecked(True)

    def on_tag_all(self, state):
        if state == Qt.Checked:
            self.tag_qyk.setChecked(False)
            self.tag_other.setChecked(False)

    def on_tag_single(self):
        # 如果任何单个标签被选中，则取消"全部"
        if self.tag_qyk.isChecked() or self.tag_other.isChecked():
            self.tag_all.setChecked(False)
        # 如果没有任何单个标签被选中，则选中"全部"
        if not self.tag_qyk.isChecked() and not self.tag_other.isChecked():
            self.tag_all.setChecked(True)

    def on_apply(self):
        self.filter_changed.emit()

    def on_reset(self):
        self.status_all.setChecked(True)
        self.tag_all.setChecked(True)
        self.amount_min.clear()
        self.amount_max.clear()
        self.date_start.clear()
        self.date_end.clear()
        self.search_order_id.clear()
        self.filter_changed.emit()

    def get_filter(self):
        # 安全转换金额输入
        def safe_float(value):
            if not value:
                return None
            try:
                return float(value)
            except ValueError:
                return None
        
        return {
            'status': self._get_selected_status(),
            'tag': self._get_selected_tag(),
            'amount_min': safe_float(self.amount_min.text()),
            'amount_max': safe_float(self.amount_max.text()),
            'date_start': self.date_start.text() if self.date_start.text() else None,
            'date_end': self.date_end.text() if self.date_end.text() else None,
            'search_order_id': self.search_order_id.text() if self.search_order_id.text() else None
        }

    def _get_selected_status(self):
        if self.status_all.isChecked():
            return 'all'
        status = []
        if self.status_completed.isChecked():
            status.append('已完成')
        if self.status_refunded.isChecked():
            status.append('已退款')
        return status

    def _get_selected_tag(self):
        if self.tag_all.isChecked():
            return 'all'
        tags = []
        if self.tag_qyk.isChecked():
            tags.append('亲友卡')
        if self.tag_other.isChecked():
            tags.append('')
        return tags

    @staticmethod
    def _parse_date(date_str):
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


class SummaryWidget(QWidget):
    """汇总统计组件"""
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 主统计卡片
        main_stats = QGroupBox("核心统计")
        main_layout = QVBoxLayout()
        
        self.total_orders = QLabel("总订单数: 0")
        self.completed_count = QLabel("已完成: 0")
        self.refund_count = QLabel("已退款: 0")
        self.completed_amount = QLabel("已完成金额: ¥0.00")
        self.refund_amount = QLabel("退款金额: ¥0.00")
        self.net_amount = QLabel("净消费: ¥0.00")
        
        main_layout.addWidget(self.total_orders)
        main_layout.addWidget(self.completed_count)
        main_layout.addWidget(self.refund_count)
        main_layout.addWidget(self.completed_amount)
        main_layout.addWidget(self.refund_amount)
        main_layout.addWidget(self.net_amount)
        main_stats.setLayout(main_layout)
        layout.addWidget(main_stats)

        # 亲友卡统计
        qyk_stats = QGroupBox("亲友卡统计")
        qyk_layout = QVBoxLayout()
        self.qyk_count = QLabel("亲友卡订单数: 0")
        self.qyk_amount = QLabel("亲友卡已完成金额: ¥0.00")
        qyk_layout.addWidget(self.qyk_count)
        qyk_layout.addWidget(self.qyk_amount)
        qyk_stats.setLayout(qyk_layout)
        layout.addWidget(qyk_stats)

        self.setLayout(layout)

    def update_summary(self, summary):
        self.total_orders.setText(f"总订单数: {summary.get('total_orders', 0)}")
        self.completed_count.setText(f"已完成: {summary.get('completed_count', 0)}")
        self.refund_count.setText(f"已退款: {summary.get('refund_count', 0)}")
        self.completed_amount.setText(f"已完成金额: ¥{summary.get('completed_amount', 0):.2f}")
        self.refund_amount.setText(f"退款金额: ¥{abs(summary.get('refund_amount', 0)):.2f}")
        self.net_amount.setText(f"净消费: ¥{summary.get('net_amount', 0):.2f}")
        self.qyk_count.setText(f"亲友卡订单数: {summary.get('qyk_count', 0)}")
        self.qyk_amount.setText(f"亲友卡已完成金额: ¥{summary.get('qyk_completed_amount', 0):.2f}")


class OrdersTable(QTableWidget):
    """订单数据表格"""
    delete_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(['序号', '订单号', '订单状态', '下单时间', '金额(元)', '标签'])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        
        self.setColumnWidth(0, 50)   # 序号
        self.setColumnWidth(2, 70)   # 状态
        self.setColumnWidth(4, 90)   # 金额
        
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.verticalHeader().setVisible(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        row = self.rowAt(pos.y())
        if row < 0:
            return
        order_id = self.item(row, 1).text() if self.item(row, 1) else ""
        menu = QMenu(self)
        delete_action = menu.addAction("🗑 删除订单")
        menu.setStyleSheet("""
            QMenu {
                background-color: #1a2633;
                color: #e0e6ed;
                border: 1px solid #3a4a5a;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
            }
            QMenu::item:selected {
                background-color: #c0392b;
            }
        """)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(order_id))
        menu.exec_(self.viewport().mapToGlobal(pos))

    def update_data(self, orders):
        self.setRowCount(0)
        for i, order in enumerate(orders, 1):
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(str(i)))
            self.setItem(row, 1, QTableWidgetItem(str(order.get('order_id', ''))))
            self.setItem(row, 2, QTableWidgetItem(order.get('status', '')))
            self.setItem(row, 3, QTableWidgetItem(order.get('datetime', '')))
            
            amount = order.get('amount', 0)
            amount_item = QTableWidgetItem(f'{float(amount):.2f}')
            if float(amount) < 0:
                amount_item.setForeground(Qt.red)
            self.setItem(row, 4, amount_item)
            
            self.setItem(row, 5, QTableWidgetItem(order.get('tags', '')))


class ProductsTable(QTableWidget):
    """商品明细表格"""
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels(['序号', '商品名称', '规格', '单价(元)', '数量', '小计(元)', '所属订单'])
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)

        self.setColumnWidth(0, 50)
        self.setColumnWidth(2, 100)
        self.setColumnWidth(3, 80)
        self.setColumnWidth(4, 60)
        self.setColumnWidth(5, 80)

        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.verticalHeader().setVisible(False)

    def update_data(self, orders):
        self.setRowCount(0)
        row_idx = 0
        for order in orders:
            order_id = str(order.get('order_id', ''))
            products = order.get('products', [])
            if not products:
                continue
            for product in products:
                row = self.rowCount()
                self.insertRow(row)
                row_idx += 1
                self.setItem(row, 0, QTableWidgetItem(str(row_idx)))
                self.setItem(row, 1, QTableWidgetItem(str(product.get('product_name', ''))))
                self.setItem(row, 2, QTableWidgetItem(str(product.get('spec', ''))))

                unit_price = product.get('unit_price', 0)
                self.setItem(row, 3, QTableWidgetItem(f'{float(unit_price):.2f}'))

                quantity = product.get('quantity', 0)
                self.setItem(row, 4, QTableWidgetItem(str(quantity)))

                subtotal = product.get('subtotal', 0)
                self.setItem(row, 5, QTableWidgetItem(f'{float(subtotal):.2f}'))

                self.setItem(row, 6, QTableWidgetItem(order_id))


class DashboardView(QWidget):
    """数据看板视图 - 使用 PyQtChart"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setStyleSheet("""
            QWidget {
                background-color: #0f1923;
                color: #e0e6ed;
            }
            QLabel {
                color: #e0e6ed;
            }
        """)
        
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(12)
        
        # 标题
        self.title_label = QLabel("🛒 购物订单数据看板")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00d4ff, stop:1 #7c3aed);
                padding: 8px 0;
            }
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)
        
        # 日期范围
        self.date_range_label = QLabel("数据时间范围：N/A")
        self.date_range_label.setStyleSheet("color: #8892a4; font-size: 13px;")
        self.date_range_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.date_range_label)
        
        # 创建滚动区域来容纳所有内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)  # 禁止内容自适应，保持原始大小
        scroll.setMinimumHeight(900)
        # 启用水平和垂直滚动条
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1a2633;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3a4a5a;
                border-radius: 6px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a5a6a;
            }
            QScrollBar:horizontal {
                background-color: #1a2633;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #3a4a5a;
                border-radius: 6px;
                min-width: 40px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #4a5a6a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        
        # 统计卡片区域
        self.stats_widget = QWidget()
        self.stats_widget.setMinimumHeight(100)
        self.stats_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        stats_layout = QHBoxLayout(self.stats_widget)
        stats_layout.setSpacing(12)
        stats_layout.setContentsMargins(0, 10, 0, 10)
        
        cards_data = [
            ("总订单数", "0", "#00d4ff"),
            ("已完成金额", "¥0", "#00e676"),
            ("退款金额", "¥0", "#ff5252"),
            ("实际净消费", "¥0", "#b388ff"),
            ("亲友卡消费", "¥0", "#ffab40"),
        ]
        
        for label, value, color in cards_data:
            card = self.create_stat_card(label, value, color)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            stats_layout.addWidget(card)
        
        scroll_layout.addWidget(self.stats_widget)
        
        # 图表区域 - 使用垂直布局
        charts_container = QWidget()
        charts_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        charts_layout = QVBoxLayout(charts_container)
        charts_layout.setSpacing(12)
        charts_layout.setStretch(0, 1)
        charts_layout.setStretch(1, 1)
        charts_layout.setStretch(2, 1)

        # 第一行：趋势图（适配宽度，高度自适应）
        row1 = QWidget()
        row1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(12)

        # 趋势图
        self.trend_chart_view = self.create_chart_view("月度消费趋势", 480)
        self.trend_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        row1_layout.addWidget(self.trend_chart_view)
        charts_layout.addWidget(row1)

        # 第二行：柱状图（适配宽度，高度自适应）
        row2 = QWidget()
        row2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        row2_layout = QHBoxLayout(row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(12)

        # 柱状图
        self.bar_chart_view = self.create_chart_view("月度订单数量 & 平均单价", 480)
        self.bar_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        row2_layout.addWidget(self.bar_chart_view)
        charts_layout.addWidget(row2)

        # 第三行：状态饼图（适配宽度）
        row3 = QWidget()
        row3.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        row3_layout = QHBoxLayout(row3)
        row3_layout.setContentsMargins(0, 0, 0, 0)
        row3_layout.setSpacing(12)

        # 状态饼图
        self.status_chart_view = self.create_chart_view("订单状态分布", 400)
        self.status_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        row3_layout.addWidget(self.status_chart_view)
        charts_layout.addWidget(row3)
        
        scroll_layout.addWidget(charts_container)
        
        # 设置滚动区域
        scroll.setWidget(scroll_content)
        self.main_layout.addWidget(scroll, 1)
        
    def create_chart_view(self, title, min_height=280):
        """创建图表视图 - 专业样式"""
        container = QWidget()
        container.setMinimumHeight(min_height)
        container.setMinimumWidth(900)
        container.setMaximumHeight(700)
        container.setMaximumWidth(4000)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        container.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 35)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #e0e6ed;
            font-size: 15px;
            font-weight: bold;
            padding-left: 12px;
            border-left: 4px solid #00d4ff;
            letter-spacing: 0.5px;
        """)
        title_label.setMinimumWidth(700)
        title_label.setMaximumHeight(30)
        layout.addWidget(title_label)

        chart_view = QChartView()
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setRenderHint(QPainter.SmoothPixmapTransform)
        chart_view.setMinimumHeight(min_height - 60)
        chart_view.setMinimumWidth(750)
        chart_view.setMaximumHeight(620)
        chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        chart_view.setStyleSheet("""
            QChartView {
                background-color: transparent;
                border: none;
            }
        """)
        layout.addWidget(chart_view)

        return container
        
    def update_dashboard(self, summary, date_range=None):
        """更新看板数据"""
        monthly = summary.get('monthly_summary', {})
        months = sorted(monthly.keys())
        
        # 如果提供了用户输入的日期范围，则显示该范围
        if date_range:
            self.date_range_label.setText(f"数据时间范围：{date_range}")
        else:
            # 否则显示数据中的月份范围
            date_range_str = f"{months[0] if months else 'N/A'} - {months[-1] if months else 'N/A'}"
            self.date_range_label.setText(f"数据时间范围：{date_range_str}")
        
        # 更新统计卡片
        self.update_stats_cards(summary)
        
        # 更新图表
        self.update_trend_chart(monthly, months)
        self.update_status_chart(summary)
        self.update_bar_chart(monthly, months)
        
    def update_stats_cards(self, summary):
        """更新统计卡片"""
        # 清除旧的卡片
        layout = self.stats_widget.layout()
        if layout:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        
        cards_data = [
            ("总订单数", str(summary.get('total_orders', 0)), "#00d4ff"),
            ("已完成金额", f"¥{summary.get('completed_amount', 0):,.0f}", "#00e676"),
            ("退款金额", f"¥{abs(summary.get('refund_amount', 0)):,.0f}", "#ff5252"),
            ("实际净消费", f"¥{summary.get('net_amount', 0):,.0f}", "#b388ff"),
            ("亲友卡消费", f"¥{summary.get('qyk_completed_amount', 0):,.0f}", "#ffab40"),
        ]
        
        for label, value, color in cards_data:
            card = self.create_stat_card(label, value, color)
            layout.addWidget(card)
            
    def create_stat_card(self, label, value, color):
        """创建统计卡片 - 专业样式"""
        card = QWidget()
        card.setMinimumSize(140, 90)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(26, 32, 44, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 16px;
            }}
            QWidget:hover {{
                border-color: {color}60;
                background-color: rgba(30, 38, 52, 0.98);
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            color: #8892a4;
            font-size: 13px;
            font-weight: normal;
            letter-spacing: 0.5px;
        """)
        label_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"""
            color: {color};
            font-size: 22px;
            font-weight: bold;
            letter-spacing: 1px;
        """)
        value_widget.setAlignment(Qt.AlignCenter)
        value_widget.setWordWrap(True)
        layout.addWidget(value_widget)

        return card

    def _make_yen_axis(self, max_val, color, font):
        """创建带 ¥ 标签的 Y 轴 - 用 QCategoryAxis 避免 sprintf 格式串中的 UTF-8 乱码"""
        max_val = self._nice_round(max_val)
        axis = QCategoryAxis()
        axis.setLabelsColor(color)
        axis.setLabelsFont(font)
        axis.setGridLineVisible(False)
        axis.setStartValue(0)

        if max_val <= 0:
            max_val = 100

        tick_count = 5
        step = max_val / tick_count
        for i in range(tick_count + 1):
            val = i * step
            axis.append(f"¥{val:,.0f}", val)

        return axis

    @staticmethod
    def _nice_round(val):
        """向上取整到美观刻度"""
        if val <= 0:
            return 100
        import math
        magnitude = 10 ** math.floor(math.log10(val))
        residual = val / magnitude
        if residual <= 1:
            nice = 1
        elif residual <= 2:
            nice = 2
        elif residual <= 5:
            nice = 5
        else:
            nice = 10
        return nice * magnitude

    def _show_trend_tooltip(self, point, state, series_name, monthly, months):
        if state and point is not None:
            from PyQt5.QtWidgets import QToolTip
            from PyQt5.QtGui import QCursor
            idx = int(point.x())
            if 0 <= idx < len(months):
                month = months[idx]
                data = monthly[month]
                info = f"{month}\n"
                if series_name == "已完成金额":
                    info += f"已完成金额: ¥{data['completed_amount']:,.2f}\n"
                    info += f"净消费: ¥{data['net_amount']:,.2f}"
                elif series_name == "退款金额":
                    info += f"退款金额: ¥{abs(data['refund_amount']):,.2f}"
                QToolTip.showText(QCursor.pos(), info)

    def _show_bar_tooltip(self, status, index, barset, monthly, months):
        if status and 0 <= index < len(months):
            from PyQt5.QtWidgets import QToolTip
            from PyQt5.QtGui import QCursor
            month = months[index]
            data = monthly[month]
            avg = data['completed_amount'] / data['completed'] if data['completed'] > 0 else 0
            info = (f"{month}\n"
                    f"订单数: {data['count']}\n"
                    f"已完成金额: ¥{data['completed_amount']:,.2f}\n"
                    f"平均单价: ¥{avg:,.2f}")
            QToolTip.showText(QCursor.pos(), info)

    def _show_bar_avg_tooltip(self, point, state, monthly, months):
        if state and point is not None:
            from PyQt5.QtWidgets import QToolTip
            from PyQt5.QtGui import QCursor
            idx = int(point.x())
            if 0 <= idx < len(months):
                month = months[idx]
                data = monthly[month]
                avg = data['completed_amount'] / data['completed'] if data['completed'] > 0 else 0
                info = (f"{month}\n"
                        f"订单数: {data['count']}\n"
                        f"已完成金额: ¥{data['completed_amount']:,.2f}\n"
                        f"平均单价: ¥{avg:,.2f}")
                QToolTip.showText(QCursor.pos(), info)

    def update_trend_chart(self, monthly, months):
        """更新趋势图 - 使用双Y轴，专业样式"""
        chart_view = self.trend_chart_view.findChild(QChartView)
        if not chart_view:
            return

        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 25))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignTop)
        chart.legend().setLabelColor(QColor("#8892a4"))
        chart.legend().setBorderColor(QColor("#3a4a5a"))
        chart.setLocalizeNumbers(False)

        # 处理空数据
        if not months:
            chart_view.setChart(chart)
            return

        # 已完成金额 - 左轴（大量级）
        completed_series = QLineSeries()
        completed_series.setName("已完成金额")
        completed_series.setColor(QColor("#00e676"))
        completed_series.setPen(QPen(QColor("#00e676"), 2.5))
        completed_series.setPointsVisible(True)
        completed_series.hovered.connect(
            lambda p, s, n="已完成金额": self._show_trend_tooltip(p, s, n, monthly, months)
        )

        # 净消费 - 左轴（大量级）
        net_series = QLineSeries()
        net_series.setName("净消费")
        net_series.setColor(QColor("#00d4ff"))
        net_series.setPen(QPen(QColor("#00d4ff"), 2.5))
        net_series.setPointsVisible(True)
        net_series.hovered.connect(
            lambda p, s, n="已完成金额": self._show_trend_tooltip(p, s, n, monthly, months)
        )

        # 退款金额 - 右轴（小量级）
        refund_series = QLineSeries()
        refund_series.setName("退款金额")
        refund_series.setColor(QColor("#ff5252"))
        refund_series.setPen(QPen(QColor("#ff5252"), 2.5))
        refund_series.setPointsVisible(True)
        refund_series.hovered.connect(
            lambda p, s, n="退款金额": self._show_trend_tooltip(p, s, n, monthly, months)
        )

        for month in months:
            data = monthly[month]
            idx = months.index(month)
            completed_series.append(idx, data['completed_amount'])
            net_series.append(idx, data['net_amount'])
            refund_series.append(idx, abs(data['refund_amount']))

        chart.addSeries(completed_series)
        chart.addSeries(net_series)
        chart.addSeries(refund_series)

        # X轴
        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        axis_x.setLabelsColor(QColor("#8892a4"))
        axis_x.setLabelsAngle(-45)
        axis_x.setLabelsFont(QFont("Heiti SC", 9))
        axis_x.setGridLineVisible(False)
        chart.addAxis(axis_x, Qt.AlignBottom)

        # 左Y轴 - 金额（大量级）
        max_amount = max(
            max([monthly[m]['completed_amount'] for m in months]) if months else 0,
            max([abs(monthly[m]['net_amount']) for m in months]) if months else 0
        )
        top = max_amount * 1.2 if max_amount > 0 else 1000
        axis_y_left = self._make_yen_axis(
            top, QColor("#8892a4"), QFont("Heiti SC", 10)
        )
        chart.addAxis(axis_y_left, Qt.AlignLeft)

        # 右Y轴 - 退款金额（小量级）
        max_refund = max([abs(monthly[m]['refund_amount']) for m in months]) if months else 0
        top_r = max_refund * 1.5 if max_refund > 0 else 100
        axis_y_right = self._make_yen_axis(
            top_r, QColor("#ff5252"), QFont("Heiti SC", 10)
        )
        chart.addAxis(axis_y_right, Qt.AlignRight)

        # 绑定轴
        completed_series.attachAxis(axis_x)
        completed_series.attachAxis(axis_y_left)
        net_series.attachAxis(axis_x)
        net_series.attachAxis(axis_y_left)
        refund_series.attachAxis(axis_x)
        refund_series.attachAxis(axis_y_right)

        chart_view.setChart(chart)
        
    def update_status_chart(self, summary):
        """更新状态饼图 - 专业样式"""
        chart_view = self.status_chart_view.findChild(QChartView)
        if not chart_view:
            return

        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)
        chart.legend().setLabelColor(QColor("#8892a4"))
        chart.legend().setBorderColor(QColor("#3a4a5a"))
        chart.setLocalizeNumbers(False)

        series = QPieSeries()
        series.setHoleSize(0.45)
        series.setPieStartAngle(90)
        series.setPieEndAngle(450)

        completed = summary.get('completed_count', 0)
        refund = summary.get('refund_count', 0)

        slice1 = QPieSlice("已完成", completed)
        slice1.setColor(QColor("#00e676"))
        slice1.setBorderColor(QColor("#00e676"))
        slice1.setBorderWidth(2)

        slice2 = QPieSlice("已退款", refund)
        slice2.setColor(QColor("#ff5252"))
        slice2.setBorderColor(QColor("#ff5252"))
        slice2.setBorderWidth(2)

        series.append(slice1)
        series.append(slice2)

        chart.addSeries(series)
        chart_view.setChart(chart)
        
    def update_bar_chart(self, monthly, months):
        """更新柱状图 - 使用双Y轴，专业样式"""
        chart_view = self.bar_chart_view.findChild(QChartView)
        if not chart_view:
            return

        chart = QChart()
        chart.setBackgroundVisible(False)
        chart.setMargins(QMargins(0, 0, 0, 25))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignTop)
        chart.legend().setLabelColor(QColor("#8892a4"))
        chart.legend().setBorderColor(QColor("#3a4a5a"))
        chart.setLocalizeNumbers(False)

        # 处理空数据
        if not months:
            chart_view.setChart(chart)
            return

        # 订单数柱状图 - 左轴（大量级）
        bar_set = QBarSet("订单数")
        counts = [monthly[m]['count'] for m in months]
        bar_set.append(counts)
        bar_set.setColor(QColor("#00d4ff"))
        bar_set.setBorderColor(QColor("#00d4ff"))

        bar_series = QBarSeries()
        bar_series.append(bar_set)
        bar_series.setBarWidth(0.7)
        bar_series.hovered.connect(
            lambda s, i, b: self._show_bar_tooltip(s, i, b, monthly, months)
        )
        chart.addSeries(bar_series)

        # 平均单价折线图 - 右轴（小量级）
        line_series = QLineSeries()
        line_series.setName("平均单价")
        line_series.setColor(QColor("#ffab40"))
        line_series.setPen(QPen(QColor("#ffab40"), 2.5))
        line_series.setPointsVisible(True)
        line_series.hovered.connect(
            lambda p, s: self._show_bar_avg_tooltip(p, s, monthly, months)
        )

        for i, month in enumerate(months):
            data = monthly[month]
            avg = data['completed_amount'] / data['completed'] if data['completed'] > 0 else 0
            line_series.append(i, avg)

        chart.addSeries(line_series)

        # X轴
        axis_x = QBarCategoryAxis()
        axis_x.append(months)
        axis_x.setLabelsColor(QColor("#8892a4"))
        axis_x.setLabelsAngle(-45)
        axis_x.setLabelsFont(QFont("Heiti SC", 9))
        axis_x.setGridLineVisible(False)
        chart.addAxis(axis_x, Qt.AlignBottom)

        # 左Y轴 - 订单数（大量级）
        max_count = max(counts) if counts else 10
        top_count = self._nice_round(max_count * 1.3) if max_count > 0 else 10
        axis_y_left = QValueAxis()
        axis_y_left.setLabelsColor(QColor("#00d4ff"))
        axis_y_left.setLabelFormat("%d")
        axis_y_left.setRange(0, top_count)
        axis_y_left.setGridLineVisible(False)
        axis_y_left.setMinorTickCount(0)
        chart.addAxis(axis_y_left, Qt.AlignLeft)

        # 右Y轴 - 平均单价（小量级）
        max_avg = max([monthly[m]['completed_amount'] / monthly[m]['completed'] if monthly[m]['completed'] > 0 else 0 for m in months]) if months else 500
        top_avg = max_avg * 1.3 if max_avg > 0 else 500
        axis_y_right = self._make_yen_axis(
            top_avg, QColor("#ffab40"), QFont("Heiti SC", 10)
        )
        chart.addAxis(axis_y_right, Qt.AlignRight)

        # 绑定轴
        bar_series.attachAxis(axis_x)
        bar_series.attachAxis(axis_y_left)
        line_series.attachAxis(axis_x)
        line_series.attachAxis(axis_y_right)

        chart_view.setChart(chart)


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频订单提取分析系统")
        self.setGeometry(100, 100, 1400, 900)
        
        self.orders = []
        self.summary = None
        
        init_db()
        self._load_from_db()
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 左侧面板 - 添加滚动区域
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)  # 允许内容自适应宽度
        left_scroll.setMinimumWidth(340)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f0f0f0;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #c0c0c0;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        left_panel = QWidget()
        left_panel.setMinimumWidth(320)  # 设置最小宽度，小于滚动区域宽度
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(10, 10, 10, 10)

        # 导入数据文件
        import_group = QGroupBox("导入数据文件")
        import_layout = QVBoxLayout()
        import_layout.setSpacing(8)
        
        import_btn_layout = QHBoxLayout()
        import_btn_layout.setSpacing(8)
        self.import_file_path = QLineEdit()
        self.import_file_path.setReadOnly(True)
        self.import_file_path.setMinimumWidth(150)
        self.import_browse_btn = QPushButton("选择数据")
        self.import_browse_btn.setMinimumWidth(80)
        self.import_browse_btn.clicked.connect(self.browse_import_file)
        import_btn_layout.addWidget(self.import_file_path, 1)
        import_btn_layout.addWidget(self.import_browse_btn)
        import_layout.addLayout(import_btn_layout)

        self.import_mode_group = QButtonGroup(self)
        self.import_mode_incremental = QRadioButton("增量导入")
        self.import_mode_incremental.setChecked(True)
        self.import_mode_full = QRadioButton("全量刷新")
        self.import_mode_group.addButton(self.import_mode_incremental)
        self.import_mode_group.addButton(self.import_mode_full)
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(16)
        mode_layout.addWidget(self.import_mode_incremental)
        mode_layout.addWidget(self.import_mode_full)
        mode_layout.addStretch()
        import_layout.addLayout(mode_layout)

        self.import_btn = QPushButton("导入数据")
        self.import_btn.setMinimumHeight(35)
        self.import_btn.clicked.connect(self.import_data)
        import_layout.addWidget(self.import_btn)
        
        import_group.setLayout(import_layout)
        left_layout.addWidget(import_group)

        # 截屏导入
        screenshot_group = QGroupBox("截屏导入")
        screenshot_layout = QVBoxLayout()
        screenshot_layout.setSpacing(8)

        screenshot_mode_layout = QHBoxLayout()
        screenshot_mode_layout.setSpacing(8)
        self.screenshot_list_radio = QCheckBox("订单列表截图")
        self.screenshot_list_radio.setChecked(True)
        self.screenshot_detail_radio = QCheckBox("订单详情截图")
        screenshot_mode_layout.addWidget(self.screenshot_list_radio)
        screenshot_mode_layout.addWidget(self.screenshot_detail_radio)
        screenshot_layout.addLayout(screenshot_mode_layout)

        self.screenshot_list_radio.stateChanged.connect(self._on_screenshot_mode_changed)
        self.screenshot_detail_radio.stateChanged.connect(self._on_screenshot_mode_changed)

        screenshot_file_layout = QHBoxLayout()
        screenshot_file_layout.setSpacing(8)
        self.screenshot_path = QLineEdit()
        self.screenshot_path.setReadOnly(True)
        self.screenshot_path.setMinimumWidth(150)
        self.screenshot_browse_btn = QPushButton("选择截图")
        self.screenshot_browse_btn.setMinimumWidth(80)
        self.screenshot_browse_btn.clicked.connect(self.browse_screenshots)
        screenshot_file_layout.addWidget(self.screenshot_path, 1)
        screenshot_file_layout.addWidget(self.screenshot_browse_btn)
        screenshot_layout.addLayout(screenshot_file_layout)

        self.screenshot_btn = QPushButton("开始识别截图")
        self.screenshot_btn.setMinimumHeight(35)
        self.screenshot_btn.clicked.connect(self.start_screenshot_processing)
        screenshot_layout.addWidget(self.screenshot_btn)

        screenshot_group.setLayout(screenshot_layout)
        left_layout.addWidget(screenshot_group)

        # 文件选择
        file_group = QGroupBox("视频文件")
        file_layout = QHBoxLayout()
        file_layout.setSpacing(8)
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.file_path.setMinimumWidth(150)
        self.browse_btn = QPushButton("选择视频")
        self.browse_btn.setMinimumWidth(80)
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_path, 1)
        file_layout.addWidget(self.browse_btn)
        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        # 拆帧频率
        fps_group = QGroupBox("拆帧设置")
        fps_layout = QHBoxLayout()
        fps_layout.setSpacing(8)
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["自动", "0.5 (每2秒1帧)", "1.0 (每秒1帧)", "2.0 (每秒2帧)"])
        self.fps_combo.setMinimumWidth(180)
        fps_layout.addWidget(QLabel("拆帧频率:"))
        fps_layout.addWidget(self.fps_combo, 1)
        fps_group.setLayout(fps_layout)
        left_layout.addWidget(fps_group)

        # 处理按钮和进度
        self.process_btn = QPushButton("开始提取")
        self.process_btn.setMinimumHeight(40)
        self.process_btn.clicked.connect(self.start_processing)
        left_layout.addWidget(self.process_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        left_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        left_layout.addWidget(self.status_label)

        # 筛选面板
        self.filter_widget = OrderFilterWidget()
        self.filter_widget.filter_changed.connect(self.apply_filter)
        left_layout.addWidget(self.filter_widget)

        # 汇总统计
        self.summary_widget = SummaryWidget()
        left_layout.addWidget(self.summary_widget)

        left_layout.addStretch()
        
        # 设置左侧面板滚动区域
        left_scroll.setWidget(left_panel)

        # 右侧面板
        right_panel = QSplitter(Qt.Vertical)
        
        # 表格标签页
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        self.orders_table = OrdersTable()
        self.orders_table.delete_requested.connect(self._on_delete_order)
        table_layout.addWidget(self.orders_table)
        
        # 商品明细标签页
        product_tab = QWidget()
        product_layout = QVBoxLayout(product_tab)
        self.products_table = ProductsTable()
        product_layout.addWidget(self.products_table)

        # 图表标签页
        chart_tab = QWidget()
        chart_tab.setStyleSheet("background-color: #0f1923;")
        chart_layout = QVBoxLayout(chart_tab)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        self.dashboard_view = DashboardView()
        chart_layout.addWidget(self.dashboard_view)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(table_tab, "📋 订单明细")
        self.tab_widget.addTab(product_tab, "🛍️ 商品明细")
        self.tab_widget.addTab(chart_tab, "📊 数据分析")
        self.tab_widget.tabBar().setStyleSheet("""
            QTabBar::tab {
                background-color: #1a2633;
                color: #8892a4;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0f1923;
                color: #00d4ff;
            }
            QTabBar::tab:hover {
                background-color: #2a3643;
            }
        """)
        right_panel.addWidget(self.tab_widget)

        # 右侧面板包装在滚动区域中，实现整体纵向滚动
        right_scroll = QScrollArea()
        right_scroll.setWidget(right_panel)
        right_scroll.setWidgetResizable(True)
        right_scroll.setMinimumWidth(600)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        right_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #1a2633;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3a4a5a;
                border-radius: 6px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a5a6a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        main_layout.addWidget(left_scroll)
        main_layout.addWidget(right_scroll, 1)

        self.apply_filter()

    def _load_from_db(self):
        try:
            session = get_session()
            all_orders = ImportService.get_all_orders(session)
            session.close()
            for o in all_orders:
                dt = o.get("datetime")
                if isinstance(dt, datetime):
                    o["datetime"] = dt.strftime("%Y/%m/%d %H:%M:%S")
            self.orders = all_orders
            if self.orders:
                self.summary = self._calculate_summary(self.orders)
        except Exception as e:
            print(f"[DB] 加载数据失败: {e}")
            self.orders = []
            self.summary = None

    def _persist_orders(self, orders, source_type, source_name, mode="incremental"):
        try:
            session = get_session()
            orders_copy = []
            for o in orders:
                order_copy = dict(o)
                dt_str = order_copy.get("datetime", "")
                if dt_str:
                    parsed = self._parse_date(dt_str)
                    if parsed:
                        order_copy["datetime"] = parsed
                    else:
                        order_copy["datetime"] = datetime.now()
                        print(f"[持久化] 日期格式无法解析: {dt_str}，使用当前时间")
                else:
                    order_copy["datetime"] = datetime.now()
                    print(f"[持久化] 订单缺少日期字段，使用当前时间")
                orders_copy.append(order_copy)

            if mode == "full_refresh":
                result = ImportService.import_orders_full_refresh(session, orders_copy, source_type, source_name)
            else:
                result = ImportService.import_orders(session, orders_copy, source_type, source_name)
            session.commit()
            session.close()

            self._load_from_db()
            self.apply_filter()
            if mode == "full_refresh":
                status_msg = f"全量刷新完成: 导入 {result['new_records']} 条"
            else:
                status_msg = f"导入完成: 新增 {result['new_records']} 条, 更新 {result['update_records']} 条"
            if result["failed_records"] > 0:
                status_msg += f", 失败 {result['failed_records']} 条"
            self.status_label.setText(status_msg)
        except Exception as e:
            import traceback
            session.rollback()
            session.close()
            self.status_label.setText(f"保存数据失败: {str(e)}")
            traceback.print_exc()

    def closeEvent(self, event):
        close_engine()
        super().closeEvent(event)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.mov *.avi *.webm *.mkv)"
        )
        if file_path:
            self.file_path.setText(file_path)
            self.status_label.setText("已选择视频文件")

    def browse_import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数据文件", "",
            "数据文件 (*.xlsx *.xls *.json);;Excel文件 (*.xlsx *.xls);;JSON文件 (*.json)"
        )
        if file_path:
            self.import_file_path.setText(file_path)
            self.status_label.setText("已选择数据文件")

    def import_data(self):
        import_file = self.import_file_path.text()
        if not import_file:
            self.status_label.setText("请先选择数据文件")
            return

        mode = "full_refresh" if self.import_mode_full.isChecked() else "incremental"

        if mode == "full_refresh":
            reply = QMessageBox.warning(
                self, "确认全量刷新",
                "全量刷新将删除所有现有订单数据，此操作不可撤销。\n\n确定要清除所有数据并重新导入吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        try:
            if import_file.endswith('.json'):
                self._import_json(import_file, mode)
            elif import_file.endswith(('.xlsx', '.xls')):
                self._import_excel(import_file, mode)
            else:
                self.status_label.setText("不支持的文件格式")
        except Exception as e:
            import traceback
            self.status_label.setText(f"导入失败: {str(e)}")
            traceback.print_exc()

    def _import_json(self, file_path, mode="incremental"):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'data' in data:
            data = data['data']
        
        orders = data.get('orders', [])
        source_name = os.path.basename(file_path)
        self._persist_orders(orders, "file", source_name, mode)

    def browse_screenshots(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择截图", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.webp);;所有文件 (*)"
        )
        if file_paths:
            display = f"已选择 {len(file_paths)} 张截图"
            self.screenshot_path.setText(display)
            self.screenshot_path.setProperty("selected_images", file_paths)

    def _on_screenshot_mode_changed(self, state):
        if self.sender() == self.screenshot_list_radio and state:
            self.screenshot_detail_radio.setChecked(False)
        elif self.sender() == self.screenshot_detail_radio and state:
            self.screenshot_list_radio.setChecked(False)

    def start_screenshot_processing(self):
        selected = self.screenshot_path.property("selected_images")
        if not selected:
            self.status_label.setText("请先选择截图文件")
            return

        if self.screenshot_list_radio.isChecked():
            mode = "order_list"
        else:
            mode = "order_detail"

        self.screenshot_btn.setEnabled(False)
        self.screenshot_browse_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在识别截图...")

        self.screenshot_thread = ScreenshotProcessThread(selected, mode)
        self.screenshot_thread.progress.connect(self.update_progress)
        self.screenshot_thread.finished.connect(self.on_screenshot_finished)
        self.screenshot_thread.error.connect(self.on_screenshot_error)
        self.screenshot_thread.start()

    def on_screenshot_finished(self, orders):
        if not orders:
            self.status_label.setText("截屏识别未提取到订单，请检查截图内容")
        else:
            source_name = f"screenshot_{len(orders)}_orders"
            self._persist_orders(orders, "screenshot", source_name)
            self.status_label.setText(f"截屏识别完成！共提取 {len(orders)} 条订单")

        self.screenshot_btn.setEnabled(True)
        self.screenshot_browse_btn.setEnabled(True)

    def on_screenshot_error(self, error_msg):
        self.status_label.setText(f"截屏识别错误: {error_msg}")
        self.screenshot_btn.setEnabled(True)
        self.screenshot_browse_btn.setEnabled(True)

    def _import_excel(self, file_path, mode="incremental"):
        import openpyxl
        
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        
        orders = []
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
                orders.append(order)
            except (ValueError, TypeError):
                continue
        
        source_name = os.path.basename(file_path)
        self._persist_orders(orders, "file", source_name, mode)

    def _calculate_summary(self, orders):
        from collections import defaultdict
        
        completed = [o for o in orders if o.get('status') == '已完成']
        refunded = [o for o in orders if o.get('status') == '已退款']
        qyk_orders = [o for o in orders if '亲友卡' in (o.get('tags', ''))]
        
        completed_amount = sum(float(o.get('amount', 0)) for o in completed)
        refund_amount = sum(float(o.get('amount', 0)) for o in refunded)
        qyk_amount = sum(float(o.get('amount', 0)) for o in qyk_orders if o.get('status') == '已完成')
        
        monthly = defaultdict(lambda: {"count": 0, "completed": 0, "refund": 0, 
                                        "completed_amount": 0.0, "refund_amount": 0.0})
        for o in orders:
            order_date = self._parse_date(o.get('datetime', ''))
            if order_date:
                month = order_date.strftime('%Y/%m')
                monthly[month]["count"] += 1
                if o.get('status') == '已完成':
                    monthly[month]["completed"] += 1
                    monthly[month]["completed_amount"] += float(o.get('amount', 0))
                elif o.get('status') == '已退款':
                    monthly[month]["refund"] += 1
                    monthly[month]["refund_amount"] += float(o.get('amount', 0))
        
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

    def _load_data(self, orders, summary):
        self.orders = orders
        self.summary = summary
        self.summary_widget.update_summary(summary)
        self.dashboard_view.update_dashboard(summary)
        self.apply_filter()
        self.tab_widget.setCurrentIndex(0)

    def start_processing(self):
        video_path = self.file_path.text()
        if not video_path:
            self.status_label.setText("请先选择视频文件")
            return

        # 获取拆帧频率
        fps_text = self.fps_combo.currentText()
        fps = None
        if fps_text != "自动":
            fps = float(fps_text.split()[0])

        # 禁用按钮
        self.process_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("处理中...")

        # 启动后台线程
        self.process_thread = ProcessingThread(video_path, fps)
        self.process_thread.progress.connect(self.update_progress)
        self.process_thread.finished.connect(self.on_process_finished)
        self.process_thread.error.connect(self.on_process_error)
        self.process_thread.start()

    def update_progress(self, value, msg):
        self.progress_bar.setValue(value)
        self.status_label.setText(msg)

    def on_process_finished(self, result):
        if result.get('success'):
            orders = result['data'].get('orders', [])

            video_path = self.file_path.text()
            source_name = os.path.basename(video_path) if video_path else "unknown"
            self._persist_orders(orders, "video", source_name)

            self.status_label.setText(f"处理完成！共提取 {len(orders)} 条订单")
        else:
            self.status_label.setText(f"处理失败: {result.get('error', '未知错误')}")

        self.process_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)

    def on_process_error(self, error_msg):
        self.status_label.setText(f"错误: {error_msg}")
        self.process_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)

    def _on_delete_order(self, order_id):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定删除订单 {order_id}？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        try:
            session = get_session()
            success = ImportService.delete_order(session, order_id)
            session.close()
            if success:
                self.orders = [o for o in self.orders if str(o.get('order_id')) != order_id]
                self.apply_filter()
                self.status_label.setText(f"已删除订单 {order_id}")
            else:
                self.orders = [o for o in self.orders if str(o.get('order_id')) != order_id]
                self.apply_filter()
                self.status_label.setText(f"订单 {order_id} 不在数据库中，已从列表移除")
        except Exception as e:
            self.status_label.setText(f"删除失败: {e}")
            import traceback
            traceback.print_exc()

    def apply_filter(self):
        if not self.orders:
            self.orders_table.update_data([])
            self.products_table.update_data([])
            return

        filter_params = self.filter_widget.get_filter()
        filtered = self.orders.copy()

        # 状态过滤
        if filter_params['status'] != 'all':
            filtered = [o for o in filtered if o.get('status') in filter_params['status']]

        # 标签过滤
        if filter_params['tag'] != 'all':
            filtered = [o for o in filtered if o.get('tags', '') in filter_params['tag']]

        # 金额范围过滤
        if filter_params['amount_min'] is not None:
            filtered = [o for o in filtered if float(o.get('amount', 0)) >= filter_params['amount_min']]
        if filter_params['amount_max'] is not None:
            filtered = [o for o in filtered if float(o.get('amount', 0)) <= filter_params['amount_max']]

        # 日期范围过滤
        if filter_params['date_start']:
            start_date = self._parse_date(filter_params['date_start'])
            if start_date:
                print(f"[DEBUG] 日期过滤开始: {filter_params['date_start']} -> {start_date}")
                filtered = [o for o in filtered if self._parse_date(o.get('datetime', '')) is not None and self._parse_date(o.get('datetime', '')) >= start_date]
                print(f"[DEBUG] 开始日期过滤后剩余: {len(filtered)} 条订单")
        if filter_params['date_end']:
            end_date = self._parse_date(filter_params['date_end'])
            if end_date:
                original_end_date = end_date
                end_date = end_date + timedelta(days=1) - timedelta(seconds=1)
                print(f"[DEBUG] 日期过滤结束: {filter_params['date_end']} -> {original_end_date} -> {end_date}")
                filtered = [o for o in filtered if self._parse_date(o.get('datetime', '')) is not None and self._parse_date(o.get('datetime', '')) <= end_date]
                print(f"[DEBUG] 结束日期过滤后剩余: {len(filtered)} 条订单")

        # 订单号搜索
        if filter_params['search_order_id']:
            search_str = filter_params['search_order_id']
            filtered = [o for o in filtered if search_str in str(o.get('order_id', ''))]

        # 更新表格
        self.orders_table.update_data(filtered)
        self.products_table.update_data(filtered)
        
        # 计算过滤后数据的统计信息
        filtered_summary = self._calculate_summary(filtered)
        
        print(f"[DEBUG] 月度汇总: {list(filtered_summary.get('monthly_summary', {}).keys())}")
        
        # 更新汇总统计
        self.summary_widget.update_summary(filtered_summary)
        
        # 更新数据看板 - 传递用户输入的日期范围或计算实际日期范围
        date_range_display = None
        if filter_params['date_start'] or filter_params['date_end']:
            # 使用用户输入的日期范围
            start_str = filter_params['date_start'] or 'N/A'
            end_str = filter_params['date_end'] or 'N/A'
            date_range_display = f"{start_str} - {end_str}"
        elif filtered:
            # 没有日期过滤时，计算从第一个订单到最后一个订单的日期范围
            dates = []
            for order in filtered:
                order_date = self._parse_date(order.get('datetime', ''))
                if order_date:
                    dates.append(order_date)
            
            if dates:
                min_date = min(dates)
                max_date = max(dates)
                # 格式化为 YYYY/MM/DD
                min_str = min_date.strftime('%Y/%m/%d')
                max_str = max_date.strftime('%Y/%m/%d')
                date_range_display = f"{min_str} - {max_str}"
        
        self.dashboard_view.update_dashboard(filtered_summary, date_range_display)
        
        # 更新状态显示
        self.status_label.setText(f"显示 {len(filtered)} 条订单（共 {len(self.orders)} 条）")


    @staticmethod
    def _parse_date(date_str):
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Heiti SC", 11))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

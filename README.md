# 视频订单提取服务

从购物App录屏视频中自动提取订单信息，生成Excel报表。

## 技术栈

- Python 3.10+
- FastAPI（Web服务）
- ffmpeg（视频拆帧）
- openpyxl（生成Excel）
- OpenAI兼容视觉API（图片OCR识别）
  - 推荐模型：豆包-1.5-vision-pro / 通义千问-VL-max / GPT-4o

## 安装

```bash
# 系统依赖
# Ubuntu/Debian: apt install ffmpeg
# macOS: brew install ffmpeg
# CentOS: yum install ffmpeg

# Python依赖
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env`，填入你的API配置：

```bash
cp .env.example .env
```

## 启动

```bash
python main.py
# 服务启动在 http://0.0.0.0:8000
```

## API

### 提取订单

```bash
POST /api/extract-orders
Content-Type: multipart/form-data

参数：
  video: 视频文件（必填）
  fps: 拆帧频率，默认0.5（每2秒1帧）

返回：
{
  "success": true,
  "data": {
    "total_orders": 146,
    "completed_count": 139,
    "refund_count": 7,
    "completed_amount": 31352.20,
    "refund_amount": -566.10,
    "net_amount": 30786.10,
    "orders": [...],
    "monthly_summary": {...},
    "excel_url": "/download/orders_20260528_234321.xlsx"
  }
}
```

### 下载Excel

```bash
GET /download/{filename}
```

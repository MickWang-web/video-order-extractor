"""
配置管理
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 视觉大模型API
VISION_API_BASE = os.getenv("VISION_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")
VISION_API_KEY = os.getenv("VISION_API_KEY", "")
VISION_MODEL = os.getenv("VISION_MODEL", "doubao-1.5-vision-pro-32k")

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# 文件存储
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
FRAMES_DIR = os.path.join(os.path.dirname(__file__), "frames")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "download")

# 数据库路径
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DATA_DIR, "orders.db")

# 确保目录存在
for d in [UPLOAD_DIR, FRAMES_DIR, OUTPUT_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)
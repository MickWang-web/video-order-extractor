"""
配置管理
"""

import os
from dotenv import load_dotenv

load_dotenv()

VISION_API_BASE = os.getenv("VISION_API_BASE", "https://ark.cn-beijing.volces.com/api/v3")
VISION_API_KEY = os.getenv("VISION_API_KEY", "")
VISION_MODEL = os.getenv("VISION_MODEL", "doubao-1.5-vision-pro-32k")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
FRAMES_DIR = os.path.join(BASE_DIR, "frames")
OUTPUT_DIR = os.path.join(BASE_DIR, "download")
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "orders.db")

for d in [UPLOAD_DIR, FRAMES_DIR, OUTPUT_DIR, DATA_DIR]:
    os.makedirs(d, exist_ok=True)

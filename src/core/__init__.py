"""
Core module - 核心配置和工具
"""

from src.core.config import (
    VISION_API_BASE,
    VISION_API_KEY,
    VISION_MODEL,
    HOST,
    PORT,
    UPLOAD_DIR,
    FRAMES_DIR,
    OUTPUT_DIR,
    DATA_DIR,
    DB_PATH,
)
from src.core.prompts import (
    ORDER_LIST_PROMPT,
    ORDER_DETAIL_PROMPT,
    OCR_PROMPT,
)
from src.core.exceptions import (
    VideoProcessingError,
    RecognitionError,
    DataParseError,
)

__all__ = [
    "VISION_API_BASE",
    "VISION_API_KEY",
    "VISION_MODEL",
    "HOST",
    "PORT",
    "UPLOAD_DIR",
    "FRAMES_DIR",
    "OUTPUT_DIR",
    "DATA_DIR",
    "DB_PATH",
    "ORDER_LIST_PROMPT",
    "ORDER_DETAIL_PROMPT",
    "OCR_PROMPT",
    "VideoProcessingError",
    "RecognitionError",
    "DataParseError",
]

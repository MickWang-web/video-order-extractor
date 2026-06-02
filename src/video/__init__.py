"""
视频处理模块
"""

from src.video.extractor import extract_frames, smart_extract_frames, get_video_duration
from src.video.recognizer import (
    recognize_frame, recognize_all_frames, parse_orders_from_text,
    get_vision_client, image_to_base64
)
from src.video.deduplicator import deduplicate_orders
from src.video.aggregator import generate_summary
from src.video.processor import process_video

__all__ = [
    "extract_frames",
    "smart_extract_frames",
    "get_video_duration",
    "recognize_frame",
    "recognize_all_frames",
    "parse_orders_from_text",
    "get_vision_client",
    "image_to_base64",
    "deduplicate_orders",
    "generate_summary",
    "process_video",
]

"""
视频帧提取模块
"""

import os
import json
import subprocess
from typing import Optional

from src.core.config import FRAMES_DIR


def extract_frames(video_path: str, fps: float = 0.5, output_dir: Optional[str] = None) -> list[str]:
    """
    使用 ffmpeg 从视频中提取关键帧

    Args:
        video_path: 视频文件路径
        fps: 每秒提取帧数，0.5表示每2秒1帧
        output_dir: 帧图片输出目录

    Returns:
        帧图片路径列表
    """
    if output_dir is None:
        output_dir = FRAMES_DIR

    os.makedirs(output_dir, exist_ok=True)

    output_pattern = os.path.join(output_dir, "frame_%04d.jpg")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",
        output_pattern
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg执行失败: {result.stderr}")

    frames = sorted([
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if f.startswith("frame_") and f.endswith(".jpg")
    ])

    return frames


def smart_extract_frames(video_path: str, output_dir: Optional[str] = None) -> list[str]:
    """
    智能拆帧：根据视频时长自动选择合适的帧率

    - ≤10秒：每秒1帧
    - 10-60秒：每2秒1帧
    - 60-300秒：每3秒1帧
    - >300秒：每5秒1帧
    """
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duration = float(json.loads(result.stdout)["format"]["duration"])

    if duration <= 10:
        fps = 1.0
    elif duration <= 60:
        fps = 0.5
    elif duration <= 300:
        fps = 1.0 / 3
    else:
        fps = 0.2

    print(f"视频时长: {duration:.1f}秒, 拆帧频率: {fps}fps")
    return extract_frames(video_path, fps, output_dir)


def get_video_duration(video_path: str) -> float:
    """获取视频时长（秒）"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(json.loads(result.stdout)["format"]["duration"])

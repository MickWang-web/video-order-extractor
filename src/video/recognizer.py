"""
视觉识别模块
"""

import os
import re
import json
import base64
import time
from typing import Optional

from openai import OpenAI

from src.core.config import VISION_API_BASE, VISION_API_KEY, VISION_MODEL
from src.core.prompts import OCR_PROMPT


def get_vision_client() -> OpenAI:
    """获取视觉大模型客户端（OpenAI兼容接口）"""
    return OpenAI(
        base_url=VISION_API_BASE,
        api_key=VISION_API_KEY
    )


def image_to_base64(image_path: str) -> str:
    """将图片转为base64编码"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def recognize_frame(client: OpenAI, image_path: str) -> list[dict]:
    """
    调用视觉大模型识别单帧图片中的订单信息

    Args:
        client: OpenAI客户端
        image_path: 帧图片路径

    Returns:
        识别到的订单列表
    """
    b64 = image_to_base64(image_path)

    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": OCR_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.1
        )

        text = response.choices[0].message.content
        orders = parse_orders_from_text(text)
        return orders

    except Exception as e:
        import traceback
        error_msg = f"识别帧 {image_path} 失败: {type(e).__name__}: {e}"
        print(error_msg)
        print("完整错误堆栈:")
        print(traceback.format_exc())
        raise


def parse_orders_from_text(text: str) -> list[dict]:
    """
    从模型返回文本中解析JSON订单数据
    模型返回可能包含 ``` json ... ``` 包裹，需要提取
    """
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = text.strip()

    try:
        orders = json.loads(json_str)
        if isinstance(orders, list):
            return orders
    except json.JSONDecodeError:
        pass

    bracket_match = re.search(r'\[[\s\S]*\]', text)
    if bracket_match:
        try:
            orders = json.loads(bracket_match.group())
            if isinstance(orders, list):
                return orders
        except json.JSONDecodeError:
            pass

    print(f"无法解析模型返回: {text[:200]}")
    return []


def recognize_all_frames(frame_paths: list[str], batch_size: int = 3) -> list[dict]:
    """
    批量识别所有帧

    Args:
        frame_paths: 帧图片路径列表
        batch_size: 并发识别的批次大小（避免API限流）

    Returns:
        所有识别到的订单（含重复）
    """
    client = get_vision_client()
    all_orders = []

    total = len(frame_paths)
    for i, frame_path in enumerate(frame_paths):
        print(f"正在识别第 {i+1}/{total} 帧: {os.path.basename(frame_path)}")

        orders = recognize_frame(client, frame_path)
        all_orders.extend(orders)
        print(f"  识别到 {len(orders)} 条订单")

        if (i + 1) % batch_size == 0 and i + 1 < total:
            print("  等待1秒避免限流...")
            time.sleep(1)

    return all_orders

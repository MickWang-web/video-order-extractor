"""
视频处理主流程
"""

import os
from datetime import datetime
from typing import Optional

from src.video.extractor import extract_frames, smart_extract_frames
from src.video.recognizer import recognize_all_frames
from src.video.deduplicator import deduplicate_orders
from src.video.aggregator import generate_summary
from src.excel.generator import generate_excel


def process_video(video_path: str, fps: Optional[float] = None) -> dict:
    """
    完整的视频订单提取流程

    Args:
        video_path: 视频文件路径
        fps: 拆帧频率，None为自动

    Returns:
        处理结果字典
    """
    print("=" * 50)
    print("开始处理视频...")

    print("\n[1/4] 提取视频帧...")
    if fps:
        frames = extract_frames(video_path, fps)
    else:
        frames = smart_extract_frames(video_path)
    print(f"共提取 {len(frames)} 帧")

    if not frames:
        return {"success": False, "error": "未能提取到任何帧，请检查视频文件"}

    print("\n[2/4] 识别订单信息...")
    raw_orders = recognize_all_frames(frames)
    print(f"原始识别到 {len(raw_orders)} 条订单（含重复）")

    print("\n[3/4] 去重汇总...")
    orders = deduplicate_orders(raw_orders)
    summary = generate_summary(orders)
    print(f"去重后 {summary['total_orders']} 条订单")
    print(f"已完成 {summary['completed_count']} 笔，退款 {summary['refund_count']} 笔")
    print(f"净消费: ¥{summary['net_amount']:.2f}")

    print("\n[4/4] 生成Excel...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"orders_{timestamp}.xlsx"
    excel_path = generate_excel(orders, summary, excel_filename)
    print(f"Excel已保存: {excel_path}")

    for f in frames:
        try:
            os.remove(f)
        except:
            pass

    print("\n处理完成！")
    print("=" * 50)

    return {
        "success": True,
        "data": {
            **summary,
            "orders": orders,
            "excel_filename": excel_filename
        }
    }

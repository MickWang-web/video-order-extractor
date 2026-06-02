"""
本地测试脚本 - 不需要启动服务，直接处理本地视频文件
用法: python test_local.py your_video.mp4
"""
import sys
import os

from src.video import process_video


def main():
    if len(sys.argv) < 2:
        print("用法: python test_local.py <视频文件路径> [拆帧fps]")
        print("示例: python test_local.py video.mp4 0.5")
        sys.exit(1)
    
    video_path = sys.argv[1]
    fps = float(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not os.path.exists(video_path):
        print(f"文件不存在: {video_path}")
        sys.exit(1)
    
    result = process_video(video_path, fps=fps)
    
    if result["success"]:
        data = result["data"]
        print(f"\n{'='*50}")
        print(f"处理结果汇总:")
        print(f"  总订单数: {data['total_orders']}")
        print(f"  已完成: {data['completed_count']} 笔, 金额 ¥{data['completed_amount']:.2f}")
        print(f"  已退款: {data['refund_count']} 笔, 金额 ¥{data['refund_amount']:.2f}")
        print(f"  净消费: ¥{data['net_amount']:.2f}")
        print(f"  Excel文件: download/{data['excel_filename']}")
        print(f"{'='*50}")
    else:
        print(f"处理失败: {result.get('error', '未知错误')}")


if __name__ == "__main__":
    main()

"""
主服务入口
"""
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import HOST, PORT, UPLOAD_DIR, OUTPUT_DIR
from video_processor import process_video

app = FastAPI(
    title="视频订单提取服务",
    description="上传购物App录屏视频，自动提取订单信息并生成Excel报表",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "视频订单提取服务运行中"}

# 跨域支持（如果需要前端调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/extract-orders")
async def extract_orders(
    video: UploadFile = File(..., description="购物App录屏视频文件"),
    fps: Optional[float] = Form(None, description="拆帧频率，如0.5表示每2秒1帧，不填则自动")
):
    """
    上传视频，提取订单信息，生成Excel报表
    """
    # 验证文件类型
    allowed_types = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"]
    if video.content_type and video.content_type not in allowed_types:
        # 有些浏览器上传mp4时content-type不对，放宽限制
        if not video.filename.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.mkv')):
            raise HTTPException(status_code=400, detail=f"不支持的视频格式: {video.content_type}")
    
    # 保存上传的视频
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = f"upload_{timestamp}_{uuid.uuid4().hex[:8]}.mp4"
    video_path = os.path.join(UPLOAD_DIR, video_filename)
    
    try:
        with open(video_path, "wb") as f:
            content = await video.read()
            f.write(content)
        
        print(f"收到视频: {video.filename}, 大小: {len(content)/1024/1024:.1f}MB")
        
        # 处理视频
        result = process_video(video_path, fps=fps)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "处理失败"))
        
        # 构建返回数据（不包含完整订单列表，太大）
        data = result["data"]
        response = {
            "success": True,
            "data": {
                "total_orders": data["total_orders"],
                "completed_count": data["completed_count"],
                "refund_count": data["refund_count"],
                "completed_amount": data["completed_amount"],
                "refund_amount": data["refund_amount"],
                "net_amount": data["net_amount"],
                "qyk_count": data["qyk_count"],
                "qyk_completed_amount": data["qyk_completed_amount"],
                "monthly_summary": data["monthly_summary"],
                "excel_url": f"/download/{data['excel_filename']}",
                "order_count": len(data.get("orders", []))
            }
        }
        
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理视频时出错: {str(e)}")
    finally:
        # 清理上传的视频文件
        try:
            os.remove(video_path)
        except:
            pass


@app.get("/download/{filename}")
async def download_excel(filename: str):
    """下载生成的Excel文件"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "video-order-extractor"}


if __name__ == "__main__":
    import uvicorn
    print(f"启动视频订单提取服务: http://{HOST}:{PORT}")
    print(f"API文档: http://{HOST}:{PORT}/docs")
    uvicorn.run(app, host=HOST, port=PORT)

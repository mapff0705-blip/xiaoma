
import json
from uuid import uuid4
from threading import Thread
import os
import base64
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile,File,Form
from fastapi.middleware.cors import CORSMiddleware
from utils.jobManager import get_job_by_id
from tasks import app as celery_app
from typing import Optional
from dotenv import load_dotenv

from dashscope import MultiModalConversation
load_dotenv(override=True)


QWEN_VL_API_KEY = os.getenv("QWEN_VL_API_KEY")
os.environ["DASHSCOPE_API_KEY"] = QWEN_VL_API_KEY
# 服务访问的端口
PORT = 8012

def image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("服务初始化完成")
    yield
    print("正在关闭...")


app = FastAPI(lifespan=lifespan)

# 启用CORS，允许任何来源访问以 /api/ 开头的接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/crewai")
async def run_flow(
        target_platform: str = Form(...),
        creator_niche: str = Form(...),
        file: Optional[UploadFile] = File(None)
):
    try:
        final_description = creator_niche

        # 如果上传了图片，调用 Qwen-VL 多模态 API
        if file:
            image_bytes = await file.read()
            if not image_bytes:
                raise HTTPException(status_code=400, detail="图片内容为空")

            image_b64 = image_to_base64(image_bytes)

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{image_b64}"},
                        {"text": "请详细描述这张图片的内容，包括物体、场景、文字、风格等关键信息。"}
                    ]
                }
            ]
            try:
                response = MultiModalConversation.call(
                    model="qwen-vl-plus",
                    messages=messages,
                    api_key=QWEN_VL_API_KEY
                )

                if response.status_code != 200:
                    raise Exception(f"API Error {response.code}: {response.message}")

                image_desc = response.output.choices[0].message.content[0]["text"]
                print("这个图片的内容是"+image_desc)
                final_description = (
                    f"用户原始描述：{creator_niche}\n\n"
                    f"图片内容分析：{image_desc}"
                )

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Qwen-VL 图像理解失败: {str(e)}")

        job_id = str(uuid4())
        inputData = {
            "target_platform": target_platform,
            "creator_niche": final_description
        }

        celery_app.send_task('tasks.kickoff_flow', args=[job_id, inputData])
        return {"job_id": job_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"启动作业时出错:\n\n {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# GET接口 /api/crew/{job_id}，查询特定作业状态
@app.get("/api/crewai/{job_id}")
async def get_status(job_id: str):
    job = get_job_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # 尝试解析作业结果为JSON格式
    try:
        result_json = json.loads(str(job.result))
    except json.JSONDecodeError:
        result_json = str(job.result)

    # 返回作业ID、状态、结果和事件的JSON响应
    return {
        "job_id": job_id,
        "status": job.status,
        "result": result_json,
        "events": [{"timestamp": event.timestamp.isoformat(), "data": event.data} for event in job.events]
    }

if __name__ == '__main__':
    print(f"在端口 {PORT} 上启动服务器")
    uvicorn.run(app, host="0.0.0.0", port=PORT)

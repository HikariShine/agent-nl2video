"""FastAPI主应用"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import trending, script, video, workflow
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config.settings import settings

app = FastAPI(
    title="NL2TK API",
    description="Natural Language to TikTok - 自动化短视频生成平台",
    version="1.0.0",
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trending.router, prefix="/api/v1/trending", tags=["热点追踪"])
app.include_router(script.router, prefix="/api/v1/script", tags=["剧本生成"])
app.include_router(video.router, prefix="/api/v1/video", tags=["视频生成"])
app.include_router(workflow.router, prefix="/api/v1/workflow", tags=["工作流"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "NL2TK API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


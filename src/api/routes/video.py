"""视频生成API路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...video_generator.generator import VideoGenerator
from ...script_generator.models import Script, Scene
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from config.settings import settings

router = APIRouter()

# 配置
VIDEO_CONFIG = {
    "strategy": "sora",
    "strategy_config": {
        "api_key": settings.openai_api_key,
        "storage_path": settings.videos_path,
    },
    "post_process": {
        "add_subtitles": True,
        "add_music": True,
    },
}


class GenerateVideoRequest(BaseModel):
    """生成视频请求"""
    script_id: Optional[str] = None
    script: Optional[dict] = None  # 剧本数据


@router.post("/generate", response_model=dict)
async def generate_video(request: GenerateVideoRequest):
    """
    生成视频
    
    Args:
        request: 生成请求
        
    Returns:
        生成的视频信息
    """
    try:
        generator = VideoGenerator(VIDEO_CONFIG)
        
        if request.script:
            # 从提供的剧本数据创建Script对象
            script_data = request.script
            scenes = [
                Scene(
                    scene_id=scene.get("scene_id", i+1),
                    duration=scene.get("duration", 5),
                    visual=scene.get("visual", ""),
                    narration=scene.get("narration", ""),
                    subtitles=scene.get("subtitles", ""),
                    music=scene.get("music"),
                )
                for i, scene in enumerate(script_data.get("scenes", []))
            ]
            
            script = Script(
                title=script_data.get("title", "未命名视频"),
                duration=script_data.get("duration", 60),
                scenes=scenes,
                hashtags=script_data.get("hashtags", []),
                description=script_data.get("description", ""),
            )
        elif request.script_id:
            # 从数据库获取剧本
            # TODO: 从数据库获取剧本
            raise HTTPException(status_code=400, detail="暂不支持从剧本ID生成，请提供script数据")
        else:
            raise HTTPException(status_code=400, detail="必须提供script或script_id")
        
        video_result = await generator.generate(script)
        
        return {
            "video_id": video_result.video_id,
            "file_path": video_result.file_path,
            "file_size": video_result.file_size,
            "duration": video_result.duration,
            "resolution": video_result.resolution,
            "format": video_result.format,
            "status": video_result.status,
            "generation_strategy": video_result.generation_strategy,
            "generation_time": video_result.generation_time,
            "error_message": video_result.error_message,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}")
async def get_video(video_id: str):
    """
    获取视频信息
    
    Args:
        video_id: 视频ID
        
    Returns:
        视频信息
    """
    # TODO: 从数据库获取视频信息
    raise HTTPException(status_code=404, detail="视频不存在")


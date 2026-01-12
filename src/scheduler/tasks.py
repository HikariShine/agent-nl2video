"""工作流任务定义"""
from ..trending_tracker.manager import TrendingTrackerManager
from ..script_generator.generator import ScriptGenerator
from ..video_generator.generator import VideoGenerator
from ..database.models import db
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config.settings import settings


# 全局配置（实际应该从配置文件读取）
TRENDING_CONFIG = {
    "trending_sources": [
        {
            "name": "douyin_hot",
            "type": "scraper",
            "enabled": True,
        }
    ]
}

SCRIPT_CONFIG = {
    "strategy": "qwen",
    "strategy_config": {
        "model": "qwen-max",
        "api_key": settings.qwen_api_key,
    },
    "temperature": 0.7,
    "max_tokens": 2000,
}

VIDEO_CONFIG = {
    "strategy": "cogvideox",  # 使用 CogVideoX 本地 AI 视频生成
    "strategy_config": {
        "storage_path": settings.videos_path,
        "model_id": "THUDM/CogVideoX-2b",  # 2B版本，适合M4
        "lazy_load": True,  # 延迟加载模型
    },
    "post_process": {
        "add_subtitles": False,  # CogVideoX生成的视频不需要额外添加字幕
        "add_music": False,
    },
}


async def fetch_trending_task(context: dict = None):
    """
    获取热点任务
    
    Args:
        context: 执行上下文
        
    Returns:
        热点数据列表
    """
    if context is None:
        context = {}
    
    manager = TrendingTrackerManager(TRENDING_CONFIG)
    trending_items = await manager.get_trending_top(limit=5)
    
    context["trending_items"] = trending_items
    return trending_items


async def generate_script_task(trending_items=None, context: dict = None):
    """
    生成剧本任务
    
    Args:
        trending_items: 热点数据列表
        context: 执行上下文
        
    Returns:
        生成的剧本列表
    """
    if context is None:
        context = {}
    if trending_items is None:
        trending_items = context.get("trending_items", [])
    
    generator = ScriptGenerator(SCRIPT_CONFIG)
    scripts = []
    
    for item in trending_items[:3]:  # 只处理前3个热点
        try:
            script = await generator.generate_from_trending(item, duration=60)
            
            # 保存剧本到数据库
            script_dict = script.to_dict()
            script_id = f"script_{int(time.time())}"
            script_dict["id"] = script_id
            script_dict["trending_id"] = item.id
            script_dict["llm_model"] = script.llm_model
            script_dict["created_at"] = script.created_at.isoformat() if script.created_at else None
            saved_id = db.save_script(script_dict)
            print(f"✅ 剧本已保存: {saved_id} -> {db.db_path}/script_{saved_id}.json")
            
            scripts.append(script)
        except Exception as e:
            print(f"生成剧本失败: {e}")
    
    context["scripts"] = scripts
    return scripts


async def generate_video_task(scripts=None, context: dict = None):
    """
    生成视频任务
    
    Args:
        scripts: 剧本列表
        context: 执行上下文
        
    Returns:
        生成的视频列表
    """
    if context is None:
        context = {}
    if scripts is None:
        scripts = context.get("scripts", [])
    
    generator = VideoGenerator(VIDEO_CONFIG)
    videos = []
    
    for script in scripts:
        try:
            video = await generator.generate(script)
            videos.append(video)
        except Exception as e:
            print(f"生成视频失败: {e}")
    
    context["videos"] = videos
    return videos


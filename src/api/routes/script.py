"""剧本生成API路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...script_generator.generator import ScriptGenerator
from ...script_generator.models import Script
from ...database.models import db
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from config.settings import settings

router = APIRouter()

# 配置
SCRIPT_CONFIG = {
    "strategy": "qwen",
    "strategy_config": {
        "model": "qwen-max",
        "api_key": settings.qwen_api_key,
    },
    "temperature": 0.7,
    "max_tokens": 2000,
}


class GenerateScriptRequest(BaseModel):
    """生成剧本请求"""
    trending_id: Optional[str] = None
    prompt: Optional[str] = None
    duration: int = 60


@router.post("/generate", response_model=dict)
async def generate_script(request: GenerateScriptRequest):
    """
    生成剧本
    
    Args:
        request: 生成请求
        
    Returns:
        生成的剧本
    """
    try:
        generator = ScriptGenerator(SCRIPT_CONFIG)
        
        if request.prompt:
            # 从自定义提示词生成
            script = await generator.generate_from_prompt(request.prompt)
        elif request.trending_id:
            # 从热点生成（需要先获取热点数据）
            trending_item = db.get_trending(request.trending_id)
            if not trending_item:
                raise HTTPException(status_code=404, detail="热点不存在")
            # TODO: 将trending_item转换为TrendingItem对象
            raise HTTPException(status_code=400, detail="暂不支持从热点ID生成，请使用prompt")
        else:
            raise HTTPException(status_code=400, detail="必须提供prompt或trending_id")
        
        # 保存剧本到数据库
        script_dict = script.to_dict()
        script_id = f"script_{int(time.time())}"
        script_dict["id"] = script_id
        script_dict["llm_model"] = script.llm_model
        script_dict["created_at"] = script.created_at.isoformat() if script.created_at else None
        saved_id = db.save_script(script_dict)
        
        script_dict["id"] = saved_id
        return script_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{script_id}")
async def get_script(script_id: str):
    """
    获取剧本详情
    
    Args:
        script_id: 剧本ID
        
    Returns:
        剧本详情
    """
    script_data = db.get_script(script_id)
    if not script_data:
        raise HTTPException(status_code=404, detail="剧本不存在")
    return script_data


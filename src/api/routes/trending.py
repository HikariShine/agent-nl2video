"""热点追踪API路由"""
from fastapi import APIRouter, HTTPException
from typing import List
from ...trending_tracker.manager import TrendingTrackerManager
from ...trending_tracker.models import TrendingItem

router = APIRouter()

# 配置（实际应该从配置文件读取）
TRENDING_CONFIG = {
    "trending_sources": [
        {
            "name": "douyin_hot",
            "type": "scraper",
            "enabled": True,
        }
    ]
}


@router.get("/", response_model=List[dict])
async def get_trending(limit: int = 10):
    """
    获取热点列表
    
    Args:
        limit: 返回数量限制
        
    Returns:
        热点数据列表
    """
    try:
        manager = TrendingTrackerManager(TRENDING_CONFIG)
        items = await manager.get_trending_top(limit=limit)
        
        # 转换为字典格式
        return [{
            "id": item.id,
            "source": item.source,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "heat_value": item.heat_value,
            "trending_score": item.trending_score,
            "keywords": item.keywords,
            "url": item.url,
        } for item in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{source}")
async def get_trending_by_source(source: str, limit: int = 10):
    """
    按数据源获取热点
    
    Args:
        source: 数据源名称
        limit: 返回数量限制
        
    Returns:
        热点数据列表
    """
    try:
        manager = TrendingTrackerManager(TRENDING_CONFIG)
        all_items = await manager.fetch_all()
        
        # 过滤指定数据源
        filtered_items = [item for item in all_items if item.source == source]
        filtered_items = filtered_items[:limit]
        
        return [{
            "id": item.id,
            "source": item.source,
            "title": item.title,
            "description": item.description,
            "category": item.category,
            "heat_value": item.heat_value,
            "trending_score": item.trending_score,
            "keywords": item.keywords,
            "url": item.url,
        } for item in filtered_items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


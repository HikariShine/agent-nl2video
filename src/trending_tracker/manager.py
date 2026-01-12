"""热点追踪管理器"""
from typing import List, Dict
from .adapter import TrendingSourceAdapter
from .douyin_adapter import DouyinScraperAdapter
from .models import TrendingItem
import asyncio


class TrendingTrackerManager:
    """热点追踪管理器"""
    
    def __init__(self, config: dict):
        """
        初始化管理器
        
        Args:
            config: 配置字典，包含所有数据源配置
        """
        self.config = config
        self.adapters: Dict[str, TrendingSourceAdapter] = {}
        self._init_adapters()
    
    def _init_adapters(self):
        """初始化所有数据源适配器"""
        sources_config = self.config.get("trending_sources", [])
        
        for source_config in sources_config:
            if not source_config.get("enabled", True):
                continue
            
            source_type = source_config.get("type", "scraper")
            source_name = source_config.get("name", "unknown")
            
            # 根据类型创建适配器
            if source_name == "douyin_hot" or source_type == "scraper":
                adapter = DouyinScraperAdapter(source_config)
                self.adapters[source_name] = adapter
            # 可以在这里添加其他适配器
            # elif source_name == "chanmama_api":
            #     adapter = ChanmamaAPIAdapter(source_config)
            #     self.adapters[source_name] = adapter
    
    async def fetch_all(self) -> List[TrendingItem]:
        """
        从所有启用的数据源获取热点数据
        
        Returns:
            合并后的热点数据列表
        """
        tasks = []
        for adapter in self.adapters.values():
            if adapter.validate_config():
                tasks.append(adapter.fetch())
        
        # 并发获取所有数据源的数据
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        all_items = []
        for result in results:
            if isinstance(result, Exception):
                print(f"获取热点数据失败: {result}")
                continue
            if isinstance(result, list):
                all_items.extend(result)
        
        # 去重（根据标题和URL）
        unique_items = self._deduplicate(all_items)
        
        # 按热度排序
        unique_items.sort(key=lambda x: x.trending_score, reverse=True)
        
        return unique_items
    
    def _deduplicate(self, items: List[TrendingItem]) -> List[TrendingItem]:
        """
        去重处理
        
        Args:
            items: 原始热点数据列表
            
        Returns:
            去重后的列表
        """
        seen = set()
        unique_items = []
        
        for item in items:
            # 使用标题和URL作为唯一标识
            key = (item.title.lower().strip(), item.url)
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        return unique_items
    
    async def get_trending_top(self, limit: int = 10) -> List[TrendingItem]:
        """
        获取Top N热点
        
        Args:
            limit: 返回数量限制
            
        Returns:
            Top N热点列表
        """
        all_items = await self.fetch_all()
        return all_items[:limit]


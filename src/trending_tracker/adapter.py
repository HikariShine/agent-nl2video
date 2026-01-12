"""数据源适配器基类"""
from abc import ABC, abstractmethod
from typing import List
from .models import TrendingItem


class TrendingSourceAdapter(ABC):
    """热点数据源适配器基类"""
    
    def __init__(self, config: dict):
        """
        初始化适配器
        
        Args:
            config: 配置字典，包含数据源相关配置
        """
        self.config = config
        self.source_name = config.get("name", "unknown")
        self.enabled = config.get("enabled", True)
    
    @abstractmethod
    async def fetch(self) -> List[TrendingItem]:
        """
        获取热点数据
        
        Returns:
            热点数据列表
        """
        pass
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            配置是否有效
        """
        return self.enabled
    
    def get_rate_limit(self) -> dict:
        """
        获取速率限制配置
        
        Returns:
            速率限制配置，格式: {"requests": 100, "period": 3600}
        """
        return self.config.get("rate_limit", {"requests": 100, "period": 3600})


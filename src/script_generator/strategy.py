"""LLM策略基类"""
from abc import ABC, abstractmethod
from typing import Optional
from .models import Script


class LLMStrategy(ABC):
    """LLM策略基类"""
    
    def __init__(self, config: dict):
        """
        初始化策略
        
        Args:
            config: 配置字典，包含API密钥等
        """
        self.config = config
        self.model_name = config.get("model_name", "default")
    
    @abstractmethod
    async def generate(self, prompt: str, config: Optional[dict] = None) -> Script:
        """
        生成剧本
        
        Args:
            prompt: 提示词
            config: 生成配置（temperature, max_tokens等）
            
        Returns:
            生成的剧本对象
        """
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """
        验证API密钥是否有效
        
        Returns:
            是否有效
        """
        pass
    
    def estimate_cost(self, tokens: int) -> float:
        """
        估算成本
        
        Args:
            tokens: token数量
            
        Returns:
            预估成本（元）
        """
        # 默认实现，子类可覆盖
        return 0.0


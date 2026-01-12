"""视频生成策略基类"""
from abc import ABC, abstractmethod
from typing import Optional
from ..script_generator.models import Script
from .models import VideoResult


class VideoGenerationStrategy(ABC):
    """视频生成策略基类"""
    
    def __init__(self, config: dict):
        """
        初始化策略
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.strategy_name = config.get("name", "unknown")
    
    @abstractmethod
    async def generate(self, script: Script, output_path: Optional[str] = None) -> VideoResult:
        """
        生成视频
        
        Args:
            script: 剧本对象
            output_path: 输出路径（可选）
            
        Returns:
            视频生成结果
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> dict:
        """
        获取策略能力信息
        
        Returns:
            能力信息字典，包含支持的分辨率、时长等
        """
        pass
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            是否有效
        """
        return True


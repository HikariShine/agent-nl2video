"""剧本生成器"""
from typing import Optional
from .strategy import LLMStrategy
from .qwen_strategy import QwenStrategy
from .prompt_templates import PromptTemplates
from .models import Script
from ..trending_tracker.models import TrendingItem


class ScriptGenerator:
    """剧本生成器"""
    
    def __init__(self, config: dict):
        """
        初始化生成器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.strategy: Optional[LLMStrategy] = None
        self._init_strategy()
    
    def _init_strategy(self):
        """初始化LLM策略"""
        strategy_type = self.config.get("strategy", "qwen")
        strategy_config = self.config.get("strategy_config", {})
        
        if strategy_type == "qwen":
            self.strategy = QwenStrategy(strategy_config)
        # 可以在这里添加其他策略
        # elif strategy_type == "hunyuan":
        #     self.strategy = HunyuanStrategy(strategy_config)
    
    async def generate_from_trending(self, trending_item: TrendingItem, 
                                     duration: int = 60) -> Script:
        """
        基于热点生成剧本
        
        Args:
            trending_item: 热点数据项
            duration: 视频时长（秒）
            
        Returns:
            生成的剧本
        """
        # 构建提示词
        prompt = PromptTemplates.script_generation_template(
            trending_title=trending_item.title,
            trending_description=trending_item.description,
            keywords=trending_item.keywords,
            duration=duration,
        )
        
        # 生成配置
        generation_config = {
            "temperature": self.config.get("temperature", 0.7),
            "max_tokens": self.config.get("max_tokens", 2000),
        }
        
        # 调用LLM生成剧本
        script = await self.strategy.generate(prompt, generation_config)
        
        # 关联热点ID
        script.trending_id = trending_item.id
        
        return script
    
    async def generate_from_prompt(self, prompt: str, 
                                   config: Optional[dict] = None) -> Script:
        """
        基于自定义提示词生成剧本
        
        Args:
            prompt: 自定义提示词
            config: 生成配置
            
        Returns:
            生成的剧本
        """
        if config is None:
            config = {}
        
        return await self.strategy.generate(prompt, config)


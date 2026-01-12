"""视频生成器"""
from typing import Optional
from ..script_generator.models import Script
from .strategy import VideoGenerationStrategy
from .sora_strategy import SoraStrategy
from .local_strategy import LocalVideoStrategy
from .cogvideo_strategy import CogVideoXStrategy
from .post_processor import VideoPostProcessor
from .models import VideoResult


class VideoGenerator:
    """视频生成器"""
    
    def __init__(self, config: dict):
        """
        初始化生成器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.strategy: Optional[VideoGenerationStrategy] = None
        self.post_processor: Optional[VideoPostProcessor] = None
        self._init_strategy()
        self._init_post_processor()
    
    def _init_strategy(self):
        """初始化视频生成策略"""
        strategy_type = self.config.get("strategy", "cogvideox")  # 默认使用CogVideoX
        strategy_config = self.config.get("strategy_config", {})
        
        if strategy_type == "cogvideox":
            self.strategy = CogVideoXStrategy(strategy_config)
        elif strategy_type == "local":
            self.strategy = LocalVideoStrategy(strategy_config)
        elif strategy_type == "sora":
            self.strategy = SoraStrategy(strategy_config)
        # 可以在这里添加其他策略
        # elif strategy_type == "gemini":
        #     self.strategy = GeminiStrategy(strategy_config)
        # elif strategy_type == "aliyun":
        #     self.strategy = AliyunStrategy(strategy_config)
        else:
            # 如果指定的策略不可用，降级到CogVideoX
            print(f"⚠️  策略 {strategy_type} 不可用，使用 CogVideoX 策略")
            self.strategy = CogVideoXStrategy(strategy_config)
    
    def _init_post_processor(self):
        """初始化后期处理器"""
        post_process_config = self.config.get("post_process", {})
        self.post_processor = VideoPostProcessor(post_process_config)
    
    async def generate(self, script: Script, output_path: Optional[str] = None) -> VideoResult:
        """
        生成视频
        
        Args:
            script: 剧本对象
            output_path: 输出路径
            
        Returns:
            视频生成结果
        """
        # 1. 使用策略生成视频
        video_result = await self.strategy.generate(script, output_path)
        
        # 2. 如果生成成功，进行后期处理
        if video_result.status == "completed" and self.post_processor:
            video_result = await self.post_processor.process(video_result, script)
        
        return video_result


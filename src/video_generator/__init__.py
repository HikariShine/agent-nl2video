"""剧本生视频模块"""
from .strategy import VideoGenerationStrategy
from .sora_strategy import SoraStrategy
from .local_strategy import LocalVideoStrategy
from .cogvideo_strategy import CogVideoXStrategy
from .models import VideoResult

__all__ = [
    "VideoGenerationStrategy",
    "SoraStrategy",
    "LocalVideoStrategy",
    "CogVideoXStrategy",
    "VideoResult",
]


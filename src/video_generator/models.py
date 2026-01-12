"""视频生成数据模型"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class VideoResult:
    """视频生成结果"""
    video_id: str
    file_path: str  # 视频文件路径
    file_size: int = 0  # 文件大小（字节）
    duration: int = 0  # 视频时长（秒）
    resolution: str = "1080p"  # 分辨率
    format: str = "mp4"  # 格式
    status: str = "completed"  # 状态: generating, completed, failed
    generation_strategy: Optional[str] = None  # 使用的生成策略
    generation_time: int = 0  # 生成耗时（秒）
    error_message: Optional[str] = None  # 错误信息
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


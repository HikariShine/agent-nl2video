"""剧本数据模型"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Scene:
    """场景/镜头"""
    scene_id: int
    duration: int  # 时长（秒）
    visual: str  # 画面描述
    narration: str  # 旁白文案
    subtitles: str  # 字幕文本
    music: Optional[str] = None  # 背景音乐类型


@dataclass
class Script:
    """视频剧本"""
    title: str  # 视频标题
    duration: int  # 总时长（秒）
    scenes: List[Scene] = field(default_factory=list)  # 场景列表
    hashtags: List[str] = field(default_factory=list)  # 标签
    description: str = ""  # 视频简介
    trending_id: Optional[str] = None  # 关联的热点ID
    llm_model: Optional[str] = None  # 使用的LLM模型
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "title": self.title,
            "duration": self.duration,
            "scenes": [
                {
                    "scene_id": scene.scene_id,
                    "duration": scene.duration,
                    "visual": scene.visual,
                    "narration": scene.narration,
                    "subtitles": scene.subtitles,
                    "music": scene.music,
                }
                for scene in self.scenes
            ],
            "hashtags": self.hashtags,
            "description": self.description,
        }


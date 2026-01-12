"""热点数据模型"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class TrendingItem:
    """热点数据项"""
    id: str
    source: str  # 数据源名称
    title: str  # 标题
    description: str = ""  # 描述
    category: str = ""  # 分类
    heat_value: float = 0.0  # 热度值
    trending_score: float = 0.0  # 综合评分
    publish_time: Optional[datetime] = None  # 发布时间
    keywords: List[str] = None  # 关键词
    url: str = ""  # 原始链接
    metadata: Dict[str, Any] = None  # 元数据
    created_at: datetime = None  # 创建时间
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()


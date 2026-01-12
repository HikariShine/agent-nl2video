"""数据库模型（简化版，实际应该使用SQLAlchemy）"""
from datetime import datetime
from typing import Optional, Dict, Any
import json
import os


class Database:
    """简单的文件数据库（用于MVP，生产环境应使用PostgreSQL）"""
    
    def __init__(self, db_path: str = "./storage/db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
    
    def save_trending(self, item: Dict[str, Any]) -> str:
        """保存热点数据"""
        item_id = item.get("id", f"trending_{int(datetime.now().timestamp())}")
        file_path = os.path.join(self.db_path, f"trending_{item_id}.json")
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(item, f, ensure_ascii=False, indent=2)
        
        return item_id
    
    def save_script(self, script: Dict[str, Any]) -> str:
        """保存剧本"""
        script_id = script.get("id", f"script_{int(datetime.now().timestamp())}")
        file_path = os.path.join(self.db_path, f"script_{script_id}.json")
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=2)
        
        return script_id
    
    def save_video(self, video: Dict[str, Any]) -> str:
        """保存视频信息"""
        video_id = video.get("video_id", f"video_{int(datetime.now().timestamp())}")
        file_path = os.path.join(self.db_path, f"video_{video_id}.json")
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(video, f, ensure_ascii=False, indent=2)
        
        return video_id
    
    def get_trending(self, item_id: str) -> Optional[Dict[str, Any]]:
        """获取热点数据"""
        file_path = os.path.join(self.db_path, f"trending_{item_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def get_script(self, script_id: str) -> Optional[Dict[str, Any]]:
        """获取剧本"""
        file_path = os.path.join(self.db_path, f"script_{script_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """获取视频信息"""
        file_path = os.path.join(self.db_path, f"video_{video_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None


# 全局数据库实例
db = Database()


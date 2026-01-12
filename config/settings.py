"""项目配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "NL2TK"
    debug: bool = False
    log_level: str = "INFO"
    
    # 数据库配置
    database_url: str = "postgresql://user:password@localhost:5432/nl2tk"
    
    # Redis 配置
    redis_url: str = "redis://localhost:6379/0"
    
    # API Keys
    qwen_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    hf_token: Optional[str] = None  # Hugging Face token
    
    # 存储配置
    storage_path: str = "./storage"
    videos_path: str = "./storage/videos"
    scripts_path: str = "./storage/scripts"
    
    # 热点追踪配置
    trending_update_interval: int = 1800  # 30分钟
    
    # 任务调度配置
    scheduler_timezone: str = "Asia/Shanghai"
    
    # 代理配置（用于 Hugging Face 模型下载）
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


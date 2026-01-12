"""任务调度器"""
import asyncio
from typing import Dict, Callable
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from .workflow import Workflow
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config.settings import settings


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
        self.workflows: Dict[str, Workflow] = {}
        self.job_handlers: Dict[str, Callable] = {}
    
    def register_workflow(self, workflow: Workflow):
        """
        注册工作流
        
        Args:
            workflow: 工作流对象
        """
        self.workflows[workflow.name] = workflow
    
    def add_job(self, job_id: str, func: Callable, trigger_type: str = "cron", 
                trigger_config: dict = None, **kwargs):
        """
        添加定时任务
        
        Args:
            job_id: 任务ID
            func: 执行函数
            trigger_type: 触发器类型 (cron, interval)
            trigger_config: 触发器配置
            **kwargs: 其他参数
        """
        if trigger_config is None:
            trigger_config = {}
        
        if trigger_type == "cron":
            trigger = CronTrigger(**trigger_config)
        elif trigger_type == "interval":
            trigger = IntervalTrigger(**trigger_config)
        else:
            raise ValueError(f"不支持的触发器类型: {trigger_type}")
        
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            **kwargs
        )
        
        self.job_handlers[job_id] = func
    
    def add_workflow_job(self, workflow_name: str, job_id: str = None,
                        trigger_type: str = "cron", trigger_config: dict = None):
        """
        添加工作流定时任务
        
        Args:
            workflow_name: 工作流名称
            job_id: 任务ID（默认使用工作流名称）
            trigger_type: 触发器类型
            trigger_config: 触发器配置
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"工作流 {workflow_name} 未注册")
        
        workflow = self.workflows[workflow_name]
        if job_id is None:
            job_id = f"workflow_{workflow_name}"
        
        async def execute_workflow():
            """执行工作流"""
            return await workflow.execute()
        
        self.add_job(job_id, execute_workflow, trigger_type, trigger_config)
    
    def start(self):
        """启动调度器"""
        self.scheduler.start()
        print("任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        print("任务调度器已停止")
    
    def pause(self):
        """暂停调度器"""
        self.scheduler.pause()
    
    def resume(self):
        """恢复调度器"""
        self.scheduler.resume()
    
    def get_jobs(self):
        """获取所有任务"""
        return self.scheduler.get_jobs()
    
    def remove_job(self, job_id: str):
        """移除任务"""
        self.scheduler.remove_job(job_id)
        if job_id in self.job_handlers:
            del self.job_handlers[job_id]


"""主入口文件"""
import asyncio
from src.api.main import app
from src.scheduler.scheduler import TaskScheduler
from src.scheduler.workflow import Workflow, WorkflowTask
from src.scheduler.tasks import fetch_trending_task, generate_script_task, generate_video_task
import uvicorn


def setup_scheduler():
    """设置定时任务"""
    scheduler = TaskScheduler()
    
    # 创建工作流
    workflow = Workflow("auto_video_generation")
    workflow.add_task(WorkflowTask(
        id="fetch_trending",
        name="获取热点",
        func=fetch_trending_task,
    ))
    workflow.add_task(WorkflowTask(
        id="generate_script",
        name="生成剧本",
        func=generate_script_task,
        depends_on=["fetch_trending"],
    ))
    workflow.add_task(WorkflowTask(
        id="generate_video",
        name="生成视频",
        func=generate_video_task,
        depends_on=["generate_script"],
    ))
    
    scheduler.register_workflow(workflow)
    
    # 添加定时任务（每2小时执行一次）
    scheduler.add_workflow_job(
        workflow_name="auto_video_generation",
        job_id="auto_video_job",
        trigger_type="interval",
        trigger_config={"hours": 2}
    )
    
    return scheduler


if __name__ == "__main__":
    # 启动调度器
    scheduler = setup_scheduler()
    scheduler.start()
    
    # 启动API服务
    uvicorn.run(app, host="0.0.0.0", port=8000)


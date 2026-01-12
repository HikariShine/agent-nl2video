"""工作流API路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...scheduler.workflow import Workflow, WorkflowTask
from ...scheduler.tasks import fetch_trending_task, generate_script_task, generate_video_task

router = APIRouter()


class CreateWorkflowRequest(BaseModel):
    """创建工作流请求"""
    name: str
    schedule: Optional[str] = None  # Cron表达式


@router.post("/create")
async def create_workflow(request: CreateWorkflowRequest):
    """
    创建工作流
    
    Args:
        request: 创建请求
        
    Returns:
        工作流信息
    """
    try:
        # 创建工作流
        workflow = Workflow(request.name)
        
        # 添加任务
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
        
        return {
            "workflow_name": workflow.name,
            "tasks": [task.id for task in workflow.tasks.values()],
            "execution_order": workflow.execution_order,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_workflow(workflow_name: str):
    """
    执行工作流
    
    Args:
        workflow_name: 工作流名称
        
    Returns:
        执行结果
    """
    try:
        # 创建临时工作流
        workflow = Workflow(workflow_name)
        
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
        
        # 执行工作流
        results = await workflow.execute()
        
        return {
            "workflow_name": workflow_name,
            "results": {
                task_id: "completed" if result is not None else "failed"
                for task_id, result in results.items()
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


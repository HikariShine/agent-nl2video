"""工作流定义"""
from dataclasses import dataclass
from typing import List, Dict, Callable, Any, Optional
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowTask:
    """工作流任务"""
    id: str
    name: str
    func: Callable
    depends_on: List[str] = None
    timeout: int = 300  # 超时时间（秒）
    retry_count: int = 3  # 重试次数
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.depends_on is None:
            self.depends_on = []


class Workflow:
    """工作流"""
    
    def __init__(self, name: str):
        """
        初始化工作流
        
        Args:
            name: 工作流名称
        """
        self.name = name
        self.tasks: Dict[str, WorkflowTask] = {}
        self.execution_order: List[str] = []
    
    def add_task(self, task: WorkflowTask):
        """
        添加任务
        
        Args:
            task: 工作流任务
        """
        self.tasks[task.id] = task
        self._update_execution_order()
    
    def _update_execution_order(self):
        """更新执行顺序（拓扑排序）"""
        # 简单的拓扑排序实现
        in_degree = {task_id: 0 for task_id in self.tasks}
        
        # 计算入度
        for task in self.tasks.values():
            for dep in task.depends_on:
                if dep in self.tasks:
                    in_degree[task.id] += 1
        
        # 拓扑排序
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        self.execution_order = []
        
        while queue:
            task_id = queue.pop(0)
            self.execution_order.append(task_id)
            
            # 更新依赖该任务的其他任务的入度
            for task in self.tasks.values():
                if task_id in task.depends_on:
                    in_degree[task.id] -= 1
                    if in_degree[task.id] == 0:
                        queue.append(task.id)
    
    async def execute(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        if context is None:
            context = {}
        
        results = {}
        
        for task_id in self.execution_order:
            task = self.tasks[task_id]
            task.status = TaskStatus.RUNNING
            
            try:
                # 准备任务参数
                task_args = {}
                for dep_id in task.depends_on:
                    if dep_id in results:
                        task_args[dep_id] = results[dep_id]
                
                # 执行任务
                if task.depends_on:
                    result = await task.func(**task_args, context=context)
                else:
                    result = await task.func(context=context)
                
                task.result = result
                task.status = TaskStatus.COMPLETED
                results[task_id] = result
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                results[task_id] = None
                print(f"任务 {task.name} 执行失败: {e}")
                # 可以选择继续执行或中断
                # break
        
        return results


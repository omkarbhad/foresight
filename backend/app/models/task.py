"""Task status management for long-running operations"""

import uuid
import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    progress: int = 0
    message: str = ""
    result: Optional[Dict] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    progress_detail: Dict = field(default_factory=dict)
    cancel_requested: bool = False

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "progress": self.progress,
            "message": self.message,
            "progress_detail": self.progress_detail,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "cancel_requested": self.cancel_requested,
        }


class TaskManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks = {}
                    cls._instance._task_lock = threading.Lock()
        return cls._instance

    def create_task(self, task_type, metadata=None):
        task_id = str(uuid.uuid4())
        now = datetime.now()
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
        with self._task_lock:
            self._tasks[task_id] = task
        return task_id

    def get_task(self, task_id):
        with self._task_lock:
            return self._tasks.get(task_id)

    def update_task(self, task_id, status=None, progress=None, message=None,
                    result=None, error=None, progress_detail=None):
        with self._task_lock:
            task = self._tasks.get(task_id)
            if task:
                task.updated_at = datetime.now()
                if status is not None:
                    task.status = status
                if progress is not None:
                    task.progress = progress
                if message is not None:
                    task.message = message
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
                if progress_detail is not None:
                    task.progress_detail = progress_detail

    def complete_task(self, task_id, result):
        self.update_task(task_id, status=TaskStatus.COMPLETED, progress=100,
                         message="Task completed", result=result)

    def fail_task(self, task_id, error):
        self.update_task(task_id, status=TaskStatus.FAILED,
                         message="Task failed", error=error)

    def cancel_task(self, task_id):
        with self._task_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return False
            task.cancel_requested = True
            task.message = "Cancellation requested..."
            task.updated_at = datetime.now()
            return True

    def list_tasks(self, task_type=None):
        with self._task_lock:
            tasks = list(self._tasks.values())
            if task_type:
                tasks = [t for t in tasks if t.task_type == task_type]
            return [t.to_dict() for t in sorted(tasks, key=lambda x: x.created_at, reverse=True)]

    def cleanup_old_tasks(self, max_age_hours=24):
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        with self._task_lock:
            old_ids = [
                tid for tid, task in self._tasks.items()
                if task.created_at < cutoff and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            ]
            for tid in old_ids:
                del self._tasks[tid]

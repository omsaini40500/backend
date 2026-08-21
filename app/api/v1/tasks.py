from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import List, Optional
from uuid import uuid4
from app.api.v1.deps import get_db, get_current_user
from app.models import Task, User, TaskChecklistItem
from app.core.permissions import RequirePermission
from app.schemas.base import CamelModel, PaginatedResponse
from app.schemas import TaskOut
from pydantic import BaseModel

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskCreate(CamelModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    status: str = "todo"
    progress: int = 0
    estimated_hours: float = 0
    spent_hours: float = 0
    project_id: Optional[str] = None
    department_id: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    assigned_to: List[str] = []
    start_date: Optional[str] = None
    due_date: Optional[str] = None

class TaskUpdate(CamelModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    estimated_hours: Optional[float] = None
    spent_hours: Optional[float] = None
    project_id: Optional[str] = None
    department_id: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_to: Optional[List[str]] = None
    start_date: Optional[str] = None
    due_date: Optional[str] = None

class ChecklistItemCreate(BaseModel):
    text: str

class ChecklistItemUpdate(BaseModel):
    done: Optional[bool] = None
    text: Optional[str] = None

class BulkStatusRequest(BaseModel):
    task_ids: List[str]
    status: str

def _serialize(task: Task, db: Session = None) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description or "",
        "priority": task.priority,
        "status": task.status,
        "progress": task.progress,
        "estimatedHours": task.estimated_hours,
        "spentHours": task.spent_hours,
        "assignedBy": task.assigned_by_user.name if task.assigned_by_user else task.assigned_by,
        "projectId": task.project_id,
        "departmentId": task.department_id,
        "category": task.category or "",
        "tags": task.tags.split(",") if task.tags else [],
        "checklist": [
            {"id": item.id, "text": item.text, "done": item.done}
            for item in task.checklist
        ],
        "comments": 0,
        "attachments": 0,
        "watchers": [],
        "assignedTo": [u.id for u in task.assignees],
        "startDate": task.start_date or "",
        "dueDate": task.due_date or "",
    }

@router.get("", dependencies=[Depends(RequirePermission("tasks.read"))])
def read_tasks(
    assigned_to: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "super_admin":
        query = db.query(Task)
    else:
        query = db.query(Task).filter(
            or_(
                Task.assignees.any(User.id == current_user.id),
                Task.assigned_by == current_user.id,
            )
        )
    if assigned_to:
        query = query.filter(Task.assignees.any(User.id == assigned_to))
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    total = query.count()
    tasks = query.options(
        joinedload(Task.assignees),
        joinedload(Task.checklist),
        joinedload(Task.assigned_by_user)
    ).offset(skip).limit(limit).all()
    return {
        "items": [_serialize(t, db) for t in tasks],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/my", dependencies=[Depends(RequirePermission("tasks.read"))])
def read_my_tasks(
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Task).filter(Task.assignees.any(User.id == current_user.id))
    total = query.count()
    tasks = query.options(
        joinedload(Task.assignees),
        joinedload(Task.checklist),
        joinedload(Task.assigned_by_user)
    ).offset(skip).limit(limit).all()
    return {
        "items": [_serialize(t, db) for t in tasks],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{task_id}", dependencies=[Depends(RequirePermission("tasks.read"))])
def read_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).options(
        joinedload(Task.assignees),
        joinedload(Task.checklist),
        joinedload(Task.assigned_by_user)
    ).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.assigned_by != current_user.id and current_user.id not in [a.id for a in task.assignees]:
        raise HTTPException(status_code=403, detail="Not authorized to view this task")
    return _serialize(task, db)

@router.post("", status_code=201, dependencies=[Depends(RequirePermission("tasks.create"))])
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    task = Task(
        id=str(uuid.uuid4())[:8],
        title=data.title,
        description=data.description,
        priority=data.priority,
        status=data.status,
        progress=data.progress,
        estimated_hours=data.estimated_hours,
        spent_hours=data.spent_hours,
        project_id=data.project_id,
        department_id=data.department_id,
        category=data.category,
        tags=",".join(data.tags) if data.tags else "",
        assigned_by=current_user.id,
        start_date=data.start_date,
        due_date=data.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    for uid in data.assigned_to:
        u = db.query(User).filter(User.id == uid).first()
        if u:
            task.assignees.append(u)
    db.commit()
    
    from app.services.activity import log_activity
    log_activity(
        db=db,
        user_id=current_user.id,
        user_name=current_user.name,
        action="Created task",
        target=task.title,
        module="Tasks"
    )
    
    return _serialize(task, db)

@router.patch("/{task_id}", dependencies=[Depends(RequirePermission("tasks.update"))])
def update_task(
    task_id: str,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role not in ("super_admin", "admin") and task.assigned_by != current_user.id and current_user.id not in [a.id for a in task.assignees]:
        raise HTTPException(status_code=403, detail="Not authorized to update this task")
        
    if data.status is not None and data.status != task.status:
        if current_user.id not in [a.id for a in task.assignees]:
            raise HTTPException(status_code=403, detail="Status of task can only be updated by the assignee")

    old_status = task.status
        
    for field, value in data.model_dump(exclude_none=True).items():
        if field == "tags":
            task.tags = ",".join(value) if value else ""
        elif field == "assigned_to":
            task.assignees = []
            for uid in value:
                u = db.query(User).filter(User.id == uid).first()
                if u:
                    task.assignees.append(u)
        else:
            setattr(task, field, value)
    db.commit()
    db.refresh(task)
    
    from app.services.activity import log_activity
    if old_status != task.status and task.status == "completed":
        action_name = "Completed task"
    elif old_status != task.status:
        action_name = "Status changed"
    else:
        action_name = "Updated task"
        
    log_activity(
        db=db,
        user_id=current_user.id,
        user_name=current_user.name,
        action=action_name,
        target=task.title,
        module="Tasks",
        old_value=old_status if old_status != task.status else None,
        new_value=task.status if old_status != task.status else None
    )
    
    return _serialize(task, db)

@router.delete("/{task_id}", status_code=204, dependencies=[Depends(RequirePermission("tasks.delete"))])
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role not in ("super_admin", "admin") and task.assigned_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this task")
    db.delete(task)
    db.commit()

@router.post("/{task_id}/assign", dependencies=[Depends(RequirePermission("tasks.assign"))])
def assign_task(
    task_id: str,
    user_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user not in task.assignees:
        task.assignees.append(user)
        db.commit()
    return _serialize(task, db)

@router.post("/{task_id}/checklist", status_code=201, dependencies=[Depends(RequirePermission("tasks.update"))])
def add_checklist_item(
    task_id: str,
    data: ChecklistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    item = TaskChecklistItem(
        id=str(uuid4())[:8],
        task_id=task_id,
        text=data.text,
        done=False,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "text": item.text, "done": item.done}

@router.patch("/{task_id}/checklist/{item_id}", dependencies=[Depends(RequirePermission("tasks.update"))])
def update_checklist_item(
    task_id: str,
    item_id: str,
    data: ChecklistItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(TaskChecklistItem).filter(TaskChecklistItem.id == item_id, TaskChecklistItem.task_id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    if data.done is not None:
        item.done = data.done
    if data.text is not None:
        item.text = data.text
    db.commit()
    db.refresh(item)
    return {"id": item.id, "text": item.text, "done": item.done}

@router.delete("/{task_id}/checklist/{item_id}", status_code=204, dependencies=[Depends(RequirePermission("tasks.update"))])
def delete_checklist_item(
    task_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(TaskChecklistItem).filter(TaskChecklistItem.id == item_id, TaskChecklistItem.task_id == task_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    db.delete(item)
    db.commit()
    return

@router.post("/{task_id}/approve", dependencies=[Depends(RequirePermission("tasks.update"))])
def approve_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != "review":
        raise HTTPException(status_code=400, detail="Task must be in review status to approve")
    task.status = "done"
    task.progress = 100
    db.commit()
    db.refresh(task)
    return _serialize(task, db)

@router.post("/bulk-status", dependencies=[Depends(RequirePermission("tasks.update"))])
def bulk_status_update(
    data: BulkStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tasks = db.query(Task).options(
        joinedload(Task.assignees),
        joinedload(Task.checklist),
        joinedload(Task.assigned_by_user)
    ).filter(Task.id.in_(data.task_ids)).all()
    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found")
    for task in tasks:
        if current_user.role not in ("super_admin", "admin") and task.assigned_by != current_user.id and current_user.id not in [a.id for a in task.assignees]:
            raise HTTPException(status_code=403, detail=f"Not authorized to update task {task.id}")
        task.status = data.status
    db.commit()
    return [_serialize(t, db) for t in tasks]

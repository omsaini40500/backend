from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.api.v1.deps import get_db, get_current_user
from app.models import Project, Task, User
from app.core.permissions import RequirePermission
from app.schemas import ProjectOut
from app.schemas.base import CamelModel

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(CamelModel):
    name: str
    description: Optional[str] = None
    status: str = "active"
    progress: int = 0
    budget: float = 0
    spent: float = 0
    manager_id: Optional[str] = None
    client_id: Optional[str] = None
    category: Optional[str] = None
    color: str = "#6366f1"
    team: List[str] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ProjectUpdate(CamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    budget: Optional[float] = None
    spent: Optional[float] = None
    manager_id: Optional[str] = None
    client_id: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    team: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

def _serialize(project: Project, db: Session = None) -> dict:
    task_count = len(project.tasks) if hasattr(project, 'tasks') else 0
    completed_count = sum(1 for t in project.tasks if t.status == "done") if hasattr(project, 'tasks') else 0
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description or "",
        "status": project.status,
        "progress": project.progress,
        "budget": project.budget,
        "spent": project.spent,
        "managerId": project.manager_id,
        "clientId": project.client_id,
        "category": project.category or "",
        "color": project.color,
        "startDate": project.start_date or "",
        "endDate": project.end_date or "",
        "team": [u.id for u in project.team_members],
        "tasks": task_count,
        "completedTasks": completed_count,
    }

@router.get("", dependencies=[Depends(RequirePermission("projects.read"))])
def read_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = db.query(Project).count()
    projects = db.query(Project).options(
        joinedload(Project.team_members),
        joinedload(Project.tasks)
    ).offset(skip).limit(limit).all()
    return {
        "items": [_serialize(p, db) for p in projects],
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{project_id}", dependencies=[Depends(RequirePermission("projects.read"))])
def read_project(project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = db.query(Project).options(
        joinedload(Project.team_members),
        joinedload(Project.tasks)
    ).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return _serialize(p, db)

@router.post("", status_code=201, dependencies=[Depends(RequirePermission("projects.create"))])
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid
    project = Project(
        id=str(uuid.uuid4())[:8],
        name=data.name,
        description=data.description,
        status=data.status,
        progress=data.progress,
        budget=data.budget,
        spent=data.spent,
        manager_id=data.manager_id or current_user.id,
        client_id=data.client_id,
        category=data.category,
        color=data.color,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    for uid in data.team:
        u = db.query(User).filter(User.id == uid).first()
        if u:
            project.team_members.append(u)
    db.commit()
    return _serialize(project, db)

@router.patch("/{project_id}", dependencies=[Depends(RequirePermission("projects.update"))])
def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role not in ("super_admin", "admin") and project.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this project")
    update_data = data.model_dump(exclude_none=True)
    if "team" in update_data:
        project.team_members = []
        for uid in update_data.pop("team"):
            u = db.query(User).filter(User.id == uid).first()
            if u:
                project.team_members.append(u)
    for field, value in update_data.items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return _serialize(project, db)

@router.delete("/{project_id}", status_code=204, dependencies=[Depends(RequirePermission("projects.delete"))])
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role not in ("super_admin", "admin") and project.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")
    db.delete(project)
    db.commit()

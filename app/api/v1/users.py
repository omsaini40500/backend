from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
from app.api.v1.deps import get_db, get_current_user
from app.models import User, Task
from app.schemas import UserOut
from app.schemas.base import CamelModel, PaginatedResponse
from app.core.security import get_password_hash, verify_password
from app.core.permissions import RequirePermission

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedResponse[UserOut], dependencies=[Depends(RequirePermission("users.read"))])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = db.query(User).count()
    users = db.query(User).options(joinedload(User.tasks)).offset(skip).limit(limit).all()

    for u in users:
        u.tasks_completed = sum(1 for t in u.tasks if t.status == 'done') if hasattr(u, 'tasks') else 0
        u.tasks_total = len(u.tasks) if hasattr(u, 'tasks') else 0

    return {
        "items": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


class UserCreate(CamelModel):
    name: str
    email: str
    role: str = "member"
    department_id: Optional[str] = None
    team_id: Optional[str] = None
    client_id: Optional[str] = None
    password: Optional[str] = None


class UserUpdate(CamelModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[str] = None
    team_id: Optional[str] = None
    client_id: Optional[str] = None
    is_active: Optional[bool] = None
    theme: Optional[str] = None


class ThemeUpdate(BaseModel):
    theme: str


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(RequirePermission("users.create"))])
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    import uuid
    user = User(
        id=f"u{uuid.uuid4().hex[:8]}",
        name=data.name,
        email=data.email,
        hashed_password=get_password_hash(data.password or "demo"),
        role=data.role,
        department_id=data.department_id,
        team_id=data.team_id,
        client_id=data.client_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user.tasks_completed = 0
    user.tasks_total = 0
    return user


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.tasks_completed = db.query(Task).filter(Task.assignees.any(id=current_user.id), Task.status == "done").count()
    current_user.tasks_total = db.query(Task).filter(Task.assignees.any(id=current_user.id)).count()
    return current_user


@router.patch("/me/theme")
def update_my_theme(
    data: ThemeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.theme not in ("dark", "light"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid theme value")
    current_user.theme = data.theme
    db.commit()
    db.refresh(current_user)
    return {"theme": current_user.theme}


@router.patch("/{user_id}", response_model=UserOut, dependencies=[Depends(RequirePermission("users.update"))])
def update_user(
    user_id: str,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    user.tasks_completed = db.query(Task).filter(Task.assignees.any(id=user.id), Task.status == "done").count()
    user.tasks_total = db.query(Task).filter(Task.assignees.any(id=user.id)).count()

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RequirePermission("users.delete"))])
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    from sqlalchemy import text
    # Delete associations and records owned solely by the user
    db.execute(text("DELETE FROM project_team_members WHERE user_id = :uid"), {"uid": user_id})
    db.execute(text("DELETE FROM task_assignees WHERE user_id = :uid"), {"uid": user_id})
    db.execute(text("DELETE FROM task_watchers WHERE user_id = :uid"), {"uid": user_id})
    db.execute(text("DELETE FROM notifications WHERE user_id = :uid"), {"uid": user_id})
    db.execute(text("DELETE FROM reset_tokens WHERE user_id = :uid"), {"uid": user_id})
    db.execute(text("DELETE FROM activity_logs WHERE user_id = :uid"), {"uid": user_id})
    db.execute(text("DELETE FROM leave_requests WHERE user_id = :uid"), {"uid": user_id})

    # Re-assign critical business records to the admin performing the deletion to preserve them
    admin_id = current_user.id
    db.execute(text("UPDATE projects SET manager_id = :admin WHERE manager_id = :uid"), {"admin": admin_id, "uid": user_id})
    db.execute(text("UPDATE tasks SET assigned_by = :admin WHERE assigned_by = :uid"), {"admin": admin_id, "uid": user_id})
    db.execute(text("UPDATE expenses SET created_by = :admin WHERE created_by = :uid"), {"admin": admin_id, "uid": user_id})
    db.execute(text("UPDATE campaigns SET created_by = :admin WHERE created_by = :uid"), {"admin": admin_id, "uid": user_id})
    db.execute(text("UPDATE approvals SET requester_id = :admin WHERE requester_id = :uid"), {"admin": admin_id, "uid": user_id})
    db.execute(text("UPDATE meetings SET created_by = :admin WHERE created_by = :uid"), {"admin": admin_id, "uid": user_id})
    db.execute(text("UPDATE recycle_bin SET deleted_by = :admin WHERE deleted_by = :uid"), {"admin": admin_id, "uid": user_id})

    db.delete(user)
    db.commit()
    return

@router.post("/{user_id}/unblock", response_model=UserOut)
def unblock_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only super admins can unblock users.")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.failed_login_attempts = 0
    user.is_blocked = False
    db.commit()
    db.refresh(user)
    
    user.tasks_completed = db.query(Task).filter(Task.assignees.any(id=user.id), Task.status == "done").count()
    user.tasks_total = db.query(Task).filter(Task.assignees.any(id=user.id)).count()
    return user

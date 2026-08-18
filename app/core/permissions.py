from fastapi import HTTPException, status, Depends
from app.models import User
from app.api.v1.deps import get_current_user

# Centralized role-permission mapping
ROLE_PERMISSIONS = {
    "super_admin": ["*"],
    "admin": [
        "tasks.create", "tasks.update", "tasks.delete", "tasks.assign", "tasks.read",
        "projects.create", "projects.update", "projects.delete", "projects.read",
        "users.create", "users.update", "users.delete", "users.read",
        "reports.read", "reports.manage",
        "clients.read", "clients.manage",
        "departments.read", "teams.read",
        "approvals.read", "approvals.manage",
        "campaigns.read", "campaigns.manage"
    ],
    "team_leader": [
        "tasks.create", "tasks.update", "tasks.assign", "tasks.read",
        "projects.read",
        "users.read",
        "reports.read",
        "clients.read",
        "departments.read", "teams.read",
        "approvals.read", "approvals.approve",
        "campaigns.read", "campaigns.manage"
    ],
    "project_manager": [
        "tasks.create", "tasks.update", "tasks.assign", "tasks.read",
        "projects.create", "projects.update", "projects.read",
        "users.read",
        "reports.read",
        "clients.read",
        "departments.read", "teams.read",
        "campaigns.read"
    ],
    "member": [
        "tasks.create", "tasks.update", "tasks.read",
        "projects.read",
        "users.read",
        "departments.read", "teams.read",
    ],
    "client": [
        "projects.read",
        "reports.read",
        "tasks.read"
    ]
}

def has_permission(user_role: str, required_permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(user_role, [])
    if "*" in perms:
        return True
    return required_permission in perms

class RequirePermission:
    def __init__(self, permission: str):
        self.permission = permission

    def __call__(self, current_user: User = Depends(get_current_user)):
        if not has_permission(current_user.role, self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Requires: {self.permission}"
            )
        return current_user

class RequireRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)):
        if current_user.role not in self.allowed_roles and current_user.role != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions."
            )
        return current_user

from typing import List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, computed_field
from .base import CamelModel

def _as_utc(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (UTC). MySQL returns naive datetimes."""
    if dt is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

class UserOut(CamelModel):
    id: str
    name: str
    email: str
    role: str
    department_id: Optional[str] = None
    team_id: Optional[str] = None
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_active_at: Optional[datetime] = None
    tasks_completed: int = 0
    tasks_total: int = 0
    theme: str = "dark"

    @computed_field
    def avatar(self) -> str:
        parts = self.name.split()
        if len(parts) >= 2:
            return parts[0][0] + parts[1][0]
        return self.name[0] if self.name else "U"
        
    @computed_field
    def status(self) -> str:
        return "active" if self.is_active else "inactive"

class Token(CamelModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(CamelModel):
    email: str | None = None

class DepartmentOut(CamelModel):
    id: str
    name: str

class TeamOut(CamelModel):
    id: str
    name: str
    department_id: Optional[str] = None

class ClientOut(CamelModel):
    id: str
    name: str
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    status: str

class ClientCreate(CamelModel):
    name: str
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    status: str = "active"

class ClientUpdate(CamelModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    status: Optional[str] = None

class ProjectOut(CamelModel):
    id: str
    name: str
    description: Optional[str] = None
    status: str
    progress: int
    budget: float
    spent: float
    manager_id: Optional[str] = None
    client_id: Optional[str] = None
    category: Optional[str] = None
    color: str
    team: List[str] = []
    tasks: int = 0
    completed_tasks: int = 0

class ChecklistItemOut(CamelModel):
    id: str
    text: str
    done: bool

class TaskOut(CamelModel):
    id: str
    title: str
    description: Optional[str] = None
    priority: str
    status: str
    progress: int
    estimated_hours: float
    spent_hours: float
    assigned_by: Optional[str] = None
    project_id: Optional[str] = None
    department_id: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    checklist: List[ChecklistItemOut] = []
    comments: int = 0
    attachments: int = 0
    watchers: List[str] = []
    assigned_to: List[str] = []

class NotificationOut(CamelModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    read: bool
    created_at: datetime
    link: Optional[str] = None

    @computed_field
    def time(self) -> str:
        if self.created_at:
            aware_dt = _as_utc(self.created_at)
            diff = datetime.now(timezone.utc) - aware_dt
            if diff.total_seconds() < 60:
                return "Just now"
            elif diff.total_seconds() < 3600:
                return f"{int(diff.total_seconds() // 60)} min ago"
            elif diff.total_seconds() < 86400:
                return f"{int(diff.total_seconds() // 3600)} hour ago"
            else:
                return aware_dt.strftime("%b %d, %Y")
        return ""

class ActivityLogOut(CamelModel):
    id: str
    user: str
    user_id: str
    action: str
    target: str
    module: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip: str
    browser: str
    location: str
    created_at: datetime

class CampaignOut(CamelModel):
    id: str
    name: str
    client: Optional[str] = None
    status: str
    start: Optional[str] = None
    end: Optional[str] = None
    team: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime

class CampaignCreate(CamelModel):
    name: str
    client: Optional[str] = None
    status: str = "Planning"
    start: Optional[str] = None
    end: Optional[str] = None
    team: Optional[str] = None

class CampaignUpdate(CamelModel):
    name: Optional[str] = None
    client: Optional[str] = None
    status: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    team: Optional[str] = None

class LeaveOut(CamelModel):
    id: str
    user_id: str
    user_name: Optional[str] = None
    type: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reason: Optional[str] = None
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

class LeaveCreate(CamelModel):
    user_id: str
    user_name: Optional[str] = None
    type: str
    start_date: str
    end_date: str
    reason: str

class LeaveUpdate(CamelModel):
    status: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

class ResetTokenOut(CamelModel):
    id: str
    token: str
    email: str
    user_id: str
    created_at: datetime
    expires_at: datetime

class MonitoringServiceOut(CamelModel):
    id: str
    name: str
    status: str
    latency: str
    uptime: str
    last_checked: datetime

class ErrorLogOut(CamelModel):
    id: str
    time: str
    level: str
    service: str
    message: str
    stack_trace: Optional[str] = None

class CronJobOut(CamelModel):
    id: str
    name: str
    schedule: str
    last_run: str
    next_run: str
    duration: str
    status: str

class AnnouncementOut(CamelModel):
    id: str
    title: str
    type: str
    priority: str
    author: str
    date: str
    content: str
    pinned: bool
    created_at: datetime

class AnnouncementCreate(CamelModel):
    title: str
    type: str
    priority: str = "medium"
    author: str
    date: str
    content: str
    pinned: bool = False

class AnnouncementUpdate(CamelModel):
    title: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    content: Optional[str] = None
    pinned: Optional[bool] = None

class MeetingOut(CamelModel):
    id: str
    title: str
    date: str
    time: str
    duration: str
    type: str
    participants: str
    agenda: str
    status: str
    meeting_link: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime

class MeetingCreate(CamelModel):
    title: str
    date: str
    time: str
    duration: str
    type: str
    participants: str
    agenda: str
    status: str = "Upcoming"
    meeting_link: Optional[str] = None

class MeetingUpdate(CamelModel):
    title: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    duration: Optional[str] = None
    type: Optional[str] = None
    participants: Optional[str] = None
    agenda: Optional[str] = None
    status: Optional[str] = None
    meeting_link: Optional[str] = None

class AutomationOut(CamelModel):
    id: str
    name: str
    trigger: str
    condition: str
    action: str
    status: str
    runs: int
    last_run: Optional[str] = None
    created_at: datetime

class AutomationCreate(CamelModel):
    name: str
    trigger: str
    condition: str
    action: str
    status: str = "Active"

class AutomationUpdate(CamelModel):
    name: Optional[str] = None
    trigger: Optional[str] = None
    condition: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    runs: Optional[int] = None
    last_run: Optional[str] = None

class AutomationTemplateOut(CamelModel):
    id: str
    name: str
    description: str
    icon: str
    trigger: str
    action: str
    uses: int

class AutomationHistoryOut(CamelModel):
    id: str
    automation_id: Optional[str] = None
    automation_name: str
    result: str
    time: str
    detail: str

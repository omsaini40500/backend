from sqlalchemy import Column, String, Integer, Boolean, Float, ForeignKey, DateTime, Table, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

# Association Tables
project_team_members = Table(
    'project_team_members',
    Base.metadata,
    Column('project_id', String(50), ForeignKey('projects.id'), primary_key=True),
    Column('user_id', String(50), ForeignKey('users.id'), primary_key=True)
)

task_assignees = Table(
    'task_assignees',
    Base.metadata,
    Column('task_id', String(50), ForeignKey('tasks.id'), primary_key=True),
    Column('user_id', String(50), ForeignKey('users.id'), primary_key=True)
)

task_watchers = Table(
    'task_watchers',
    Base.metadata,
    Column('task_id', String(50), ForeignKey('tasks.id'), primary_key=True),
    Column('user_id', String(50), ForeignKey('users.id'), primary_key=True)
)

class Department(Base):
    __tablename__ = "departments"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), index=True)

class Team(Base):
    __tablename__ = "teams"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), index=True)
    department_id = Column(String(50), ForeignKey("departments.id"))

class User(Base):
    __tablename__ = "users"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50))
    department_id = Column(String(50), ForeignKey("departments.id"), nullable=True)
    team_id = Column(String(50), ForeignKey("teams.id"), nullable=True)
    client_id = Column(String(50), ForeignKey("clients.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_active_at = Column(DateTime, nullable=True)
    theme = Column(String(20), default="dark")

    client = relationship("Client")
    department_rel = relationship("Department")
    tasks = relationship("Task", secondary=task_assignees, back_populates="assignees")

    @property
    def client_name(self):
        return self.client.name if self.client else None
        
    @property
    def department(self):
        return self.department_rel.name if self.department_rel else None

class Client(Base):
    __tablename__ = "clients"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(150), index=True)
    industry = Column(String(100))
    contact_name = Column(String(100))
    contact_email = Column(String(255))
    status = Column(String(50))

class Project(Base):
    __tablename__ = "projects"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(200), index=True)
    description = Column(Text)
    status = Column(String(50))
    progress = Column(Integer)
    budget = Column(Float)
    spent = Column(Float)
    manager_id = Column(String(50), ForeignKey("users.id"))
    client_id = Column(String(50), ForeignKey("clients.id"), nullable=True)
    category = Column(String(100))
    color = Column(String(20))
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    team_members = relationship("User", secondary=project_team_members)
    tasks = relationship("Task")

class TaskChecklistItem(Base):
    __tablename__ = "checklist_items"
    id = Column(String(50), primary_key=True, index=True)
    task_id = Column(String(50), ForeignKey("tasks.id"))
    text = Column(Text)
    done = Column(Boolean, default=False)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text)
    priority = Column(String(50))
    status = Column(String(50))
    progress = Column(Integer)
    estimated_hours = Column(Float)
    estimated_days = Column(Float)
    spent_hours = Column(Float)
    assigned_by = Column(String(50), ForeignKey("users.id"), nullable=True)
    project_id = Column(String(50), ForeignKey("projects.id"))
    department_id = Column(String(50), ForeignKey("departments.id"))
    category = Column(String(100))
    tags = Column(String(500))  # comma-separated
    start_date = Column(String(50), nullable=True)
    due_date = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    assignees = relationship("User", secondary=task_assignees, back_populates="tasks")
    watchers = relationship("User", secondary=task_watchers)
    checklist = relationship("TaskChecklistItem")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])

    @property
    def tags_list(self):
        return self.tags.split(',') if self.tags else []

    @tags_list.setter
    def tags_list(self, value):
        self.tags = ','.join(value) if value else ""

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"))
    type = Column(String(50))
    title = Column(String(255))
    message = Column(Text)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    link = Column(String(255), nullable=True)

class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"))
    user_name = Column(String(100))
    action = Column(String(200))
    target = Column(String(200))
    module = Column(String(100))
    old_value = Column(String(500), nullable=True)
    new_value = Column(String(500), nullable=True)
    ip = Column(String(50))
    browser = Column(String(100))
    location = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class RecycleBinItem(Base):
    __tablename__ = "recycle_bin"
    id = Column(String(50), primary_key=True, index=True)
    item_type = Column(String(50))
    item_id = Column(String(50))
    deleted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    deleted_by = Column(String(50), ForeignKey("users.id"))

class Approval(Base):
    __tablename__ = "approvals"
    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(100), nullable=True)
    priority = Column(String(50), default="medium")
    status = Column(String(50), default="Pending")
    requester_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    requester_name = Column(String(100), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(String(50), primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(String(50), nullable=False)
    created_by = Column(String(50), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CompanyBudget(Base):
    __tablename__ = "company_budgets"
    id = Column(String(50), primary_key=True, index=True)
    month = Column(String(7), unique=True, nullable=False, index=True) # e.g. "2026-08"
    amount = Column(Float, nullable=False, default=0.0)
    created_by = Column(String(50), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(200), index=True)
    client = Column(String(150))
    status = Column(String(50), default="Planning")
    start = Column(String(50))
    end = Column(String(50))
    team = Column(Text)
    created_by = Column(String(50), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    user_name = Column(String(100))
    type = Column(String(50))
    start_date = Column(String(50))
    end_date = Column(String(50))
    reason = Column(Text)
    status = Column(String(50), default="pending")
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ResetToken(Base):
    __tablename__ = "reset_tokens"
    id = Column(String(50), primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True)
    email = Column(String(255))
    user_id = Column(String(50), ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime)

class ServiceHealth(Base):
    __tablename__ = "monitoring_services"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100))
    status = Column(String(50))
    latency = Column(String(50))
    uptime = Column(String(50))
    last_checked = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ErrorLog(Base):
    __tablename__ = "monitoring_errors"
    id = Column(String(50), primary_key=True, index=True)
    time = Column(String(100))
    level = Column(String(20))
    service = Column(String(100))
    message = Column(Text)
    stack_trace = Column(Text, nullable=True)

class CronJob(Base):
    __tablename__ = "monitoring_cron"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100))
    schedule = Column(String(50))
    last_run = Column(String(100))
    next_run = Column(String(100))
    duration = Column(String(50))
    status = Column(String(50))

class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255))
    type = Column(String(50))
    priority = Column(String(50), default="medium")
    author = Column(String(100))
    date = Column(String(50))
    content = Column(Text)
    pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(String(50), primary_key=True, index=True)
    title = Column(String(255))
    date = Column(String(50))
    time = Column(String(50))
    duration = Column(String(50))
    type = Column(String(50))
    participants = Column(Text)
    agenda = Column(Text)
    status = Column(String(50), default="Upcoming")
    meeting_link = Column(String(255), nullable=True)
    created_by = Column(String(50), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Automation(Base):
    __tablename__ = "automations"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255))
    trigger = Column(String(100))
    condition = Column(String(255))
    action = Column(String(100))
    status = Column(String(50), default="Active")
    runs = Column(Integer, default=0)
    last_run = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AutomationTemplate(Base):
    __tablename__ = "automation_templates"
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255))
    description = Column(Text)
    icon = Column(String(50))
    trigger = Column(String(100))
    action = Column(String(100))
    uses = Column(Integer, default=0)

class AutomationHistory(Base):
    __tablename__ = "automation_history"
    id = Column(String(50), primary_key=True, index=True)
    automation_id = Column(String(50), ForeignKey("automations.id"), nullable=True)
    automation_name = Column(String(255))
    result = Column(String(50))
    time = Column(String(100))
    detail = Column(Text)

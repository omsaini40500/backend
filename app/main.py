from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from app.db.base import Base
from app.db.session import engine
from app.api.v1 import auth, users, tasks, projects, departments, teams, clients, notifications, activity_logs, recycle_bin, reports, approvals, emails, expenses, campaigns, leave, monitoring, announcements, meetings, automations
from app.core.config import get_settings
from app.core.security import get_password_hash
from app.models import User, Department, Team, Client, Project, Task, Notification, ActivityLog, RecycleBinItem, Approval, Campaign, LeaveRequest, ServiceHealth, ErrorLog, CronJob, Announcement, Meeting, Automation, AutomationTemplate, AutomationHistory
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

settings = get_settings()



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Base.metadata.create_all(bind=engine)  # Handled by Alembic now
    yield

app = FastAPI(
    title="flash Agency API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if not origins:
    origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router,           prefix="/api/v1")
app.include_router(users.router,          prefix="/api/v1")
app.include_router(tasks.router,          prefix="/api/v1")
app.include_router(projects.router,       prefix="/api/v1")
app.include_router(departments.router,    prefix="/api/v1")
app.include_router(teams.router,          prefix="/api/v1")
app.include_router(clients.router,        prefix="/api/v1")
app.include_router(notifications.router,  prefix="/api/v1")
app.include_router(activity_logs.router,  prefix="/api/v1")
app.include_router(reports.router,        prefix="/api/v1")
app.include_router(recycle_bin.router,    prefix="/api/v1")
app.include_router(approvals.router,      prefix="/api/v1")
app.include_router(emails.router,         prefix="/api/v1")
app.include_router(expenses.router,       prefix="/api/v1")
app.include_router(campaigns.router,      prefix="/api/v1")
app.include_router(leave.router,          prefix="/api/v1")
app.include_router(monitoring.router,     prefix="/api/v1")
app.include_router(announcements.router,  prefix="/api/v1")
app.include_router(meetings.router,       prefix="/api/v1")
app.include_router(automations.router,    prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Flash Agency API"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the exception here in a real production app (e.g., using logging module)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

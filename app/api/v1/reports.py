from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from app.api.v1.deps import get_db, get_current_user
from app.models import Task, Project, User

router = APIRouter(prefix="/reports", tags=["reports"])


def _avatar_initials(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:1].upper() if name else "U"


def _get_period_bounds(period: str):
    now = datetime.now(timezone.utc)
    if period == "weekly":
        start = now - timedelta(days=7)
    elif period == "quarterly":
        start = now - timedelta(days=90)
    else:
        start = now - timedelta(days=30)
    return start, now


@router.get("/summary")
def read_report_summary(period: str = "monthly", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    start, end = _get_period_bounds(period)

    total_tasks = db.query(func.count(Task.id)).scalar() or 0
    completed_tasks = db.query(func.count(Task.id)).filter(Task.status == "done").scalar() or 0
    progress_sum = db.query(func.coalesce(func.sum(Task.progress), 0)).scalar() or 0
    avg_hours = float(db.query(func.coalesce(func.avg(Task.spent_hours), 0)).scalar() or 0)

    prev_start = start - (end - start)
    prev_total = db.query(func.count(Task.id)).filter(Task.created_at >= prev_start, Task.created_at < start).scalar() or 0
    prev_completed = db.query(func.count(Task.id)).filter(Task.status == "done", Task.created_at >= prev_start, Task.created_at < start).scalar() or 0
    prev_hours = float(db.query(func.coalesce(func.avg(Task.spent_hours), 0)).filter(Task.created_at >= prev_start, Task.created_at < start).scalar() or 0)
    prev_progress = db.query(func.coalesce(func.sum(Task.progress), 0)).filter(Task.created_at >= prev_start, Task.created_at < start).scalar() or 0

    if prev_total > 0:
        tasks_change = int(round(((total_tasks - prev_total) / prev_total) * 100))
    else:
        tasks_change = total_tasks

    prev_avg_productivity = int(round((prev_completed / prev_total) * 100)) if prev_total else 0
    curr_productivity = int(round((completed_tasks / total_tasks) * 100)) if total_tasks else 0
    if prev_avg_productivity > 0:
        avg_change = int(round(((curr_productivity - prev_avg_productivity) / prev_avg_productivity) * 100))
    else:
        avg_change = curr_productivity

    if prev_hours > 0:
        hours_change = round(avg_hours - prev_hours, 1)
    else:
        hours_change = 0.0

    prev_utilization = int(round((prev_progress / prev_total))) if prev_total else 0
    curr_utilization = int(round((progress_sum / total_tasks))) if total_tasks else 0
    if prev_utilization > 0:
        util_change = int(round(((curr_utilization - prev_utilization) / prev_utilization) * 100))
    else:
        util_change = curr_utilization

    change_values = {
        "avg": avg_change,
        "tasks": tasks_change,
        "hours": hours_change,
        "utilization": util_change,
    }

    projects = db.query(Project).all()
    revenue_trend = []
    team_radar = []
    task_trends = []

    for project in projects:
        project_tasks = db.query(Task).filter(Task.project_id == project.id).all()
        created = len(project_tasks)
        completed = sum(1 for task in project_tasks if task.status == "done")
        efficiency = int(round((completed / created) * 100)) if created else 0

        revenue_trend.append({
            "month": project.name,
            "revenue": float(project.spent or 0),
            "target": float(project.budget or 0),
        })
        team_radar.append({
            "subject": project.name if len(project.name) <= 20 else project.name[:20] + "…",
            "a": efficiency,
            "b": project.progress or 0,
        })
        task_trends.append({
            "label": project.name,
            "created": created,
            "completed": completed,
        })

    users = db.query(User).all()
    user_rows = []
    for user in users:
        total = db.query(func.count(Task.id)).filter(Task.assignees.any(User.id == user.id)).scalar() or 0
        completed = db.query(func.count(Task.id)).filter(Task.assignees.any(User.id == user.id), Task.status == "done").scalar() or 0
        user_rows.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "departmentId": user.department_id,
            "tasksCompleted": completed,
            "tasksTotal": total,
            "avatar": _avatar_initials(user.name),
        })

    avg_productivity = int(round((completed_tasks / total_tasks) * 100)) if total_tasks else 0
    team_utilization = int(round((progress_sum / total_tasks))) if total_tasks else 0

    return {
        "avgProductivity": avg_productivity,
        "tasksCompleted": completed_tasks,
        "avgHoursPerTask": round(avg_hours, 1),
        "teamUtilization": team_utilization,
        "avgProductivityChange": change_values["avg"],
        "tasksCompletedChange": change_values["tasks"],
        "avgHoursPerTaskChange": change_values["hours"],
        "teamUtilizationChange": change_values["utilization"],
        "revenueTrend": revenue_trend,
        "teamRadar": team_radar,
        "users": user_rows,
        "taskTrends": task_trends,
    }

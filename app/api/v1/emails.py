from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.api.v1.deps import get_db, get_current_user
from app.models import User, Task
from app.core.config import get_settings

router = APIRouter(prefix="/emails", tags=["emails"])

settings = get_settings()


class DailySummaryPayload(BaseModel):
    to: str
    subject: str
    html: str
    text: str


class DailySummaryResponse(BaseModel):
    success: bool
    message: str


def _send_email_smtp(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    if not settings.smtp_username or not settings.smtp_password:
        print("=" * 60)
        print("EMAIL NOT SENT - SMTP not configured")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Text: {text_body[:200]}...")
        print("=" * 60)
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email

        part_text = MIMEText(text_body, "plain")
        part_html = MIMEText(html_body, "html")
        msg.attach(part_text)
        msg.attach(part_html)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_from_email, to_email, msg.as_string())

        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


@router.post("/daily-summary", response_model=DailySummaryResponse)
def send_daily_summary_email(
    payload: DailySummaryPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    super_admin = db.query(User).filter(User.role == "super_admin").first()
    if not super_admin:
        raise HTTPException(status_code=404, detail="Super admin not found")

    recipient = payload.to or super_admin.email or settings.super_admin_email

    sent = _send_email_smtp(
        to_email=recipient,
        subject=payload.subject,
        html_body=payload.html,
        text_body=payload.text,
    )

    if sent:
        return DailySummaryResponse(success=True, message=f"Daily summary email sent to {recipient}")
    else:
        return DailySummaryResponse(success=False, message="SMTP not configured. Email content logged to console.")


@router.get("/daily-summary/preview", response_model=dict)
def preview_daily_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admin can preview emails")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.status == "done").count()
    pending_tasks = db.query(Task).filter(Task.status == "todo").count()
    in_progress_tasks = db.query(Task).filter(Task.status == "in_progress").count()
    blocked_tasks = db.query(Task).filter(Task.status == "blocked").count()

    tasks = db.query(Task).all()
    task_list = []
    for task in tasks:
        task_list.append({
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
            "assignedTo": [u.name for u in task.assignees],
            "dueDate": task.due_date,
        })

    return {
        "date": today,
        "to": settings.super_admin_email,
        "subject": f"Daily Task Summary - {today}",
        "stats": {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": pending_tasks + in_progress_tasks,
            "blocked": blocked_tasks,
        },
        "tasks": task_list,
    }

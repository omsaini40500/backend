import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import ActivityLog

def log_activity(
    db: Session,
    user_id: str,
    user_name: str,
    action: str,
    target: str,
    module: str,
    ip: str = "127.0.0.1",
    browser: str = "Unknown",
    location: str = "Unknown",
    old_value: str = None,
    new_value: str = None,
):
    try:
        log_entry = ActivityLog(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            user_name=user_name,
            action=action,
            target=target,
            module=module,
            old_value=old_value,
            new_value=new_value,
            ip=ip,
            browser=browser,
            location=location,
            created_at=datetime.now(timezone.utc)
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to log activity: {e}")

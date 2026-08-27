from app.db.session import SessionLocal
from app.models import User
from app.models import ResetToken
from datetime import datetime, timedelta, timezone
import uuid
import secrets
db = SessionLocal()
user = db.query(User).filter(User.email == 'akshaynaithani@gmail.com').first()
if user:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    db_token = ResetToken(id=str(uuid.uuid4())[:8], token=token, email=user.email, user_id=user.id, created_at=datetime.now(timezone.utc), expires_at=expires)
    db.add(db_token)
    db.commit()
    print(f'https://task-management-system-6cmr.vercel.app/reset-password?token={token}&email={user.email}')

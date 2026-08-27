from app.db.session import SessionLocal
from sqlalchemy import text
db = SessionLocal()
rs = db.execute(text("SELECT token, email FROM reset_tokens WHERE email='akshaynaithani@gmail.com' ORDER BY created_at DESC LIMIT 1")).first()
if rs:
    print(f'https://task-management-system-6cmr.vercel.app/reset-password?token={rs[0]}&email={rs[1]}')
else:
    print('No token')

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import jwt
from app.db.session import SessionLocal
from app.api.v1.deps import get_db, get_current_user
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.config import get_settings
from app.models import User, ResetToken
from app.schemas import Token, UserOut
from pydantic import BaseModel

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    token: str
    new_password: str

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

def _generate_reset_token() -> str:
    import secrets
    return secrets.token_urlsafe(32)

_reset_tokens: dict = {}

@router.post("/login", response_model=Token)
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"email": user.email, "user_id": user.id, "role": user.role},
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(data={"email": user.email, "user_id": user.id, "role": user.role})
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="none",
        secure=True,
        max_age=settings.access_token_expire_minutes * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=f"Bearer {refresh_token}",
        httponly=True,
        samesite="none",
        secure=True,
        max_age=settings.access_token_expire_minutes * 60 * 24 # 24 times longer for refresh
    )
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh_token_endpoint(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
        token = auth_header.split(" ")[1]
        
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        email = payload.get("email")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        new_access = create_access_token(
            data={"email": user.email, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires,
        )
        new_refresh = create_refresh_token(data={"email": user.email, "user_id": user.id, "role": user.role})
        
        response.set_cookie(
            key="access_token",
            value=f"Bearer {new_access}",
            httponly=True,
            samesite="none",
            secure=True,
            max_age=settings.access_token_expire_minutes * 60
        )
        response.set_cookie(
            key="refresh_token",
            value=f"Bearer {new_refresh}",
            httponly=True,
            samesite="none",
            secure=True,
            max_age=settings.access_token_expire_minutes * 60 * 24
        )
        
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        return {"message": "If an account with that email exists, a password reset link has been sent."}

    token = _generate_reset_token()
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    db_token = ResetToken(
        id=str(uuid4())[:8],
        token=token,
        email=user.email,
        user_id=user.id,
        created_at=datetime.now(timezone.utc),
        expires_at=expires,
    )
    db.add(db_token)
    db.commit()

    reset_link = f"http://localhost:8443/reset-password?token={token}&email={user.email}"
    subject = "Reset your password - Flash Communications"
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ font-family: 'Inter', Arial, sans-serif; background: #0d0e14; color: #e2e8f0; padding: 20px; }}
        .container {{ max-width: 500px; margin: 0 auto; background: #13141a; border-radius: 12px; padding: 24px; border: 1px solid rgba(255,255,255,0.06); }}
        .header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.06); }}
        .logo {{ width: 32px; height: 32px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; }}
        .title {{ font-size: 18px; font-weight: 600; color: white; }}
        .btn {{ display: inline-block; padding: 10px 20px; background: #6366f1; color: white; text-decoration: none; border-radius: 8px; font-weight: 500; margin: 16px 0; }}
        .footer {{ margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.06); text-align: center; font-size: 11px; color: #4b5563; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <div class="logo">F</div>
          <div>
            <div class="title">Reset your password</div>
            <div style="font-size: 12px; color: #64748b;">Flash Communications</div>
          </div>
        </div>
        <p style="color: #94a3b8; font-size: 14px; line-height: 1.6;">
          Hi {user.name},<br><br>
          We received a request to reset your password. Click the button below to create a new password.
        </p>
        <div style="text-align: center;">
          <a href="{reset_link}" class="btn">Reset Password</a>
        </div>
        <p style="color: #64748b; font-size: 12px; line-height: 1.6;">
          If you didn't request this, you can safely ignore this email.<br>
          This link will expire in 30 minutes.
        </p>
        <div class="footer">
          Flash Communications Task Management System<br>
          This is an automated email.
        </div>
      </div>
    </body>
    </html>
    """
    text = f"""
Reset your password - Flash Communications

Hi {user.name},

We received a request to reset your password. Click the link below to create a new password:

{reset_link}

If you didn't request this, you can safely ignore this email. This link will expire in 30 minutes.

---
Flash Communications Task Management System
This is an automated email.
    """.strip()

    _send_email_smtp(user.email, subject, html, text)
    return {"message": "If an account with that email exists, a password reset link has been sent."}

@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_record = db.query(ResetToken).filter(ResetToken.token == data.token).first()
    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if token_record.email != data.email:
        raise HTTPException(status_code=400, detail="Invalid token for this email")

    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        db.delete(token_record)
        db.commit()
        raise HTTPException(status_code=400, detail="Token expired")

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    from app.core.security import get_password_hash
    user.hashed_password = get_password_hash(data.new_password)
    db.delete(token_record)
    db.commit()

    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

from datetime import UTC, datetime, timedelta
import hashlib
import secrets
import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from app.api.deps import DbSession, get_current_user
from app.core.config import get_settings
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models import PasswordResetToken, RefreshToken, Role, User
from app.schemas import AuthResponse, ForgotPasswordRequest, LoginRequest, RegisterRequest, ResetPasswordRequest, TokenRefreshRequest, UserResponse
from app.services.email import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


def token_pair(user: User, db: DbSession) -> AuthResponse:
    settings = get_settings()
    access = create_token(str(user.id), "access", timedelta(minutes=settings.access_token_expire_minutes))
    refresh = create_token(str(user.id), "refresh", timedelta(days=settings.refresh_token_expire_days))
    payload = decode_token(refresh, "refresh")
    db.add(RefreshToken(user_id=user.id, jti=payload["jti"], expires_at=datetime.fromtimestamp(payload["exp"], UTC)))
    db.commit()
    return AuthResponse(access_token=access, refresh_token=refresh, user=user)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: DbSession):
    email = str(body.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account already exists for this email")
    user = User(full_name=body.full_name.strip(), email=email, password_hash=hash_password(body.password), role=Role.farmer)
    db.add(user); db.commit(); db.refresh(user)
    return token_pair(user, db)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: DbSession):
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    return token_pair(user, db)


@router.post("/refresh", response_model=AuthResponse)
def refresh(body: TokenRefreshRequest, db: DbSession):
    try:
        payload = decode_token(body.refresh_token, "refresh")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    token = db.scalar(select(RefreshToken).where(RefreshToken.jti == payload["jti"], RefreshToken.revoked.is_(False)))
    user = db.get(User, int(payload["sub"]))
    if not token or not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")
    token.revoked = True; db.commit()
    return token_pair(user, db)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: TokenRefreshRequest, db: DbSession):
    try:
        payload = decode_token(body.refresh_token, "refresh")
        token = db.scalar(select(RefreshToken).where(RefreshToken.jti == payload["jti"]))
        if token:
            token.revoked = True; db.commit()
    except jwt.InvalidTokenError:
        pass


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(body: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: DbSession):
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    if user:
        raw_token = secrets.token_urlsafe(48)
        db.add(PasswordResetToken(user_id=user.id, token_hash=hashlib.sha256(raw_token.encode()).hexdigest(), expires_at=datetime.now(UTC) + timedelta(minutes=30)))
        db.commit()
        settings = get_settings()
        if settings.environment == "development":
            return {"message": "Reset token created for local development", "reset_token": raw_token}
        background_tasks.add_task(send_password_reset_email, user.email, raw_token)
    return {"message": "If the account exists, password reset instructions will be sent."}


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(body: ResetPasswordRequest, db: DbSession):
    hashed = hashlib.sha256(body.token.encode()).hexdigest()
    record = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hashed, PasswordResetToken.used.is_(False)))
    if not record or record.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user = db.get(User, record.user_id)
    user.password_hash = hash_password(body.password); record.used = True
    for refresh in db.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id)):
        refresh.revoked = True
    db.commit()

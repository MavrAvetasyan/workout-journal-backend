from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import (
    DEBUG_AUTH_CODES,
    LOGIN_CODE_MAX_ATTEMPTS,
    LOGIN_CODE_RESEND_SECONDS,
    LOGIN_CODE_TTL_MINUTES,
)
from ..database import get_db
from ..deps import get_current_user
from ..mailer import send_login_code_email
from ..models import LoginCode, User
from ..schemas import (
    LoginCodeResponse,
    LoginRequest,
    RegisterRequest,
    RequestLoginCodeRequest,
    TokenResponse,
    UserRead,
    VerifyLoginCodeRequest,
)
from ..security import (
    create_access_token,
    generate_login_code,
    hash_login_code,
    hash_password,
    utcnow,
    verify_login_code,
    verify_password,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def _get_or_create_user(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user

    user = User(email=email, password_hash="")
    db.add(user)
    db.flush()
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user=user)


@router.post("/request-code", response_model=LoginCodeResponse)
def request_code(payload: RequestLoginCodeRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = _get_or_create_user(db, email)
    now = utcnow()

    latest_code = db.scalar(
        select(LoginCode)
        .where(LoginCode.email == email)
        .order_by(LoginCode.created_at.desc())
        .limit(1)
    )
    if latest_code and (now - latest_code.created_at) < timedelta(seconds=LOGIN_CODE_RESEND_SECONDS):
        wait_seconds = LOGIN_CODE_RESEND_SECONDS - int((now - latest_code.created_at).total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Try again in {max(wait_seconds, 1)} seconds",
        )

    code = generate_login_code()
    login_code = LoginCode(
        user_id=user.id,
        email=email,
        code_hash=hash_login_code(email=email, code=code),
        expires_at=now + timedelta(minutes=LOGIN_CODE_TTL_MINUTES),
    )
    db.add(login_code)
    db.commit()

    send_login_code_email(
        email=email,
        code=code,
        expires_minutes=LOGIN_CODE_TTL_MINUTES,
    )

    return LoginCodeResponse(
        expires_in_seconds=LOGIN_CODE_TTL_MINUTES * 60,
        next_request_in_seconds=LOGIN_CODE_RESEND_SECONDS,
        debug_code=code if DEBUG_AUTH_CODES else None,
    )


@router.post("/verify-code", response_model=TokenResponse)
def verify_code(payload: VerifyLoginCodeRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    code = payload.code.strip()
    now = utcnow()

    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    login_code = db.scalar(
        select(LoginCode)
        .where(LoginCode.email == email, LoginCode.consumed_at.is_(None))
        .order_by(LoginCode.created_at.desc())
        .limit(1)
    )
    if not login_code or login_code.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code expired, request a new one")

    if login_code.attempts >= LOGIN_CODE_MAX_ATTEMPTS:
        login_code.consumed_at = now
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many attempts, request a new code")

    login_code.attempts += 1
    if not verify_login_code(email=email, code=code, expected_hash=login_code.code_hash):
        if login_code.attempts >= LOGIN_CODE_MAX_ATTEMPTS:
            login_code.consumed_at = now
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid code")

    login_code.consumed_at = now
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from ..database import get_db
from ..models import User, Organization
from ..schemas import RegisterRequest, LoginRequest
from ..auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from ..utils import get_or_create_default_org

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register")
@router.post("/register/")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    username = req.username or req.email
    if not username or not req.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username/email and password are required."
        )

    # Check existing
    res = await db.execute(
        select(User).where(or_(User.username == username, User.email == req.email))
    )
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email/username already exists."
        )

    default_org = await get_or_create_default_org(db)

    new_user = User(
        username=username,
        email=req.email,
        hashed_password=get_password_hash(req.password),
        first_name=req.first_name,
        last_name=req.last_name,
        organization_id=default_org.id,
        role="CA_FIRM_PARTNER"
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token_data = {"user_id": str(new_user.id), "username": new_user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "message": "User registered successfully",
        "tokens": {
            "refresh": refresh_token,
            "access": access_token
        },
        "user": {
            "id": str(new_user.id),
            "username": new_user.username,
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name
        }
    }


@router.post("/login")
@router.post("/login/")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    identifier = req.username or req.email
    if not identifier or not req.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email/username and password are required."
        )

    # Support login by email or username
    res = await db.execute(
        select(User).where(or_(User.username == identifier, User.email == identifier))
    )
    user = res.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials."
        )

    token_data = {"user_id": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return {
        "tokens": {
            "refresh": refresh_token,
            "access": access_token
        },
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "designation": user.designation,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser
        }
    }


@router.get("/me")
@router.get("/me/")
async def current_user(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff
    }


@router.post("/token/refresh")
@router.post("/token/refresh/")
async def token_refresh(data: dict, db: AsyncSession = Depends(get_db)):
    refresh_token = data.get("refresh")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="refresh token required")
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type")
    user_id = payload.get("user_id")
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    new_access = create_access_token({"user_id": str(user.id), "username": user.username})
    return {"access": new_access}


@router.post("/token/verify")
@router.post("/token/verify/")
async def token_verify(data: dict):
    token = data.get("token")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="token required")
    decode_token(token)
    return {}

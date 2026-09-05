from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.core.auth import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Merchant Authentication"])

class LoginRequest(BaseModel):
    email: str
    password: str

class UserProfileResponse(BaseModel):
    id: str
    merchant_id: str
    email: str
    name: str
    role: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates merchant user and returns a signed JWT access token."""
    email_clean = req.email.lower().strip()
    stmt = select(User).where(User.email == email_clean)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    # Self-heal initial demo accounts on first login if database was unseeded
    if not user and email_clean in ["admin@acrobatics.com", "ops@acrobatics.com"]:
        from app.core.auth import ensure_initial_users
        try:
            await ensure_initial_users(db)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()
        except Exception:
            pass

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "merchant_id": user.merchant_id,
        "name": user.name
    })

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfileResponse(
            id=user.id,
            merchant_id=user.merchant_id,
            email=user.email,
            name=user.name,
            role=user.role
        )
    )

@router.get("/me", response_model=UserProfileResponse)
async def get_me(user: Optional[User] = Depends(get_current_user)):
    """Returns profile of currently authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated."
        )
    return UserProfileResponse(
        id=user.id,
        merchant_id=user.merchant_id,
        email=user.email,
        name=user.name,
        role=user.role
    )

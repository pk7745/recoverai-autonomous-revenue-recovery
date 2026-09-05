import hmac
import hashlib
import base64
import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hashes password using PBKDF2-HMAC-SHA256 with 100,000 iterations and random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against salted PBKDF2 hash in constant time."""
    try:
        salt, key_hex = hashed_password.split("$")
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(key.hex(), key_hex)
    except Exception:
        return False

async def ensure_initial_users(db: AsyncSession):
    """
    Idempotently ensures default merchant and demo users (MERCHANT_ADMIN and
    OPERATIONS_AGENT) exist with properly hashed passwords.
    """
    from app.models.merchant import Merchant
    
    # 1. Ensure Merchant
    stmt = select(Merchant).where(Merchant.id == "merch_razorpay_demo")
    res = await db.execute(stmt)
    merchant = res.scalar_one_or_none()
    if not merchant:
        merchant = Merchant(
            id="merch_razorpay_demo",
            name="Acrobatics Apparel Pvt Ltd",
            api_key_id="rzp_test_recoverai2026",
            webhook_secret="whsec_recoverai_super_secret_webhook_2026",
            autonomous_limit=5000.0,
            max_retries=2,
            min_retry_interval_mins=30,
            risk_threshold=0.70
        )
        db.add(merchant)
        await db.flush()

    # 2. Ensure Admin User
    admin_stmt = select(User).where(User.email == "admin@acrobatics.com")
    admin_res = await db.execute(admin_stmt)
    admin_user = admin_res.scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            id="usr_admin",
            merchant_id=merchant.id,
            email="admin@acrobatics.com",
            name="Vikramaditya (Lead Admin)",
            hashed_password=hash_password("RecoverAI2026!"),
            role="MERCHANT_ADMIN"
        )
        db.add(admin_user)
    else:
        admin_user.role = "MERCHANT_ADMIN"
        admin_user.hashed_password = hash_password("RecoverAI2026!")

    # 3. Ensure Ops User
    ops_stmt = select(User).where(User.email == "ops@acrobatics.com")
    ops_res = await db.execute(ops_stmt)
    ops_user = ops_res.scalar_one_or_none()
    if not ops_user:
        ops_user = User(
            id="usr_ops",
            merchant_id=merchant.id,
            email="ops@acrobatics.com",
            name="Neha Sharma (Ops Agent)",
            hashed_password=hash_password("RecoverAI2026!"),
            role="OPERATIONS_AGENT"
        )
        db.add(ops_user)
    else:
        ops_user.role = "OPERATIONS_AGENT"
        ops_user.hashed_password = hash_password("RecoverAI2026!")

    await db.commit()

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _b64url_decode(s: str) -> bytes:
    pad = len(s) % 4
    if pad:
        s += "=" * (4 - pad)
    return base64.urlsafe_b64decode(s.encode("utf-8"))

def create_access_token(payload: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates an HMAC-SHA256 signed JWT token."""
    header = {"alg": "HS256", "typ": "JWT"}
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=24))
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(datetime.now(timezone.utc).timestamp())})

    header_b64 = _b64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(to_encode).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    secret_key = settings.JWT_SECRET_KEY.encode("utf-8")
    signature = hmac.new(secret_key, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Optional[dict]:
    """Validates signature and expiration of JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        secret_key = settings.JWT_SECRET_KEY.encode("utf-8")
        expected_sig = hmac.new(secret_key, signing_input, hashlib.sha256).digest()
        provided_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, provided_sig):
            return None

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        exp = payload.get("exp")
        if exp and exp < datetime.now(timezone.utc).timestamp():
            return None

        return payload
    except Exception:
        return None

async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Resolves authenticated user from Bearer JWT. Returns None if unauthenticated."""
    if not auth or not auth.credentials:
        return None

    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        return None

    stmt = select(User).where(User.id == payload["sub"])
    res = await db.execute(stmt)
    return res.scalar_one_or_none()

def require_role(allowed_roles: List[str]):
    """Enforces specific RBAC roles on endpoints."""
    async def role_checker(
        auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        if not auth or not auth.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please log in.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        user = await get_current_user(auth, db)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {user.role} role is not authorized to perform this operation. Required: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker

"""
Authentication router — register & login.

No passwords: login is identifier-based (consumer ID / vehicle number / DL number).
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.database import create_user, find_user_by_identifier

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Request / Response models ──────────────────────────────

class RegisterRequest(BaseModel):
    name: str
    phone: str
    consumer_id: str
    vehicle_number: Optional[str] = None
    dl_number: Optional[str] = None


class LoginRequest(BaseModel):
    identifier: str
    identifierType: str  # 'challan' | 'vehicle' | 'dl'


class AuthResponse(BaseModel):
    user: dict
    token: str


# ── Endpoints ──────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """Register a new user and return an auth token."""
    if not req.name.strip() or not req.phone.strip() or not req.consumer_id.strip():
        raise HTTPException(status_code=400, detail="Name, phone and consumer ID are required.")

    try:
        user = create_user(
            name=req.name,
            phone=req.phone,
            consumer_id=req.consumer_id,
            vehicle_number=req.vehicle_number,
            dl_number=req.dl_number,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    token = str(uuid.uuid4())
    logger.info(f"Registered user {user['id']} ({user['name']})")
    return AuthResponse(user=user, token=token)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Login with a unique identifier (consumer ID, vehicle number or DL number)."""
    user = find_user_by_identifier(req.identifier, req.identifierType)
    if not user:
        raise HTTPException(status_code=404, detail="No user found with that identifier.")

    token = str(uuid.uuid4())
    logger.info(f"User {user['id']} logged in via {req.identifierType}")
    return AuthResponse(user=user, token=token)

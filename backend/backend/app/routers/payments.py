from fastapi import APIRouter, HTTPException
from app.models import PaymentRequest, PaymentResponse, ServiceType
from app.services.navigator import UtilityNavigator
import uuid
from functools import lru_cache

router = APIRouter()

# Track active payment sessions
active_sessions: dict = {}

# Cached singleton navigator instance to avoid expensive re-initialization
@lru_cache(maxsize=1)
def get_navigator() -> UtilityNavigator:
    """Return cached UtilityNavigator instance."""
    return UtilityNavigator()


@router.post("/initiate", response_model=PaymentResponse)
async def initiate_payment(request: PaymentRequest):
    """Initiate payment and get QR code"""
    try:
        navigator = get_navigator()
        qr_base64 = await navigator.navigate_to_payment(
            service_type=request.service_type,
            consumer_id=request.consumer_id
        )
        
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            "account_id": request.account_id,
            "status": "pending"
        }
        
        return PaymentResponse(
            success=True,
            qr_code_base64=qr_base64,
            session_id=session_id
        )
    except Exception as e:
        return PaymentResponse(
            success=False,
            error_message=str(e)
        )


@router.get("/status/{session_id}")
async def check_payment_status(session_id: str):
    """Check payment session status"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]


@router.post("/confirm/{session_id}")
async def confirm_payment(session_id: str):
    """Mark payment as confirmed (called after user scans QR)"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    active_sessions[session_id]["status"] = "completed"
    return {"message": "Payment confirmed", "status": "completed"}

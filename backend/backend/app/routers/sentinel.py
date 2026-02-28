"""
OneWay Sentinel Router - Motor Violation Assistant API

Endpoints for:
- Violation reporting with AI analysis
- Parking dispute resolution
- Vehicle registry management
"""
import base64
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.models import (
    ViolationReport, RegistryEntry, ViolationType, ViolationStatus,
    ViolationAnalysisRequest, ViolationAnalysisResponse,
    ParkingAssistRequest, ParkingAssistResponse
)
from app.database import (
    create_violation_report, get_all_violation_reports, update_violation_status,
    get_violation_report, add_registry_entry, find_registry_by_plate, 
    get_all_registry_entries, delete_registry_entry
)
from app.services.sentinel_engine import get_sentinel_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sentinel", tags=["Sentinel"])

# Directory for storing violation images
VIOLATIONS_DIR = Path(__file__).resolve().parent.parent / "violations"
VIOLATIONS_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Violation Reporting
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=ViolationAnalysisResponse)
async def analyze_violation(request: ViolationAnalysisRequest):
    """
    Analyze an uploaded image for traffic violations.
    
    - Extracts EXIF metadata (GPS, timestamp)
    - Uses AI to detect license plate and violation type
    - Verifies image authenticity
    - Generates MVD email draft
    """
    try:
        # Decode image
        image_bytes = base64.b64decode(request.image_base64)
        
        engine = get_sentinel_engine()
        
        # Extract EXIF data
        exif_data = engine.extract_exif_data(image_bytes)
        
        # Use device location as fallback if EXIF doesn't have GPS
        if not exif_data.get("latitude") and request.device_latitude:
            exif_data["latitude"] = request.device_latitude
            exif_data["longitude"] = request.device_longitude
            exif_data["location_string"] = f"{request.device_latitude:.6f}, {request.device_longitude:.6f}"
            exif_data["location_source"] = "device"
        
        # Analyze with AI
        analysis = await engine.analyze_violation(image_bytes)
        
        # Save image
        image_id = str(uuid.uuid4())
        image_path = VIOLATIONS_DIR / f"{image_id}.jpg"
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        
        # Sanitize violation_type before saving
        valid_types = {"no_helmet", "triple_riding", "wrong_side", "no_parking", "signal_jump", "obstruction", "other"}
        raw_type = analysis.get("violation_type", "other") or "other"
        clean_violation_type = raw_type if raw_type in valid_types else "other"
        
        # Create report in database
        report_data = create_violation_report(
            plate_number=analysis.get("plate"),
            violation_type=clean_violation_type,
            violation_description=analysis.get("violation", ""),
            formal_description=analysis.get("description", ""),
            location=exif_data.get("location_string"),
            latitude=exif_data.get("latitude"),
            longitude=exif_data.get("longitude"),
            timestamp=exif_data.get("timestamp"),
            image_path=str(image_path),
            is_authentic=analysis.get("is_authentic", True),
            confidence=analysis.get("confidence", 0.0),
            status="verified" if analysis.get("is_authentic") else "rejected"
        )
        
        # Generate MVD email
        mvd_email = engine.generate_mvd_email(analysis, exif_data, image_bytes)
        
        # Sanitize violation_type - map invalid values to "other"
        valid_violation_types = {"no_helmet", "triple_riding", "wrong_side", "no_parking", "signal_jump", "obstruction", "other"}
        raw_violation_type = report_data["violation_type"] or "other"
        sanitized_violation_type = raw_violation_type if raw_violation_type in valid_violation_types else "other"
        
        report = ViolationReport(
            id=report_data["id"],
            plate_number=report_data["plate_number"],
            violation_type=sanitized_violation_type,
            violation_description=report_data["violation_description"],
            formal_description=report_data["formal_description"],
            location=report_data["location"],
            latitude=report_data["latitude"],
            longitude=report_data["longitude"],
            timestamp=report_data["timestamp"],
            is_authentic=bool(report_data["is_authentic"]),
            confidence=report_data["confidence"],
            status=report_data["status"],
            created_at=report_data["created_at"]
        )
        
        return ViolationAnalysisResponse(
            success=True,
            report=report,
            exif_data=exif_data,
            mvd_email=mvd_email
        )
        
    except Exception as e:
        logger.error(f"Violation analysis failed: {e}")
        return ViolationAnalysisResponse(
            success=False,
            error_message=str(e)
        )


@router.get("/reports", response_model=List[ViolationReport])
async def get_reports():
    """Get all violation reports."""
    reports = get_all_violation_reports()
    valid_violation_types = {"no_helmet", "triple_riding", "wrong_side", "no_parking", "signal_jump", "obstruction", "other"}
    
    return [
        ViolationReport(
            id=r["id"],
            plate_number=r["plate_number"],
            violation_type=r["violation_type"] if r["violation_type"] in valid_violation_types else "other",
            violation_description=r["violation_description"],
            formal_description=r["formal_description"],
            location=r["location"],
            latitude=r["latitude"],
            longitude=r["longitude"],
            timestamp=r["timestamp"],
            is_authentic=bool(r["is_authentic"]),
            confidence=r["confidence"],
            status=r["status"],
            created_at=r["created_at"]
        )
        for r in reports
    ]


class StatusUpdateRequest(BaseModel):
    status: ViolationStatus


@router.patch("/reports/{report_id}/status")
async def update_report_status(report_id: str, request: StatusUpdateRequest):
    """Update the status of a violation report."""
    updated = update_violation_status(report_id, request.status.value)
    if not updated:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"success": True, "status": request.status}


@router.post("/reports/{report_id}/send-mvd")
async def send_to_mvd(report_id: str):
    """
    Send violation report email with photograph to configured recipient.
    """
    # Get the report
    report = get_violation_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Check if already sent
    if report["status"] == "emailed_to_mvd":
        return {
            "success": True,
            "message": "Report was already sent",
            "status": "emailed_to_mvd"
        }
    
    # Load the image
    image_path = report.get("image_path")
    if not image_path or not Path(image_path).exists():
        raise HTTPException(status_code=404, detail="Evidence image not found")
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    # Prepare analysis and exif data from stored report
    analysis = {
        "plate": report["plate_number"],
        "violation": report["violation_description"],
        "violation_type": report["violation_type"],
        "description": report["formal_description"],
        "is_authentic": bool(report["is_authentic"]),
        "confidence": report["confidence"]
    }
    
    exif_data = {
        "timestamp": report["timestamp"],
        "location_string": report["location"],
        "latitude": report["latitude"],
        "longitude": report["longitude"]
    }
    
    # Send the email
    engine = get_sentinel_engine()
    email_result = await engine.send_violation_email(
        analysis, exif_data, image_bytes, report_id
    )
    
    if email_result.get("success"):
        # Update status
        update_violation_status(report_id, "emailed_to_mvd")
        return {
            "success": True,
            "message": f"Report emailed to {email_result.get('recipient')}",
            "message_id": email_result.get("message_id"),
            "status": "emailed_to_mvd"
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to send email: {email_result.get('error')}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Parking Assistant
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/parking-assist", response_model=ParkingAssistResponse)
async def parking_assist(request: ParkingAssistRequest):
    """
    Trigger parking obstruction resolution.
    
    - Looks up plate in registry
    - Triggers automated call (currently logged, pending voice integration)
    """
    # Look up in registry
    registry_entry = find_registry_by_plate(request.plate_number)
    
    if not registry_entry:
        return ParkingAssistResponse(
            success=False,
            owner_found=False,
            message=f"Vehicle {request.plate_number} not found in OneWay Registry"
        )
    
    # Trigger call
    engine = get_sentinel_engine()
    call_result = await engine.trigger_parking_call(
        request.plate_number,
        registry_entry["owner_phone"]
    )
    
    return ParkingAssistResponse(
        success=True,
        owner_found=True,
        call_status=call_result["status"],
        message=call_result["message"]
    )


# ─────────────────────────────────────────────────────────────────────────────
# Vehicle Registry
# ─────────────────────────────────────────────────────────────────────────────

class RegistryCreateRequest(BaseModel):
    plate_number: str
    owner_name: str | None = None
    owner_phone: str


@router.post("/registry", response_model=RegistryEntry)
async def create_registry_entry(request: RegistryCreateRequest):
    """Add or update a vehicle in the registry."""
    entry = add_registry_entry(
        request.plate_number,
        request.owner_name,
        request.owner_phone
    )
    return RegistryEntry(
        id=entry["id"],
        plate_number=entry["plate_number"],
        owner_name=entry["owner_name"],
        owner_phone=entry["owner_phone"],
        created_at=entry["created_at"]
    )


@router.get("/registry", response_model=List[RegistryEntry])
async def get_registry():
    """Get all registry entries."""
    entries = get_all_registry_entries()
    return [
        RegistryEntry(
            id=e["id"],
            plate_number=e["plate_number"],
            owner_name=e["owner_name"],
            owner_phone=e["owner_phone"],
            created_at=e["created_at"]
        )
        for e in entries
    ]


@router.get("/registry/{plate_number}", response_model=RegistryEntry | None)
async def lookup_plate(plate_number: str):
    """Look up a plate in the registry."""
    entry = find_registry_by_plate(plate_number)
    if not entry:
        return None
    return RegistryEntry(
        id=entry["id"],
        plate_number=entry["plate_number"],
        owner_name=entry["owner_name"],
        owner_phone=entry["owner_phone"],
        created_at=entry["created_at"]
    )


@router.delete("/registry/{entry_id}")
async def remove_registry_entry(entry_id: str):
    """Delete a registry entry."""
    deleted = delete_registry_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True}

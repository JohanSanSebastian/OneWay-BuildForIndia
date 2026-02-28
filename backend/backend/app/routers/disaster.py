"""
OneWay Disaster & Infrastructure Sentinel Router

Endpoints for:
- Disaster/infrastructure incident reporting with AI analysis
- Kerala geospatial incident mapping
- Authority identification and notification
- Emergency contact directory
"""
import base64
import uuid
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.models import (
    DisasterIncident, IncidentCategory, IncidentSeverity, IncidentStatus,
    IncidentAnalysisRequest, IncidentAnalysisResponse, AuthorityContact
)
from app.database import (
    create_disaster_incident, get_all_disaster_incidents, get_active_disaster_incidents,
    update_disaster_incident_status, get_disaster_incident, get_disaster_incidents_by_district,
    get_disaster_incident_stats
)
from app.services.disaster_engine import get_disaster_engine
from app.services.kerala_authorities import KeralaAuthorityDirectory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/disaster", tags=["Disaster Sentinel"])

# Directory for storing incident images
INCIDENTS_DIR = Path(__file__).resolve().parent.parent / "incidents"
INCIDENTS_DIR.mkdir(exist_ok=True)

# Initialize authority directory
authority_directory = KeralaAuthorityDirectory()


# ─────────────────────────────────────────────────────────────────────────────
# Incident Reporting & Analysis
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=IncidentAnalysisResponse)
async def analyze_incident(request: IncidentAnalysisRequest):
    """
    Analyze an uploaded image for disaster or infrastructure issues.
    
    - Extracts EXIF metadata (GPS, timestamp)
    - Uses AI to classify incident type and severity
    - Identifies relevant authorities
    - Generates call script and formal report
    """
    try:
        # Decode image
        image_bytes = base64.b64decode(request.image_base64)
        
        engine = get_disaster_engine()
        
        # Extract EXIF data
        exif_data = engine.extract_exif_data(image_bytes)
        
        # Use device location as fallback if EXIF doesn't have GPS
        if not exif_data.get("latitude") and request.device_latitude:
            exif_data["latitude"] = request.device_latitude
            exif_data["longitude"] = request.device_longitude
            exif_data["location_string"] = f"{request.device_latitude:.6f}, {request.device_longitude:.6f}"
            exif_data["location_source"] = "device"
        
        # Analyze with AI
        analysis = await engine.analyze_incident(image_bytes)
        
        # Determine district from coordinates
        district = authority_directory.get_district_from_coordinates(
            exif_data.get("latitude"),
            exif_data.get("longitude")
        )
        
        # Save image
        incident_id = str(uuid.uuid4())
        image_path = INCIDENTS_DIR / f"{incident_id}.jpg"
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        
        # Identify relevant authorities
        authorities = engine.identify_authorities(
            category=analysis.get("category", "obstruction"),
            subcategory=analysis.get("subcategory", "other"),
            latitude=exif_data.get("latitude"),
            longitude=exif_data.get("longitude")
        )
        
        # Create incident in database
        incident_data = create_disaster_incident(
            category=analysis.get("category", "obstruction"),
            subcategory=analysis.get("subcategory", "other"),
            severity=analysis.get("severity", "P3"),
            description=analysis.get("description", ""),
            detailed_description=analysis.get("detailed_description", ""),
            location=exif_data.get("location_string"),
            latitude=exif_data.get("latitude"),
            longitude=exif_data.get("longitude"),
            district=district,
            landmarks=analysis.get("landmarks"),
            extracted_text=analysis.get("extracted_text", []),
            timestamp=exif_data.get("timestamp"),
            image_path=str(image_path),
            is_valid=analysis.get("is_valid_incident", True),
            confidence=analysis.get("confidence", 0.0),
            status="verified" if analysis.get("is_valid_incident") else "rejected",
            recommended_authority=analysis.get("recommended_authority")
        )
        
        # Generate call script
        call_script = engine.generate_call_script(analysis, exif_data, incident_id)
        
        # Generate formal report
        formal_report = engine.generate_formal_report(analysis, exif_data, incident_id, authorities)
        
        # Build response incident
        incident = DisasterIncident(
            id=incident_data["id"],
            category=incident_data["category"],
            subcategory=incident_data["subcategory"],
            severity=incident_data["severity"],
            description=incident_data["description"],
            detailed_description=incident_data["detailed_description"],
            location=incident_data["location"],
            latitude=incident_data["latitude"],
            longitude=incident_data["longitude"],
            district=incident_data["district"],
            landmarks=incident_data["landmarks"],
            extracted_text=incident_data["extracted_text"],
            timestamp=incident_data["timestamp"],
            is_valid=incident_data["is_valid"],
            confidence=incident_data["confidence"],
            status=incident_data["status"],
            recommended_authority=incident_data["recommended_authority"],
            created_at=incident_data["created_at"]
        )
        
        return IncidentAnalysisResponse(
            success=True,
            incident=incident,
            exif_data=exif_data,
            authorities=authorities,
            call_script=call_script,
            formal_report=formal_report
        )
        
    except Exception as e:
        logger.error(f"Incident analysis failed: {e}", exc_info=True)
        return IncidentAnalysisResponse(
            success=False,
            error_message=str(e)
        )


@router.get("/incidents", response_model=List[DisasterIncident])
async def get_incidents(active_only: bool = False):
    """Get all disaster incidents, optionally filtered to active only."""
    if active_only:
        incidents = get_active_disaster_incidents()
    else:
        incidents = get_all_disaster_incidents()
    
    return [
        DisasterIncident(
            id=i["id"],
            category=i["category"],
            subcategory=i["subcategory"],
            severity=i["severity"],
            description=i["description"],
            detailed_description=i.get("detailed_description"),
            location=i["location"],
            latitude=i["latitude"],
            longitude=i["longitude"],
            district=i.get("district"),
            landmarks=i.get("landmarks"),
            extracted_text=i.get("extracted_text", []),
            timestamp=i["timestamp"],
            is_valid=i["is_valid"],
            confidence=i["confidence"],
            status=i["status"],
            recommended_authority=i.get("recommended_authority"),
            authorities_notified=i.get("authorities_notified", []),
            created_at=i["created_at"],
            updated_at=i.get("updated_at")
        )
        for i in incidents
    ]


@router.get("/incidents/{incident_id}", response_model=DisasterIncident)
async def get_incident_by_id(incident_id: str):
    """Get a single incident by ID."""
    incident = get_disaster_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return DisasterIncident(
        id=incident["id"],
        category=incident["category"],
        subcategory=incident["subcategory"],
        severity=incident["severity"],
        description=incident["description"],
        detailed_description=incident.get("detailed_description"),
        location=incident["location"],
        latitude=incident["latitude"],
        longitude=incident["longitude"],
        district=incident.get("district"),
        landmarks=incident.get("landmarks"),
        extracted_text=incident.get("extracted_text", []),
        timestamp=incident["timestamp"],
        is_valid=incident["is_valid"],
        confidence=incident["confidence"],
        status=incident["status"],
        recommended_authority=incident.get("recommended_authority"),
        authorities_notified=incident.get("authorities_notified", []),
        created_at=incident["created_at"],
        updated_at=incident.get("updated_at")
    )


class UpdateStatusRequest(BaseModel):
    status: IncidentStatus
    authorities_notified: List[str] = []


@router.patch("/incidents/{incident_id}/status")
async def update_incident_status(incident_id: str, request: UpdateStatusRequest):
    """Update the status of an incident."""
    incident = update_disaster_incident_status(
        incident_id, 
        request.status.value,
        request.authorities_notified if request.authorities_notified else None
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return {"success": True, "incident": incident}


@router.post("/incidents/{incident_id}/notify")
async def notify_authorities(incident_id: str):
    """Mark an incident as authorities notified."""
    incident = get_disaster_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get authorities for this incident
    authorities = authority_directory.get_authorities(
        category=incident["category"],
        subcategory=incident["subcategory"],
        latitude=incident.get("latitude"),
        longitude=incident.get("longitude")
    )
    
    authority_names = [a["name"] for a in authorities]
    
    updated = update_disaster_incident_status(
        incident_id,
        "authority_notified",
        authority_names
    )
    
    return {
        "success": True,
        "authorities_notified": authority_names,
        "incident": updated
    }


# ─────────────────────────────────────────────────────────────────────────────
# Geospatial & Statistics
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/map-data")
async def get_map_data():
    """
    Get incident data formatted for map display.
    Returns only incidents with valid coordinates.
    """
    incidents = get_active_disaster_incidents()
    
    map_markers = []
    for i in incidents:
        if i.get("latitude") and i.get("longitude"):
            map_markers.append({
                "id": i["id"],
                "latitude": i["latitude"],
                "longitude": i["longitude"],
                "category": i["category"],
                "subcategory": i["subcategory"],
                "severity": i["severity"],
                "description": i["description"],
                "status": i["status"],
                "district": i.get("district"),
                "timestamp": i.get("timestamp") or i["created_at"]
            })
    
    return {
        "markers": map_markers,
        "count": len(map_markers),
        "bounds": {
            "north": 12.8,
            "south": 8.2,
            "east": 77.4,
            "west": 74.8
        }
    }


@router.get("/stats")
async def get_stats():
    """Get incident statistics."""
    return get_disaster_incident_stats()


@router.get("/districts/{district}/incidents")
async def get_district_incidents(district: str):
    """Get all incidents for a specific district."""
    incidents = get_disaster_incidents_by_district(district)
    return incidents


# ─────────────────────────────────────────────────────────────────────────────
# Authority Directory
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/authorities")
async def get_all_authorities():
    """Get all emergency contacts and authorities."""
    return authority_directory.get_all_emergency_contacts()


@router.get("/authorities/search")
async def search_authorities(q: str):
    """Search for authorities by name or department."""
    return authority_directory.search_authority(q)


@router.get("/authorities/for-incident/{incident_id}")
async def get_authorities_for_incident(incident_id: str):
    """Get recommended authorities for a specific incident."""
    incident = get_disaster_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    authorities = authority_directory.get_authorities(
        category=incident["category"],
        subcategory=incident["subcategory"],
        latitude=incident.get("latitude"),
        longitude=incident.get("longitude")
    )
    
    return {
        "incident_id": incident_id,
        "severity": incident["severity"],
        "category": incident["category"],
        "authorities": authorities
    }


# ─────────────────────────────────────────────────────────────────────────────
# Call Script Generation
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/incidents/{incident_id}/call-script")
async def get_call_script(incident_id: str):
    """Generate a call script for reporting an incident."""
    incident = get_disaster_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    engine = get_disaster_engine()
    
    exif_data = {
        "location_string": incident.get("location"),
        "latitude": incident.get("latitude"),
        "longitude": incident.get("longitude"),
        "timestamp": incident.get("timestamp")
    }
    
    analysis = {
        "category": incident["category"],
        "subcategory": incident["subcategory"],
        "severity": incident["severity"],
        "description": incident["description"],
        "landmarks": incident.get("landmarks")
    }
    
    return engine.generate_call_script(analysis, exif_data, incident_id)

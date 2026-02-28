from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime


class ServiceType(str, Enum):
    KSEB = "kseb"
    KWA = "kwa"
    ECHALLAN = "echallan"
    KSMART = "ksmart"


class PaymentStatus(str, Enum):
    PAID = "paid"
    UNPAID = "unpaid"
    PENDING = "pending"


class UtilityAccount(BaseModel):
    id: Optional[str] = None
    service_type: ServiceType
    consumer_id: str
    number_plate: Optional[str] = None
    consumer_name: Optional[str] = None
    label: Optional[str] = None  # e.g., "Home", "Office", "Neighbor"
    profile_id: Optional[str] = None


class UtilityBill(BaseModel):
    account_id: str
    service_type: ServiceType
    consumer_name: str
    amount_due: float
    due_date: Optional[str] = None
    status: PaymentStatus
    units_consumed: Optional[float] = None
    billing_period: Optional[str] = None


class BillingHistory(BaseModel):
    account_id: str
    date: str
    amount: float
    units: Optional[float] = None
    status: PaymentStatus


class Profile(BaseModel):
    id: Optional[str] = None
    name: str
    accounts: List[UtilityAccount] = []


class PaymentRequest(BaseModel):
    account_id: str
    service_type: ServiceType
    consumer_id: str


class PaymentResponse(BaseModel):
    success: bool
    qr_code_base64: Optional[str] = None
    error_message: Optional[str] = None
    session_id: Optional[str] = None


class NavigationRequest(BaseModel):
    service_type: ServiceType
    consumer_id: str
    number_plate: Optional[str] = None


class ScrapedData(BaseModel):
    consumer_name: str
    amount_due: float
    status: PaymentStatus
    additional_info: dict = {}
    history: List[BillingHistory] = []


# ─────────────────────────────────────────────────────────────────────────────
# Sentinel Models (Motor Violation Assistant)
# ─────────────────────────────────────────────────────────────────────────────

class ViolationType(str, Enum):
    NO_HELMET = "no_helmet"
    TRIPLE_RIDING = "triple_riding"
    WRONG_SIDE = "wrong_side"
    NO_PARKING = "no_parking"
    SIGNAL_JUMP = "signal_jump"
    OBSTRUCTION = "obstruction"
    OTHER = "other"


class ViolationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EMAILED = "emailed_to_mvd"
    CALL_DISPATCHED = "call_dispatched"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class ViolationReport(BaseModel):
    id: Optional[str] = None
    plate_number: Optional[str] = None
    violation_type: ViolationType
    violation_description: str
    formal_description: str
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: Optional[str] = None
    image_path: Optional[str] = None
    is_authentic: bool = True
    confidence: float = 0.0
    status: ViolationStatus = ViolationStatus.PENDING
    created_at: Optional[str] = None


class RegistryEntry(BaseModel):
    id: Optional[str] = None
    plate_number: str
    owner_name: Optional[str] = None
    owner_phone: str
    created_at: Optional[str] = None


class ViolationAnalysisRequest(BaseModel):
    image_base64: str
    device_latitude: Optional[float] = None
    device_longitude: Optional[float] = None
    device_location_accuracy: Optional[float] = None


class ViolationAnalysisResponse(BaseModel):
    success: bool
    report: Optional[ViolationReport] = None
    exif_data: Optional[dict] = None
    mvd_email: Optional[dict] = None
    error_message: Optional[str] = None


class ParkingAssistRequest(BaseModel):
    plate_number: str


class ParkingAssistResponse(BaseModel):
    success: bool
    owner_found: bool = False
    call_status: Optional[str] = None
    message: str


# ─────────────────────────────────────────────────────────────────────────────
# Disaster & Infrastructure Sentinel Models
# ─────────────────────────────────────────────────────────────────────────────

class IncidentCategory(str, Enum):
    NATURAL_DISASTER = "natural_disaster"
    INFRASTRUCTURE = "infrastructure" 
    OBSTRUCTION = "obstruction"


class IncidentSeverity(str, Enum):
    P1 = "P1"  # Critical - Immediate
    P2 = "P2"  # High - Within 1 hour
    P3 = "P3"  # Medium - Within 4 hours
    P4 = "P4"  # Low - Within 24 hours


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    VERIFIED = "verified"
    AUTHORITY_NOTIFIED = "authority_notified"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class DisasterIncident(BaseModel):
    id: Optional[str] = None
    category: IncidentCategory
    subcategory: str
    severity: IncidentSeverity
    description: str
    detailed_description: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    landmarks: Optional[str] = None
    extracted_text: List[str] = []
    timestamp: Optional[str] = None
    image_path: Optional[str] = None
    is_valid: bool = True
    confidence: float = 0.0
    status: IncidentStatus = IncidentStatus.REPORTED
    recommended_authority: Optional[str] = None
    authorities_notified: List[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class IncidentAnalysisRequest(BaseModel):
    image_base64: str
    device_latitude: Optional[float] = None
    device_longitude: Optional[float] = None
    device_location_accuracy: Optional[float] = None
    user_description: Optional[str] = None


class IncidentAnalysisResponse(BaseModel):
    success: bool
    incident: Optional[DisasterIncident] = None
    exif_data: Optional[dict] = None
    authorities: Optional[List[dict]] = None
    call_script: Optional[dict] = None
    formal_report: Optional[dict] = None
    error_message: Optional[str] = None


class AuthorityContact(BaseModel):
    name: str
    department: str
    phone: str
    alt_phone: Optional[str] = None
    email: Optional[str] = None
    type: str  # emergency, utility, government
    level: str  # state, district
    district: Optional[str] = None

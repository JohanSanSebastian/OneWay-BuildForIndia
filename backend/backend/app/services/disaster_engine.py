"""
OneWay Disaster & Infrastructure Sentinel Engine

Provides:
- AI-powered scene classification (Natural Disaster, Infrastructure, Obstruction)
- Severity scoring (P1-P4)
- OCR for landmark text extraction
- Geospatial location processing
- Authority identification and routing
"""
import base64
import json
import logging
import asyncio
from typing import Optional, Tuple, List
from datetime import datetime
from functools import wraps
from io import BytesIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from app.config import settings
from app.services.kerala_authorities import KeralaAuthorityDirectory

logger = logging.getLogger(__name__)


# Singleton instance
_disaster_engine_instance = None


def get_disaster_engine():
    """Get or create the singleton DisasterEngine instance."""
    global _disaster_engine_instance
    if _disaster_engine_instance is None:
        _disaster_engine_instance = DisasterEngine()
    return _disaster_engine_instance


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for async retry with exponential backoff."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (ClientError, BotoCoreError, Exception) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {e}. Retrying in {current_delay}s...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed: {e}")
            raise last_exception
        return wrapper
    return decorator


class DisasterEngine:
    """
    AI-powered disaster and infrastructure issue detection engine.
    """
    
    # Issue categories as per PRD
    CATEGORIES = {
        "natural_disaster": ["landslide", "flood", "cyclone", "earthquake", "storm_damage"],
        "infrastructure": ["broken_power_line", "pothole", "road_damage", "water_main_break", "collapsed_structure"],
        "obstruction": ["fallen_tree", "vehicle_accident", "debris", "blocked_drain", "construction_hazard"]
    }
    
    # Severity levels
    SEVERITY_LEVELS = {
        "P1": {"label": "Critical", "response_time": "Immediate", "color": "#DC2626"},
        "P2": {"label": "High", "response_time": "Within 1 hour", "color": "#F97316"},
        "P3": {"label": "Medium", "response_time": "Within 4 hours", "color": "#EAB308"},
        "P4": {"label": "Low", "response_time": "Within 24 hours", "color": "#22C55E"},
    }
    
    def __init__(self):
        config = Config(
            region_name=settings.aws_region,
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )
        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            config=config,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.model_id = settings.bedrock_model_id
        self.authority_directory = KeralaAuthorityDirectory()
    
    def _detect_media_type(self, image_data: bytes) -> str:
        """Detect image media type from magic bytes."""
        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            return 'image/png'
        elif image_data[:2] == b'\xff\xd8':
            return 'image/jpeg'
        elif image_data[:6] in (b'GIF87a', b'GIF89a'):
            return 'image/gif'
        elif image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            return 'image/webp'
        return 'image/png'

    def extract_exif_data(self, image_bytes: bytes) -> dict:
        """Extract EXIF metadata from image including GPS coordinates and timestamp."""
        result = {
            "timestamp": None,
            "latitude": None,
            "longitude": None,
            "location_string": None,
            "device": None
        }
        
        try:
            image = Image.open(BytesIO(image_bytes))
            exif_data = image._getexif()
            
            if not exif_data:
                return result
            
            # Extract basic EXIF data
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                
                if tag == "DateTimeOriginal":
                    result["timestamp"] = str(value)
                elif tag == "Make":
                    result["device"] = str(value)
                elif tag == "Model" and result.get("device"):
                    result["device"] += f" {value}"
            
            # Extract GPS data
            gps_info = exif_data.get(34853)  # GPSInfo tag
            if gps_info:
                gps_data = {}
                for key, val in gps_info.items():
                    decoded = GPSTAGS.get(key, key)
                    gps_data[decoded] = val
                
                lat = self._convert_to_degrees(gps_data.get("GPSLatitude"))
                lon = self._convert_to_degrees(gps_data.get("GPSLongitude"))
                
                if lat and lon:
                    if gps_data.get("GPSLatitudeRef") == "S":
                        lat = -lat
                    if gps_data.get("GPSLongitudeRef") == "W":
                        lon = -lon
                    
                    result["latitude"] = lat
                    result["longitude"] = lon
                    result["location_string"] = f"{lat:.6f}, {lon:.6f}"
        
        except Exception as e:
            logger.warning(f"EXIF extraction failed: {e}")
        
        return result
    
    def _convert_to_degrees(self, value) -> Optional[float]:
        """Convert GPS coordinates to degrees."""
        if not value:
            return None
        try:
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        except (TypeError, IndexError, ZeroDivisionError):
            return None

    @async_retry(max_attempts=3, delay=1.0)
    async def analyze_incident(self, image_bytes: bytes) -> dict:
        """
        Analyze an image to detect disasters or infrastructure issues.
        Returns category, subcategory, severity, description, and extracted text.
        """
        media_type = self._detect_media_type(image_bytes)
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        analysis_prompt = """Analyze this image for disaster or infrastructure issues in Kerala, India.

Classify the issue into one of these categories:
1. NATURAL_DISASTER: landslide, flood, cyclone, earthquake, storm_damage
2. INFRASTRUCTURE: broken_power_line, pothole, road_damage, water_main_break, collapsed_structure
3. OBSTRUCTION: fallen_tree, vehicle_accident, debris, blocked_drain, construction_hazard

Assign a severity level:
- P1 (Critical): Life-threatening, requires immediate response
- P2 (High): Significant danger, response within 1 hour
- P3 (Medium): Moderate impact, response within 4 hours
- P4 (Low): Minor issue, can wait up to 24 hours

Also extract any visible text from signboards or landmarks that could help identify the location.

Respond ONLY with valid JSON in this exact format:
{
    "category": "natural_disaster|infrastructure|obstruction",
    "subcategory": "specific issue type from the list above",
    "severity": "P1|P2|P3|P4",
    "description": "Brief description of what you see",
    "detailed_description": "Detailed description for official report",
    "extracted_text": ["any", "visible", "text", "from", "signboards"],
    "landmarks": "Description of identifiable landmarks",
    "is_valid_incident": true/false,
    "confidence": 0.0-1.0,
    "recommended_authority": "KSEB|PWD|Fire_Rescue|Police|LSGD|KWA"
}"""

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": media_type.split('/')[1],
                            "source": {"bytes": image_bytes}
                        }
                    },
                    {"text": analysis_prompt}
                ]
            }
        ]
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.bedrock.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"maxTokens": 1024, "temperature": 0.1}
            )
        )
        
        response_text = response['output']['message']['content'][0]['text']
        
        # Parse JSON from response
        try:
            # Try to extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                analysis = json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {response_text}")
            analysis = {
                "category": "obstruction",
                "subcategory": "other",
                "severity": "P3",
                "description": "Unable to analyze image",
                "detailed_description": response_text[:500],
                "extracted_text": [],
                "landmarks": "",
                "is_valid_incident": False,
                "confidence": 0.0,
                "recommended_authority": "LSGD"
            }
        
        return analysis

    def identify_authorities(
        self, 
        category: str, 
        subcategory: str, 
        latitude: Optional[float], 
        longitude: Optional[float]
    ) -> List[dict]:
        """
        Identify the relevant authorities based on issue type and location.
        """
        return self.authority_directory.get_authorities(
            category=category,
            subcategory=subcategory,
            latitude=latitude,
            longitude=longitude
        )

    def generate_call_script(self, analysis: dict, exif_data: dict, report_id: str) -> dict:
        """
        Generate a call script for the user to read when contacting authorities.
        """
        severity_info = self.SEVERITY_LEVELS.get(analysis.get("severity", "P3"), self.SEVERITY_LEVELS["P3"])
        
        location_desc = exif_data.get("location_string") or "Location pending GPS verification"
        landmarks = analysis.get("landmarks", "")
        
        script = f"""Hello, I would like to report a {severity_info['label'].lower()} priority incident.

INCIDENT TYPE: {analysis.get('subcategory', 'Unknown').replace('_', ' ').title()}
CATEGORY: {analysis.get('category', 'Unknown').replace('_', ' ').title()}
SEVERITY: {analysis.get('severity', 'P3')} - {severity_info['label']}

LOCATION: {location_desc}
{f'LANDMARKS: {landmarks}' if landmarks else ''}

DESCRIPTION: {analysis.get('description', 'Incident reported via OneWay Sentinel')}

This report has been logged with ID: {report_id}

I have photographic evidence attached to this report. Please dispatch assistance as per the severity level."""

        return {
            "script": script,
            "severity": analysis.get("severity", "P3"),
            "severity_label": severity_info["label"],
            "response_time": severity_info["response_time"],
            "report_id": report_id
        }

    def generate_formal_report(
        self, 
        analysis: dict, 
        exif_data: dict, 
        report_id: str,
        authorities: List[dict]
    ) -> dict:
        """
        Generate a formal report for submission to authorities.
        """
        now = datetime.now()
        timestamp = exif_data.get("timestamp") or now.strftime("%Y-%m-%d %H:%M:%S")
        
        authority_list = "\n".join([
            f"- {a['name']} ({a['department']}): {a.get('phone', 'N/A')}"
            for a in authorities
        ])
        
        body = f"""DISASTER & INFRASTRUCTURE INCIDENT REPORT
=========================================

REPORT ID: {report_id}
GENERATED: {now.strftime('%Y-%m-%d %H:%M:%S')}

INCIDENT CLASSIFICATION
-----------------------
Category: {analysis.get('category', 'Unknown').replace('_', ' ').title()}
Type: {analysis.get('subcategory', 'Unknown').replace('_', ' ').title()}
Severity: {analysis.get('severity', 'P3')} - {self.SEVERITY_LEVELS.get(analysis.get('severity', 'P3'), {}).get('label', 'Medium')}
Confidence: {analysis.get('confidence', 0) * 100:.1f}%

LOCATION DETAILS
----------------
Coordinates: {exif_data.get('location_string') or 'Not available'}
Latitude: {exif_data.get('latitude') or 'N/A'}
Longitude: {exif_data.get('longitude') or 'N/A'}
Landmarks: {analysis.get('landmarks') or 'None identified'}
Extracted Text: {', '.join(analysis.get('extracted_text', [])) or 'None'}

INCIDENT DESCRIPTION
--------------------
{analysis.get('detailed_description') or analysis.get('description', 'No description available')}

RECOMMENDED AUTHORITIES
-----------------------
{authority_list}

---
This report was auto-generated by OneWay Disaster Sentinel.
Evidence photograph attached.
"""

        return {
            "report_id": report_id,
            "subject": f"[{analysis.get('severity', 'P3')}] {analysis.get('subcategory', 'Incident').replace('_', ' ').title()} - {report_id[:8]}",
            "body": body,
            "timestamp": timestamp
        }


# Initialize singleton on module load
def _init():
    global _disaster_engine_instance
    try:
        _disaster_engine_instance = DisasterEngine()
        logger.info("DisasterEngine initialized successfully")
    except Exception as e:
        logger.warning(f"DisasterEngine initialization deferred: {e}")

_init()

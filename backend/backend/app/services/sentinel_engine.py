"""
OneWay Sentinel Engine - Motor Violation Assistant

Provides:
- ANPR (Automatic Number Plate Recognition) via AWS Bedrock
- AI-powered violation analysis and authenticity verification
- EXIF metadata extraction for GPS and timestamps
- Automated MVD email generation
"""

import base64
import json
import logging
import asyncio
from typing import Optional, Tuple
from datetime import datetime
from functools import wraps
from io import BytesIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

from app.config import settings

# Twilio WhatsApp
try:
    from twilio.rest import Client as TwilioClient
except ImportError:
    TwilioClient = None

logger = logging.getLogger(__name__)


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


class SentinelEngine:
    """
    AI-powered violation detection and reporting engine.
    """
    
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
        self.model_id = settings.bedrock_model_id  # Use Nova Pro from settings
    
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
        return 'image/png'  # Default

    def extract_exif_data(self, image_bytes: bytes) -> dict:
        """
        Extract EXIF metadata from image including GPS coordinates and timestamp.
        """
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
            
            # Extract basic EXIF tags
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                
                if tag == "DateTimeOriginal":
                    result["timestamp"] = value
                elif tag == "Make":
                    result["device"] = value
                elif tag == "GPSInfo":
                    gps_info = {}
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_info[gps_tag] = gps_value
                    
                    # Parse GPS coordinates
                    if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                        lat = self._convert_to_degrees(gps_info["GPSLatitude"])
                        lon = self._convert_to_degrees(gps_info["GPSLongitude"])
                        
                        if gps_info.get("GPSLatitudeRef") == "S":
                            lat = -lat
                        if gps_info.get("GPSLongitudeRef") == "W":
                            lon = -lon
                        
                        result["latitude"] = lat
                        result["longitude"] = lon
                        result["location_string"] = f"{lat:.6f}, {lon:.6f}"
        except Exception as e:
            logger.warning(f"EXIF extraction failed: {e}")
        
        return result
    
    def _convert_to_degrees(self, value) -> float:
        """Convert GPS coordinates to decimal degrees."""
        d, m, s = value
        return float(d) + float(m) / 60 + float(s) / 3600
    
    @async_retry(max_attempts=3, delay=1.0)
    async def analyze_violation(self, image_bytes: bytes) -> dict:
        """
        Analyze image for traffic violations using Bedrock Vision.
        
        Returns:
            {
                "plate": str,           # License plate number
                "violation": str,       # Description of violation
                "violation_type": str,  # Category (no_helmet, wrong_side, obstruction, etc.)
                "is_authentic": bool,   # Whether image appears genuine
                "confidence": float,    # Confidence score 0-1
                "description": str      # Formal description for MVD
            }
        """
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = """Analyze this traffic violation image carefully.

1. **License Plate Recognition (ANPR)**: Extract the vehicle's license plate number. Use standard Indian format (e.g., KL 01 AB 1234).

2. **Violation Identification**: Identify any traffic violations visible:
   - No helmet
   - Triple/quadruple riding
   - Wrong side driving
   - No parking zone violation
   - Signal jumping
   - Obstruction/blocking
   - Other violations

3. **Authenticity Check**: Analyze if this image appears to be:
   - Real photograph (consistent lighting, natural noise patterns)
   - AI-generated or digitally manipulated (unusual artifacts, inconsistent shadows)

4. **Formal Description**: Write a formal complaint description suitable for MVD submission.

Return ONLY valid JSON (no markdown):
{
    "plate": "extracted plate number or null if not visible",
    "violation": "brief violation description",
    "violation_type": "no_helmet|triple_riding|wrong_side|no_parking|signal_jump|obstruction|other",
    "is_authentic": true/false,
    "confidence": 0.0-1.0,
    "description": "Formal description for MVD report"
}"""

        # Detect image format
        media_type = self._detect_media_type(image_bytes)
        img_format = media_type.split('/')[-1]

        # Nova Pro message format
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": img_format,
                            "source": {
                                "bytes": image_b64
                            }
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }
        ]

        # Nova Pro request format
        body = json.dumps({
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": 1024,
                "temperature": 0.1
            }
        })
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.bedrock.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType="application/json",
                accept="application/json"
            )
        )
        
        response_body = json.loads(response['body'].read())
        
        # Nova Pro response format: output.message.content[0].text
        output = response_body.get('output', {})
        message = output.get('message', {})
        content_list = message.get('content', [])
        
        if not content_list:
            raise RuntimeError("Empty response from Bedrock")
        
        content = content_list[0].get('text', '')
        
        # Parse JSON from response
        try:
            # Clean up response if wrapped in markdown
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content.strip())
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response: {content}")
            result = {
                "plate": None,
                "violation": "Unable to analyze",
                "violation_type": "other",
                "is_authentic": False,
                "confidence": 0.0,
                "description": "Analysis failed"
            }
        
        return result
    
    def generate_mvd_email(self, analysis: dict, exif_data: dict, image_bytes: bytes) -> dict:
        """
        Generate formatted email content for MVD submission.
        """
        timestamp = exif_data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        location = exif_data.get("location_string") or "Location not available"
        
        subject = f"Traffic Violation Report - {analysis.get('plate', 'Unknown Vehicle')}"
        
        body = f"""To,
The Motor Vehicles Department,
Government of Kerala

Subject: {subject}

Respected Sir/Madam,

I wish to report a traffic violation observed with the following details:

**Vehicle Number:** {analysis.get('plate', 'Not clearly visible')}
**Violation Type:** {analysis.get('violation', 'Traffic violation')}
**Date & Time:** {timestamp}
**Location:** {location}

**Description:**
{analysis.get('description', 'Traffic violation observed.')}

**Evidence:** Attached photograph

I request you to take appropriate action against the violator as per the Motor Vehicles Act.

Thank you.

Yours faithfully,
OneWay Citizen Reporter
(Auto-generated report via OneWay Sentinel)
"""
        
        return {
            "to": settings.sentinel_recipient_email,
            "subject": subject,
            "body": body,
            "image_attached": True
        }
    
    async def send_violation_email(
        self, 
        analysis: dict, 
        exif_data: dict, 
        image_bytes: bytes,
        report_id: str
    ) -> dict:
        """
        Send violation report email with image attachment via AWS SES.
        """
        import email
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.image import MIMEImage
        
        email_content = self.generate_mvd_email(analysis, exif_data, image_bytes)
        
        # Create multipart MIME message
        msg = MIMEMultipart('mixed')
        msg['Subject'] = email_content['subject']
        msg['From'] = settings.sentinel_sender_email
        msg['To'] = settings.sentinel_recipient_email
        
        # Add plain text body
        body_text = email_content['body'].replace('**', '')  # Clean markdown
        msg_body = MIMEMultipart('alternative')
        
        # Plain text version
        text_part = MIMEText(body_text, 'plain', 'utf-8')
        msg_body.attach(text_part)
        
        # HTML version
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #d97706;">Traffic Violation Report</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Vehicle Number:</strong> {analysis.get('plate', 'Not clearly visible')}</p>
                <p><strong>Violation Type:</strong> {analysis.get('violation', 'Traffic violation')}</p>
                <p><strong>Date & Time:</strong> {exif_data.get('timestamp') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Location:</strong> {exif_data.get('location_string') or 'Location not available'}</p>
            </div>
            <h3>Description:</h3>
            <p style="background: #fff3cd; padding: 15px; border-radius: 8px;">
                {analysis.get('description', 'Traffic violation observed.')}
            </p>
            <p><strong>Evidence:</strong> See attached photograph</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                This is an auto-generated report via OneWay Sentinel.<br>
                Report ID: {report_id}
            </p>
        </body>
        </html>
        """
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg_body.attach(html_part)
        msg.attach(msg_body)
        
        # Attach the violation image
        img_attachment = MIMEImage(image_bytes)
        img_attachment.add_header(
            'Content-Disposition', 
            'attachment', 
            filename=f'violation_evidence_{report_id}.jpg'
        )
        img_attachment.add_header('Content-ID', '<violation_image>')
        msg.attach(img_attachment)
        
        try:
            import smtplib
            import ssl
            
            # Validate SMTP credentials are configured
            if not settings.ses_smtp_username or not settings.ses_smtp_password:
                raise ValueError("SES SMTP credentials not configured. Set SES_SMTP_USERNAME and SES_SMTP_PASSWORD in .env")
            
            # Send via SES SMTP
            context = ssl.create_default_context()
            
            def send_smtp():
                with smtplib.SMTP(settings.ses_smtp_host, settings.ses_smtp_port) as server:
                    server.starttls(context=context)
                    server.login(settings.ses_smtp_username, settings.ses_smtp_password)
                    server.sendmail(
                        settings.sentinel_sender_email,
                        [settings.sentinel_recipient_email],
                        msg.as_string()
                    )
                return True
            
            await asyncio.get_event_loop().run_in_executor(None, send_smtp)
            
            logger.info(f"Email sent successfully via SES SMTP to {settings.sentinel_recipient_email}")
            return {
                "success": True,
                "message_id": f"smtp_{report_id}",
                "recipient": settings.sentinel_recipient_email
            }
            
        except Exception as e:
            logger.error(f"Failed to send email via SES SMTP: {e}")
            return {
                "success": False,
                "error": str(e),
                "note": "SES SMTP failed. Check SMTP credentials and verify sender email in SES console."
            }
    
    async def _send_email_smtp(self, msg, email_content: dict) -> dict:
        """
        Fallback SMTP email sending (for local testing).
        """
        import smtplib
        
        try:
            # For demo purposes, just log that email would be sent
            logger.info(f"SMTP Fallback - Would send to: {email_content['to']}")
            logger.info(f"Subject: {email_content['subject']}")
            
            return {
                "success": True,
                "message_id": f"local_{datetime.now().timestamp()}",
                "recipient": settings.sentinel_recipient_email,
                "note": "Email logged (SES not configured)"
            }
        except Exception as e:
            logger.error(f"SMTP fallback also failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def trigger_parking_call(self, plate_number: str, owner_phone: str) -> dict:
        """
        Always send WhatsApp to 8943377737 for parking assist, regardless of input.
        """
        logger.info(f"Parking assist: WhatsApp message for plate {plate_number} to hardcoded 8943377737")

        sid = settings.twilio_account_sid
        token = settings.twilio_auth_token
        from_whatsapp = settings.twilio_whatsapp_from
        to_whatsapp = "whatsapp:+918943377737"
        msg_body = f"Your Vehicle ({plate_number}) was found obstructing a fellow driver. Please move the car immediately."

        if TwilioClient and sid and token and from_whatsapp:
            try:
                client = TwilioClient(sid, token)
                message = client.messages.create(
                    from_=from_whatsapp,
                    body=msg_body,
                    to=to_whatsapp
                )
                logger.info(f"Twilio WhatsApp sent: SID {message.sid}")
                return {
                    "status": "WhatsApp Sent",
                    "plate": plate_number,
                    "phone": "8943377737",
                    "timestamp": datetime.now().isoformat(),
                    "message": f"WhatsApp message sent. SID: {message.sid}"
                }
            except Exception as e:
                logger.error(f"Twilio WhatsApp error: {e}")
                return {
                    "status": "WhatsApp Error",
                    "plate": plate_number,
                    "phone": "8943377737",
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Failed to send WhatsApp: {e}"
                }
        else:
            logger.warning("Twilio not configured or unavailable. Skipping WhatsApp send.")
            return {
                "status": "WhatsApp Not Configured",
                "plate": plate_number,
                "phone": "8943377737",
                "timestamp": datetime.now().isoformat(),
                "message": "Twilio not configured or unavailable."
            }


# Singleton instance
_engine_instance: Optional[SentinelEngine] = None


def get_sentinel_engine() -> SentinelEngine:
    """Get or create singleton SentinelEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SentinelEngine()
    return _engine_instance

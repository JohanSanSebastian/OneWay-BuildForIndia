"""
Production-ready CAPTCHA solver using AWS Bedrock with Claude 3.5 Sonnet vision.

This module provides enterprise-grade CAPTCHA solving capabilities with:
- Automatic retry with exponential backoff
- Proper error handling and structured logging
- Connection pooling via boto3
- Support for multiple image formats
- Confidence scoring via multi-attempt solving
"""
import base64
import logging
import asyncio
from typing import Optional, Union, Tuple
from functools import wraps
from collections import Counter

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
import json

from app.config import settings

# Configure logging
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
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed: {e}")
            
            raise last_exception
        return wrapper
    return decorator


class CaptchaSolver:
    """
    Production-ready CAPTCHA solver using AWS Bedrock with Claude 3.5 Sonnet.
    
    This class handles CAPTCHA image transcription using Claude's vision
    capabilities through AWS Bedrock Runtime API.
    
    Example:
        solver = CaptchaSolver()
        captcha_text = await solver.solve(image_base64)
    """
    
    # Supported models for vision tasks
    NOVA_PRO_MODEL = "amazon.nova-pro-v1:0"
    CLAUDE_SONNET_MODEL = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def __init__(self, model_id: Optional[str] = None):
        """
        Initialize the CAPTCHA solver.
        
        Args:
            model_id: Optional Bedrock model ID. Defaults to Nova Pro 1.0.
        """
        self.model_id = model_id or self.NOVA_PRO_MODEL
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Bedrock Runtime client with production settings."""
        try:
            # Production boto3 config with retries and connection pooling
            boto_config = Config(
                region_name=settings.aws_region,
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                connect_timeout=10,
                read_timeout=60,
                max_pool_connections=25
            )
            
            client_kwargs = {
                'service_name': 'bedrock-runtime',
                'config': boto_config
            }
            
            # Use explicit credentials if provided, otherwise use default chain
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                client_kwargs['aws_access_key_id'] = settings.aws_access_key_id
                client_kwargs['aws_secret_access_key'] = settings.aws_secret_access_key
                client_kwargs['region_name'] = settings.aws_region
            
            self._client = boto3.client(**client_kwargs)
            logger.info(f"Bedrock Runtime client initialized for region: {settings.aws_region}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise RuntimeError(f"Bedrock client initialization failed: {e}")
    
    @property
    def client(self):
        """Get the Bedrock client, initializing if necessary."""
        if self._client is None:
            self._initialize_client()
        return self._client
    
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
    
    def _prepare_image_content(
        self, 
        image_data: Union[str, bytes], 
        media_type: Optional[str] = None
    ) -> dict:
        """
        Prepare image content for the Bedrock API (Nova Pro format).
        
        Args:
            image_data: Base64 string or raw bytes
            media_type: Optional media type override
            
        Returns:
            Image content block for Nova Pro API
        """
        if isinstance(image_data, bytes):
            detected_type = self._detect_media_type(image_data)
            base64_data = base64.b64encode(image_data).decode('utf-8')
        else:
            base64_data = image_data
            try:
                raw_bytes = base64.b64decode(image_data)
                detected_type = self._detect_media_type(raw_bytes)
            except Exception:
                detected_type = 'image/png'
        
        # Extract format from media type (e.g., "image/png" -> "png")
        img_format = (media_type or detected_type).split('/')[-1]
        
        # Nova Pro format for images
        return {
            "image": {
                "format": img_format,
                "source": {
                    "bytes": base64_data
                }
            }
        }
    
    @async_retry(max_attempts=3, delay=0.5, backoff=2.0)
    async def solve(
        self, 
        captcha_image: Union[str, bytes],
        media_type: Optional[str] = None
    ) -> str:
        """
        Solve a CAPTCHA image using Nova Pro vision.
        
        Args:
            captcha_image: Base64 encoded string or raw bytes of the CAPTCHA image
            media_type: Optional MIME type of the image
            
        Returns:
            The transcribed CAPTCHA text
            
        Raises:
            RuntimeError: If CAPTCHA solving fails after all retries
        """
        logger.info("Starting CAPTCHA solving with Nova Pro Vision...")
        
        image_content = self._prepare_image_content(captcha_image, media_type)
        
        # Nova Pro message format
        messages = [
            {
                "role": "user",
                "content": [
                    image_content,
                    {
                        "text": (
                            "You are a CAPTCHA text extractor. Look at this CAPTCHA image "
                            "and extract the text/characters shown. Return ONLY the exact "
                            "characters you see, with no explanation, formatting, quotes, "
                            "or additional text. If you cannot read it clearly, make your "
                            "best attempt. The CAPTCHA typically contains alphanumeric characters."
                        )
                    }
                ]
            }
        ]
        
        # Nova Pro request format
        request_body = {
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": 50,
                "temperature": 0  # Deterministic output
            }
        }
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=json.dumps(request_body)
                )
            )
            
            response_body = json.loads(response['body'].read())
            
            # Nova Pro response format: output.message.content[0].text
            output = response_body.get('output', {})
            message = output.get('message', {})
            content = message.get('content', [])
            
            if not content:
                raise RuntimeError("Empty response from Bedrock")
            
            captcha_text = content[0].get('text', '').strip()
            captcha_text = self._clean_captcha_response(captcha_text)
            
            logger.info(f"CAPTCHA solved successfully: {len(captcha_text)} characters")
            return captcha_text
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"Bedrock API error [{error_code}]: {error_message}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bedrock response: {e}")
            raise RuntimeError(f"Invalid response format: {e}")
    
    def _clean_captcha_response(self, text: str) -> str:
        """Clean and normalize CAPTCHA response text."""
        text = text.strip()
        text = text.replace('"', '').replace("'", '')
        text = text.replace('`', '').replace('*', '')
        
        prefixes_to_remove = [
            'the text is',
            'the captcha is',
            'the characters are',
            'i can see',
            'the image shows',
        ]
        
        text_lower = text.lower()
        for prefix in prefixes_to_remove:
            if text_lower.startswith(prefix):
                text = text[len(prefix):].strip()
                text = text.lstrip(':').strip()
                break
        
        return text.upper()
    
    async def solve_with_confidence(
        self, 
        captcha_image: Union[str, bytes],
        attempts: int = 3
    ) -> Tuple[str, float]:
        """
        Solve CAPTCHA with confidence scoring via multiple attempts.
        
        Args:
            captcha_image: The CAPTCHA image data
            attempts: Number of solving attempts to make
            
        Returns:
            Tuple of (captcha_text, confidence_score)
        """
        results = []
        
        for i in range(attempts):
            try:
                result = await self.solve(captcha_image)
                results.append(result)
            except Exception as e:
                logger.warning(f"Attempt {i+1} failed: {e}")
                continue
        
        if not results:
            raise RuntimeError("All CAPTCHA solving attempts failed")
        
        counter = Counter(results)
        most_common, count = counter.most_common(1)[0]
        confidence = count / len(results)
        
        logger.info(f"CAPTCHA solved with {confidence:.0%} confidence: {most_common}")
        return most_common, confidence

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """
    Production configuration for OneWay API.
    
    All settings can be overridden via environment variables.
    """
    
    # AWS Configuration
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    
    # AWS Bedrock Configuration
    bedrock_model_id: str = "amazon.nova-pro-v1:0"
    bedrock_agent_id: Optional[str] = None
    bedrock_agent_alias_id: Optional[str] = None
    bedrock_max_iterations: int = 15
    bedrock_timeout_seconds: int = 300
    
    # Utility Portal URLs
    kseb_url: str = "https://johansansebastian.github.io/oneway_sites/kseb/"
    kwa_url: str = "https://johansansebastian.github.io/oneway_sites/kwa/"
    echallan_url: str = "https://johansansebastian.github.io/oneway_sites/echallan/"
    ksmart_url: str = "https://johansansebastian.github.io/oneway_sites/ksmart/"
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # Logging
    log_level: str = "INFO"
    
    # Session Management
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 100
    
    # Sentinel Email Configuration
    sentinel_recipient_email: str = "aayyuusshh0909@gmail.com"
    sentinel_sender_email: str = "johansanseb@gmail.com"
    
    # SES SMTP Configuration
    ses_smtp_host: str = "email-smtp.us-east-1.amazonaws.com"
    ses_smtp_port: int = 587
    ses_smtp_username: Optional[str] = None
    ses_smtp_password: Optional[str] = None
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"

    @property
    def has_explicit_aws_keys(self) -> bool:
        return bool(self.aws_access_key_id and self.aws_secret_access_key)


settings = Settings()

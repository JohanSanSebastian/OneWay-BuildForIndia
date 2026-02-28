import logging
from contextlib import asynccontextmanager

import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, utilities, profiles, payments, sentinel, disaster
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("OneWay API starting up...")
    logger.info(f"AWS Region: {settings.aws_region}")
    logger.info(f"Bedrock Model: {settings.bedrock_model_id}")
    logger.info(f"Debug Mode: {settings.debug}")
    
    # Validate AWS credentials availability (explicit keys OR default credential chain)
    session_kwargs = {"region_name": settings.aws_region}
    if settings.has_explicit_aws_keys:
        session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
    
    session = boto3.Session(**session_kwargs)
    credentials = session.get_credentials()
    if credentials is None:
        raise RuntimeError(
            "AWS credentials not found. Configure backend/.env with AWS_ACCESS_KEY_ID and "
            "AWS_SECRET_ACCESS_KEY, or provide credentials via AWS default chain."
        )

    if settings.has_explicit_aws_keys:
        logger.info("AWS credentials loaded from backend/.env")
    else:
        logger.info("AWS credentials resolved from default credential chain")
    
    yield
    
    # Shutdown
    logger.info("OneWay API shutting down...")


app = FastAPI(
    title="OneWay API",
    description="Unified Utility-as-a-Service Dashboard API powered by AWS Bedrock",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(utilities.router, prefix="/api/utilities", tags=["Utilities"])
app.include_router(profiles.router, prefix="/api/profiles", tags=["Profiles"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(sentinel.router, prefix="/api", tags=["Sentinel"])
app.include_router(disaster.router, prefix="/api", tags=["Disaster Sentinel"])


@app.get("/")
async def root():
    return {"message": "Welcome to OneWay API", "status": "operational"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

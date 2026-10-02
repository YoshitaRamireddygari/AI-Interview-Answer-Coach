from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import (
    validation_exception_handler,
    sqlalchemy_exception_handler,
    gemini_exception_handler,
    timeout_exception_handler,
    global_exception_handler
)
from app.services.gemini_service import GeminiServiceError
from app.db.session import init_db
from app.api.v1.router import api_router

from app.core.rate_limiter import RateLimitMiddleware

# Requirement 3: Create database tables automatically during development
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle context manager.
    Initializes SQLite database tables on startup.
    """
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI Interview Answer Coach",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Rate Limiting & Oversized Payload Protection Middleware
app.add_middleware(RateLimitMiddleware)

# Register custom exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(GeminiServiceError, gemini_exception_handler)
app.add_exception_handler(TimeoutError, timeout_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Mount router at both /api and /api/v1 for complete endpoint flexibility
app.include_router(api_router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """
    Root endpoint welcome route.
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API (Stage 6 Pipeline Complete)",
        "docs": "/docs",
        "health_check": "/api/health",
        "analyze_endpoint": "/api/analyze",
        "analyses_endpoint": "/api/analyses"
    }

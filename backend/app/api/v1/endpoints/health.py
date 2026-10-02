from fastapi import APIRouter
from app.schemas.health import HealthCheckResponse
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse, summary="GET Health Check")
@router.post("/health", response_model=HealthCheckResponse, summary="POST Health Check")
def health_check():
    """
    Returns application operational status.
    """
    return HealthCheckResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT
    )

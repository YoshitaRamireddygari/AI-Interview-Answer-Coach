from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """
    Schema for health check endpoint response.
    """
    status: str = Field(..., json_schema_extra={"example": "healthy"}, description="Operational status of the server")
    service: str = Field(..., json_schema_extra={"example": "AI Interview Answer Coach"}, description="Service name")
    environment: str = Field(..., json_schema_extra={"example": "development"}, description="Current environment mode")

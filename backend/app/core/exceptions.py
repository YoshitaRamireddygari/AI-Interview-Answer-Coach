import re
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.services.gemini_service import (
    GeminiServiceError,
    GeminiAPIKeyError,
    GeminiParseError,
    GeminiAPIError
)

logger = logging.getLogger(__name__)


def sanitize_error_message(msg: str) -> str:
    """
    Sanitizes exception messages to ensure API keys, internal paths,
    or raw stack traces are never exposed to clients.
    """
    if not msg:
        return ""
    # Mask potential API keys (AIzaSy..., etc.)
    sanitized = re.sub(r'AIzaSy[A-Za-z0-9_-]{33}', '[REDACTED_API_KEY]', msg)
    # Mask key=... patterns
    sanitized = re.sub(r'(api_key|key)=["\']?[A-Za-z0-9_-]+["\']?', r'\1=[REDACTED_KEY]', sanitized, flags=re.IGNORECASE)
    # Remove file paths if present
    sanitized = re.sub(r'/[a-zA-Z0-9_\-./]+/(site-packages|app|backend)/', '.../', sanitized)
    return sanitized


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom exception handler for Pydantic validation errors (HTTP 422).
    Returns clean, structured error response.
    """
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": err["msg"]
        })
        
    return JSONResponse(
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        content={
            "error": "Validation Error",
            "message": "Invalid input provided in request payload.",
            "details": errors
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Exception handler for database layer errors (HTTP 500).
    Formats database failures cleanly without exposing sensitive internals.
    """
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "message": "A database operation failed while processing your request.",
            "detail": "Database operation failed."
        }
    )


async def gemini_exception_handler(request: Request, exc: Exception):
    """
    Exception handler for Gemini AI Service errors (HTTP 502/503/504).
    """
    logger.error(f"Gemini Service error: {str(exc)}")

    if isinstance(exc, GeminiAPIKeyError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "AI Service Configuration Error",
                "message": "Gemini API key is not configured on the server.",
                "detail": "Please configure GEMINI_API_KEY environment variable."
            }
        )

    if isinstance(exc, GeminiParseError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error": "Malformed AI Response",
                "message": "Received malformed evaluation output from AI service.",
                "detail": sanitize_error_message(str(exc))
            }
        )

    if isinstance(exc, TimeoutError) or getattr(exc, "is_timeout", False):
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": "Gateway Timeout",
                "message": "Request timed out while communicating with external AI service.",
                "detail": "AI evaluation request timed out."
            }
        )

    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": "AI Service Error",
            "message": "Failed to communicate with AI evaluation service.",
            "detail": sanitize_error_message(str(exc))
        }
    )


async def timeout_exception_handler(request: Request, exc: TimeoutError):
    """
    Exception handler for timeout errors (HTTP 504).
    """
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "error": "Gateway Timeout",
            "message": "Request timed out while processing your request.",
            "detail": "Timeout occurred during processing."
        }
    )


async def global_exception_handler(request: Request, exc: Exception):
    """
    Global catch-all exception handler to ensure unhandled errors return structured JSON.
    Guarantees no sensitive tracebacks or API keys are exposed to clients.
    """
    logger.error(f"Unhandled server error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing your request.",
            "detail": sanitize_error_message(str(exc))
        }
    )

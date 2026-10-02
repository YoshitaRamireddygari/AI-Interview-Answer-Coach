import time
import logging
from collections import defaultdict
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Lightweight in-memory Rate Limiting and Oversized Request Protection Middleware.
    Suitable for portfolio deployment to prevent API abuse and Denial of Service (DoS).
    """

    def __init__(
        self, 
        app, 
        max_requests_per_minute: int = 40,
        max_payload_bytes: int = 1_048_576  # 1 MB max request size
    ):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.max_payload_bytes = max_payload_bytes
        self.request_records = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Payload Size Check
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_payload_bytes:
            logger.warning(f"Rejected oversized request from client: {content_length} bytes")
            return JSONResponse(
                status_code=getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413),
                content={
                    "error": "Payload Too Large",
                    "message": f"Request body exceeds maximum allowed limit of {self.max_payload_bytes // 1024} KB.",
                    "detail": "Please reduce the size of your submitted input."
                }
            )

        # 2. IP Rate Limiting for mutating API routes
        if request.method in ["POST", "PUT", "DELETE"] and request.url.path.startswith("/api"):
            client_ip = request.client.host if request.client else "127.0.0.1"
            now = time.time()
            window_start = now - 60.0

            # Filter out requests older than 1 minute for target IP
            active_timestamps = [
                t for t in self.request_records.get(client_ip, []) if t > window_start
            ]

            if active_timestamps:
                self.request_records[client_ip] = active_timestamps
            elif client_ip in self.request_records:
                del self.request_records[client_ip]

            if len(self.request_records.get(client_ip, [])) >= self.max_requests:
                logger.warning(f"Rate limit exceeded for IP {client_ip} on path {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    headers={"Retry-After": "60"},
                    content={
                        "error": "Rate Limit Exceeded",
                        "message": f"Too many requests. Maximum allowed is {self.max_requests} requests per minute.",
                        "detail": "Please wait a minute before submitting another analysis request."
                    }
                )

            # Record current request timestamp
            self.request_records[client_ip].append(now)

        return await call_next(request)

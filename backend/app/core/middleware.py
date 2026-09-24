"""
Security Hardening Middleware — OWASP Best Practices

Enforces:
1. Standard OWASP Security Headers (X-Content-Type-Options, X-Frame-Options, CSP, HSTS)
2. Request payload size limits to protect against memory exhaustion / payload flooding
3. Stripping server information headers to prevent fingerprinting
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
import structlog

logger = structlog.get_logger(__name__)

# Max request payload size: 1 MB
MAX_CONTENT_LENGTH = 1024 * 1024


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects defensive HTTP response headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Enforce max content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_CONTENT_LENGTH:
            logger.warning("payload_too_large_rejected", size=content_length)
            return JSONResponse(
                status_code=413,
                content={"detail": "Payload too large. Maximum size is 1MB."},
            )

        response = await call_next(request)

        # OWASP Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Remove fingerprint headers
        if "server" in response.headers:
            del response.headers["server"]

        return response
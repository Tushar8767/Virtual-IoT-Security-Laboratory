"""
Phase 11 Tests — Security Hardening & Edge Protection

Tests:
1. X-Content-Type-Options header present
2. X-Frame-Options: DENY header present
3. Server header is stripped (no fingerprinting)
4. Payload size limit rejects oversized bodies (> 1MB) with 413
"""

import pytest
from httpx import AsyncClient, ASGITransport


class TestSecurityHardening:
    """Test OWASP security headers and payload boundaries."""

    @pytest.mark.asyncio
    async def test_security_headers_injected(self):
        from app.main import app

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            res = await client.get("/api/health")
            assert res.status_code == 200

            # Verify OWASP headers
            headers = res.headers
            assert headers.get("X-Content-Type-Options") == "nosniff"
            assert headers.get("X-Frame-Options") == "DENY"
            assert "strict-origin" in headers.get("Referrer-Policy", "")
            assert "server" not in headers

    @pytest.mark.asyncio
    async def test_oversized_payload_rejected_with_413(self):
        from app.main import app

        # Construct oversized payload (> 1MB)
        large_string = "A" * (1024 * 1024 + 100)
        large_payload = {"device_id": "TEST", "data": large_string}

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            res = await client.post("/api/telemetry/ingest", json=large_payload)
            assert res.status_code == 413
            assert "Payload too large" in res.json()["detail"]
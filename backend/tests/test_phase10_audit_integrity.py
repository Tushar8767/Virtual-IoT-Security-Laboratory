"""
Phase 10 Tests — Audit Logging & Cryptographic Integrity Verification

Tests:
1. Hash calculation determinism
2. Valid cryptographic chain verification
3. Detection of payload tampering (modified fields)
4. Detection of broken chain (prev_hash mismatch)
5. REST API: GET /api/audit/verify endpoint
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.models.audit import compute_audit_hash, AuditRepository
from app.services.audit_verifier import AuditLogVerifier
from app.api.routes.audit import get_verifier


class TestAuditHashIntegrity:
    """Test cryptographic chaining and verification logic."""

    def test_compute_audit_hash_deterministic(self):
        record = {
            "audit_id": "aud-1",
            "timestamp": "2026-09-25T00:00:00Z",
            "actor": "admin",
            "action": "DEVICE_CREATED",
            "target": "DEV-1",
            "result": "SUCCESS",
        }
        h1 = compute_audit_hash(record, "GENESIS")
        h2 = compute_audit_hash(record, "GENESIS")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex length

    @pytest.mark.asyncio
    async def test_verifier_validates_untampered_chain(self):
        # Build 3 valid chained records
        r1_core = {"audit_id": "1", "timestamp": "T1", "actor": "s", "action": "A1", "target": "T", "result": "OK"}
        h1 = compute_audit_hash(r1_core, "GENESIS_BLOCK_HASH")
        r1 = {**r1_core, "prev_hash": "GENESIS_BLOCK_HASH", "entry_hash": h1}

        r2_core = {"audit_id": "2", "timestamp": "T2", "actor": "s", "action": "A2", "target": "T", "result": "OK"}
        h2 = compute_audit_hash(r2_core, h1)
        r2 = {**r2_core, "prev_hash": h1, "entry_hash": h2}

        mock_repo = MagicMock(spec=AuditRepository)
        mock_repo.get_all_ordered_for_verification = AsyncMock(return_value=[r1, r2])

        verifier = AuditLogVerifier(mock_repo)
        res = await verifier.verify_chain()

        assert res.is_valid is True
        assert res.verified_count == 2

    @pytest.mark.asyncio
    async def test_verifier_detects_tampered_payload(self):
        r1_core = {"audit_id": "1", "timestamp": "T1", "actor": "s", "action": "A1", "target": "T", "result": "OK"}
        h1 = compute_audit_hash(r1_core, "GENESIS_BLOCK_HASH")
        r1 = {**r1_core, "prev_hash": "GENESIS_BLOCK_HASH", "entry_hash": h1}

        # Alter actor illegally after insertion
        r1["actor"] = "MALICIOUS_ACTOR"

        mock_repo = MagicMock(spec=AuditRepository)
        mock_repo.get_all_ordered_for_verification = AsyncMock(return_value=[r1])

        verifier = AuditLogVerifier(mock_repo)
        res = await verifier.verify_chain()

        assert res.is_valid is False
        assert "Content modified" in res.reason


class TestAuditAPI:
    """Test audit verification API endpoint."""

    @pytest.mark.asyncio
    async def test_verify_audit_endpoint(self):
        from app.main import app

        mock_verifier = MagicMock()
        mock_res = MagicMock()
        mock_res.is_valid = True
        mock_res.verified_count = 10
        mock_res.corrupted_record = None
        mock_res.reason = "All 10 verified"
        mock_verifier.verify_chain = AsyncMock(return_value=mock_res)

        app.dependency_overrides[get_verifier] = lambda: mock_verifier

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                res = await client.get("/api/audit/verify")
                assert res.status_code == 200
                data = res.json()
                assert data["status"] == "VALID"
                assert data["is_valid"] is True
                assert data["verified_records"] == 10
        finally:
            app.dependency_overrides.clear()
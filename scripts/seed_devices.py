#!/usr/bin/env python3
"""
Device Seeding Script — Virtual IoT Security Laboratory

Registers and provisions standard reference devices into the database:
1. LPC2138-TEMP-001   (Embedded Proteus Node: LPC2138 + LM35 Sensor)
2. PY-TEMP-001        (Virtual Python Temperature Sensor)
3. PY-MOTION-001      (Virtual Python Motion Detector)
4. PY-ACTUATOR-001    (Virtual Python Smart Actuator)

Usage:
    python scripts/seed_devices.py
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone

# Add backend directory to sys.path so we can import models and services
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

# Load environment from root or backend
env_path = ROOT_DIR / ".env"
if not env_path.exists():
    env_path = BACKEND_DIR / ".env"
load_dotenv(env_path)

from app.core.database import connect_to_mongodb, close_mongodb_connection, get_database
from app.models.device import DeviceType, DeviceStatus, TrustState, DEFAULT_CAPABILITIES
from app.models.audit import AuditAction, AuditResult, AuditRepository
from app.repositories.device_repository import DeviceRepository
from app.core.security import generate_device_credential_pair, generate_correlation_id


# Standard devices to seed
SEED_DEVICES = [
    {
        "device_id": "LPC2138-TEMP-001",
        "device_name": "Proteus LPC2138 Temperature Sensor",
        "device_type": DeviceType.TEMPERATURE_SENSOR,
        "description": "Hardware-in-the-loop Proteus simulation node with LM35 on ADC0.0 via UART0 (9600 baud)",
        "heartbeat_interval_seconds": 15,
        "metadata": {
            "source": "proteus_simulation",
            "mcu": "LPC2138",
            "sensor": "LM35",
            "adc_channel": "AD0.0",
            "uart": "UART0",
            "baudrate": 9600,
        },
    },
    {
        "device_id": "PY-TEMP-001",
        "device_name": "Virtual Facility Temperature Sensor",
        "device_type": DeviceType.TEMPERATURE_SENSOR,
        "description": "Python software simulated temperature sensor node",
        "heartbeat_interval_seconds": 15,
        "metadata": {"source": "python_simulator", "location": "Server Room A"},
    },
    {
        "device_id": "PY-MOTION-001",
        "device_name": "Virtual Hallway Motion Sensor",
        "device_type": DeviceType.MOTION_SENSOR,
        "description": "Python software simulated PIR motion detector",
        "heartbeat_interval_seconds": 20,
        "metadata": {"source": "python_simulator", "location": "East Wing Corridor"},
    },
    {
        "device_id": "PY-ACTUATOR-001",
        "device_name": "Virtual Smart HVAC Actuator",
        "device_type": DeviceType.SMART_ACTUATOR,
        "description": "Python software simulated cooling/heating control actuator",
        "heartbeat_interval_seconds": 30,
        "metadata": {"source": "python_simulator", "location": "HVAC Unit 1"},
    },
]


async def seed_all_devices():
    """Connect to database, seed devices, and provision credentials."""
    print("=" * 65)
    print("  VIRTUAL IOT SECURITY LABORATORY — DEVICE SEEDER")
    print("=" * 65)

    await connect_to_mongodb()
    db = get_database()
    device_repo = DeviceRepository(db)
    audit_repo = AuditRepository(db)

    provisioned_credentials = []

    for dev in SEED_DEVICES:
        device_id = dev["device_id"]
        existing = await device_repo.find_by_id(device_id)

        if existing:
            print(f"[-] Device already exists: {device_id} ({existing['status']})")
            continue

        # Generate credentials
        plain_key, hashed_key = generate_device_credential_pair()
        credential_id = f"cred-{device_id.lower()}"
        now = datetime.now(timezone.utc)
        correlation_id = generate_correlation_id()

        # Build device document
        caps = DEFAULT_CAPABILITIES.get(dev["device_type"], [])
        document = {
            "device_id": device_id,
            "device_name": dev["device_name"],
            "device_type": dev["device_type"].value,
            "status": DeviceStatus.PROVISIONED.value,
            "trust_state": TrustState.TRUSTED.value,
            "firmware_version": "1.0.0",
            "capabilities": [c.value for c in caps],
            "description": dev["description"],
            "heartbeat_interval_seconds": dev["heartbeat_interval_seconds"],
            "missed_heartbeats": 0,
            "credential": {
                "credential_id": credential_id,
                "hashed_key": hashed_key,
                "created_at": now,
                "expires_at": None,
                "is_revoked": False,
            },
            "created_at": now,
            "updated_at": now,
            "last_seen": None,
            "provisioned_at": now,
            "metadata": dev["metadata"],
        }

        await device_repo.insert(document)

        # Audit logs
        await audit_repo.log(
            action=AuditAction.DEVICE_CREATED,
            target=device_id,
            result=AuditResult.SUCCESS,
            actor="seed_script",
            correlation_id=correlation_id,
            metadata={"device_type": dev["device_type"].value},
        )
        await audit_repo.log(
            action=AuditAction.DEVICE_PROVISIONED,
            target=device_id,
            result=AuditResult.SUCCESS,
            actor="seed_script",
            correlation_id=correlation_id,
            metadata={"credential_id": credential_id},
        )

        print(f"[+] Seeded & Provisioned: {device_id}")
        provisioned_credentials.append((device_id, plain_key))

    print("\n" + "=" * 65)
    print("  PROVISIONED CREDENTIALS (SAVE SECURELY)")
    print("=" * 65)
    for dev_id, key in provisioned_credentials:
        print(f"Device: {dev_id.ljust(22)} API Key: {key}")
    print("=" * 65)

    await close_mongodb_connection()
    print("Seeding finished.\n")


if __name__ == "__main__":
    asyncio.run(seed_all_devices())
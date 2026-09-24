#!/usr/bin/env python3
"""
Reset Lab Script

Returns the lab to a clean state by clearing the database.
WARNING: This deletes all device, telemetry, and event data.

Usage:
    python scripts/reset_lab.py [--confirm]
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))


async def reset_lab():
    """Drop all lab collections and recreate indexes."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")

        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        db_name = os.getenv("MONGODB_DATABASE", "iot_security_lab")

        client = AsyncIOMotorClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        await client.admin.command("ping")

        db = client[db_name]

        collections = [
            "devices", "telemetry", "security_events",
            "alerts", "audit_logs", "scenarios", "investigations",
        ]

        for collection in collections:
            await db[collection].drop()
            print(f"  Dropped: {collection}")

        print(f"\nDatabase '{db_name}' reset complete.")
        client.close()

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    confirm = "--confirm" in sys.argv

    if not confirm:
        print("WARNING: This will delete ALL lab data.")
        response = input("Type 'yes' to confirm: ")
        if response.lower() != "yes":
            print("Reset cancelled.")
            sys.exit(0)

    print("Resetting Virtual IoT Security Lab...")
    asyncio.run(reset_lab())
    print("Done.")

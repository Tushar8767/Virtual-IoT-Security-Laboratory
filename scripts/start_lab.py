#!/usr/bin/env python3
"""
Start Lab Script

Convenience script to start all lab components in development mode.
Starts:
1. Backend API server (uvicorn)
2. Device Simulator (Phase 2+)

Usage:
    python scripts/start_lab.py

Prerequisites:
    - MongoDB running (local or Docker)
    - MQTT broker running (local or Docker)
    - Backend virtual environment set up
    - .env file configured

For infrastructure only (MongoDB + MQTT):
    docker compose up mongodb mosquitto -d
"""

import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND_DIR = ROOT / "backend"


def start_backend():
    """Start the FastAPI backend server."""
    print("Starting Virtual IoT Security Lab Backend...")
    print(f"Backend dir: {BACKEND_DIR}")

    venv_python = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = BACKEND_DIR / ".venv" / "bin" / "python"

    if not venv_python.exists():
        print("ERROR: Virtual environment not found.")
        print("Run: python -m venv backend/.venv && backend/.venv/Scripts/pip install -r backend/requirements.txt")
        sys.exit(1)

    return subprocess.Popen(
        [
            str(venv_python), "-m", "uvicorn",
            "app.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info",
        ],
        cwd=str(BACKEND_DIR),
        env={**os.environ},
    )


if __name__ == "__main__":
    print("=" * 60)
    print("  VIRTUAL IOT SECURITY LABORATORY")
    print("  Start Lab Script")
    print("=" * 60)

    backend_proc = start_backend()

    print("\n Backend:   http://localhost:8000")
    print(" API Docs:  http://localhost:8000/api/docs")
    print(" Health:    http://localhost:8000/api/health")
    print(" WebSocket: ws://localhost:8000/ws")
    print("\nPress Ctrl+C to stop.\n")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping lab...")
        backend_proc.terminate()
        print("Lab stopped.")

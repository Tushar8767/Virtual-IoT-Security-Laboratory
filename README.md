# Virtual IoT Security Laboratory

> A fully working, software-only Virtual IoT / Embedded Security Laboratory.
> No physical hardware required.

[![Phase](https://img.shields.io/badge/Phase-0%20Complete-green)](#)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-blue)](#)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20TypeScript-blue)](#)
[![Database](https://img.shields.io/badge/Database-MongoDB-green)](#)
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-orange)](#)

---

## Overview

The **Virtual IoT Security Laboratory** is a software-defined IoT security simulation environment.
It simulates a realistic connected-device ecosystem — without any physical hardware — and provides:

- Virtual device simulation (temperature sensors, motion sensors, actuators, industrial controllers)
- Device lifecycle management with state machine enforcement
- Device identity, authentication, and capability-based authorization
- Real-time telemetry pipeline (MQTT → backend → WebSocket → dashboard)
- Deterministic security detection engine with 8+ rule types
- Controlled attack scenario simulation (7 scenarios — all contained within the virtual lab)
- Security event investigation with event correlation
- Immutable audit logging
- Professional React dashboard with real-time updates

This project is designed as both a **Software Engineering** and **Cybersecurity / IoT Security** flagship project.

---

## Architecture

```
                    VIRTUAL IOT SECURITY LAB
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
   Device Simulator     Gateway Layer       Attack Simulator
          |                   |                   |
          +-------------------+-------------------+
                              |
                    Communication Layer
                         MQTT / HTTP
                              |
                              v
                    Secure IoT Gateway
                              |
              +---------------+---------------+
              |                               |
              v                               v
       Device Management                Telemetry Pipeline
              |                               |
              +---------------+---------------+
                              |
                              v
                       Backend API (FastAPI)
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
         MongoDB        Security Engine    Event Engine
             |                |                |
             +----------------+----------------+
                              |
                              v
                       React Dashboard
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite |
| Backend | Python 3.13, FastAPI, Pydantic v2 |
| Database | MongoDB 7.0 (motor async driver) |
| MQTT Broker | Eclipse Mosquitto 2.0 |
| Authentication | bcrypt, python-jose (JWT) |
| Async | asyncio, aiomqtt |
| Testing | pytest, pytest-asyncio, httpx |
| Logging | structlog (structured JSON logging) |
| Containerization | Docker Compose (MongoDB + Mosquitto) |

---

## Project Structure

```
virtual-iot-security-lab/
├── .env.example              # Environment template — copy to .env
├── docker-compose.yml        # MongoDB + Mosquitto for local dev
│
├── backend/                  # FastAPI backend application
│   ├── app/
│   │   ├── main.py           # Application entry point
│   │   ├── core/             # Config, logging, DB, MQTT, security
│   │   ├── api/              # Routes + WebSocket
│   │   ├── models/           # Domain models (Phase 1+)
│   │   ├── schemas/          # Pydantic schemas (Phase 1+)
│   │   ├── services/         # Business logic (Phase 1+)
│   │   ├── repositories/     # Database access (Phase 1+)
│   │   ├── security/         # Detection engine (Phase 7+)
│   │   ├── telemetry/        # Telemetry pipeline (Phase 4+)
│   │   └── events/           # Event engine (Phase 7+)
│   └── tests/                # Backend tests
│
├── device_simulator/         # Virtual IoT device framework
│   ├── devices/              # Device implementations
│   ├── protocols/            # MQTT client wrappers
│   ├── telemetry/            # Telemetry generators
│   ├── behaviors/            # Normal/abnormal behavior profiles
│   └── scenarios/            # Attack scenario helpers
│
├── attack_simulator/         # Controlled attack scenarios
│   ├── scenarios/            # Individual attack scenario scripts
│   └── engine/               # Scenario orchestration
│
├── frontend/                 # React TypeScript dashboard
│   └── src/
│       ├── pages/            # Page components
│       ├── components/       # Reusable UI components
│       ├── services/         # API + WebSocket clients
│       ├── hooks/            # Custom React hooks
│       └── types/            # TypeScript type definitions
│
├── scripts/                  # Utility scripts
│   ├── start_lab.py          # Start all lab components
│   ├── seed_devices.py       # Create sample devices (Phase 1+)
│   └── reset_lab.py          # Reset lab to clean state
│
└── docs/                     # Documentation
    ├── architecture.md
    ├── security-model.md
    ├── threat-model.md
    ├── api.md
    └── attack-scenarios.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (local install OR Docker)
- MQTT Broker — Eclipse Mosquitto (local install OR Docker)

### Option A — Docker Infrastructure (Recommended)

Start MongoDB and Mosquitto in Docker, run backend/frontend locally:

```bash
# 1. Start infrastructure
docker compose up mongodb mosquitto -d

# 2. Set up backend
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # Windows
# OR: .venv/bin/pip install -r requirements.txt  # Linux/Mac

# 3. Configure environment
cp ../.env.example ../.env
# Edit .env if needed (defaults work for local dev)

# 4. Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Set up and start frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Option B — Local MongoDB + Mosquitto

Install MongoDB and Mosquitto locally, then follow steps 2-5 above.

### Access Points

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:5173 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/api/docs |
| Health Check | http://localhost:8000/api/health |
| WebSocket | ws://localhost:8000/ws |

---

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Critical settings to change:**
- `SECRET_KEY` — generate a strong random key
- `DEVICE_PROVISIONING_SECRET` — used to provision device credentials

Never commit `.env` to version control.

---

## Running Tests

```bash
cd backend
.venv\Scripts\python -m pytest tests/ -v
```

---

## Implementation Phases

| Phase | Name | Status |
|-------|------|--------|
| **0** | Project Foundation | ✅ **Complete** |
| 1 | Device Domain | 🔄 Next |
| 2 | Device Simulator | ⏳ Pending |
| 3 | MQTT Communication | ⏳ Pending |
| 4 | Telemetry Pipeline | ⏳ Pending |
| 5 | Frontend Dashboard | ⏳ Pending |
| 6 | Auth & Authorization | ⏳ Pending |
| 7 | Security Detection Engine | ⏳ Pending |
| 8 | Attack Simulation | ⏳ Pending |
| 9 | Investigation | ⏳ Pending |
| 10 | Audit Logging | ⏳ Pending |
| 11 | Hardening | ⏳ Pending |
| 12 | Testing | ⏳ Pending |
| 13 | Polish | ⏳ Pending |

---

## Security Notice

This is a **virtual/simulated** IoT security environment.

- All attack simulations operate only within this application's own virtual environment.
- No real network scanning, exploitation, or unauthorized access to any external systems.
- This is a software simulation — no real hardware is involved.

---

## Future Extensions (Not Implemented)

- AWS IoT Core integration
- Certificate-based device identity (X.509)
- Real hardware support (ESP32)
- ML-based anomaly detection
- SIEM integration
- Rakshak integration

---

## License

MIT

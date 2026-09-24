#!/usr/bin/env python3
r"""
Proteus LPC2138 UART Bridge Runner

Connects the Proteus VSM LPC2138 + LM35 simulation to the Virtual IoT Security Laboratory.

Usage:
  1. Simulated Mode (no hardware/com0com needed):
     backend\.venv\Scripts\python scripts/run_proteus_bridge.py --simulate

  2. Live Virtual COM Port Mode (e.g., com0com COM1 <-> COM2):
     backend\.venv\Scripts\python scripts/run_proteus_bridge.py --port COM2 --baud 9600
"""

import sys
import time
import argparse
import random
import httpx
from pathlib import Path

# Add project root and backend to sys.path
_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = _ROOT / "backend"
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from device_simulator.protocols.uart_bridge import ProteusUartBridge

API_URL = "http://localhost:8000/api/telemetry/ingest"
DEVICE_ID = "LPC2138-TEMP-001"
API_KEY = "dev-secret-lpc2138"


def send_to_api(payload: dict):
    try:
        res = httpx.post(API_URL, json=payload, timeout=3.0)
        if res.status_code in (200, 201):
            print(f"[BRIDGE -> API] ✅ Ingested packet #{payload.get('sequence_number')} | Temp: {payload.get('values', {}).get('temperature_c')}°C")
        else:
            print(f"[BRIDGE -> API] ❌ Rejected ({res.status_code}): {res.text}")
    except Exception as e:
        print(f"[BRIDGE -> API] ⚠️ Failed to forward telemetry: {e}")


def run_simulated():
    print("=" * 60)
    print("📡 PROTEUS LPC2138 UART BRIDGE — SIMULATED HARDWARE MODE")
    print(f"Device: {DEVICE_ID} (ARM7TDMI + LM35 ADC)")
    print(f"Forwarding to: {API_URL}")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    bridge = ProteusUartBridge(
        device_id=DEVICE_ID,
        api_key=API_KEY,
        on_telemetry_parsed=send_to_api,
    )

    seq = 1
    base_temp = 25.0

    try:
        while True:
            # Generate realistic ADC & Temperature reading matching LPC2138 main.c
            fluctuation = random.uniform(-1.0, 1.2)
            temp = round(base_temp + fluctuation, 1)
            adc_val = int((temp * 1023) / 330)

            # Emitted line exactly matching simulation/main.c
            raw_line = f"TELEMETRY;DEVICE_ID={DEVICE_ID};TYPE=TEMPERATURE_SENSOR;SEQ={seq};ADC={adc_val};TEMP={temp}\r\n"
            print(f"[PROTEUS UART0 RAW] >> {raw_line.strip()}")

            bridge.parse_raw_line(raw_line)
            seq += 1
            time.sleep(3.0)
    except KeyboardInterrupt:
        print("\n[BRIDGE] Stopped cleanly.")


def run_serial(port: str, baud: int):
    try:
        import serial
    except ImportError:
        print("ERROR: pyserial is required for COM port mode.")
        print("Install via: backend\\.venv\\Scripts\\pip install pyserial")
        sys.exit(1)

    print("=" * 60)
    print(f"📡 PROTEUS LPC2138 UART BRIDGE — SERIAL PORT MODE ({port} @ {baud} baud)")
    print(f"Listening for Proteus UART0 emissions...")
    print("=" * 60)

    bridge = ProteusUartBridge(
        device_id=DEVICE_ID,
        api_key=API_KEY,
        on_telemetry_parsed=send_to_api,
    )

    try:
        ser = serial.Serial(port, baud, timeout=1.0)
    except Exception as e:
        print(f"ERROR: Could not open {port}: {e}")
        print("\nTip: To test without physical or virtual COM ports, run:")
        print("python scripts/run_proteus_bridge.py --simulate")
        sys.exit(1)

    while True:
        try:
            line = ser.readline().decode("utf-8", errors="replace")
            if line:
                print(f"[UART RECV] {line.strip()}")
                bridge.parse_raw_line(line)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[UART ERROR] {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proteus LPC2138 UART Bridge")
    parser.add_argument("--simulate", action="store_true", help="Run simulated hardware stream")
    parser.add_argument("--port", type=str, default=None, help="Serial port (e.g. COM2)")
    parser.add_argument("--baud", type=int, default=9600, help="Baud rate (default: 9600)")

    args = parser.parse_args()

    if args.port:
        run_serial(args.port, args.baud)
    else:
        run_simulated()

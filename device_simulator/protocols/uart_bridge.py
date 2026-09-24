"""
UART Bridge for Proteus LPC2138 LM35 Node

Reads serial data emitted from Proteus Virtual Terminal via UART0 (9600 baud, 8N1).
Parses temperature readings, constructs standard lab telemetry payloads,
and forwards them to the IoT Gateway.
"""

import re
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable
import structlog

logger = structlog.get_logger(__name__)


class ProteusUartBridge:
    """
    Bridge connecting Proteus LPC2138 serial output to the IoT Lab.
    """

    def __init__(
        self,
        device_id: str = "LPC2138-TEMP-001",
        api_key: Optional[str] = None,
        on_telemetry_parsed: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ):
        self.device_id = device_id
        self.api_key = api_key
        self.on_telemetry_parsed = on_telemetry_parsed
        self.sequence_number = 0

    def parse_raw_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parses serial output lines from LPC2138 main.c.
        Supports standard formats such as:
        - "TEMP: 26.5 C"
        - "LPC2138-TEMP-001: 28.0"
        - JSON line: '{"temp": 25.4}'
        """
        cleaned = line.strip()
        if not cleaned:
            return None

        temp_val: Optional[float] = None

        # Format 1: JSON
        if cleaned.startswith("{") and cleaned.endswith("}"):
            try:
                data = json.loads(cleaned)
                temp_val = float(data.get("temp", data.get("temperature", 0)))
            except Exception:
                pass

        # Format 2: Proteus Key=Value format (e.g. TELEMETRY;...;TEMP=25)
        if temp_val is None:
            match = re.search(r"TEMP[=:]\s*([-+]?\d*\.?\d+)", cleaned, re.IGNORECASE)
            if match:
                try:
                    temp_val = float(match.group(1))
                except ValueError:
                    temp_val = None

        # Format 3: Fallback number search
        if temp_val is None:
            match = re.search(r"[-+]?\d*\.\d+|\d+", cleaned)
            if match:
                try:
                    temp_val = float(match.group())
                except ValueError:
                    temp_val = None

        if temp_val is None:
            return None

        self.sequence_number += 1
        now = datetime.now(timezone.utc).isoformat()

        payload = {
            "event_id": f"tel-uart-{uuid.uuid4().hex[:8]}",
            "device_id": self.device_id,
            "device_type": "temperature_sensor",
            "timestamp": now,
            "telemetry_type": "temperature_sensor_telemetry",
            "sequence_number": self.sequence_number,
            "firmware_version": "1.0.0",
            "correlation_id": str(uuid.uuid4()),
            "values": {
                "temperature_c": temp_val,
                "temperature_f": round((temp_val * 9 / 5) + 32, 2),
                "unit": "Celsius",
                "source": "proteus_lpc2138_uart0",
                "raw_reading": cleaned,
            },
        }

        if self.api_key:
            payload["api_key"] = self.api_key

        if self.on_telemetry_parsed:
            self.on_telemetry_parsed(payload)

        return payload
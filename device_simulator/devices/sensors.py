"""
Concrete Virtual Device Implementations

Simulates realistic sensor readings for:
1. VirtualTemperatureSensor (LM35 equivalent, range 15.0°C – 35.0°C, anomaly support)
2. VirtualMotionSensor (PIR motion detector with event counts)
3. VirtualSmartActuator (HVAC actuator with state, setpoint, power consumption)
"""

import random
from typing import Dict, Any
from device_simulator.devices.base import VirtualDevice
from app.models.device import DeviceType


class VirtualTemperatureSensor(VirtualDevice):
    """
    Virtual temperature sensor simulating an LM35 sensor.
    Output: temperature_c, temperature_f, unit, status.
    """

    def __init__(self, device_id: str, device_name: str = "Virtual Temperature Sensor", **kwargs):
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            device_type=DeviceType.TEMPERATURE_SENSOR.value,
            **kwargs,
        )
        self.base_temp = 24.0

    def generate_sensor_values(self) -> Dict[str, Any]:
        if self.mode == "abnormal":
            # Simulate high temperature anomaly outside normal range (e.g. 75.0°C to 110.0°C)
            temp = round(random.uniform(75.0, 110.0), 2)
        else:
            # Normal fluctuation (+/- 1.5 degrees around base)
            fluctuation = random.uniform(-1.5, 1.5)
            temp = round(self.base_temp + fluctuation, 2)

        return {
            "temperature_c": temp,
            "temperature_f": round((temp * 9 / 5) + 32, 2),
            "unit": "Celsius",
            "ambient_variance": round(random.uniform(0.01, 0.05), 3),
            "sensor_health": "OPTIMAL" if self.mode != "abnormal" else "OVERHEATING",
        }


class VirtualMotionSensor(VirtualDevice):
    """
    Virtual PIR motion sensor.
    Output: motion_detected (bool), confidence, ambient_light_lux, trigger_count.
    """

    def __init__(self, device_id: str, device_name: str = "Virtual Motion Sensor", **kwargs):
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            device_type=DeviceType.MOTION_SENSOR.value,
            **kwargs,
        )
        self.trigger_count = 0

    def generate_sensor_values(self) -> Dict[str, Any]:
        # 30% chance of motion under normal conditions, 95% under stress/abnormal
        motion_probability = 0.95 if self.mode in ("stress", "abnormal") else 0.30
        detected = random.random() < motion_probability

        if detected:
            self.trigger_count += 1

        return {
            "motion_detected": detected,
            "confidence": round(random.uniform(0.85, 0.99), 2) if detected else 0.0,
            "ambient_light_lux": round(random.uniform(150.0, 450.0), 1),
            "total_trigger_count": self.trigger_count,
        }


class VirtualSmartActuator(VirtualDevice):
    """
    Virtual smart HVAC actuator.
    Output: state (ON/OFF), target_temp, power_watts, duty_cycle_percent.
    """

    def __init__(self, device_id: str, device_name: str = "Virtual Smart Actuator", **kwargs):
        super().__init__(
            device_id=device_id,
            device_name=device_name,
            device_type=DeviceType.SMART_ACTUATOR.value,
            **kwargs,
        )
        self.state = "ON"
        self.target_temp = 22.0

    def generate_sensor_values(self) -> Dict[str, Any]:
        return {
            "actuator_state": self.state,
            "target_setpoint_c": self.target_temp,
            "power_consumption_watts": round(random.uniform(350.0, 480.0), 1) if self.state == "ON" else 5.0,
            "duty_cycle_percent": round(random.uniform(60.0, 85.0), 1) if self.state == "ON" else 0.0,
        }
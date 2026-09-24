"""
Application Configuration

All settings are loaded from environment variables.
Defaults are safe for local development only.
Use .env file (copy from .env.example) to configure.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All sensitive values must be provided via environment / .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    APP_ENV: str = "development"
    APP_NAME: str = "Virtual IoT Security Lab"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # --- Backend API ---
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # --- MongoDB ---
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "iot_security_lab"
    MONGODB_MAX_POOL_SIZE: int = 10

    # --- MQTT Broker ---
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_BROKER_WS_PORT: int = 9001
    MQTT_CLIENT_ID_PREFIX: str = "iot-lab-backend"

    # --- Security ---
    SECRET_KEY: str = "INSECURE_DEFAULT_CHANGE_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Device Credentials ---
    DEVICE_PROVISIONING_SECRET: str = "INSECURE_DEFAULT_CHANGE_IN_PRODUCTION"

    # --- Telemetry Retention ---
    TELEMETRY_MAX_RECORDS_PER_DEVICE: int = 1000
    TELEMETRY_RETENTION_HOURS: int = 24

    # --- Detection Engine Thresholds ---
    AUTH_FAILURE_THRESHOLD: int = 5
    AUTH_FAILURE_WINDOW_SECONDS: int = 60
    TELEMETRY_RATE_THRESHOLD: int = 10
    TELEMETRY_RATE_WINDOW_SECONDS: int = 60
    HEARTBEAT_TIMEOUT_SECONDS: int = 60

    # --- Simulation Defaults ---
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS: int = 15
    DEFAULT_TELEMETRY_INTERVAL_SECONDS: int = 10

    @field_validator("DEBUG", mode="before")
    @classmethod
    def coerce_debug(cls, v):
        """
        Safely coerce DEBUG to bool.
        Handles system env vars that set DEBUG to non-bool strings
        (e.g. Node.js sets DEBUG=release, DEBUG=* etc.)
        """
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes", "on")
        return bool(v)

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def warn_insecure_secret(cls, v):
        if v == "INSECURE_DEFAULT_CHANGE_IN_PRODUCTION":
            import warnings
            warnings.warn(
                "SECRET_KEY is using the insecure default. "
                "Set a strong SECRET_KEY in your .env file.",
                stacklevel=2,
            )
        return v


# Global settings instance
settings = Settings()

"""Configuration management using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure Service Bus Configuration
    complaint_send_primary_connection_string: str
    service_bus_queue_name: str = "complaints-event"

    # Unified logs (Azure Storage Queue)
    # If connection string is empty, unified logging is disabled.
    unified_logs_storage_connection_string: str = ""
    unified_logs_queue_name: str = "grooming-service-logs"

    # Application Configuration
    app_name: str = "ComplaintService"
    app_version: str = "0.1.0"
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()

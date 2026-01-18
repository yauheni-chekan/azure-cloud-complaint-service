"""Tests for configuration management."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_with_env_vars(mock_env_vars: None) -> None:  # noqa: ARG001
    """Test that settings load correctly from environment variables."""
    settings = Settings()

    assert settings.complaint_send_primary_connection_string == (
        "Endpoint=sb://test.servicebus.windows.net/;"
        "SharedAccessKeyName=test;SharedAccessKey=testkey123"
    )
    assert settings.service_bus_queue_name == "test-complaints-queue"
    assert settings.debug is False


def test_settings_default_values(mock_env_vars: None) -> None:  # noqa: ARG001
    """Test that default values are applied correctly."""
    settings = Settings()

    assert settings.app_name == "ComplaintService"
    assert settings.app_version == "0.1.0"
    assert settings.service_bus_queue_name == "test-complaints-queue"


def test_settings_debug_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test debug mode configuration."""
    monkeypatch.setenv(
        "COMPLAINT_SEND_PRIMARY_CONNECTION_STRING",
        "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test",
    )
    monkeypatch.setenv("DEBUG", "True")

    settings = Settings()
    assert settings.debug is True


def test_settings_missing_required_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that validation fails when required fields are missing."""
    # Clear all environment variables that Settings expects
    monkeypatch.delenv("COMPLAINT_SEND_PRIMARY_CONNECTION_STRING", raising=False)
    monkeypatch.delenv("SERVICE_BUS_QUEUE_NAME", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_VERSION", raising=False)

    # Also prevent loading from .env file
    monkeypatch.setattr(
        "app.config.Settings.model_config",
        {
            "env_file": None,
            "case_sensitive": False,
            "extra": "ignore",
        },
    )

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "complaint_send_primary_connection_string" in str(exc_info.value)


def test_settings_custom_queue_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test custom queue name configuration."""
    monkeypatch.setenv(
        "COMPLAINT_SEND_PRIMARY_CONNECTION_STRING",
        "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test",
    )
    monkeypatch.setenv("SERVICE_BUS_QUEUE_NAME", "custom-queue")

    settings = Settings()
    assert settings.service_bus_queue_name == "custom-queue"


def test_settings_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment variables are case insensitive."""
    monkeypatch.setenv(
        "complaint_send_primary_connection_string",
        "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=test",
    )

    settings = Settings()
    assert settings.complaint_send_primary_connection_string.startswith("Endpoint=sb://test")

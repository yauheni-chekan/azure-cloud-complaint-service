"""Pytest configuration and shared fixtures."""

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

# Ensure required settings exist before any app modules are imported.
# (Some modules instantiate Settings at import-time.)
os.environ.setdefault(
    "COMPLAINT_SEND_PRIMARY_CONNECTION_STRING",
    "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=testkey123",
)
os.environ.setdefault("SERVICE_BUS_QUEUE_NAME", "test-complaints-queue")
os.environ.setdefault("DEBUG", "False")

from app.main import app


@pytest.fixture
def sample_booking_id() -> UUID:
    """Sample booking UUID for testing."""
    return UUID("123e4567-e89b-12d3-a456-426614174000")


@pytest.fixture
def sample_complaint_data(sample_booking_id: UUID) -> dict[str, str]:
    """Sample complaint request data."""
    return {
        "bookingId": str(sample_booking_id),
        "description": "The groomer arrived 2 hours late and did not properly groom my pet.",
    }


@pytest.fixture
def sample_timestamp() -> datetime:
    """Sample timestamp for testing."""
    return datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock environment variables for testing."""
    monkeypatch.setenv(
        "COMPLAINT_SEND_PRIMARY_CONNECTION_STRING",
        "Endpoint=sb://test.servicebus.windows.net/;SharedAccessKeyName=test;SharedAccessKey=testkey123",
    )
    monkeypatch.setenv("SERVICE_BUS_QUEUE_NAME", "test-complaints-queue")
    monkeypatch.setenv("DEBUG", "False")


@pytest.fixture
def test_client() -> TestClient:
    """FastAPI TestClient instance."""
    return TestClient(app)


@pytest.fixture
async def mock_servicebus_sender(mocker) -> AsyncMock:
    """Mock Azure Service Bus sender."""
    mock_sender = AsyncMock()
    mock_sender.send_messages = AsyncMock()

    # Mock the sender context manager
    mock_sender_context = AsyncMock()
    mock_sender_context.__aenter__ = AsyncMock(return_value=mock_sender)
    mock_sender_context.__aexit__ = AsyncMock(return_value=None)

    # Mock the client
    mock_client = MagicMock()
    mock_client.get_queue_sender = MagicMock(return_value=mock_sender_context)
    mock_client.close = AsyncMock()

    # Mock the client context manager
    mock_client_context = AsyncMock()
    mock_client_context.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_context.__aexit__ = AsyncMock(return_value=None)

    # Patch ServiceBusClient.from_connection_string
    mocker.patch(
        "app.services.servicebus_client.ServiceBusClient.from_connection_string",
        return_value=mock_client_context,
    )

    return mock_sender


@pytest.fixture
def mock_servicebus_client_connected(mocker) -> MagicMock:  # noqa: ARG001
    """Mock connected ServiceBusComplaintSender."""
    from app.services.servicebus_client import ServiceBusComplaintSender

    mock_client = MagicMock()
    mock_sender = AsyncMock()

    # Mock get_queue_sender
    mock_sender_context = AsyncMock()
    mock_sender_context.__aenter__ = AsyncMock(return_value=mock_sender)
    mock_sender_context.__aexit__ = AsyncMock(return_value=None)

    mock_client.get_queue_sender = MagicMock(return_value=mock_sender_context)
    mock_client.close = AsyncMock()

    # Create instance and inject mock client
    sender = ServiceBusComplaintSender()
    sender._client = mock_client

    return sender


@pytest.fixture
def mock_datetime(mocker, sample_timestamp: datetime):
    """Mock datetime.now to return a fixed timestamp."""
    mock_dt = mocker.patch("app.api.v1.endpoints.datetime")
    mock_dt.now.return_value = sample_timestamp
    return mock_dt

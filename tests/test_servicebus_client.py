"""Tests for Azure Service Bus client."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from azure.servicebus import ServiceBusMessage

from app.services.servicebus_client import ServiceBusComplaintSender


class TestServiceBusComplaintSender:
    """Tests for ServiceBusComplaintSender class."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mocker) -> None:
        """Test successful connection to Service Bus."""
        mock_client = MagicMock()
        mock_from_conn = mocker.patch(
            "app.services.servicebus_client.ServiceBusClient.from_connection_string",
            return_value=mock_client,
        )

        sender = ServiceBusComplaintSender()
        await sender.connect()

        assert sender._client == mock_client
        mock_from_conn.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, mocker) -> None:
        """Test connection failure handling."""
        mocker.patch(
            "app.services.servicebus_client.ServiceBusClient.from_connection_string",
            side_effect=Exception("Connection failed"),
        )

        sender = ServiceBusComplaintSender()

        with pytest.raises(Exception, match="Connection failed"):
            await sender.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        """Test disconnection from Service Bus."""
        sender = ServiceBusComplaintSender()
        mock_client = AsyncMock()
        sender._client = mock_client

        await sender.disconnect()

        mock_client.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_client(self) -> None:
        """Test disconnect when client is None does not raise error."""
        sender = ServiceBusComplaintSender()
        sender._client = None

        # Should not raise any exception
        await sender.disconnect()

    @pytest.mark.asyncio
    async def test_send_complaint_success(
        self,
        sample_booking_id: UUID,
    ) -> None:
        """Test successful complaint message sending."""
        # Setup mocks
        mock_sender = AsyncMock()
        mock_sender_context = AsyncMock()
        mock_sender_context.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender_context.__aexit__ = AsyncMock(return_value=None)

        mock_client = MagicMock()
        mock_client.get_queue_sender = MagicMock(return_value=mock_sender_context)

        sender = ServiceBusComplaintSender()
        sender._client = mock_client

        # Send complaint
        timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        await sender.send_complaint(
            booking_id=sample_booking_id,
            description="Test complaint",
            timestamp=timestamp,
        )

        # Verify queue sender was called
        mock_client.get_queue_sender.assert_called_once_with(queue_name=sender._queue_name)

        # Verify message was sent
        mock_sender.send_messages.assert_awaited_once()

        # Verify message content
        call_args = mock_sender.send_messages.call_args
        sent_message = call_args[0][0]
        assert isinstance(sent_message, ServiceBusMessage)

        # Parse and verify message body
        message_body = json.loads(str(sent_message))
        assert message_body["bookingId"] == str(sample_booking_id)
        assert message_body["description"] == "Test complaint"
        assert message_body["timestamp"] == timestamp.isoformat()

    @pytest.mark.asyncio
    async def test_send_complaint_no_client(
        self,
        sample_booking_id: UUID,
    ) -> None:
        """Test send complaint fails when client is not connected."""
        sender = ServiceBusComplaintSender()
        sender._client = None

        timestamp = datetime.now(UTC)

        with pytest.raises(RuntimeError, match="Service Bus client is not connected"):
            await sender.send_complaint(
                booking_id=sample_booking_id,
                description="Test",
                timestamp=timestamp,
            )

    @pytest.mark.asyncio
    async def test_send_complaint_failure(
        self,
        sample_booking_id: UUID,
    ) -> None:
        """Test send complaint handles sending failures."""
        # Setup mocks
        mock_sender = AsyncMock()
        mock_sender.send_messages = AsyncMock(side_effect=Exception("Send failed"))

        mock_sender_context = AsyncMock()
        mock_sender_context.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender_context.__aexit__ = AsyncMock(return_value=None)

        mock_client = MagicMock()
        mock_client.get_queue_sender = MagicMock(return_value=mock_sender_context)

        sender = ServiceBusComplaintSender()
        sender._client = mock_client

        timestamp = datetime.now(UTC)

        with pytest.raises(Exception, match="Send failed"):
            await sender.send_complaint(
                booking_id=sample_booking_id,
                description="Test",
                timestamp=timestamp,
            )

    @pytest.mark.asyncio
    async def test_context_manager(self, mocker) -> None:
        """Test async context manager behavior."""
        mock_client = MagicMock()
        mock_client.close = AsyncMock()

        mocker.patch(
            "app.services.servicebus_client.ServiceBusClient.from_connection_string",
            return_value=mock_client,
        )

        sender = ServiceBusComplaintSender()

        async with sender:
            assert sender._client == mock_client

        # Verify disconnect was called
        mock_client.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_message_format(
        self,
        sample_booking_id: UUID,
    ) -> None:
        """Test that message is formatted correctly as JSON."""
        mock_sender = AsyncMock()
        mock_sender_context = AsyncMock()
        mock_sender_context.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender_context.__aexit__ = AsyncMock(return_value=None)

        mock_client = MagicMock()
        mock_client.get_queue_sender = MagicMock(return_value=mock_sender_context)

        sender = ServiceBusComplaintSender()
        sender._client = mock_client

        timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        description = "Groomer was unprofessional"

        await sender.send_complaint(
            booking_id=sample_booking_id,
            description=description,
            timestamp=timestamp,
        )

        # Get the message that was sent
        call_args = mock_sender.send_messages.call_args
        sent_message = call_args[0][0]

        # Verify it's a ServiceBusMessage
        assert isinstance(sent_message, ServiceBusMessage)

        # Verify content type
        assert sent_message.content_type == "application/json"

        # Parse and verify JSON structure
        message_body = json.loads(str(sent_message))
        assert "bookingId" in message_body
        assert "description" in message_body
        assert "timestamp" in message_body
        assert message_body["bookingId"] == str(sample_booking_id)
        assert message_body["description"] == description

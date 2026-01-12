"""Azure Service Bus client for sending complaint messages."""

import json
import logging
from datetime import datetime
from typing import Any, Self
from uuid import UUID

from azure.servicebus import ServiceBusMessage
from azure.servicebus.aio import ServiceBusClient

from app.config import settings

logger = logging.getLogger(__name__)


class ServiceBusComplaintSender:
    """Async Azure Service Bus sender for complaint messages."""

    def __init__(self) -> None:
        """Initialize the Service Bus client."""
        self._client: ServiceBusClient | None = None
        self._connection_string = settings.complaint_send_primary_connection_string
        self._queue_name = settings.service_bus_queue_name

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Establish connection to Azure Service Bus."""
        try:
            self._client = ServiceBusClient.from_connection_string(
                conn_str=self._connection_string,
                logging_enable=settings.debug,
            )
            logger.info("Connected to Azure Service Bus")
        except Exception:
            logger.exception("Failed to connect to Service Bus")
            raise

    async def disconnect(self) -> None:
        """Close connection to Azure Service Bus."""
        if self._client:
            await self._client.close()
            logger.info("Disconnected from Azure Service Bus")

    async def send_complaint(
        self,
        booking_id: UUID,
        description: str,
        timestamp: datetime,
    ) -> None:
        """Send a complaint message to the Service Bus queue.

        :param booking_id: UUID of the booking associated with the complaint
        :param description: Complaint description text
        :param timestamp: Timestamp when complaint was received
        """
        if self._client is None:
            msg = "Service Bus client is not connected"
            raise RuntimeError(msg)

        message_body: dict[str, Any] = {
            "bookingId": str(booking_id),
            "description": description,
            "timestamp": timestamp.isoformat(),
        }

        try:
            async with self._client.get_queue_sender(
                queue_name=self._queue_name,
            ) as sender:
                message = ServiceBusMessage(
                    body=json.dumps(message_body),
                    content_type="application/json",
                )

                await sender.send_messages(message)
                logger.info(
                    "Successfully sent complaint for booking %s to queue %s",
                    booking_id,
                    self._queue_name,
                )

        except Exception:
            logger.exception(
                "Failed to send complaint for booking %s",
                booking_id,
            )
            raise


complaint_sender = ServiceBusComplaintSender()

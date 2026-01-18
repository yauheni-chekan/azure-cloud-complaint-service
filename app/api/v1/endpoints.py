"""API v1 endpoints for ComplaintService."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.config import settings
from app.schemas import ComplaintRequest, ComplaintResponse, HealthResponse
from app.services.servicebus_client import complaint_sender
from app.services.unified_log_queue import get_unified_log_sender

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/complaints",
    status_code=status.HTTP_201_CREATED,
    summary="Submit a complaint",
    description=(
        "Submit a complaint for a specific booking. "
        "The complaint will be forwarded to Azure Service Bus for processing."
    ),
    responses={
        201: {
            "description": "Complaint successfully submitted and queued for processing",
        },
        422: {"description": "Validation error - invalid request body"},
        500: {"description": "Internal server error - failed to send message to queue"},
    },
)
async def create_complaint(
    complaint: ComplaintRequest,
    background_tasks: BackgroundTasks,
) -> ComplaintResponse:
    """Submit a complaint for a booking.

    This endpoint accepts complaint details and forwards them asynchronously
    to Azure Service Bus for processing by the BookingService.

    :param complaint: Complaint details including bookingId and description
    :return: ComplaintResponse with confirmation and timestamp
    :raises HTTPException: If message cannot be sent to Service Bus
    """
    timestamp = datetime.now(UTC)

    try:
        async with complaint_sender:
            await complaint_sender.send_complaint(
                booking_id=complaint.booking_id,
                description=complaint.description,
                timestamp=timestamp,
            )

        logger.info("Complaint submitted for booking %s", complaint.booking_id)

        unified_logs = get_unified_log_sender()
        if unified_logs is not None:
            background_tasks.add_task(
                unified_logs.send,
                level="INFO",
                event="complaint.submitted",
                message="Complaint submitted and forwarded to Service Bus",
                bookingId=str(complaint.booking_id),
                serviceBusQueue=settings.service_bus_queue_name,
                timestamp=timestamp.isoformat(),
            )

        return ComplaintResponse(
            message="Complaint submitted successfully",
            booking_id=complaint.booking_id,
            timestamp=timestamp,
        )

    except Exception:
        logger.exception("Failed to submit complaint")
        unified_logs = get_unified_log_sender()
        if unified_logs is not None:
            background_tasks.add_task(
                unified_logs.send,
                level="ERROR",
                event="complaint.failed",
                message="Failed to submit complaint",
                bookingId=str(complaint.booking_id),
                serviceBusQueue=settings.service_bus_queue_name,
            )
        msg = "Failed to submit complaint. Please try again later."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=msg,
        ) from None


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of the ComplaintService API",
    responses={200: {"description": "Service is healthy and operational"}},
)
async def health_check() -> HealthResponse:
    """:return: HealthResponse with service status information"""
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
    )

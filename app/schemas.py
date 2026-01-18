"""Pydantic schemas for request and response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ComplaintRequest(BaseModel):
    """Request schema for submitting a complaint."""

    booking_id: UUID = Field(
        ...,
        description="UUID of the booking associated with this complaint",
        alias="bookingId",
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Detailed description of the complaint",
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "bookingId": "123e4567-e89b-12d3-a456-426614174000",
                    "description": "The groomer was 2 hours late and didn't properly groom my pet.",
                }
            ]
        },
    }


class ComplaintResponse(BaseModel):
    """Response schema after complaint submission."""

    message: str = Field(..., description="Success message")
    booking_id: UUID = Field(
        ...,
        description="UUID of the booking associated with this complaint",
        alias="bookingId",
    )
    timestamp: datetime = Field(..., description="Timestamp when complaint was received")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Complaint submitted successfully",
                    "bookingId": "123e4567-e89b-12d3-a456-426614174000",
                    "timestamp": "2024-01-15T10:30:00Z",
                }
            ]
        },
    }


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")

    model_config = {
        "json_schema_extra": {
            "examples": [{"status": "healthy", "service": "ComplaintService", "version": "0.1.0"}]
        }
    }

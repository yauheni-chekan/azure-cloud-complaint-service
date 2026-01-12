"""Tests for Pydantic schemas."""

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas import ComplaintRequest, ComplaintResponse, HealthResponse


class TestComplaintRequest:
    """Tests for ComplaintRequest schema."""

    def test_valid_complaint_request(self, sample_booking_id: UUID) -> None:
        """Test valid complaint request creation."""
        data = {
            "bookingId": str(sample_booking_id),
            "description": "The groomer was late.",
        }
        complaint = ComplaintRequest(**data)

        assert complaint.booking_id == sample_booking_id
        assert complaint.description == "The groomer was late."

    def test_complaint_request_with_field_name(self, sample_booking_id: UUID) -> None:
        """Test complaint request using Python field names."""
        complaint = ComplaintRequest(
            booking_id=sample_booking_id,
            description="Service was poor.",
        )

        assert complaint.booking_id == sample_booking_id
        assert complaint.description == "Service was poor."

    def test_complaint_request_invalid_uuid(self) -> None:
        """Test that invalid UUID raises validation error."""
        data = {
            "bookingId": "not-a-valid-uuid",
            "description": "Test description",
        }

        with pytest.raises(ValidationError) as exc_info:
            ComplaintRequest(**data)

        errors = exc_info.value.errors()
        # Error location uses the alias name when validation fails
        assert any(error["loc"] == ("bookingId",) for error in errors)

    def test_complaint_request_missing_booking_id(self) -> None:
        """Test that missing bookingId raises validation error."""
        data = {"description": "Test description"}

        with pytest.raises(ValidationError) as exc_info:
            ComplaintRequest(**data)

        errors = exc_info.value.errors()
        # Error location uses the alias name
        assert any(error["loc"] == ("bookingId",) for error in errors)
        assert any(error["type"] == "missing" for error in errors)

    def test_complaint_request_missing_description(self, sample_booking_id: UUID) -> None:
        """Test that missing description raises validation error."""
        data = {"bookingId": str(sample_booking_id)}

        with pytest.raises(ValidationError) as exc_info:
            ComplaintRequest(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("description",) for error in errors)

    def test_complaint_request_empty_description(self, sample_booking_id: UUID) -> None:
        """Test that empty description raises validation error."""
        data = {
            "bookingId": str(sample_booking_id),
            "description": "",
        }

        with pytest.raises(ValidationError) as exc_info:
            ComplaintRequest(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("description",) for error in errors)

    def test_complaint_request_description_too_long(self, sample_booking_id: UUID) -> None:
        """Test that description exceeding max length raises validation error."""
        data = {
            "bookingId": str(sample_booking_id),
            "description": "x" * 2001,  # Max is 2000
        }

        with pytest.raises(ValidationError) as exc_info:
            ComplaintRequest(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("description",) for error in errors)

    def test_complaint_request_serialization(self, sample_booking_id: UUID) -> None:
        """Test complaint request serialization to JSON."""
        complaint = ComplaintRequest(
            booking_id=sample_booking_id,
            description="Test complaint",
        )

        json_data = complaint.model_dump(by_alias=True, mode="json")
        assert json_data["bookingId"] == str(sample_booking_id)
        assert json_data["description"] == "Test complaint"


class TestComplaintResponse:
    """Tests for ComplaintResponse schema."""

    def test_valid_complaint_response(
        self, sample_booking_id: UUID, sample_timestamp: datetime
    ) -> None:
        """Test valid complaint response creation."""
        response = ComplaintResponse(
            message="Complaint submitted successfully",
            booking_id=sample_booking_id,
            timestamp=sample_timestamp,
        )

        assert response.message == "Complaint submitted successfully"
        assert response.booking_id == sample_booking_id
        assert response.timestamp == sample_timestamp

    def test_complaint_response_with_alias(
        self, sample_booking_id: UUID, sample_timestamp: datetime
    ) -> None:
        """Test complaint response creation using alias."""
        response = ComplaintResponse(
            message="Success",
            bookingId=sample_booking_id,
            timestamp=sample_timestamp,
        )

        assert response.booking_id == sample_booking_id

    def test_complaint_response_serialization(
        self, sample_booking_id: UUID, sample_timestamp: datetime
    ) -> None:
        """Test complaint response serialization with alias."""
        response = ComplaintResponse(
            message="Success",
            booking_id=sample_booking_id,
            timestamp=sample_timestamp,
        )

        json_data = response.model_dump(by_alias=True, mode="json")
        assert json_data["bookingId"] == str(sample_booking_id)
        assert json_data["message"] == "Success"
        assert "timestamp" in json_data

    def test_complaint_response_populate_by_name(
        self, sample_booking_id: UUID, sample_timestamp: datetime
    ) -> None:
        """Test that populate_by_name allows both field name and alias."""
        # Should work with Python field name
        response1 = ComplaintResponse(
            message="Test",
            booking_id=sample_booking_id,
            timestamp=sample_timestamp,
        )
        assert response1.booking_id == sample_booking_id

        # Should also work with alias
        response2 = ComplaintResponse(
            message="Test",
            bookingId=sample_booking_id,
            timestamp=sample_timestamp,
        )
        assert response2.booking_id == sample_booking_id


class TestHealthResponse:
    """Tests for HealthResponse schema."""

    def test_valid_health_response(self) -> None:
        """Test valid health response creation."""
        response = HealthResponse(
            status="healthy",
            service="ComplaintService",
            version="0.1.0",
        )

        assert response.status == "healthy"
        assert response.service == "ComplaintService"
        assert response.version == "0.1.0"

    def test_health_response_missing_field(self) -> None:
        """Test that missing required field raises validation error."""
        data = {"status": "healthy", "service": "ComplaintService"}

        with pytest.raises(ValidationError) as exc_info:
            HealthResponse(**data)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("version",) for error in errors)

    def test_health_response_serialization(self) -> None:
        """Test health response serialization."""
        response = HealthResponse(
            status="healthy",
            service="ComplaintService",
            version="0.1.0",
        )

        json_data = response.model_dump()
        assert json_data["status"] == "healthy"
        assert json_data["service"] == "ComplaintService"
        assert json_data["version"] == "0.1.0"

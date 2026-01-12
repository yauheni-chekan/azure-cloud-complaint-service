"""Tests for API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient


class TestComplaintsEndpoint:
    """Tests for POST /api/v1/complaints endpoint."""

    def test_create_complaint_success(
        self,
        test_client: TestClient,
        sample_complaint_data: dict[str, str],
        sample_booking_id: UUID,
        sample_timestamp: datetime,
        mocker,
    ) -> None:
        """Test successful complaint submission."""
        # Mock datetime to return fixed timestamp
        mock_dt = mocker.patch("app.api.v1.endpoints.datetime")
        mock_dt.now.return_value = sample_timestamp

        # Mock Service Bus sender
        mock_sender = AsyncMock()
        mock_sender_context = AsyncMock()
        mock_sender_context.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender_context.__aexit__ = AsyncMock(return_value=None)

        mock_client = MagicMock()
        mock_client.get_queue_sender = MagicMock(return_value=mock_sender_context)
        mock_client.close = AsyncMock()

        with patch(
            "app.services.servicebus_client.ServiceBusClient.from_connection_string"
        ) as mock_sb:
            mock_sb.return_value = mock_client

            response = test_client.post("/api/v1/complaints", json=sample_complaint_data)

        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Complaint submitted successfully"
        assert data["bookingId"] == str(sample_booking_id)
        assert "timestamp" in data

    def test_create_complaint_invalid_uuid(self, test_client: TestClient) -> None:
        """Test complaint submission with invalid UUID."""
        invalid_data = {
            "bookingId": "not-a-uuid",
            "description": "Test complaint",
        }

        response = test_client.post("/api/v1/complaints", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_complaint_missing_booking_id(self, test_client: TestClient) -> None:
        """Test complaint submission without bookingId."""
        invalid_data = {"description": "Test complaint"}

        response = test_client.post("/api/v1/complaints", json=invalid_data)

        assert response.status_code == 422

    def test_create_complaint_missing_description(
        self, test_client: TestClient, sample_booking_id: UUID
    ) -> None:
        """Test complaint submission without description."""
        invalid_data = {"bookingId": str(sample_booking_id)}

        response = test_client.post("/api/v1/complaints", json=invalid_data)

        assert response.status_code == 422

    def test_create_complaint_empty_description(
        self, test_client: TestClient, sample_booking_id: UUID
    ) -> None:
        """Test complaint submission with empty description."""
        invalid_data = {
            "bookingId": str(sample_booking_id),
            "description": "",
        }

        response = test_client.post("/api/v1/complaints", json=invalid_data)

        assert response.status_code == 422

    def test_create_complaint_description_too_long(
        self, test_client: TestClient, sample_booking_id: UUID
    ) -> None:
        """Test complaint submission with description exceeding max length."""
        invalid_data = {
            "bookingId": str(sample_booking_id),
            "description": "x" * 2001,  # Max is 2000
        }

        response = test_client.post("/api/v1/complaints", json=invalid_data)

        assert response.status_code == 422

    def test_create_complaint_servicebus_failure(
        self,
        test_client: TestClient,
        sample_complaint_data: dict[str, str],
        mocker,  # noqa: ARG002
    ) -> None:
        """Test complaint submission when Service Bus fails."""
        # Mock Service Bus to raise an exception
        mock_sender = AsyncMock()
        mock_sender.send_messages = AsyncMock(side_effect=Exception("Service Bus error"))

        mock_sender_context = AsyncMock()
        mock_sender_context.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender_context.__aexit__ = AsyncMock(return_value=None)

        mock_client = MagicMock()
        mock_client.get_queue_sender = MagicMock(return_value=mock_sender_context)
        mock_client.close = AsyncMock()

        with patch(
            "app.services.servicebus_client.ServiceBusClient.from_connection_string"
        ) as mock_sb:
            mock_sb.return_value = mock_client

            response = test_client.post("/api/v1/complaints", json=sample_complaint_data)

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Failed to submit complaint" in data["detail"]

    def test_create_complaint_invalid_json(self, test_client: TestClient) -> None:
        """Test complaint submission with malformed JSON."""
        response = test_client.post(
            "/api/v1/complaints",
            data="not json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_create_complaint_extra_fields_ignored(
        self,
        test_client: TestClient,
        sample_booking_id: UUID,
        mocker,  # noqa: ARG002
    ) -> None:
        """Test that extra fields in request are ignored."""
        mock_sender = AsyncMock()
        mock_sender_context = AsyncMock()
        mock_sender_context.__aenter__ = AsyncMock(return_value=mock_sender)
        mock_sender_context.__aexit__ = AsyncMock(return_value=None)

        mock_client = MagicMock()
        mock_client.get_queue_sender = MagicMock(return_value=mock_sender_context)
        mock_client.close = AsyncMock()

        with patch(
            "app.services.servicebus_client.ServiceBusClient.from_connection_string"
        ) as mock_sb:
            mock_sb.return_value = mock_client

            data_with_extra = {
                "bookingId": str(sample_booking_id),
                "description": "Test complaint",
                "extraField": "should be ignored",
            }

            response = test_client.post("/api/v1/complaints", json=data_with_extra)

        # Should succeed despite extra field
        assert response.status_code == 201


class TestHealthEndpoint:
    """Tests for GET /api/v1/health endpoint."""

    def test_health_check_success(self, test_client: TestClient) -> None:
        """Test health check returns correct status."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ComplaintService"
        assert data["version"] == "0.1.0"

    def test_health_check_response_structure(self, test_client: TestClient) -> None:
        """Test health check response has required fields."""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data


class TestRootEndpoint:
    """Tests for GET / root endpoint."""

    def test_root_endpoint(self, test_client: TestClient) -> None:
        """Test root endpoint returns service information."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    def test_root_endpoint_links(self, test_client: TestClient) -> None:
        """Test root endpoint provides correct links."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["docs"] == "/docs"
        assert data["health"] == "/api/v1/health"
        assert data["service"] == "ComplaintService"
        assert data["version"] == "0.1.0"


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_schema_accessible(self, test_client: TestClient) -> None:
        """Test that OpenAPI schema is accessible."""
        response = test_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_swagger_ui_accessible(self, test_client: TestClient) -> None:
        """Test that Swagger UI is accessible."""
        response = test_client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_accessible(self, test_client: TestClient) -> None:
        """Test that ReDoc is accessible."""
        response = test_client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

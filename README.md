# ComplaintService

A lightweight FastAPI microservice that receives complaint submissions and forwards them asynchronously to Azure Service Bus Queue for processing by the BookingService.

## Overview

ComplaintService is part of a pet grooming booking system. It acts as a stateless message forwarder that:
- Accepts complaint submissions via REST API
- Validates request data using Pydantic schemas
- Adds timestamps to complaints
- Forwards complaint messages to Azure Service Bus Queue (`complaints-event`)
- Returns confirmation to the client

## Architecture

```
Client → ComplaintService API → Azure Service Bus Queue → BookingService
```

The service does not store complaints in a database or validate booking IDs. It focuses solely on receiving and forwarding complaint data asynchronously.

## Features

- ✅ **FastAPI Framework** - Modern, high-performance async API
- ✅ **Pydantic Validation** - Automatic request/response validation
- ✅ **Azure Service Bus Integration** - Async message queuing
- ✅ **API Versioning** - Versioned endpoints (`/api/v1/`)
- ✅ **OpenAPI Documentation** - Auto-generated interactive docs
- ✅ **Health Check Endpoint** - Service monitoring support
- ✅ **CORS Support** - Cross-origin resource sharing
- ✅ **Structured Logging** - Comprehensive logging for debugging

## Prerequisites

- Python 3.13+
- Azure Service Bus namespace with a queue named `complaints-event`
- Service Bus connection string with Send permissions

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd azure-cloud-complaint-service
```

### 2. Install dependencies

Using pip:

```bash
pip install -e .
```

Or using uv (recommended):

```bash
uv sync
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
COMPLAINT_SEND_PRIMARY_CONNECTION_STRING=Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<key-name>;SharedAccessKey=<key>
SERVICE_BUS_QUEUE_NAME=complaints-event
DEBUG=False
```

## Usage

### Running the service

#### Development mode (with auto-reload):

```bash
uv run -m app.main
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production mode:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The service will be available at `http://localhost:8000`

### Interactive API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### POST /api/v1/complaints

Submit a complaint for a booking.

**Request Body:**

```json
{
  "bookingId": "123e4567-e89b-12d3-a456-426614174000",
  "description": "The groomer arrived 2 hours late and did not properly groom my pet."
}
```

**Response (201 Created):**

```json
{
  "message": "Complaint submitted successfully",
  "bookingId": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2024-01-15T10:30:00.123456Z"
}
```

**Validation:**
- `bookingId`: Must be a valid UUID
- `description`: Required, 1-2000 characters

**Error Responses:**
- `422 Unprocessable Entity`: Invalid request body
- `500 Internal Server Error`: Failed to send message to Service Bus

### GET /api/v1/health

Health check endpoint for monitoring.

**Response (200 OK):**

```json
{
  "status": "healthy",
  "service": "ComplaintService",
  "version": "0.1.0"
}
```

## Message Format

Messages sent to the Azure Service Bus queue have the following JSON structure:

```json
{
  "bookingId": "123e4567-e89b-12d3-a456-426614174000",
  "description": "Complaint text",
  "timestamp": "2024-01-15T10:30:00.123456Z"
}
```

## Project Structure

```
azure-cloud-complaint-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings management (Pydantic)
│   ├── schemas.py           # Pydantic models
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints.py # API v1 routes
│   └── services/
│       ├── __init__.py
│       └── servicebus_client.py # Azure Service Bus client
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared test fixtures
│   ├── test_config.py       # Configuration tests
│   ├── test_schemas.py      # Schema validation tests
│   ├── test_servicebus_client.py # Service Bus tests
│   └── test_endpoints.py    # API endpoint tests
├── .env                     # Environment variables
├── .gitignore
├── pyproject.toml           # Project dependencies
├── README.md
└── main.py                  # Legacy entry point (not used)
```

## Configuration

Configuration is managed via environment variables using Pydantic Settings:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `COMPLAINT_SEND_PRIMARY_CONNECTION_STRING` | Azure Service Bus connection string | - | Yes |
| `SERVICE_BUS_QUEUE_NAME` | Name of the Service Bus queue | `complaints-event` | No |
| `APP_NAME` | Application name | `ComplaintService` | No |
| `APP_VERSION` | Application version | `0.1.0` | No |
| `DEBUG` | Enable debug mode | `False` | No |

### CORS Configuration

The service is configured with permissive CORS settings for development:
- `allow_origins=["*"]` - Accepts requests from any origin
- `allow_credentials=False` - Credentials (cookies, auth headers) are not allowed

**For production**, you should configure CORS appropriately:

```python
# Option 1: Keep wildcard origins (no credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # Must be False with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Option 2: Specify explicit origins (with or without credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com",
    ],
    allow_credentials=True,  # Can be True with explicit origins
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Note**: The CORS specification prohibits using `allow_origins=["*"]` with `allow_credentials=True`. Modern browsers will reject this configuration.

## Development

### Running tests

Run all tests with coverage:

```bash
pytest
```

Run specific test file:

```bash
pytest tests/test_endpoints.py
```

Run with verbose output:

```bash
pytest -v
```

Generate HTML coverage report:

```bash
pytest --cov=app --cov-report=html
```

The coverage report will be available in `htmlcov/index.html`.

### Test Coverage

The test suite includes:

- **Configuration Tests** (`test_config.py`) - Settings validation and environment variable loading
- **Schema Tests** (`test_schemas.py`) - Pydantic model validation and serialization
- **Service Bus Tests** (`test_servicebus_client.py`) - Azure Service Bus integration with mocking
- **Endpoint Tests** (`test_endpoints.py`) - API endpoint behavior, validation, and error handling

Coverage goal: >90% across all modules

### Code formatting

Format code with Ruff:

```bash
ruff format .
```

### Linting

Lint code with Ruff:

```bash
ruff check .
```

Fix auto-fixable issues:

```bash
ruff check --fix .
```

### Type checking

```bash
mypy app/
```

## Deployment

### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY app/ ./app/
COPY .env .env

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t complaint-service .
docker run -p 8000:8000 complaint-service
```

### Azure App Service

1. Create an Azure App Service (Python 3.13)
2. Configure environment variables in Application Settings
3. Deploy using Azure CLI or GitHub Actions

## Monitoring

- Use the `/api/v1/health` endpoint for health checks
- Monitor Azure Service Bus metrics for queue depth and message processing
- Review application logs for errors and debugging

## Related Services

This service is part of a larger pet grooming system:

- **BookingService**: Manages bookings, users, and pets
- **GroomerService**: Manages groomer profiles and reviews
- **ComplaintService**: This service - forwards complaints to Service Bus

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please open an issue in the repository.

"""ComplaintService FastAPI application."""

import logging
from collections.abc import Generator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1 import router as v1_router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Suppress verbose Azure SDK logs (only show warnings and errors)
logging.getLogger("azure").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> Generator[None]:
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    logger.info("Service Bus Queue: %s", settings.service_bus_queue_name)
    yield
    # Shutdown
    logger.info("Shutting down %s", settings.app_name)


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Microservice for handling and forwarding complaints to Azure Service Bus",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
# NOTE: For production, either:
# 1. Use allow_origins=["*"] with allow_credentials=False (current config), OR
# 2. Specify explicit origins with allow_credentials=True, e.g.:
#    allow_origins=["https://example.com", "https://app.example.com"]
#    allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Wildcard allowed when credentials are disabled
    allow_credentials=False,  # Must be False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(v1_router, prefix="/api/v1", tags=["v1"])


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )

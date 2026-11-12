"""Health check endpoints."""

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Project imports
from app.api.dependencies import get_session
from app.schemas.common import ApiResponse, success_response
from app.services.health import check_database

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=ApiResponse[dict[str, str]], summary="Liveness probe")
def health() -> ApiResponse[dict[str, str]]:
    """Report that the process is running."""
    return success_response({"status": "ok"}, code="HEALTHY")


@router.get("/health/ready", response_model=ApiResponse[dict[str, str]], summary="Readiness probe")
def readiness(session: Session = Depends(get_session)) -> ApiResponse[dict[str, str]]:
    """Report that the database answers queries."""
    check_database(session)
    return success_response({"status": "ready", "database": "ok"}, code="READY")

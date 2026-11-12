"""Audit log endpoints."""

# Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Project imports
from app.api.dependencies import Pagination, get_admin_principal, get_pagination, get_session
from app.core.principal import Principal
from app.repositories.audit import AuditRepository
from app.schemas.audit import AuditLogRead
from app.schemas.common import ApiResponse, Page, success_response

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get(
    "",
    response_model=ApiResponse[Page[AuditLogRead]],
    summary="List the immutable audit log",
)
def list_audit_logs(
    pagination: Pagination = Depends(get_pagination),
    principal: Principal = Depends(get_admin_principal),
    session: Session = Depends(get_session),
) -> ApiResponse[Page[AuditLogRead]]:
    """Return the administrative actions recorded for the tenant, newest first."""
    repository = AuditRepository(session, principal.tenant_id)
    entries = repository.list_entries(limit=pagination.limit, offset=pagination.offset)
    total = repository.count_entries()
    page = Page[AuditLogRead](
        items=[AuditLogRead.model_validate(entry) for entry in entries],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return success_response(page, code="AUDIT_LOG_LIST")

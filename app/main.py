"""BankOS API entrypoint."""

# Standard library
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

# Third-party
from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Project imports
from app.api.dependencies import ip_limiter
from app.api.v1 import health, tenants
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.correlation import correlation_context, generate_correlation_id
from app.core.errors import BankOSError, RateLimitError
from app.core.logging import configure_logging, get_logger
from app.db.session import create_schema
from app.schemas.common import error_response, success_response

settings = get_settings()
configure_logging(settings)
logger = get_logger(__name__)

_DOCS_PREFIXES = ("/docs", "/redoc", "/openapi.json")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Create the schema before serving traffic."""
    create_schema()
    logger.info("BankOS API started", extra={"environment": settings.environment})
    yield
    logger.info("BankOS API stopped")


def create_app() -> FastAPI:
    """Build the FastAPI application with middleware and error handling."""
    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=(
            "Multi-tenant banking platform as a service. Every endpoint is scoped to the "
            "tenant encoded in the access token."
        ),
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
        openapi_tags=[
            {"name": "Authentication", "description": "Login and session profile."},
            {"name": "Tenants", "description": "Tenant registration and configuration."},
            {"name": "Users", "description": "Users of the current tenant."},
            {"name": "Accounts", "description": "Accounts, deposits and withdrawals."},
            {"name": "Transfers", "description": "Quotes and money transfers."},
            {"name": "Transactions", "description": "Transaction history."},
            {"name": "Audit", "description": "Immutable administrative audit log."},
            {"name": "Health", "description": "Liveness and readiness probes."},
        ],
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID", "X-Idempotent-Replayed"],
    )

    @application.middleware("http")
    async def correlation_and_rate_limit(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Attach a correlation id and protect the API from request floods."""
        incoming = request.headers.get("X-Correlation-ID", "").strip()
        correlation_id = incoming[:64] if incoming else generate_correlation_id()
        with correlation_context(correlation_id):
            if request.url.path.startswith(settings.api_v1_prefix) or request.url.path.startswith(
                tuple(_DOCS_PREFIXES)
            ):
                if not request.url.path.startswith(_DOCS_PREFIXES):
                    client = request.client.host if request.client else "unknown"
                    try:
                        ip_limiter.check(client)
                    except RateLimitError as exc:
                        return _error_json(exc, correlation_id)
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response

    application.include_router(health.router)
    application.include_router(tenants.router, prefix=settings.api_v1_prefix)
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.exception_handler(BankOSError)
    async def bankos_error_handler(_: Request, exc: BankOSError) -> JSONResponse:
        return _error_json(
            exc,
            error_response(code=exc.code, message=exc.message, details=exc.details).correlation_id,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(
                error_response(
                    code="VALIDATION_ERROR",
                    message="The request body or parameters are not valid",
                    details=exc.errors(),
                )
            ),
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(code="HTTP_ERROR", message=str(exc.detail)).model_dump(
                mode="json"
            ),
            headers=dict(exc.headers or {}),
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error")
        return JSONResponse(
            status_code=500,
            content=error_response(
                code="INTERNAL_ERROR", message="An unexpected error occurred"
            ).model_dump(mode="json"),
        )

    @application.get("/", tags=["Health"], summary="API index")
    def index() -> dict[str, object]:
        """Return service metadata and links."""
        return success_response(
            {
                "name": settings.app_name,
                "version": "1.0.0",
                "docs": "/docs" if settings.docs_enabled else None,
                "api": settings.api_v1_prefix,
            },
            code="SERVICE_INFO",
        ).model_dump(mode="json")

    return application


def _error_json(exc: BankOSError, correlation_id: str) -> JSONResponse:
    """Render a domain error with its headers and correlation id."""
    body = error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        correlation_id=correlation_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=body.model_dump(mode="json"),
        headers={**exc.headers, "X-Correlation-ID": correlation_id},
    )


app = create_app()

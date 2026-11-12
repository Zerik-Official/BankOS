"""Tenant registration and configuration service."""

# Standard library
import uuid
from decimal import Decimal

# Third-party
from sqlalchemy.orm import Session

# Project imports
from app.core.errors import BusinessValidationError, ConflictError, NotFoundError
from app.core.principal import Principal, ensure_admin
from app.core.security import hash_password
from app.models.enums import CommissionType, UserRole
from app.models.tenant import ExchangeRate, Tenant
from app.models.user import User
from app.repositories.tenant import ExchangeRateRepository, TenantRepository
from app.schemas.tenant import (
    ExchangeRateBulkRequest,
    ExchangeRateRead,
    TenantRead,
    TenantRegisterRequest,
    TenantRegisterResponse,
    TenantUpdateRequest,
)
from app.schemas.user import UserRead
from app.services.audit import AuditService


class TenantService:
    """Create tenants and manage their isolated configuration."""

    def __init__(self, session: Session) -> None:
        self.session: Session = session
        self.tenants: TenantRepository = TenantRepository(session)

    def get_model(self, tenant_id: uuid.UUID) -> Tenant:
        """Return an active tenant or raise a not found error."""
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant", str(tenant_id))
        return tenant

    def register(self, payload: TenantRegisterRequest) -> TenantRegisterResponse:
        """Create a tenant together with its first administrator."""
        if self.tenants.get_by_slug(payload.slug) is not None:
            raise ConflictError(
                "The tenant slug is already registered",
                code="TENANT_SLUG_TAKEN",
                details={"slug": payload.slug},
            )
        self._validate_commission(payload.commission_type, payload.commission_value)

        tenant = Tenant(
            name=payload.name,
            slug=payload.slug,
            base_currency=payload.base_currency,
            max_transaction_amount=payload.max_transaction_amount,
            commission_type=payload.commission_type,
            commission_value=payload.commission_value,
            webhook_url=payload.webhook_url,
            is_active=True,
        )
        self.session.add(tenant)
        self.session.flush()

        admin = User(
            tenant_id=tenant.id,
            email=payload.admin_email,
            full_name=payload.admin_full_name,
            password_hash=hash_password(payload.admin_password),
            role=UserRole.ADMINISTRATOR,
            is_active=True,
        )
        self.session.add(admin)
        self.session.flush()

        audit = AuditService(self.session, tenant.id)
        audit.record(
            actor_user_id=admin.id,
            action="tenant.created",
            entity_type="tenant",
            entity_id=str(tenant.id),
            new_state={"name": tenant.name, "slug": tenant.slug},
        )
        audit.record(
            actor_user_id=admin.id,
            action="user.created",
            entity_type="user",
            entity_id=str(admin.id),
            new_state={"email": admin.email, "role": admin.role.value},
        )
        self.session.commit()
        return TenantRegisterResponse(
            tenant=TenantRead.model_validate(tenant),
            admin=UserRead.model_validate(admin),
        )

    def get_current(self, principal: Principal) -> TenantRead:
        """Return the tenant of the caller."""
        return TenantRead.model_validate(self.get_model(principal.tenant_id))

    def update(self, principal: Principal, payload: TenantUpdateRequest) -> TenantRead:
        """Update the configuration of the caller tenant and audit the change."""
        ensure_admin(principal)
        tenant = self.get_model(principal.tenant_id)
        fields = payload.model_fields_set
        if not fields:
            return TenantRead.model_validate(tenant)

        previous = self._snapshot(tenant)
        commission_type = (
            payload.commission_type
            if payload.commission_type is not None
            else tenant.commission_type
        )
        commission_value = (
            payload.commission_value
            if payload.commission_value is not None
            else tenant.commission_value
        )
        self._validate_commission(commission_type, commission_value)

        if "name" in fields and payload.name is not None:
            tenant.name = payload.name
        if "base_currency" in fields and payload.base_currency is not None:
            tenant.base_currency = payload.base_currency
        if "max_transaction_amount" in fields and payload.max_transaction_amount is not None:
            tenant.max_transaction_amount = payload.max_transaction_amount
        if "commission_type" in fields and payload.commission_type is not None:
            tenant.commission_type = payload.commission_type
        if "commission_value" in fields and payload.commission_value is not None:
            tenant.commission_value = payload.commission_value
        if "webhook_url" in fields:
            tenant.webhook_url = payload.webhook_url
        if "is_active" in fields and payload.is_active is not None:
            tenant.is_active = payload.is_active

        AuditService(self.session, tenant.id).record(
            actor_user_id=principal.user_id,
            action="tenant.config.updated",
            entity_type="tenant",
            entity_id=str(tenant.id),
            previous_state=previous,
            new_state=self._snapshot(tenant),
        )
        self.session.commit()
        return TenantRead.model_validate(tenant)

    def list_rates(self, principal: Principal) -> list[ExchangeRateRead]:
        """Return the static rate table of the tenant."""
        rates = ExchangeRateRepository(self.session, principal.tenant_id).list_all()
        return [ExchangeRateRead.model_validate(rate) for rate in rates]

    def replace_rates(
        self, principal: Principal, payload: ExchangeRateBulkRequest
    ) -> list[ExchangeRateRead]:
        """Replace the static rate table of the tenant."""
        ensure_admin(principal)
        tenant = self.get_model(principal.tenant_id)
        repository = ExchangeRateRepository(self.session, tenant.id)

        pairs: set[tuple[str, str]] = set()
        for item in payload.rates:
            if item.source_currency == item.target_currency:
                raise BusinessValidationError(
                    "A currency cannot be converted to itself in the rate table",
                    code="INVALID_EXCHANGE_RATE",
                    details={"currency": item.source_currency},
                )
            pair = (item.source_currency, item.target_currency)
            if pair in pairs:
                raise BusinessValidationError(
                    "The rate table contains duplicated currency pairs",
                    code="DUPLICATE_EXCHANGE_RATE",
                    details={"pair": list(pair)},
                )
            pairs.add(pair)

        previous = [
            {
                "source_currency": rate.source_currency,
                "target_currency": rate.target_currency,
                "rate": format(Decimal(rate.rate), "f"),
            }
            for rate in repository.list_all()
        ]
        repository.delete_all()
        for item in payload.rates:
            self.session.add(
                ExchangeRate(
                    tenant_id=tenant.id,
                    source_currency=item.source_currency,
                    target_currency=item.target_currency,
                    rate=item.rate,
                )
            )
        self.session.flush()

        new_state = [
            {
                "source_currency": item.source_currency,
                "target_currency": item.target_currency,
                "rate": format(item.rate, "f"),
            }
            for item in payload.rates
        ]
        AuditService(self.session, tenant.id).record(
            actor_user_id=principal.user_id,
            action="tenant.exchange_rates.replaced",
            entity_type="tenant",
            entity_id=str(tenant.id),
            previous_state={"rates": previous},
            new_state={"rates": new_state},
        )
        self.session.commit()
        return self.list_rates(principal)

    @staticmethod
    def _validate_commission(commission_type: CommissionType, value: Decimal) -> None:
        if commission_type is CommissionType.PERCENTAGE and Decimal(value) > Decimal(100):
            raise BusinessValidationError(
                "A percentage commission cannot exceed 100",
                code="INVALID_COMMISSION",
                details={"commission_value": format(value, "f")},
            )
        if Decimal(value) < 0:
            raise BusinessValidationError(
                "The commission cannot be negative",
                code="INVALID_COMMISSION",
                details={"commission_value": format(value, "f")},
            )

    @staticmethod
    def _snapshot(tenant: Tenant) -> dict[str, object]:
        return {
            "name": tenant.name,
            "base_currency": tenant.base_currency,
            "max_transaction_amount": tenant.max_transaction_amount,
            "commission_type": tenant.commission_type,
            "commission_value": tenant.commission_value,
            "webhook_url": tenant.webhook_url,
            "is_active": tenant.is_active,
        }

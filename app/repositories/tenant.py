"""Tenant and exchange rate repositories."""

# Standard library
import uuid

# Third-party
from sqlalchemy import select
from sqlalchemy.orm import Session

# Project imports
from app.models.tenant import ExchangeRate, Tenant
from app.repositories.base import BaseRepository, TenantScopedRepository


class TenantRepository(BaseRepository[Tenant]):
    """Persistence for tenants, the only cross-tenant scoped repository."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Tenant)

    def get_by_slug(self, slug: str) -> Tenant | None:
        """Return the tenant that owns the slug."""
        return self.session.scalars(select(Tenant).where(Tenant.slug == slug)).first()


class ExchangeRateRepository(TenantScopedRepository[ExchangeRate]):
    """Static exchange rates configured by a tenant."""

    def __init__(self, session: Session, tenant_id: uuid.UUID) -> None:
        super().__init__(session, ExchangeRate, tenant_id)

    def list_all(self) -> list[ExchangeRate]:
        """Return the whole rate table of the tenant."""
        statement = (
            select(ExchangeRate)
            .where(ExchangeRate.tenant_id == self.tenant_id)
            .order_by(ExchangeRate.source_currency, ExchangeRate.target_currency)
        )
        return list(self.session.scalars(statement).all())

    def get_pair(self, source_currency: str, target_currency: str) -> ExchangeRate | None:
        """Return the configured rate for a currency pair."""
        statement = select(ExchangeRate).where(
            ExchangeRate.tenant_id == self.tenant_id,
            ExchangeRate.source_currency == source_currency,
            ExchangeRate.target_currency == target_currency,
        )
        return self.session.scalars(statement).first()

    def delete_all(self) -> None:
        """Remove every rate of the tenant before replacing the table."""
        for rate in self.list_all():
            self.session.delete(rate)
        self.session.flush()

"""Generic repository primitives."""

# Standard library
import uuid
from typing import Generic, TypeVar

# Third-party
from sqlalchemy import func, select
from sqlalchemy.orm import Session

# Project imports
from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Common persistence operations for one model."""

    def __init__(self, session: Session, model: type[ModelT]) -> None:
        self.session: Session = session
        self.model: type[ModelT] = model

    def get(self, entity_id: uuid.UUID) -> ModelT | None:
        """Return one row by primary key."""
        return self.session.get(self.model, entity_id)

    def get_all(self) -> list[ModelT]:
        """Return every row of the table."""
        return list(self.session.scalars(select(self.model)).all())

    def add(self, entity: ModelT) -> ModelT:
        """Persist a new entity and flush it."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        """Delete an entity."""
        self.session.delete(entity)

    def count(self) -> int:
        """Count every row of the table."""
        return int(self.session.scalar(select(func.count()).select_from(self.model)) or 0)


class TenantScopedRepository(BaseRepository[ModelT], Generic[ModelT]):
    """Repository that can only see rows of one tenant."""

    def __init__(self, session: Session, model: type[ModelT], tenant_id: uuid.UUID) -> None:
        super().__init__(session, model)
        self.tenant_id: uuid.UUID = tenant_id

    def get(self, entity_id: uuid.UUID) -> ModelT | None:
        """Return a row only when it belongs to the tenant."""
        statement = select(self.model).where(
            self.model.id == entity_id,  # type: ignore[attr-defined]
            self.model.tenant_id == self.tenant_id,  # type: ignore[attr-defined]
        )
        return self.session.scalars(statement).first()

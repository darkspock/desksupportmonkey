from contextvars import ContextVar
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type, Optional, List, Generator, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DisconnectionError
import logging

from core.config import settings
from core.base import Base

# Database engine configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Context variable to store the session
db_session: ContextVar[Session] = ContextVar("db_session")

# Generic type for entities
T = TypeVar('T')


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    db_session.set(db)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class DatabaseInterface(ABC):
    """Interface for database operations."""

    @abstractmethod
    def get_session(self) -> Session:
        """Get a database session."""
        pass


class SQLAlchemyDatabase(DatabaseInterface):
    """SQLAlchemy implementation with robust error handling."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_session(self) -> Session:
        try:
            return db_session.get()
        except LookupError:
            return self._create_session()

    def _create_session(self) -> Session:
        """Create a new session with error handling."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                session = SessionLocal()
                session.execute(text("SELECT 1"))
                return session
            except (OperationalError, DisconnectionError) as e:
                retry_count += 1
                self.logger.warning(
                    f"Database connection attempt {retry_count} failed: {str(e)}"
                )

                if retry_count >= max_retries:
                    self.logger.error("Max database connection retries exceeded")
                    raise

                engine.dispose()

        return SessionLocal()

    @property
    def session(self) -> Session:
        """Property to get session - used by DI container."""
        return self.get_session()

    @property
    def engine(self):
        """Expose engine for middleware access."""
        return engine


class RepositoryInterface(ABC, Generic[T]):
    """Generic interface for repositories."""

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Get all entities."""
        pass

    @abstractmethod
    def update(self, entity_id: str, entity_data: dict[str, Any]) -> Optional[T]:
        """Update an entity."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete an entity."""
        pass


class BaseRepository(RepositoryInterface[T]):
    """Base repository implementation."""

    def __init__(self, database: DatabaseInterface, model: Type[T]):
        self.database = database
        self.model = model

    def create(self, entity: T) -> T:
        session = self.database.get_session()
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return entity

    def get_by_id(self, entity_id: str) -> Optional[T]:
        session = self.database.get_session()
        return session.execute(
            select(self.model).where(self.model.id == entity_id)  # type: ignore
        ).scalar_one_or_none()

    def get_all(self) -> List[T]:
        session = self.database.get_session()
        return list(session.execute(select(self.model)).scalars().all())

    def update(self, entity_id: str, entity_data: dict[str, Any]) -> Optional[T]:
        session = self.database.get_session()
        entity = session.execute(
            select(self.model).where(self.model.id == entity_id)  # type: ignore
        ).scalar_one_or_none()
        if entity:
            for key, value in entity_data.items():
                setattr(entity, key, value)
            session.commit()
            session.refresh(entity)
            return entity
        return None

    def delete(self, entity_id: str) -> bool:
        session = self.database.get_session()
        entity = session.execute(
            select(self.model).where(self.model.id == entity_id)  # type: ignore
        ).scalar_one_or_none()
        if entity:
            session.delete(entity)
            session.commit()
            return True
        return False


# Global database instance
database = SQLAlchemyDatabase()

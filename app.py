import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from adapters.http.api.health import router as health_router
from adapters.http.api.auth.routers import router as auth_router
from adapters.http.api.companies.routers import router as companies_router
from adapters.http.api.departments.routers import router as departments_router
from adapters.http.api.users.routers import router as users_router
from adapters.http.api.assets.routers import router as assets_router
from adapters.http.api.requests.routers import router as requests_router
from adapters.http.api.my.routers import router as my_router
from adapters.http.api.dashboard.routers import router as dashboard_router
from adapters.http.ws.websocket import router as ws_router
from adapters.http.middleware.error_handler import register_error_handlers
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    application = FastAPI(
        title="DeskSupportMonkey",
        description="IT Service Desk & Asset Inventory Platform",
        version="0.1.0",
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handlers
    register_error_handlers(application)

    # Routers
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(companies_router)
    application.include_router(departments_router)
    application.include_router(users_router)
    application.include_router(assets_router)
    application.include_router(requests_router)
    application.include_router(my_router)
    application.include_router(dashboard_router)
    application.include_router(ws_router)

    @application.on_event("startup")
    async def startup():
        from sqlalchemy import create_engine, text
        try:
            engine = create_engine(settings.DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            logger.info("Database connected: %s", settings.POSTGRES_DB)
        except Exception as e:
            logger.error("Database connection failed: %s", str(e))

        # Super admin auto-creation
        _ensure_super_admin()

        # Ensure S3 reports bucket exists
        _ensure_storage_bucket()

    return application


def _ensure_super_admin() -> None:
    """Create super admin user on startup if SUPER_ADMIN_EMAIL is set."""
    super_admin_email = os.environ.get("SUPER_ADMIN_EMAIL")
    if not super_admin_email:
        return

    try:
        from core.database import SessionLocal
        from src.auth_bc.user.domain.entities import User
        from src.auth_bc.user.domain.enums import UserRole
        from src.auth_bc.user.infrastructure.repository import UserRepository

        session = SessionLocal()
        try:
            repo = UserRepository(session)
            existing = repo.find_by_email(super_admin_email)
            if existing:
                logger.info("Super admin already exists: %s", super_admin_email)
                return

            user = User.create(
                email=super_admin_email,
                role=UserRole.SUPER_ADMIN,
                company_id=None,
            )
            repo.save(user)
            session.commit()
            logger.info("Super admin created: %s", super_admin_email)
        except Exception as e:
            session.rollback()
            logger.warning("Failed to create super admin: %s", str(e))
        finally:
            session.close()
    except Exception as e:
        logger.warning("Super admin auto-creation skipped: %s", str(e))


def _ensure_storage_bucket() -> None:
    """Ensure the reports S3 bucket exists on startup."""
    try:
        from core.storage import S3StorageService
        storage = S3StorageService()
        bucket = settings.s3.S3_REPORTS_BUCKET
        if storage.ensure_bucket(bucket):
            logger.info("Storage bucket ready: %s", bucket)
        else:
            logger.warning("Failed to ensure storage bucket: %s", bucket)
    except Exception as e:
        logger.warning("Storage bucket check skipped: %s", str(e))


app = create_app()

import logging
import os

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from adapters.http.api.health import router as health_router
from adapters.http.api.auth.routers import router as auth_router
from adapters.http.api.companies.routers import router as companies_router
from adapters.http.api.departments.routers import router as departments_router
from adapters.http.api.users.routers import router as users_router
from adapters.http.api.assets.routers import router as assets_router
from adapters.http.api.requests.routers import router as requests_router
from adapters.http.api.my.routers import router as my_router
from adapters.http.api.dashboard.routers import router as dashboard_router
from adapters.http.api.registration.routers import router as registration_router
from adapters.http.api.reports.routers import router as reports_router
from adapters.http.api.auth.api_keys_router import router as api_keys_router
from adapters.http.api.employee_roles.routers import router as employee_roles_router
from adapters.http.api.equipment_profiles.routers import router as equipment_profiles_router
from adapters.http.api.settings.routers import router as settings_router
from adapters.http.api.settings.classification_router import router as classification_settings_router
from adapters.http.api.settings.procurement_routers import router as procurement_settings_router
from adapters.http.api.vendors.routers import router as vendors_router
from adapters.http.api.purchase_orders.routers import router as purchase_orders_router
from adapters.http.api.appointments.routers import router as appointments_router
from adapters.http.api.shipments.routers import router as shipments_router
from adapters.http.api.addresses.routers import router as addresses_router
from adapters.http.api.availability.routers import router as availability_router
from adapters.http.api.budgets.routers import router as budgets_router
from adapters.http.api.maintenance.routers import router as maintenance_router
from adapters.http.api.maintenance_templates.routers import (
    router as maintenance_templates_router,
)
from adapters.http.api.billing.routers import router as billing_router
from adapters.http.ws.websocket import router as ws_router
from adapters.http.middleware.error_handler import register_error_handlers
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.2,
        send_default_pii=False,
    )
    logger.info("Sentry initialized for %s", settings.ENVIRONMENT)


def create_app() -> FastAPI:
    application = FastAPI(
        title="Desk Support Monkey",
        description="IT Service Desk & Asset Inventory Platform",
        version="0.1.0",
    )

    # Security headers
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # type: ignore[override]
            response: Response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
            return response

    application.add_middleware(SecurityHeadersMiddleware)

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handlers
    register_error_handlers(application)

    # Routers
    application.include_router(health_router)
    application.include_router(auth_router)
    application.include_router(registration_router)
    application.include_router(companies_router)
    application.include_router(departments_router)
    application.include_router(users_router)
    application.include_router(assets_router)
    application.include_router(requests_router)
    application.include_router(my_router)
    application.include_router(dashboard_router)
    application.include_router(reports_router)
    application.include_router(api_keys_router)
    application.include_router(employee_roles_router)
    application.include_router(equipment_profiles_router)
    application.include_router(settings_router)
    application.include_router(classification_settings_router)
    application.include_router(procurement_settings_router)
    application.include_router(vendors_router)
    application.include_router(purchase_orders_router)
    application.include_router(appointments_router)
    application.include_router(shipments_router)
    application.include_router(addresses_router)
    application.include_router(availability_router)
    application.include_router(budgets_router)
    application.include_router(maintenance_router)
    application.include_router(maintenance_templates_router)
    application.include_router(billing_router)
    application.include_router(ws_router)

    # MCP SSE transport (conditional)
    if settings.mcp.MCP_ENABLED:
        from adapters.mcp.sse import create_sse_app
        application.mount(
            settings.mcp.MCP_SSE_PATH,
            create_sse_app(),
        )
        logger.info(
            "MCP SSE mounted at %s",
            settings.mcp.MCP_SSE_PATH,
        )

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

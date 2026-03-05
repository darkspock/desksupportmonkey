from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    MAGIC_LINK_EXPIRE_HOURS: int = 24

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class CelerySettings(BaseSettings):
    CELERY_BROKER_URL: str = "redis://localhost:6399/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6399/0"
    CELERY_TASK_TIME_LIMIT: int = 300  # 5 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 270  # 4.5 minutes

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class S3Settings(BaseSettings):
    AWS_ACCESS_KEY_ID: str = "minioadmin"
    AWS_SECRET_ACCESS_KEY: str = "minioadmin"
    AWS_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: str = "http://localhost:9002"
    S3_REPORTS_BUCKET: str = "dsm-reports"
    S3_SIGNED_URL_EXPIRY: int = 3600  # 1 hour

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class ReportSettings(BaseSettings):
    REPORT_RETENTION_DAYS: int = 365
    REPORT_MAX_RETRIES: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class AISettings(BaseSettings):
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore",
    )


class MCPSettings(BaseSettings):
    MCP_ENABLED: bool = False
    MCP_TRANSPORT: str = "stdio"
    MCP_SSE_PATH: str = "/mcp"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class StripeSettings(BaseSettings):
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""
    STRIPE_PRICE_PREMIUM: str = ""
    STRIPE_PRICE_ENTERPRISE: str = ""
    OPEN_SOURCE_MODE: bool = True
    UPGRADE_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "dsm_dev"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5444

    # Brand
    BRAND_NAME: str = "DeskSupportMonkey"
    BRAND_SHORT_NAME: str = "DS Monkey"
    BRAND_SLUG: str = "dsm"
    BRAND_LOGO_EXT: str = "png"
    BRAND_FAVICON_EXT: str = "png"
    BRAND_LOGIN_EXT: str = "png"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Email (Brevo HTTP API in production, console in dev)
    SMTP_FROM_EMAIL: str = "noreply@desksupportmonkey.com"
    SMTP_FROM_NAME: str = ""
    BREVO_API_KEY: str = ""
    ADMIN_EMAIL: str = "admin@desksupportmonkey.com"

    # Monitoring
    SENTRY_DSN: str = ""

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"
    CORS_ORIGINS: str = ""

    @property
    def smtp_from_name(self) -> str:
        return self.SMTP_FROM_NAME or self.BRAND_NAME

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS:
            return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return [self.FRONTEND_URL]

    # Auth settings (nested)
    auth: AuthSettings = AuthSettings()

    # Celery settings (nested)
    celery: CelerySettings = CelerySettings()

    # S3 settings (nested)
    s3: S3Settings = S3Settings()

    # Report settings (nested)
    report: ReportSettings = ReportSettings()

    # AI settings (nested)
    ai: AISettings = AISettings()

    # MCP settings (nested)
    mcp: MCPSettings = MCPSettings()

    # Stripe / Billing settings (nested)
    stripe: StripeSettings = StripeSettings()

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

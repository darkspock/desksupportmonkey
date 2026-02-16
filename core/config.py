from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthSettings(BaseSettings):
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    MAGIC_LINK_EXPIRE_HOURS: int = 24

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class CelerySettings(BaseSettings):
    CELERY_BROKER_URL: str = "redis://localhost:6398/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6398/0"
    CELERY_TASK_TIME_LIMIT: int = 300  # 5 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 270  # 4.5 minutes

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class S3Settings(BaseSettings):
    AWS_ACCESS_KEY_ID: str = "minioadmin"
    AWS_SECRET_ACCESS_KEY: str = "minioadmin"
    AWS_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_REPORTS_BUCKET: str = "dsm-reports"
    S3_SIGNED_URL_EXPIRY: int = 3600  # 1 hour

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class ReportSettings(BaseSettings):
    REPORT_RETENTION_DAYS: int = 365
    REPORT_MAX_RETRIES: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class Settings(BaseSettings):
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "dsm_dev"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5443

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Email settings
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1028
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@desksupportmonkey.com"
    SMTP_FROM_NAME: str = "DeskSupportMonkey"
    SMTP_USE_TLS: bool = False
    BREVO_API_KEY: str = ""

    # Frontend
    FRONTEND_URL: str = "http://localhost:5173"

    # Auth settings (nested)
    auth: AuthSettings = AuthSettings()

    # Celery settings (nested)
    celery: CelerySettings = CelerySettings()

    # S3 settings (nested)
    s3: S3Settings = S3Settings()

    # Report settings (nested)
    report: ReportSettings = ReportSettings()

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

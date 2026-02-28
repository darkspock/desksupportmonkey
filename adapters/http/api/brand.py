import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from core.config import settings

router = APIRouter(tags=["brand"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]
BRANDS_DIR = PROJECT_ROOT / "web" / "app" / "public" / "brands"

_SAFE_FILENAME = re.compile(r"^[a-zA-Z0-9_.-]+$")


@router.get("/api/v1/brand")
def get_brand_config():
    """Return brand configuration. Public — no auth required."""
    return {
        "data": {
            "name": settings.BRAND_NAME,
            "shortName": settings.BRAND_SHORT_NAME,
            "slug": settings.BRAND_SLUG,
            "logoPath": f"/api/v1/brand/assets/logo.{settings.BRAND_LOGO_EXT}",
            "faviconPath": f"/api/v1/brand/assets/favicon.{settings.BRAND_FAVICON_EXT}",
            "loginImagePath": f"/api/v1/brand/assets/brand-login.{settings.BRAND_LOGIN_EXT}",
            "themePath": "/api/v1/brand/assets/theme.css",
            "openSourceMode": settings.stripe.OPEN_SOURCE_MODE,
            "upgradeUrl": settings.stripe.UPGRADE_URL,
        }
    }


@router.get("/api/v1/brand/assets/{filename}")
def get_brand_asset(filename: str):
    """Serve a brand asset file for the configured brand. Public — no auth."""
    if not _SAFE_FILENAME.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = (BRANDS_DIR / settings.BRAND_SLUG / filename).resolve()

    # Prevent path traversal
    if not str(filepath).startswith(str(BRANDS_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")

    if not filepath.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")

    return FileResponse(filepath)

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class CreateReportRequest(BaseModel):
    type: str
    parameters: Optional[dict[str, Any]] = None


class ReportResponse(BaseModel):
    id: str
    type: str
    status: str
    parameters: Optional[dict[str, Any]] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ReportListItemResponse(BaseModel):
    id: str
    type: str
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DownloadResponse(BaseModel):
    download_url: str

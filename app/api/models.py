"""API Request and Response Models."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ConvertRequest(BaseModel):
    source_path: str
    target_format: str
    output_destination: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    overwrite_policy: Optional[str] = "rename"


class BatchConvertRequest(BaseModel):
    items: List[ConvertRequest]


class CancelJobResponse(BaseModel):
    job_id: str
    cancelled: bool
    message: str


class SettingsUpdateRequest(BaseModel):
    theme: Optional[str] = None
    default_output_dir: Optional[str] = None
    overwrite_policy: Optional[str] = None
    max_workers: Optional[int] = None
    history_retention_days: Optional[int] = None
    custom_ffmpeg_path: Optional[str] = None
    custom_pandoc_path: Optional[str] = None
    custom_libreoffice_path: Optional[str] = None

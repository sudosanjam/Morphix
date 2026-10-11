"""FastAPI route handlers for Morphix."""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, JSONResponse

from app.config import config, VERSION, APP_NAME
from app.core.registry import registry
from app.core.detector import detect_file_format, canonical_format
from app.core.metadata import inspect_file
from app.core.jobs import jobs, JobState
from app.services.history import history
from app.services.presets import presets
from app.services.diagnostics import run_diagnostics
from app.api.models import ConvertRequest, BatchConvertRequest, SettingsUpdateRequest

router = APIRouter()


@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "app": APP_NAME,
        "version": VERSION,
        "offline": True
    }


@router.get("/capabilities")
def get_capabilities():
    """Return all formats, families, engines, and routes."""
    return {
        "formats": registry.get_all_supported_formats(),
        "engines": registry.get_engine_statuses(),
        "routes": [
            {
                "id": r.id,
                "engine": r.engine_name,
                "source_formats": r.source_formats,
                "target_formats": r.target_formats,
                "lossiness": r.lossiness,
                "metadata_preservation": r.metadata_preservation,
                "potential_info_loss": r.potential_info_loss,
                "warnings": r.warnings,
                "available": r.is_available(),
                "settings_schema": {
                    k: v.model_dump() for k, v in r.settings_schema.items()
                }
            }
            for r in registry.routes
        ]
    }


@router.get("/capabilities/targets")
def get_targets_for_format(source_format: str):
    """Return valid targets and settings for a given source format."""
    targets = registry.get_available_targets(source_format)
    return {"source_format": source_format, "targets": targets}


@router.post("/inspect")
def inspect_file_endpoint(path: str = Form(...)):
    """Inspect local file metadata."""
    file_p = Path(path).resolve()
    if not file_p.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    try:
        data = inspect_file(file_p)
        # Also include available target formats
        data["available_targets"] = registry.get_available_targets(data["format"])
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload")
async def upload_file_endpoint(file: UploadFile = File(...)):
    """Upload a file to the local temp directory for processing."""
    # Clean filename
    safe_name = Path(file.filename or "upload.bin").name
    temp_dir = config.temp_dir / "uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / safe_name

    # Handle collisions
    if temp_file.exists():
        import uuid
        temp_file = temp_dir / f"{temp_file.stem}_{uuid.uuid4().hex[:6]}{temp_file.suffix}"

    with open(temp_file, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    try:
        meta = inspect_file(temp_file)
        meta["available_targets"] = registry.get_available_targets(meta["format"])
        return {
            "uploaded": True,
            "path": str(temp_file),
            "filename": temp_file.name,
            "metadata": meta
        }
    except Exception as e:
        return {
            "uploaded": True,
            "path": str(temp_file),
            "filename": temp_file.name,
            "metadata": {"format": "unknown", "error": str(e), "available_targets": []}
        }


@router.post("/convert")
def submit_convert_job(req: ConvertRequest):
    """Queue a single conversion job."""
    src = Path(req.source_path).resolve()
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"Source file not found: {src}")

    job = jobs.submit_job(
        source_path=src,
        target_format=req.target_format,
        output_destination=req.output_destination,
        settings=req.settings,
        overwrite_policy=req.overwrite_policy
    )
    return job.model_dump()


@router.post("/batch")
def submit_batch_convert_jobs(req: BatchConvertRequest):
    """Queue multiple conversion jobs."""
    submitted = []
    for item in req.items:
        src = Path(item.source_path).resolve()
        if src.exists():
            job = jobs.submit_job(
                source_path=src,
                target_format=item.target_format,
                output_destination=item.output_destination,
                settings=item.settings,
                overwrite_policy=item.overwrite_policy
            )
            submitted.append(job.model_dump())
    return {"submitted_count": len(submitted), "jobs": submitted}


@router.get("/jobs")
def list_jobs_endpoint():
    """List all current in-memory jobs."""
    return [j.model_dump() for j in jobs.list_jobs()]


@router.get("/jobs/{job_id}")
def get_job_endpoint(job_id: str):
    """Get single job status and progress."""
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.model_dump()


@router.post("/jobs/{job_id}/cancel")
def cancel_job_endpoint(job_id: str):
    """Cancel a running or pending conversion job."""
    success = jobs.cancel_job(job_id)
    return {
        "job_id": job_id,
        "cancelled": success,
        "message": "Job cancellation initiated" if success else "Job could not be cancelled"
    }


@router.get("/jobs/{job_id}/download")
def download_job_output(job_id: str):
    """Download converted output file."""
    job = jobs.get_job(job_id)
    if not job or not job.target_path:
        raise HTTPException(status_code=404, detail="Job or output not found")

    p = Path(job.target_path).resolve()
    if not p.exists():
        raise HTTPException(status_code=404, detail="Output file does not exist on disk")

    return FileResponse(
        path=str(p),
        filename=p.name,
        media_type="application/octet-stream"
    )


@router.post("/open-folder")
def open_folder_endpoint(path: str = Form(...)):
    """Open folder in Windows Explorer or Linux file manager."""
    p = Path(path).resolve()
    target_dir = p.parent if p.is_file() else p
    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Directory not found")

    try:
        if sys.platform == "win32":
            if p.is_file() and p.exists():
                subprocess.Popen(f'explorer /select,"{p}"', shell=False)
            else:
                os.startfile(str(target_dir))
        else:
            subprocess.Popen(["xdg-open", str(target_dir)])
        return {"opened": True, "path": str(target_dir)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open directory: {str(e)}")


@router.get("/history")
def get_history_endpoint(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    search: Optional[str] = None
):
    return history.list_history(limit=limit, offset=offset, status=status, search=search)


@router.delete("/history")
def clear_history_endpoint():
    count = history.clear_history()
    return {"cleared": count}


@router.get("/presets")
def list_presets_endpoint(category: Optional[str] = None):
    return [p.model_dump() for p in presets.list_presets(category=category)]


@router.post("/presets")
def create_preset_endpoint(preset_data: Dict[str, Any]):
    p = presets.create_preset(
        name=preset_data["name"],
        description=preset_data.get("description", ""),
        category=preset_data.get("category", "image"),
        target_format=preset_data["target_format"],
        settings=preset_data.get("settings", {})
    )
    return p.model_dump()


@router.delete("/presets/{preset_id}")
def delete_preset_endpoint(preset_id: str):
    success = presets.delete_preset(preset_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete preset (preset not found or is built-in)")
    return {"deleted": True}


@router.get("/diagnostics")
def get_diagnostics_endpoint():
    return run_diagnostics()


@router.get("/settings")
def get_settings_endpoint():
    return config.settings.model_dump()


@router.post("/settings")
def update_settings_endpoint(req: SettingsUpdateRequest):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    new_settings = config.update_settings(updates)
    return new_settings.model_dump()


@router.post("/settings/clean-temp")
def clean_temp_endpoint():
    cleaned = config.clean_temp_files()
    return {"cleaned_files_count": cleaned}

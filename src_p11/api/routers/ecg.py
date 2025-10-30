"""
ECG processing API router.
Handles the /ecg/process-inline endpoint for image processing.
"""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from api.dependencies import (
    get_settings,
    get_storage_root,
    validate_content_type,
    validate_file_size,
)
from ecgcourse.pipeline.image_ingest import process_image
from persistence.storage import get_storage

router = APIRouter()


@router.post("/process-inline")
async def process_inline(
    file: UploadFile = File(..., description="ECG image file (PNG/JPEG)"),
    deskew: bool = Form(False, description="Apply rotation correction"),
    normalize: bool = Form(False, description="Normalize scale for px/mm ~10"),
    auto_grid: bool = Form(False, description="Enable automatic grid detection and segmentation"),
    rpeaks_lead: Optional[str] = Form(None, description="Lead for R-peak detection (e.g., II, V2)"),
    rpeaks_robust: bool = Form(
        False, description="Use robust R-peak detection (Pan-Tompkins-like)"
    ),
    intervals: bool = Form(False, description="Calculate PR/QRS/QT/QTc intervals"),
    sexo: Optional[str] = Form(None, description="Patient sex (M/F) for QTc thresholds"),
    persist: bool = Query(False, description="Save report to persistent storage"),
    compact: bool = Query(False, description="Return compact response (exclude full report)"),
):
    """
    Process ECG image inline and return structured report.

    Accepts multipart form with image file and processing parameters.
    Returns JSON with full report and summary, or compact response.

    With persist=true, saves report and returns report_id for later retrieval.
    """
    settings = get_settings()

    # Validate file size
    if file.size and not validate_file_size(file.size):
        raise HTTPException(
            status_code=413, detail=f"File too large. Maximum size: {settings.max_file_mb}MB"
        )

    # Validate content type
    if not validate_content_type(file.content_type or ""):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. "
            f"Supported: {', '.join(settings.supported_formats)}",
        )

    try:
        # Read file data
        file_data = await file.read()

        # Additional size check after reading (in case content-length was missing)
        if not validate_file_size(len(file_data)):
            raise HTTPException(
                status_code=413, detail=f"File too large. Maximum size: {settings.max_file_mb}MB"
            )

        # Process image using pure function
        report = process_image(
            image_data=file_data,
            deskew=deskew,
            normalize=normalize,
            auto_grid=auto_grid,
            rpeaks_lead=rpeaks_lead,
            rpeaks_robust=rpeaks_robust,
            intervals=intervals,
            sexo=sexo,
            schema_version="0.4.0",
        )

        # Create summary
        summary = {
            "version": report["version"],
            "capabilities": report["capabilities"],
            "fc_bpm": report["measures"].get("fc_bpm"),
            "flags_count": len(report["flags"]),
            "processing_successful": len(
                [f for f in report["flags"] if "unavailable" in f or "failed" in f]
            )
            == 0,
        }

        response_data = {"summary": summary}

        # Handle persistence
        if persist:
            storage = get_storage(get_storage_root())
            report_id = storage.save_report(report)
            response_data["report_id"] = report_id
            response_data["message"] = "Report saved successfully"

        # Include full report unless compact mode requested
        if not compact:
            response_data["report"] = report

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        # Log error in production but don't expose internal details
        logging.error(f"Image processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Image processing failed")

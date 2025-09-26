"""
Reports API router.
Handles listing and retrieving stored ECG reports.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Any

from api.dependencies import get_storage_root
from persistence.storage import get_storage

router = APIRouter()

@router.get("/list")
async def list_reports(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of reports to return"),
    offset: int = Query(0, ge=0, description="Number of reports to skip")
):
    """
    List stored ECG reports with pagination.
    
    Returns lightweight metadata (id, created_at, capabilities, fc_bpm if present).
    Results are sorted by creation time (newest first).
    """
    try:
        storage = get_storage(get_storage_root())
        reports, total_count = storage.list_reports(limit=limit, offset=offset)
        
        return JSONResponse(
            status_code=200,
            content={
                "reports": reports,
                "pagination": {
                    "limit": limit,
                    "offset": offset, 
                    "total": total_count,
                    "has_more": offset + len(reports) < total_count
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list reports: {str(e)}"
        )

@router.get("/{report_id}")
async def get_report(report_id: str):
    """
    Retrieve a specific ECG report by ID.
    
    Returns the complete report object as originally stored.
    """
    try:
        storage = get_storage(get_storage_root())
        report = storage.get_report(report_id)
        
        if report is None:
            raise HTTPException(
                status_code=404,
                detail=f"Report not found: {report_id}"
            )
        
        return JSONResponse(
            status_code=200,
            content=report
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve report: {str(e)}"
        )
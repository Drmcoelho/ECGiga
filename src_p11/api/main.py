#!/usr/bin/env python3
"""
FastAPI main application for ECG Course API.
Phase 4 - PR B: JSON Persistence + Functional Ingest Endpoint
"""

from fastapi import FastAPI

from api.routers import ecg, reports

app = FastAPI(
    title="ECG Course API",
    description="API for ECG image processing and report management",
    version="0.4.0",
)

app.include_router(ecg.router, prefix="/ecg", tags=["ECG Processing"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])


@app.get("/")
async def root():
    return {
        "service": "ECG Course API",
        "version": "0.4.0",
        "description": "ECG image processing and report management",
        "endpoints": {
            "ecg_process": "/ecg/process-inline",
            "reports_list": "/reports/list",
            "report_get": "/reports/{report_id}",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.4.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

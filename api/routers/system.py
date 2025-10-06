"""System endpoints: health and version information."""
import shutil
from typing import Dict, Any, List
from fastapi import APIRouter

from api.dependencies import get_config

router = APIRouter(
    prefix="",
    tags=["system"]
)


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.
    
    Returns basic service status and capabilities.
    """
    # Check if tesseract is available (optional OCR dependency)
    tesseract_available = shutil.which("tesseract") is not None
    
    # Get basic config
    config = get_config()
    
    return {
        "status": "ok",
        "tesseract": tesseract_available,
        "api_key_configured": config["api_key_configured"]
    }


@router.get("/version")
async def version_info() -> Dict[str, Any]:
    """Version information endpoint.
    
    Returns application version and supported schema versions.
    """
    # Read version from VERSION file
    try:
        with open("VERSION", "r") as f:
            app_version = f.read().strip()
    except FileNotFoundError:
        app_version = "0.0.0-dev"
    
    # Supported schema versions based on reporting/schema/ files
    schema_supported = ["0.2.0", "0.3.0", "0.4.0", "0.5.0"]
    
    return {
        "app_version": app_version,
        "schema_supported": schema_supported
    }
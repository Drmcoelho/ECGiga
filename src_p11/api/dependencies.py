"""
API dependencies and configuration management.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Storage configuration
    ecg_storage_root: str = "storage/"
    
    # File upload limits
    max_file_mb: int = 8
    
    # Supported image formats
    supported_formats: list = ["image/png", "image/jpeg", "image/jpg"]
    
    model_config = {"env_file": ".env"}

_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def get_storage_root() -> Path:
    """Get the storage root directory as Path object."""
    settings = get_settings()
    storage_path = Path(settings.ecg_storage_root)
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path

def validate_file_size(content_length: int) -> bool:
    """Validate file size against configured maximum."""
    settings = get_settings()
    max_bytes = settings.max_file_mb * 1024 * 1024
    return content_length <= max_bytes

def validate_content_type(content_type: str) -> bool:
    """Validate file content type against supported formats."""
    settings = get_settings()
    return content_type.lower() in [fmt.lower() for fmt in settings.supported_formats]
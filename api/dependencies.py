"""API dependencies and shared functionality."""
import os
from typing import Optional


def get_api_key() -> Optional[str]:
    """Get API key from environment variables.
    
    Returns:
        API key if configured, None otherwise.
    """
    return os.getenv("API_KEY")


def get_config() -> dict:
    """Get basic configuration for the API.
    
    Returns:
        Configuration dictionary.
    """
    return {
        "api_key_configured": get_api_key() is not None
    }
"""FastAPI main application."""
from fastapi import FastAPI

from api.routers import system


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="ECGiga API",
        description="ECG analysis and educational platform API",
        version="0.0.0-p0"
    )
    
    # Include routers
    app.include_router(system.router)
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
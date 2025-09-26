# API Reference

## Overview

This document describes the ECGiga FastAPI application, which provides a REST API for ECG analysis and educational platform functionality.

**Status:** Phase 4 (Phase 4A baseline implemented)

## Running the API Locally

To start the API server locally:

```bash
uvicorn api.main:app --reload
```

The API will be available at: http://127.0.0.1:8000

Interactive API documentation will be available at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Phase 4 Roadmap

### Phase 4A (Current) - Baseline
- ✅ Basic FastAPI application structure
- ✅ System endpoints (`/health`, `/version`)
- ✅ Environment-driven config
- ✅ Basic test coverage

### Upcoming Phases
- **Phase 4B**: Persistence layer and ingest endpoints
- **Phase 4C**: Refactored ingest pipeline integration
- **Phase 4D**: Dynamic quiz endpoints with progress persistence
- **Phase 4E**: Plugin registry and endpoint
- **Phase 4F**: Export functionality (Markdown/FHIR)
- **Phase 4G**: Authentication, metrics, and CLI integration
- **Phase 4H**: Async job handling and hardening

## Current Endpoints

### System Endpoints

#### GET /health
Health check endpoint that returns service status and capabilities.

**Response:**
```json
{
    "status": "ok",
    "tesseract": true,
    "api_key_configured": false
}
```

#### GET /version
Returns application version and supported schema versions.

**Response:**
```json
{
    "app_version": "0.0.0-p0",
    "schema_supported": ["0.2.0", "0.3.0", "0.4.0", "0.5.0"]
}
```

## Configuration

The API supports basic environment-driven configuration:

- `API_KEY`: Optional API key (placeholder for future authentication)

## Dependencies

- **FastAPI**: >=0.111.0 - Web framework
- **Uvicorn**: >=0.30.0 - ASGI server
- **pytesseract**: Optional OCR capability (detected in health endpoint)

## Testing

Run the API tests:

```bash
pytest tests_api/ -v
```
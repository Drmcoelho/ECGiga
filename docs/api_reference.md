# ECGiga — API Reference

## Overview

The ECGiga MCP (Model Context Protocol) server exposes a set of RESTful
endpoints via FastAPI.  The server runs on port **8000** by default and
provides tools for ECG analysis, quiz validation, and report generation.

Base URL: `http://localhost:8000`

---

## Authentication

All protected endpoints require a Bearer token in the `Authorization` header.

```
Authorization: Bearer <token>
```

Tokens are obtained via the `/auth/login` endpoint and are valid for 24 hours.

### `POST /auth/register`

Create a new user account.

**Request body:**

```json
{
  "username": "dr_silva",
  "email": "silva@hospital.br",
  "password": "secure-password-123"
}
```

**Response (201):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "dr_silva",
  "email": "silva@hospital.br",
  "created_at": "2025-01-15T10:30:00+00:00"
}
```

### `POST /auth/login`

Authenticate and receive a token.

**Request body:**

```json
{
  "username": "dr_silva",
  "password": "secure-password-123"
}
```

**Response (200):**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "expires_in": 86400
}
```

**Error (401):**

```json
{
  "detail": "Invalid credentials"
}
```

---

## MCP Tool Endpoints

### `POST /tools/quiz_validate`

Validate a quiz answer and return feedback.

**Request body:**

```json
{
  "question_id": "arrhythmia_001",
  "selected_answer": "B",
  "quiz_bank": "arritmias"
}
```

**Response (200):**

```json
{
  "correct": true,
  "explanation": "Correto! A fibrilação atrial é caracterizada por...",
  "explanation_camera": "Na analogia da câmera, a FA é como uma câmera tremendo...",
  "score_delta": 1
}
```

### `POST /tools/analyze_intervals`

Analyze ECG intervals from extracted values.

**Request body:**

```json
{
  "rr_intervals_ms": [820, 830, 815, 840],
  "pr_ms": 160,
  "qrs_ms": 88,
  "qt_ms": 380
}
```

**Response (200):**

```json
{
  "heart_rate_bpm": 73,
  "rhythm": "sinusal_regular",
  "pr_status": "normal",
  "qrs_status": "normal",
  "qtc_bazett": 382,
  "qtc_fridericia": 375,
  "qt_status": "normal",
  "flags": [],
  "interpretation_pt": "Ritmo sinusal regular, intervalos normais.",
  "camera_analogy_pt": "A câmera está funcionando normalmente..."
}
```

### `POST /tools/ecg_image_process`

Process an uploaded ECG image.

**Request body (multipart/form-data):**

| Field     | Type   | Description                          |
|-----------|--------|--------------------------------------|
| `file`    | file   | ECG image (PNG, JPEG, TIFF)          |
| `layout`  | string | Layout hint: "12lead", "single", "rhythm" |

**Response (200):**

```json
{
  "status": "success",
  "grid_detected": true,
  "scale": {"mm_per_px_x": 0.25, "mm_per_px_y": 0.1},
  "leads_detected": 12,
  "traces": {
    "II": {"peaks_idx": [100, 350, 600], "rr_sec": [1.0, 1.0]}
  },
  "intervals": {
    "PR_ms": 160,
    "QRS_ms": 90,
    "QT_ms": 380,
    "QTc_B": 380
  },
  "axis": {"angle_deg": 60, "label": "Normal"},
  "report_id": "abc123"
}
```

### `POST /tools/generate_ecg`

Generate a synthetic ECG with specified parameters.

**Request body:**

```json
{
  "hr_bpm": 72,
  "pr_ms": 160,
  "qrs_ms": 90,
  "qt_ms": 380,
  "axis_deg": 60,
  "pathology": null,
  "duration_s": 10,
  "format": "plotly_json"
}
```

**Response (200):**

```json
{
  "params": {"hr_bpm": 72, "pr_ms": 160, "...": "..."},
  "leads": {"I": [0.01, 0.02, "..."], "II": ["..."]},
  "plotly_figure": {"data": ["..."], "layout": {"..."}}
}
```

### `POST /tools/simulate_drug`

Simulate a drug's effect on ECG.

**Request body:**

```json
{
  "drug_name": "amiodarona",
  "baseline_hr": 72
}
```

**Response (200):**

```json
{
  "drug": "amiodarona",
  "effects": {
    "qt_prolongation": true,
    "pr_prolongation": true,
    "hr_decrease": true
  },
  "description_pt": "Amiodarona: antiarrítmico classe III...",
  "camera_analogy": "Múltiplos filtros na lente...",
  "modified_ecg_leads": {"I": ["..."], "II": ["..."]}
}
```

### `POST /tools/check_interactions`

Check drug interactions affecting the ECG.

**Request body:**

```json
{
  "drugs": ["amiodarona", "fluoroquinolona", "haloperidol"]
}
```

**Response (200):**

```json
{
  "warnings": [
    "⚠ ALTO RISCO: Múltiplas drogas que prolongam o QT..."
  ],
  "risk_level": "high",
  "recommendation_pt": "Monitorar ECG continuamente. Considerar ECG de 12 derivações a cada 8h."
}
```

---

## SSE (Server-Sent Events) Endpoint

### `GET /sse`

Establish a Server-Sent Events connection for real-time updates.

**Event types:**

| Event          | Description                                    |
|----------------|------------------------------------------------|
| `hello`        | Connection established                         |
| `analysis`     | Real-time analysis progress                    |
| `quiz_update`  | Quiz score updates                             |
| `ecg_stream`   | Streaming ECG data for real-time display        |

**Example event:**

```
event: analysis
data: {"status": "processing", "step": "grid_detection", "progress": 0.3}
```

---

## Health Check

### `GET /health`

Returns server health status.  Used by Docker health checks and load balancers.

**Response (200):**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "uptime_seconds": 3600
}
```

---

## Error Codes

| HTTP Code | Meaning                | Common Causes                              |
|-----------|------------------------|--------------------------------------------|
| 400       | Bad Request            | Missing required fields, invalid parameters |
| 401       | Unauthorized           | Missing or expired token                    |
| 403       | Forbidden              | Insufficient permissions                    |
| 404       | Not Found              | Unknown endpoint or resource                |
| 413       | Payload Too Large      | Image file exceeds 20 MB limit              |
| 422       | Unprocessable Entity   | Valid JSON but failed schema validation     |
| 429       | Too Many Requests      | Rate limit exceeded (100 req/min)           |
| 500       | Internal Server Error  | Unexpected server-side failure              |

**Error response format:**

```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE",
  "field": "optional_field_name"
}
```

---

## Rate Limiting

- **Unauthenticated:** 20 requests/minute
- **Authenticated:** 100 requests/minute
- **Image upload:** 10 requests/minute

Rate limit headers are included in every response:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705312800
```

---

## Data Formats

### ECG Values

All ECG measurements follow these conventions:

- **Time intervals:** milliseconds (ms)
- **Voltage:** millivolts (mV)
- **Heart rate:** beats per minute (bpm)
- **Axis:** degrees (-180 to +180)
- **Sampling rate:** Hz (default 500 Hz for generated ECGs)

### Lead Names

Standard 12-lead nomenclature:
`I`, `II`, `III`, `aVR`, `aVL`, `aVF`, `V1`, `V2`, `V3`, `V4`, `V5`, `V6`

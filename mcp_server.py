"""
Skeleton MCP server for ECGiga tools.

This FastAPI application provides a minimal prototype of the MCP
server described in the project instructions.  It exposes three
placeholder tools — `quiz_validate`, `analyze_intervals` and
`ecg_image_process` — and an SSE endpoint at `/sse`.  All tool
endpoints currently return a stubbed response indicating that the
feature is not yet implemented.  The SSE endpoint emits a single
"hello" event to establish a connection.  This file is intended as
scaffolding to unblock early integration work; it does not attempt
to fully implement the MCP specification or the underlying business
logic.  Extend or replace these stubs with the real implementations
as the project progresses.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import AsyncGenerator, Dict, List, Any
import json

# Additional imports for tool implementations
import os
import math
import requests
import jsonschema
from jsonschema import ValidationError

app = FastAPI(title="ECGiga MCP Server", version="0.1.0")


def sse_event(event: str, data: Any) -> str:
    """Serialize a Server‑Sent Events (SSE) message.

    Parameters
    ----------
    event: str
        Name of the SSE event.
    data: Any
        JSON‑serializable payload.

    Returns
    -------
    str
        A formatted SSE message string.
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/sse")
async def sse_endpoint() -> StreamingResponse:
    """Minimal Server‑Sent Events endpoint.

    This yields a single "hello" event to signal that the server is
    alive.  In a full implementation this endpoint would produce
    continuous updates or handshake messages as required by the MCP
    protocol.  Clients must set the `Accept` header to
    `text/event-stream` when connecting.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        # Yield a single handshake event then complete.
        yield sse_event("hello", {"message": "MCP server skeleton ready"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class QuizValidateInput(BaseModel):
    """Input schema for the quiz_validate tool.

    Parameters
    ----------
    path: str
        Path to the quiz file to validate.  This could be a JSON
        file containing multiple choice questions and their
        metadata.
    """

    path: str = Field(..., description="Path to the quiz JSON file")


class QuizValidateOutput(BaseModel):
    """Output schema for the quiz_validate tool."""

    valid: bool
    errors: List[str]


@app.post("/quiz_validate", response_model=QuizValidateOutput)
async def quiz_validate(data: QuizValidateInput) -> QuizValidateOutput:
    """
    Validate a quiz bank against the MCQ schema defined in
    ``quiz/schema/mcq.schema.json``.

    The function accepts a path that can be either a local file path
    or an HTTP(S) URL.  It attempts to load the JSON content and
    validate each question entry against the predefined schema.  The
    schema is inlined here to avoid external file dependencies.  If
    any validation errors occur they are collected and returned.
    """
    errors: List[str] = []
    valid = True

    # Inline MCQ schema (draft 2020‑12) for validation
    mcq_schema: Dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "ECG MCQ",
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "topic": {"type": "string"},
            "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
            "stem": {"type": "string"},
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2
            },
            "answer_index": {"type": "integer", "minimum": 0},
            "explanation": {"type": "string"}
        },
        "required": [
            "id", "topic", "difficulty", "stem", "options", "answer_index", "explanation"
        ]
    }

    try:
        # Load JSON content from file or URL
        if data.path.startswith("http://") or data.path.startswith("https://"):
            resp = requests.get(data.path)
            resp.raise_for_status()
            content = resp.text
        else:
            # Expand user (~) and check file exists
            file_path = os.path.expanduser(data.path)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

        # Parse JSON
        quiz_data = json.loads(content)

        # Determine the list of items to validate
        if isinstance(quiz_data, dict) and "questions" in quiz_data:
            items = quiz_data["questions"]
        elif isinstance(quiz_data, list):
            items = quiz_data
        else:
            items = [quiz_data]

        # Validate each item against the schema
        for idx, item in enumerate(items):
            try:
                jsonschema.validate(instance=item, schema=mcq_schema)
            except ValidationError as ve:
                valid = False
                # Include index to help locate invalid item
                errors.append(f"item {idx}: {ve.message}")
    except Exception as e:
        valid = False
        errors.append(str(e))

    return QuizValidateOutput(valid=valid, errors=errors)


class AnalyzeIntervalsInput(BaseModel):
    """Input schema for the analyze_intervals tool."""

    pr_ms: float = Field(..., description="PR interval (ms)")
    qrs_ms: float = Field(..., description="QRS duration (ms)")
    qt_ms: float = Field(..., description="QT interval (ms)")
    rr_ms: float = Field(..., description="RR interval (ms)")


class AnalyzeIntervalsOutput(BaseModel):
    """Output schema for the analyze_intervals tool."""

    qtc_ms: float
    flags: List[str]
    explanation: str


@app.post("/analyze_intervals", response_model=AnalyzeIntervalsOutput)
async def analyze_intervals(data: AnalyzeIntervalsInput) -> AnalyzeIntervalsOutput:
    """
    Analyze cardiac intervals and calculate QTc (Bazett) with basic
    clinical flagging.

    Given PR, QRS, QT and RR intervals (in milliseconds), the
    corrected QT is calculated using Bazett's formula.  Flags are
    appended based on simple threshold rules:

      - PR > 200 ms → first‑degree AV block
      - PR < 120 ms and QRS < 120 ms → possible pre‑excitation
      - QRS ≥ 120 ms → complete bundle branch block/ventricular origin
      - QRS 110–119 ms → incomplete bundle branch block
      - QTc ≥ 460 ms → prolonged QT
      - QTc < 350 ms → short QT

    The explanation string concatenates all flags for human readability.
    """
    pr_ms = data.pr_ms
    qrs_ms = data.qrs_ms
    qt_ms = data.qt_ms
    rr_ms = data.rr_ms

    # Compute QTc using Bazett formula (ms)
    try:
        rr_sec = rr_ms / 1000.0
        qtc_ms = qt_ms / math.sqrt(rr_sec) if rr_sec > 0 else float("nan")
    except Exception:
        qtc_ms = float("nan")

    flags: List[str] = []

    # Flagging rules
    if pr_ms is not None:
        if pr_ms > 200:
            flags.append("PR > 200 ms: possível BAV de 1º grau")
        elif pr_ms < 120 and (qrs_ms is None or qrs_ms < 120):
            flags.append("PR < 120 ms: considerar pré‑excitação")

    if qrs_ms is not None:
        if qrs_ms >= 120:
            flags.append("QRS ≥ 120 ms: possível bloqueio de ramo completo/origem ventricular")
        elif 110 <= qrs_ms < 120:
            flags.append("QRS 110–119 ms: possível bloqueio de ramo incompleto")

    # QTc thresholds (sex‑agnostic, conservative)
    if not math.isnan(qtc_ms):
        if qtc_ms >= 460:
            flags.append("QTc prolongado (≥460 ms)")
        elif qtc_ms < 350:
            flags.append("QTc possivelmente curto (<350 ms)")

    explanation = "; ".join(flags) if flags else "Intervalos dentro de limites de referência"

    return AnalyzeIntervalsOutput(
        qtc_ms=qtc_ms,
        flags=flags,
        explanation=explanation,
    )


class ECGImageProcessInput(BaseModel):
    """Input schema for the ecg_image_process tool."""

    image_url: str = Field(..., description="URL of the ECG image to process")
    ops: List[str] = Field(..., description="List of operations to apply, e.g. deskew, normalize, rpeaks")


class ECGImageProcessOutput(BaseModel):
    """Output schema for the ecg_image_process tool."""

    report: Dict[str, Any]


@app.post("/ecg_image_process", response_model=ECGImageProcessOutput)
async def ecg_image_process(data: ECGImageProcessInput) -> ECGImageProcessOutput:
    """
    Process an ECG image and return a structured report.

    This simplified implementation fetches the image from the provided
    URL and performs very limited processing.  If ``normalize`` is
    requested (i.e., 'normalize' present in ``ops``), the image is
    converted to grayscale.  For any other operations the function
    returns a placeholder flag indicating that the feature is not
    implemented.  The returned report contains basic metadata and
    echoes back the operations requested.

    Note: This function does not perform any deskew, segmentation,
    R‑peak detection or interval measurements.  Extend this stub with
    calls into your computer vision pipeline for full functionality.
    """
    report: Dict[str, Any] = {
        "meta": {
            "source": "ecg_image_process_stub",
            "fetched_url": data.image_url,
        },
        "capabilities": [],
        "flags": [],
        "ops_requested": data.ops,
        "measures": {},
    }

    try:
        # Download the image data
        resp = requests.get(data.image_url)
        resp.raise_for_status()
        img_bytes = resp.content

        # Attempt minimal processing using Pillow
        from PIL import Image
        import io

        img = Image.open(io.BytesIO(img_bytes))
        # Normalize: convert to grayscale if requested
        if any(op.lower() == "normalize" for op in data.ops):
            img = img.convert("L")
            report["capabilities"].append("normalize")
        # Additional ops not yet implemented
        unhandled = [op for op in data.ops if op.lower() not in {"normalize"}]
        if unhandled:
            report["flags"].append(f"ops_not_implemented: {', '.join(unhandled)}")
        # Optionally, we could save or analyze the image further here
    except Exception as e:
        report["flags"].append(f"error: {str(e)[:200]}")

    return ECGImageProcessOutput(report=report)


class ToolDefinition(BaseModel):
    """Definition of a single tool in the MCP catalog."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


@app.get("/catalog")
async def catalog() -> JSONResponse:
    """Return a catalog of available tools and their schemas.

    The MCP spec requires the server to advertise its tools.  This
    endpoint returns a JSON object describing the names, human
    descriptions and JSON schemas for input/output of each tool.
    Clients can introspect this to drive dynamic calling.
    """
    tools: List[ToolDefinition] = [
        ToolDefinition(
            name="quiz_validate",
            description="Validate a multiple‑choice quiz bank",
            input_schema=QuizValidateInput.model_json_schema(),
            output_schema=QuizValidateOutput.model_json_schema(),
        ),
        ToolDefinition(
            name="analyze_intervals",
            description="Calculate QTc and derive flags from measured intervals",
            input_schema=AnalyzeIntervalsInput.model_json_schema(),
            output_schema=AnalyzeIntervalsOutput.model_json_schema(),
        ),
        ToolDefinition(
            name="ecg_image_process",
            description="Process an ECG image and extract structured data",
            input_schema=ECGImageProcessInput.model_json_schema(),
            output_schema=ECGImageProcessOutput.model_json_schema(),
        ),
    ]
    return JSONResponse(content={"tools": [json.loads(tool.model_dump_json()) for tool in tools]})

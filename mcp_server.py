"""
Servidor MCP do ECGiga — API completa para ferramentas de análise de ECG.

Este módulo implementa o servidor MCP (Model Context Protocol) do ECGiga,
expondo endpoints reais e funcionais para:

  /quiz_validate     — Validação de bancos MCQ contra schema JSON.
  /analyze_intervals — Cálculo de QTc (Bazett) e flags clínicas.
  /ecg_image_process — Pipeline completo de CV: deskew, normalização,
                       grade, segmentação 12D, R-peaks, intervalos, eixo.
  /ecg_interpret     — Interpretação offline com regras clínicas e patologias.
  /quiz_adaptive     — Quiz adaptativo baseado no laudo do ECG.
  /catalog           — Catálogo de ferramentas (schemas I/O).
  /health            — Verificação de saúde com uptime e módulos.
  /sse               — Server-Sent Events para handshake MCP.

Todos os endpoints retornam dados estruturados (JSON) e estão integrados
com os módulos de CV (cv/), patologia (pathology/), processamento
de sinal (signal_processing/) e IA offline (ai/).
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import AsyncGenerator, Dict, List, Any, Optional
import json
import logging
import time

# Imports adicionais para implementação das ferramentas
import os
import math
import requests
import jsonschema
from jsonschema import ValidationError

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ecgiga.mcp")

app = FastAPI(
    title="ECGiga MCP Server",
    version="0.5.0",
    description="Servidor de ferramentas MCP para análise de ECG educacional",
)

# Tempo de início para health check
_START_TIME = time.time()


def sse_event(event: str, data: Any) -> str:
    """Serializa uma mensagem Server-Sent Events (SSE).

    Parâmetros
    ----------
    event : str
        Nome do evento SSE.
    data : Any
        Payload serializável em JSON.

    Retorna
    -------
    str
        String formatada conforme o protocolo SSE.
    """
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/sse")
async def sse_endpoint() -> StreamingResponse:
    """Endpoint Server-Sent Events para handshake MCP.

    Emite um evento "hello" sinalizando que o servidor está ativo.
    Clientes devem definir o header ``Accept: text/event-stream``
    ao conectar.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        # Emite evento de handshake e encerra.
        yield sse_event("hello", {"message": "Servidor MCP ECGiga pronto"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class QuizValidateInput(BaseModel):
    """Schema de entrada para a ferramenta quiz_validate.

    Parâmetros
    ----------
    path : str
        Caminho (local ou URL) para o arquivo JSON do quiz contendo
        questões de múltipla escolha e seus metadados.
    """

    path: str = Field(..., description="Caminho para o arquivo JSON do quiz")


class QuizValidateOutput(BaseModel):
    """Schema de saída para a ferramenta quiz_validate."""

    valid: bool
    errors: List[str]


@app.post("/quiz_validate", response_model=QuizValidateOutput)
async def quiz_validate(data: QuizValidateInput) -> QuizValidateOutput:
    """
    Valida um banco de questões MCQ contra o schema JSON padrão.

    Aceita um caminho local ou URL HTTP(S). Carrega o JSON e valida
    cada questão contra o schema (inlined). Erros são coletados e
    retornados para que o autor possa corrigir as questões.
    """
    errors: List[str] = []
    valid = True

    # Schema MCQ inline (draft 2020-12) para validação
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
        # Carrega conteúdo JSON de arquivo ou URL
        if data.path.startswith("http://") or data.path.startswith("https://"):
            resp = requests.get(data.path)
            resp.raise_for_status()
            content = resp.text
        else:
            # Expande ~ e verifica se o arquivo existe
            file_path = os.path.expanduser(data.path)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

        # Parseia o JSON
        quiz_data = json.loads(content)

        # Determina a lista de itens para validar
        if isinstance(quiz_data, dict) and "questions" in quiz_data:
            items = quiz_data["questions"]
        elif isinstance(quiz_data, list):
            items = quiz_data
        else:
            items = [quiz_data]

        # Valida cada item contra o schema
        for idx, item in enumerate(items):
            try:
                jsonschema.validate(instance=item, schema=mcq_schema)
            except ValidationError as ve:
                valid = False
                # Inclui índice para facilitar localização do item inválido
                errors.append(f"item {idx}: {ve.message}")
    except Exception as e:
        valid = False
        errors.append(str(e))

    return QuizValidateOutput(valid=valid, errors=errors)


class AnalyzeIntervalsInput(BaseModel):
    """Schema de entrada para a ferramenta analyze_intervals."""

    pr_ms: float = Field(..., description="PR interval (ms)")
    qrs_ms: float = Field(..., description="QRS duration (ms)")
    qt_ms: float = Field(..., description="QT interval (ms)")
    rr_ms: float = Field(..., description="RR interval (ms)")


class AnalyzeIntervalsOutput(BaseModel):
    """Schema de saída para a ferramenta analyze_intervals."""

    qtc_ms: float
    flags: List[str]
    explanation: str


@app.post("/analyze_intervals", response_model=AnalyzeIntervalsOutput)
async def analyze_intervals(data: AnalyzeIntervalsInput) -> AnalyzeIntervalsOutput:
    """
    Analisa intervalos cardíacos e calcula QTc (Bazett) com flags clínicas.

    Recebe PR, QRS, QT e RR em milissegundos. O QT corrigido é calculado
    pela fórmula de Bazett. Flags são geradas por regras de limiar:

      - PR > 200 ms → BAV de 1º grau
      - PR < 120 ms e QRS < 120 ms → possível pré-excitação
      - QRS ≥ 120 ms → bloqueio de ramo completo / origem ventricular
      - QRS 110–119 ms → bloqueio de ramo incompleto
      - QTc ≥ 460 ms → QT prolongado
      - QTc < 350 ms → QT curto

    A string de explicação concatena todas as flags para leitura humana.
    """
    pr_ms = data.pr_ms
    qrs_ms = data.qrs_ms
    qt_ms = data.qt_ms
    rr_ms = data.rr_ms

    # Valida RR antes de calcular QTc
    if rr_ms <= 0:
        raise HTTPException(
            status_code=422,
            detail="rr_ms deve ser positivo para cálculo de QTc",
        )

    # Calcula QTc pela fórmula de Bazett (ms)
    rr_sec = rr_ms / 1000.0
    qtc_ms = qt_ms / math.sqrt(rr_sec)

    flags: List[str] = []

    # Regras de flag clínicas
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

    # Limiares de QTc (conservadores, sem distinção de sexo)
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
    """Schema de entrada para a ferramenta ecg_image_process."""

    image_url: str = Field(..., description="URL da imagem de ECG para processamento")
    ops: List[str] = Field(..., description="Lista de operações: deskew, normalize, grid, segment, rpeaks, intervals, axis")


class ECGImageProcessOutput(BaseModel):
    """Schema de saída para a ferramenta ecg_image_process."""

    report: Dict[str, Any]


@app.post("/ecg_image_process", response_model=ECGImageProcessOutput)
async def ecg_image_process(data: ECGImageProcessInput) -> ECGImageProcessOutput:
    """
    Processa uma imagem de ECG pelo pipeline completo de visão computacional.

    Operações suportadas (via lista ``ops``):
      - ``deskew``     — Corrige rotação da imagem.
      - ``normalize``  — Normaliza escala para ~10 px/mm.
      - ``grid``       — Detecta período de grade (autocorrelação).
      - ``segment``    — Segmenta 12 derivações (layout 3×4).
      - ``rpeaks``     — Detecta R-peaks (Pan-Tompkins-like).
      - ``intervals``  — Mede PR/QRS/QT/QTc (multi-evidência).
      - ``axis``       — Calcula eixo frontal a partir de I e aVF.
    """
    import numpy as np
    from PIL import Image
    import io

    report: Dict[str, Any] = {
        "meta": {
            "source": "ecg_image_process",
            "fetched_url": data.image_url,
        },
        "capabilities": [],
        "flags": [],
        "ops_requested": data.ops,
        "measures": {},
    }

    try:
        resp = requests.get(data.image_url, timeout=30)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        ops_lower = [op.lower() for op in data.ops]

        # Correção de rotação (deskew)
        if "deskew" in ops_lower:
            from cv.deskew import estimate_rotation_angle, rotate_image
            info = estimate_rotation_angle(img, search_deg=6.0, step=0.5)
            img = rotate_image(img, info["angle_deg"])
            report["capabilities"].append("deskew")
            report["measures"]["deskew_angle_deg"] = info["angle_deg"]

        # Normalização de escala
        if "normalize" in ops_lower:
            from cv.normalize import normalize_scale
            img, scale, pxmm = normalize_scale(img, 10.0)
            report["capabilities"].append("normalize")
            report["measures"]["normalize_scale"] = scale
            report["measures"]["px_per_mm_estimated"] = pxmm

        arr = np.asarray(img)
        gray = np.asarray(img.convert("L"))

        # Detecção de grade
        grid_info = None
        if "grid" in ops_lower or "segment" in ops_lower or "rpeaks" in ops_lower or "intervals" in ops_lower or "axis" in ops_lower:
            from cv.grid_detect import estimate_grid_period_px
            grid_info = estimate_grid_period_px(arr)
            report["capabilities"].append("grid")
            report["measures"]["grid"] = grid_info

        # Segmentação 12 derivações
        seg_leads = None
        if "segment" in ops_lower or "rpeaks" in ops_lower or "intervals" in ops_lower or "axis" in ops_lower:
            from cv.segmentation import find_content_bbox
            from cv.segmentation_ext import segment_layout
            bbox = find_content_bbox(gray)
            seg_leads = segment_layout(gray, layout="3x4", bbox=bbox)
            report["capabilities"].append("segment")
            report["measures"]["content_bbox"] = bbox
            report["measures"]["leads_count"] = len(seg_leads)

        # Detecção de R-peaks
        rpeaks_result = None
        pxsec = 250.0
        if ("rpeaks" in ops_lower or "intervals" in ops_lower or "axis" in ops_lower) and seg_leads:
            from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, estimate_px_per_sec
            from cv.rpeaks_robust import pan_tompkins_like
            lab2box = {d["lead"]: d["bbox"] for d in seg_leads}
            lead = "II" if "II" in lab2box else next(iter(lab2box.keys()))
            x0, y0, x1, y1 = lab2box[lead]
            crop = gray[y0:y1, x0:x1]
            trace = smooth_signal(extract_trace_centerline(crop), win=11)
            pxmm = (grid_info.get("px_small_x") or grid_info.get("px_small_y") or 10.0) if grid_info else 10.0
            pxsec = estimate_px_per_sec(pxmm, 25.0) or 250.0
            rpeaks_result = pan_tompkins_like(trace, pxsec)
            peaks = rpeaks_result.get("peaks_idx", [])
            report["capabilities"].append("rpeaks")
            report["measures"]["rpeaks_lead"] = lead
            report["measures"]["rpeaks_count"] = len(peaks)
            if len(peaks) >= 2:
                rr = np.diff(peaks) / pxsec
                report["measures"]["hr_bpm"] = round(60.0 / float(np.median(rr)), 1)

        # Medição de intervalos (PR/QRS/QT/QTc)
        if "intervals" in ops_lower and rpeaks_result and seg_leads:
            from cv.intervals_refined import intervals_refined_from_trace
            lab2box = {d["lead"]: d["bbox"] for d in seg_leads}
            lead = report["measures"].get("rpeaks_lead", "II")
            x0, y0, x1, y1 = lab2box[lead]
            crop = gray[y0:y1, x0:x1]
            trace = smooth_signal(extract_trace_centerline(crop), win=11)
            iv = intervals_refined_from_trace(trace, rpeaks_result["peaks_idx"], pxsec)
            report["capabilities"].append("intervals")
            report["measures"]["intervals"] = iv.get("median", {})

        # Cálculo do eixo frontal (I/aVF)
        if "axis" in ops_lower and rpeaks_result and seg_leads:
            from cv.axis import frontal_axis_from_image
            lab2box = {d["lead"]: d["bbox"] for d in seg_leads}
            if "I" in lab2box and "aVF" in lab2box:
                peaks = rpeaks_result.get("peaks_idx", [])
                axis = frontal_axis_from_image(
                    gray,
                    {"I": lab2box["I"], "aVF": lab2box["aVF"]},
                    {"I": peaks, "aVF": peaks},
                    {"I": pxsec, "aVF": pxsec},
                )
                report["capabilities"].append("axis")
                report["measures"]["axis"] = {
                    "angle_deg": axis.get("angle_deg"),
                    "label": axis.get("label"),
                }

    except Exception as e:
        report["flags"].append(f"error: {str(e)[:200]}")

    return ECGImageProcessOutput(report=report)


class ToolDefinition(BaseModel):
    """Definição de uma ferramenta no catálogo MCP."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


@app.get("/catalog")
async def catalog() -> JSONResponse:
    """Retorna o catálogo de ferramentas disponíveis e seus schemas.

    O protocolo MCP exige que o servidor divulgue suas ferramentas.
    Este endpoint retorna um JSON com nomes, descrições e schemas
    JSON de entrada/saída de cada ferramenta. Clientes podem usar
    este catálogo para chamadas dinâmicas.
    """
    tools: List[ToolDefinition] = [
        ToolDefinition(
            name="quiz_validate",
            description="Valida um banco de questões de múltipla escolha (MCQ)",
            input_schema=QuizValidateInput.model_json_schema(),
            output_schema=QuizValidateOutput.model_json_schema(),
        ),
        ToolDefinition(
            name="analyze_intervals",
            description="Calcula QTc e gera flags clínicas a partir de intervalos medidos",
            input_schema=AnalyzeIntervalsInput.model_json_schema(),
            output_schema=AnalyzeIntervalsOutput.model_json_schema(),
        ),
        ToolDefinition(
            name="ecg_image_process",
            description="Processa imagem de ECG e extrai dados estruturados (CV pipeline)",
            input_schema=ECGImageProcessInput.model_json_schema(),
            output_schema=ECGImageProcessOutput.model_json_schema(),
        ),
        ToolDefinition(
            name="ecg_interpret",
            description="Interpreta ECG usando regras offline e detecção de patologias",
            input_schema=ECGInterpretInput.model_json_schema(),
            output_schema=ECGInterpretOutput.model_json_schema(),
        ),
        ToolDefinition(
            name="quiz_adaptive",
            description="Gera quiz adaptativo baseado no report de ECG",
            input_schema=QuizAdaptiveInput.model_json_schema(),
            output_schema=QuizAdaptiveOutput.model_json_schema(),
        ),
    ]
    return JSONResponse(content={"tools": [json.loads(tool.model_dump_json()) for tool in tools]})


# ---------------------------------------------------------------------------
# Endpoint de saúde (health check)
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check() -> JSONResponse:
    """Verificação de saúde do servidor.

    Retorna status OK com uptime e versão. Utilizado pelo Docker
    HEALTHCHECK e por sistemas de monitorização.
    """
    uptime = time.time() - _START_TIME
    return JSONResponse(content={
        "status": "ok",
        "version": "0.5.0",
        "uptime_seconds": round(uptime, 1),
        "modules": {
            "pathology": _check_module("pathology"),
            "signal_processing": _check_module("signal_processing"),
            "ai": _check_module("ai"),
            "quiz": _check_module("quiz"),
            "education": _check_module("education"),
        },
    })


def _check_module(name: str) -> str:
    """Verifica se um módulo está disponível."""
    try:
        __import__(name)
        return "disponível"
    except ImportError:
        return "indisponível"


# ---------------------------------------------------------------------------
# Interpretação de ECG com IA offline
# ---------------------------------------------------------------------------

class ECGInterpretInput(BaseModel):
    """Entrada para interpretação de ECG."""
    intervals: Dict[str, float] = Field(
        ..., description="Intervalos medidos: PR_ms, QRS_ms, QT_ms, QTc_B, RR_s"
    )
    axis_deg: Optional[float] = Field(None, description="Eixo frontal em graus")
    axis_label: Optional[str] = Field(None, description="Label do eixo (normal, esquerda, direita)")
    flags: List[str] = Field(default_factory=list, description="Flags clínicas")
    st_changes: Optional[Dict[str, str]] = Field(None, description="Alterações de ST por derivação")
    patient_age: Optional[int] = Field(None, description="Idade do paciente")
    patient_sex: Optional[str] = Field(None, description="Sexo: M ou F")


class ECGInterpretOutput(BaseModel):
    """Saída da interpretação de ECG."""
    interpretation: str
    differentials: List[str]
    recommendations: List[str]
    severity: str
    confidence: str
    pathology_findings: Dict[str, Any] = Field(default_factory=dict)


@app.post("/ecg_interpret", response_model=ECGInterpretOutput)
async def ecg_interpret(data: ECGInterpretInput) -> ECGInterpretOutput:
    """Interpreta um ECG usando regras offline e detecção de patologias.

    Combina o módulo de regras offline (ai.offline_rules) com os
    novos módulos de detecção de patologias para uma interpretação
    abrangente.
    """
    logger.info("Requisição de interpretação recebida")

    # Montar report dict no formato interno
    report = {
        "intervals_refined": {"median": data.intervals},
        "axis": {"angle_deg": data.axis_deg, "label": data.axis_label or ""},
        "flags": data.flags,
    }
    if data.st_changes:
        report["st_changes"] = data.st_changes

    # Interpretação base com regras offline
    try:
        from ai.offline_rules import interpret_report
        result = interpret_report(report)
    except Exception as e:
        logger.error(f"Erro na interpretação offline: {e}")
        result = {
            "interpretation": "Erro na interpretação",
            "differentials": [],
            "recommendations": ["Repetir análise"],
            "severity": "unknown",
            "confidence": "baixa",
        }

    # Detecção de patologias adicionais
    pathology_findings: Dict[str, Any] = {}

    try:
        from pathology.arrhythmia import detect_rhythm_irregularity
        rr_s = data.intervals.get("RR_s")
        if rr_s and rr_s > 0:
            # Simular série RR a partir do RR médio para análise básica
            rr_series = [rr_s] * 10
            rhythm = detect_rhythm_irregularity(rr_series)
            pathology_findings["rhythm"] = {
                "pattern": rhythm["pattern"],
                "details": rhythm["details"],
            }
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Erro na análise de ritmo: {e}")

    try:
        from pathology.electrolyte import detect_hyperkalemia_pattern
        hyper_k = detect_hyperkalemia_pattern(report)
        if hyper_k["detected"]:
            pathology_findings["hyperkalemia"] = {
                "stage": hyper_k["stage"],
                "findings": hyper_k["findings"],
            }
            result["differentials"].extend(hyper_k.get("recommendations", []))
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Erro na detecção de hipercalemia: {e}")

    # NSTEMI se ST changes disponíveis
    if data.st_changes:
        try:
            from pathology.ischemia import detect_nstemi_pattern
            nstemi = detect_nstemi_pattern(data.st_changes)
            if nstemi["detected"]:
                pathology_findings["nstemi"] = {
                    "territory": nstemi["territory"],
                    "risk": nstemi["risk_assessment"],
                    "criteria": nstemi["criteria_met"],
                }
                result["differentials"].extend(nstemi["criteria_met"])
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Erro na detecção de NSTEMI: {e}")

    # Limiares ajustados por demografia
    if data.patient_age or data.patient_sex:
        try:
            from pathology.thresholds import get_adjusted_thresholds
            thresholds = get_adjusted_thresholds(data.patient_age, data.patient_sex)
            pathology_findings["adjusted_thresholds"] = {
                "age_group": thresholds["age_group"],
                "hr_range": thresholds["hr_range"],
                "qtc_upper_ms": thresholds["qtc_upper_ms"],
            }
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Erro nos limiares ajustados: {e}")

    return ECGInterpretOutput(
        interpretation=result.get("interpretation", ""),
        differentials=result.get("differentials", []),
        recommendations=result.get("recommendations", []),
        severity=result.get("severity", "unknown"),
        confidence=result.get("confidence", "moderada"),
        pathology_findings=pathology_findings,
    )


# ---------------------------------------------------------------------------
# Quiz adaptativo
# ---------------------------------------------------------------------------

class QuizAdaptiveInput(BaseModel):
    """Entrada para quiz adaptativo."""
    report: Optional[Dict[str, Any]] = Field(
        None, description="Report de ECG para personalizar quiz"
    )
    n_questions: int = Field(6, description="Número de questões", ge=1, le=50)
    seed: Optional[int] = Field(None, description="Semente para reprodutibilidade")


class QuizAdaptiveOutput(BaseModel):
    """Saída do quiz adaptativo."""
    questions: List[Dict[str, Any]]
    tags: List[str]


@app.post("/quiz_adaptive", response_model=QuizAdaptiveOutput)
async def quiz_adaptive(data: QuizAdaptiveInput) -> QuizAdaptiveOutput:
    """Gera um quiz adaptativo baseado no report de ECG.

    Utiliza o motor de quiz para selecionar questões relevantes
    aos achados do ECG analisado.
    """
    logger.info(f"Quiz adaptativo: {data.n_questions} questões")

    try:
        from quiz.engine import build_adaptive_quiz
        report = data.report or {}
        result = build_adaptive_quiz(
            report,
            n_questions=data.n_questions,
            seed=data.seed or 42,
        )
        return QuizAdaptiveOutput(
            questions=result.get("questions", []),
            tags=result.get("tags", []),
        )
    except Exception as e:
        logger.error(f"Erro no quiz adaptativo: {e}")
        return QuizAdaptiveOutput(questions=[], tags=[])

"""
Roteador de processamento de ECG.

Gerencia o endpoint /ecg/process-inline para processamento de imagens
de ECG através do pipeline de visão computacional.
"""

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import io

from api.dependencies import get_settings, get_storage_root, validate_file_size, validate_content_type
from persistence.storage import get_storage
from ecgcourse.pipeline.image_ingest import process_image

router = APIRouter()

@router.post("/process-inline")
async def process_inline(
    file: UploadFile = File(..., description="Arquivo de imagem de ECG (PNG/JPEG)"),
    deskew: bool = Form(False, description="Aplicar correção de rotação"),
    normalize: bool = Form(False, description="Normalizar escala para px/mm ~10"),
    auto_grid: bool = Form(False, description="Habilitar detecção automática de grade e segmentação"),
    rpeaks_lead: Optional[str] = Form(None, description="Derivação para detecção de R-peaks (ex.: II, V2)"),
    rpeaks_robust: bool = Form(False, description="Usar detecção robusta de R-peaks (Pan-Tompkins-like)"),
    intervals: bool = Form(False, description="Calcular intervalos PR/QRS/QT/QTc"),
    sexo: Optional[str] = Form(None, description="Sexo do paciente (M/F) para limiares de QTc"),
    persist: bool = Query(False, description="Salvar laudo em armazenamento persistente"),
    compact: bool = Query(False, description="Retornar resposta compacta (sem laudo completo)")
):
    """
    Processa imagem de ECG inline e retorna laudo estruturado.

    Aceita formulário multipart com arquivo de imagem e parâmetros de
    processamento. Retorna JSON com laudo completo e resumo, ou resposta
    compacta. Com persist=true, salva o laudo e retorna report_id para
    consulta posterior.
    """
    settings = get_settings()

    # Validar tamanho do arquivo
    if file.size and not validate_file_size(file.size):
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande. Tamanho máximo: {settings.max_file_mb}MB"
        )

    # Validar tipo de conteúdo
    if not validate_content_type(file.content_type or ""):
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de arquivo não suportado: {file.content_type}. "
                   f"Suportados: {', '.join(settings.supported_formats)}"
        )

    try:
        # Ler dados do arquivo
        file_data = await file.read()

        # Verificação adicional de tamanho (caso content-length ausente)
        if not validate_file_size(len(file_data)):
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo muito grande. Tamanho máximo: {settings.max_file_mb}MB"
            )

        # Processar imagem via função pura do pipeline
        report = process_image(
            image_data=file_data,
            deskew=deskew,
            normalize=normalize,
            auto_grid=auto_grid,
            rpeaks_lead=rpeaks_lead,
            rpeaks_robust=rpeaks_robust,
            intervals=intervals,
            sexo=sexo,
            schema_version="0.4.0"
        )

        # Montar resumo
        summary = {
            "version": report["version"],
            "capabilities": report["capabilities"],
            "fc_bpm": report["measures"].get("fc_bpm"),
            "flags_count": len(report["flags"]),
            "processing_successful": len([f for f in report["flags"] if "unavailable" in f or "failed" in f]) == 0
        }

        response_data = {
            "summary": summary
        }

        # Persistência (se solicitada)
        if persist:
            storage = get_storage(get_storage_root())
            report_id = storage.save_report(report)
            response_data["report_id"] = report_id
            response_data["message"] = "Laudo salvo com sucesso"

        # Incluir laudo completo exceto em modo compacto
        if not compact:
            response_data["report"] = report

        return JSONResponse(
            status_code=200,
            content=response_data
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha no processamento da imagem: {str(e)}"
        )
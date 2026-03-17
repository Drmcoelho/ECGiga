"""
Roteador de laudos da API.

Gerencia listagem e recuperação de laudos de ECG armazenados
no sistema de persistência.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Any

from api.dependencies import get_storage_root
from persistence.storage import get_storage

router = APIRouter()

@router.get("/list")
async def list_reports(
    limit: int = Query(50, ge=1, le=100, description="Número máximo de laudos a retornar"),
    offset: int = Query(0, ge=0, description="Número de laudos a pular (paginação)")
):
    """
    Lista laudos de ECG armazenados com paginação.

    Retorna metadados leves (id, created_at, capabilities, fc_bpm se presente).
    Resultados ordenados por data de criação (mais recentes primeiro).
    """
    try:
        storage = get_storage(get_storage_root())
        reports, total_count = storage.list_reports(limit=limit, offset=offset)

        return JSONResponse(
            status_code=200,
            content={
                "reports": reports,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total_count,
                    "has_more": offset + len(reports) < total_count
                }
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao listar laudos: {str(e)}"
        )

@router.get("/{report_id}")
async def get_report(report_id: str):
    """
    Recupera um laudo de ECG específico pelo ID.

    Retorna o objeto completo do laudo conforme armazenado originalmente.
    """
    try:
        storage = get_storage(get_storage_root())
        report = storage.get_report(report_id)

        if report is None:
            raise HTTPException(
                status_code=404,
                detail=f"Laudo não encontrado: {report_id}"
            )

        return JSONResponse(
            status_code=200,
            content=report
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao recuperar laudo: {str(e)}"
        )
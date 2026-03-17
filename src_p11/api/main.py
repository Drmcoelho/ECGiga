#!/usr/bin/env python3
"""
Aplicação principal FastAPI para a API do ECGiga.

Expõe endpoints para processamento de imagens de ECG e
gerenciamento de laudos (persistência JSON).
"""

from fastapi import FastAPI
from api.routers import ecg, reports

app = FastAPI(
    title="API ECGiga",
    description="API para processamento de imagens de ECG e gerenciamento de laudos",
    version="0.4.0"
)

app.include_router(ecg.router, prefix="/ecg", tags=["Processamento de ECG"])
app.include_router(reports.router, prefix="/reports", tags=["Laudos"])

@app.get("/")
async def root():
    """Informações do serviço e endpoints disponíveis."""
    return {
        "serviço": "API ECGiga",
        "versão": "0.4.0",
        "descrição": "Processamento de imagens de ECG e gerenciamento de laudos",
        "endpoints": {
            "ecg_processar": "/ecg/process-inline",
            "laudos_listar": "/reports/list",
            "laudo_obter": "/reports/{report_id}"
        }
    }

@app.get("/health")
async def health():
    """Verificação de saúde do servidor."""
    return {"status": "ok", "versão": "0.4.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
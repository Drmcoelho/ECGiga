# Dev — ingest image (p3)

## Pipeline p3 (MVP)
1. Abrir imagem via Pillow (PNG/JPG). PDF: suportado apenas se backend disponível no Pillow (1ª página).
2. Procurar sidecar META: `<arquivo>.meta.json` ou `--meta path.json`.
3. Se META presente:
   - Ler calibração: dpi, mm/mV, ms/div, layout.
   - Ler medidas provisionadas (educacionais no MVP): PR/QRS/QT/RR/FC, I/aVF.
   - Calcular QTc (Bazett/Fridericia) e eixo.
4. Montar `report` conforme `reporting/schema/report.schema.json` e salvar (`--report`).

> p4–p6: OCR da grade, segmentação das derivações, extração de intervalos com detecção de ondas, calibração automática.

## Limitações (intencionais para MVP p3)
- Sem CV robusta: dependemos de META para escala/medidas confiáveis.
- Upload no Dash não roda análise pesada; serve de preview e teste do contrato de META.

## Contrato de META (exemplo)
```json
{
  "dpi": 300,
  "mm_per_mV": 10,
  "ms_per_div": 200,
  "leads_layout": "3x4",
  "sexo": "M",
  "measures": {
    "pr_ms": 160, "qrs_ms": 100, "qt_ms": 380, "rr_ms": 800, "fc_bpm": 75,
    "lead_i_mv": 6, "avf_mv": 3
  },
  "patient_id": "ID-OPCIONAL",
  "age": 55, "context": "Texto livre."
}
```

# Dev — Parte 6/30 (Layout/Lead OCR + R-peaks) — 2025-09-25


## O que foi adicionado
- **OCR leve de rótulos** (`cv.lead_ocr`): template matching (OpenCV) + fallback **pytesseract** (opcional) + *fuzzy matching* (rapidfuzz).
- **Detecção automática de layout** (`cv.lead_ocr.choose_layout`): avalia candidatos (3x4, 6x2, 3x4+ritmo) comparando rótulos esperados e seleciona o maior escore.
- **R-peaks a partir de imagem** (`cv.rpeaks_from_image`): traçado 1D por coluna (mínimo da banda central), *smoothing* e picos por **z-score** → FC/RR.

## Integração CLI
- `python -m ecgcourse cv detect-layout <img> --json`
- `python -m ecgcourse cv detect-leads <img> --layout 3x4 --json`
- `python -m ecgcourse cv rpeaks <img> --layout 3x4 --lead II --speed 25 --json`
- `python -m ecgcourse ingest image <img> --deskew --normalize --auto-grid --auto-leads --rpeaks-lead II --schema-v3 --report`

## Schema v0.3
- Bloco `layout_detection` com `layout`, `score`, `labels[{{bbox,label,score}}]`.
- Bloco `rpeaks` com `lead_used`, `peaks_idx`, `rr_sec`, `hr_bpm_mean`, `hr_bpm_median`.

## Limitações e roadmap
- OCR depende de *render* simples e/ou Tesseract; para impressões ruidosas, considerar *text spotting* dedicado (p7–p8).
- R-peaks via imagem é uma aproximação; precisão melhora com **normalização de escala**, **deskew** e **contraste**. P7: picos R mais robustos e estimativa de **PR/QRS/QT** (onsets/offsets) validada com grade.

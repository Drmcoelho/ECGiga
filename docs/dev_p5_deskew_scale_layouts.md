# Dev — Parte 5/30 (Deskew + Normalização + Layouts) — 2025-09-25

## Novidades
- **Deskew**: `cv.deskew.estimate_rotation_angle` (varredura ±6°; métrica = variância de projeções de gradiente). `rotate_image` aplica correção.
- **Normalização de escala**: `cv.normalize.normalize_scale` estima px/mm via grade e redimensiona para alvo (10 px/mm, *clamped* 0.5–2×).
- **Layouts**: `cv.segmentation_ext.segment_layout` suporta `3x4`, `6x2` e `3x4+rhythm (II)`.

## Integração CLI
- `python -m ecgcourse cv deskew <img> --save out.png`
- `python -m ecgcourse cv normalize <img> --pxmm 10 --save out.png`
- `python -m ecgcourse cv layout-seg <img> --layout 6x2 --json`
- `python -m ecgcourse ingest image <img> --deskew --normalize --auto-grid --schema-v2 --report`

## Considerações técnicas
- A métrica de deskew é robusta para pequenas rotações típicas de scanners; picos de ruído podem afetar o score, mas a busca bruta suaviza.
- A normalização adota **no-upscale agressivo** (máx 2×) para preservar legibilidade e *throughput* no web build.
- Layouts não padronizados ainda dependerão de escolha manual no p5; detecção automática de layout entra no p6 (OCR de rótulos e *template matching*).

# Dev — Parte 9/30 (robustez, overlay, export) — 2025-09-26

## Novidades
- **Estatística robusta (MAD)** para exclusão de batimentos atípicos e medianas robustas (QTc B/F recalculadas).
- **Overlay**: visual marcando **R** e **onset/offset QRS** no lead escolhido.
- **Export** de laudo para **Markdown/HTML** com resumo didático + JSON completo.

### CLI
```bash
# Robustez (MAD) + export
python -m ecgcourse report export reports/caso.json --md reports/caso.md --html reports/caso.html --robust

# Overlay
python -m ecgcourse cv overlay samples/ecg_images/synthetic_12lead.png --lead II --out reports/overlays/caso_overlay.png
```

### API
- `cv/robust_outliers.py`: `robust_from_intervals(intervals_refined, prefer='QT_ms')` → `median_robust`, `beats_used`, `mask`.
- `cv/overlay.py`: `draw_overlay(image_path, leads_boxes, rpeaks_map, intervals, out_path, highlight_lead)`.
- `reporting/export.py`: `export(report_json, out_md, out_html)`.

# Dev — Parte 8/30 (Intervalos refinados + Eixo + Quiz adaptativo) — 2025-09-26

- **intervalos_refined**: gradiente/energia/estabilidade + guard-rails 60–200 ms (QRS).
- **axis**: I/aVF → ângulo (graus) e rótulo clínico.
- **quiz adaptativo**: baseado nas métricas do laudo.

CLI essencial:
```bash
python -m ecgcourse cv intervals-refined <img> --layout 3x4 --lead II --json
python -m ecgcourse cv axis             <img> --layout 3x4 --json
python -m ecgcourse ingest image <img>   --deskew --normalize --auto-grid --auto-leads   --rpeaks-lead II --rpeaks-robust --intervals --intervals-refined --axis   --schema-v5 --report
python -m ecgcourse quiz adaptive reports/<arquivo>.json --n 6 --out quizzes/<arquivo>.adaptive.json
```

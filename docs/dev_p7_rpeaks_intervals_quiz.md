# Dev — Parte 7/30 (R-peaks robustos + Intervalos + Quiz) — 2025-09-25

## R-peaks robustos (Pan‑Tompkins-like)
- Filtro banda limitada por **diferença de médias móveis** (janela curta vs. longa).
- Derivada → quadrado → integração por janela (≈150 ms) → **threshold adaptativo** com **refratário** (≈200 ms).
- Saída: índices de R em **pixels** e parâmetros do filtro.

## Onsets/offsets e intervalos
- QRS *onset/offset* por gradiente absoluto com limiar relativo e estabilidade por 15 ms.
- T-end: retorno sustentado do gradiente a ~0 por 30 ms até 520 ms após QRS.
- P-onset (aprox.): aumento sustentado do gradiente nos 280 ms anteriores ao QRS.
- Interpolação para **ms** via `px_per_sec = px_per_mm × speed_mm/s` (tipicamente 25). Cálculo de **QTc** (Bazett, Fridericia).

## Quiz dinâmico (MCQ)
- Gera perguntas com base em **RR/FC, PR, QRS, QT, QTc**, incluindo explicações concisas e gabarito.

## CLI
```bash
# R-peaks robustos e intervalos por lead
python -m ecgcourse cv rpeaks-robust <img> --layout 3x4 --lead II --json
python -m ecgcourse cv intervals      <img> --layout 3x4 --lead II --json

# Ingestão completa + laudo v0.4
python -m ecgcourse ingest image <img>   --deskew --normalize --auto-grid --auto-leads   --rpeaks-lead II --rpeaks-robust --intervals --schema-v4 --report

# Quiz a partir do laudo
python -m ecgcourse quiz build reports/<arquivo>.json --out quizzes/<arquivo>.quiz.json
```

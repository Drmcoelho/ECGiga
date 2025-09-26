# Dev — Parte 12/30 (Bloqueios, HVE estendido, Quiz) — 2025-09-26

## Novidades
- **Bloqueios (BRD/BRE)**: heurística baseada em **QRS (ms)** + morfologia **V1/V2** e **I/V6** com contagem de picos (RSR'/entalhes) e razões R/S.
- **HVE estendido**: **Sokolow-Lyon** e **Cornell product** (mm·ms; thresholds 2440 (M) / 2000 (F)).
- **Quiz a partir do laudo**: gera MCQs coerentes com intervalos, eixo, condução e HVE.

### CLI
```bash
# Bloqueios
python -m ecgcourse blocks detect samples/ecg_images/synthetic_12lead.png --json

# HVE estendido
python -m ecgcourse hypertrophy extended samples/ecg_images/synthetic_12lead.png --sex male --json

# Quiz a partir do laudo
python -m ecgcourse quiz from-report reports/synthetic_12lead.json --out quizzes/synthetic.quiz.json
```

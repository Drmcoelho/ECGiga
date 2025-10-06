# Dev — Parte 11/30 (Ritmo, Transição R/S, HVE) — 2025-09-26

## Novidades
- **Ritmo**: HR, RR-variability (SDNN, CV-RR) e rótulo heurístico (sinusal provável / irregular / indeterminado) com pista de P por energia.
- **Transição R/S** (V1–V6): razão R/S por precordial e detecção do ponto de transição (precoce/tardia/normal).
- **Checklist HVE**: índices **Sokolow-Lyon** e **Cornell** em **mm** (calibração pela grade), com thresholds por sexo e decisão binária.

### CLI
```bash
# Ritmo
python -m ecgcourse rhythm analyze samples/ecg_images/synthetic_12lead.png --lead II --json

# Transição V1–V6
python -m ecgcourse precordials transition samples/ecg_images/synthetic_12lead.png --json

# HVE (defina --sex male|female)
python -m ecgcourse checklist lvh samples/ecg_images/synthetic_12lead.png --sex male --json
```

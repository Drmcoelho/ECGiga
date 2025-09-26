# Dev — Parte 10/30 (Hexaxial, overlay embed, validate) — 2025-09-26

## Novidades
- **Eixo (hexaxial)**: usa I, II, III, aVR, aVL, aVF com soma vetorial ponderada por |amplitude líquida| → ângulo e rótulo.
- **Export com overlay embutido**: HTML recebe `<img>` base64 com a marcação do caso.
- **Validador leve**: checagens de tipo e presença de campos críticos; comando `report validate`.

### CLI
```bash
# Eixo hexaxial direto da imagem
python -m ecgcourse cv axis-hex samples/ecg_images/synthetic_12lead.png --json

# Export com overlay embutido (após gerar overlay)
python -m ecgcourse report export reports/caso.json --md reports/caso.md --html reports/caso.html --overlay reports/overlays/caso_overlay.png

# Validação de laudo (checagem leve)
python -m ecgcourse report validate reports/caso.json
```

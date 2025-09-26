# Dev — Parte 14/30 (Anotações & Avaliação) — 2025-09-26

## Novidades
- **Schema de anotações v0.1** (`reporting/schema/annotation.schema.v0.1.json`): padroniza rótulos **P/PR/QRS/ST/T/U/artifact/other**.
- **Overlay colorido** (`cv/overlay_boxes.py`): gera PNG com caixas coloridas e rótulos.
- **CLI de anotações** (`annotations/cli.py`):
  - `annotations validate` — valida `annotations.json` (usa `jsonschema` se disponível).
  - `annotations compare` — compara **aluno vs gabarito** usando **IoU** (limiar default 0.3) e produz **precisão/recall/F1** por rótulo + Macro-F1.
  - `annotations overlay` — exporta imagem com as caixas desenhadas.
- **Case Player** (web):
  - **Rótulo atual** (dropdown) para caixas.
  - **Carregar gabarito** (`.json`) e **Comparar** → exibe **Macro-F1** + detalhamento por rótulo.
  - **Salvar como gabarito**: exporta `gabarito.annotations.json` no formato canônico.

## Fluxos
```bash
# 1) Validar um annotations.json
python -m ecgcourse annotations validate annotations/aluno.annotations.json

# 2) Comparar com gabarito (gera relatório)
python -m ecgcourse annotations compare annotations/aluno.annotations.json annotations/gabarito.annotations.json --iou 0.35 --out reports/annotations_eval.json

# 3) Gerar overlay colorido
python -m ecgcourse annotations overlay src_unzipped/samples/ecg_images/synthetic_12lead.png annotations/aluno.annotations.json --out reports/overlays/aluno_boxes.png

# 4) Case Player (web) para anotação/avaliação manual
python -m ecgcourse web case-player --port 8013
open http://127.0.0.1:8013
# -> carregue a imagem, calibre, rotule as caixas, salve JSON, carregue gabarito e compare
```

# Dev — Parte 13/30 (Mega interativo & prática) — 2025-09-26

## Novidades
- **Case Player (web)** estático, sem dependências externas:
  - **Calibração** (px/mm por dois cliques em 5 mm), **paquímetro** (tempo, ms & FC), **régua** (mm/mV) e **caixas** (segmentos).
  - **Salvar** anotações em **JSON**.
- **Prática/Quiz (CLI/TUI)** com **Rich**: executa MCQs com feedback instantâneo e score.
- **Geração de casos**: `practice build` cria JSONs a partir de laudos existentes; `practice serve` publica o player.

### Fluxos
```bash
# 1) Gerar casos a partir de laudos
python -m ecgcourse practice build reports web_app/case_player/cases

# 2) Servir o Case Player
python -m ecgcourse practice serve --port 8013
# ou
python -m ecgcourse web case-player --port 8013

# 3) Abrir no navegador e carregar imagens/casos
open http://127.0.0.1:8013

# 4) Rodar quiz (TUI) com um quiz gerado
python -m ecgcourse quiz from-report reports/caso.json --out quizzes/caso.quiz.json
python -m ecgcourse practice quiz quizzes/caso.quiz.json --n 8
```

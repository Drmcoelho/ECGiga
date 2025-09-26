# Dev — Parte 16/30 (Correção visual + Auto-MCQ + Relatório + Pages) — 2025-09-26

## Novidades
- **Case Player — Corrija-me**: sobreposição **TP/FP/FN** (verde/vermelho/amarelo) com **IoU** e **deltas** sugeridos (Δx,Δy,Δw,Δh).
- **Quiz ilustrado automático** a partir do **laudo v0.5** (+ overlay opcional do gabarito).
- **Relatório HTML de desempenho** (macro-F1 e flags por rótulo).
- **Kit GitHub Pages**: home (`web_app/index.html`) + workflow `.github/workflows/pages.yml`.

### CLI (novos fluxos)
```bash
# 1) Auto-MCQ ilustrado a partir do laudo (gera JSON; opcional: HTML)
python -m ecgcourse auto quiz-illustrated reports/caso.json --image samples/ecg_images/synthetic_12lead.png --overlay annotations/gabarito.annotations.json --out-quiz quizzes/auto.quiz.json --out-html web_app/quiz_html/quiz_auto.html

# 2) Relatório HTML de desempenho (a partir de avaliações IoU/F1)
python -m ecgcourse perf report-html "reports/annotations_eval*.json" reports/performance.html

# 3) Case Player: Corrija-me (interativo)
python -m ecgcourse web case-player --port 8013
# -> Carregue ECG, faça suas caixas, carregue gabarito e clique em 'Corrigir-me (IoU)'
```

# Arquitetura — visão p0

- **CLI (Typer/Rich)** para quizzes, utilitários e análises rápidas.
- **Web (Dash)** para gráficos interativos (multi-derivações, zoom, overlays) e casos.
- **Notebooks** complementares (demonstrações/experimentos).
- **Quiz JSON Schema** garante consistência e validação de banco MCQ.
- **IA (GPT‑5)** integrará laudo preliminar e tutoria guiada em p2/p3.

Decisões:
- **Python** centraliza análise/educação; **JS/Dash** cuida do front interativo.
- **Licenças abertas** (MIT/CC‑BY‑SA) para longevidade e colaboração.

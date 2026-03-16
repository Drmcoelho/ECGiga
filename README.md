# ECGiga — Plataforma Educacional de ECG

[![Tests](https://github.com/Drmcoelho/ECGiga/actions/workflows/test.yml/badge.svg)](https://github.com/Drmcoelho/ECGiga/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/Drmcoelho/ECGiga)](LICENSE)

Megaprojeto educacional interativo para interpretação de ECG, combinando
visão computacional, inteligência artificial offline, simulação e quiz
adaptativo — 100% em português.

## Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| **CV Pipeline** (`cv/`) | Deskew, normalização, detecção de grade, segmentação 12 derivações, R-peaks (Pan-Tompkins), intervalos PR/QRS/QT/QTc, eixo frontal |
| **Patologias** (`pathology/`) | Arritmias, bloqueios, isquemia (STEMI/NSTEMI), Brugada, canalopatias, pericardite, TEP, marcapasso, eletrólitos |
| **Quiz Adaptativo** (`quiz/`) | Motor adaptativo, repetição espaçada (SM-2), rastreamento de progresso, banco com 60+ questões |
| **Educação** (`education/`) | Analogia das câmeras, mnemônico CAFÉ, conteúdo didático interativo |
| **Simulação** (`simulation/`) | Gerador de ECG 12 derivações, efeitos de drogas, canais iônicos |
| **IA Offline** (`ai/`) | Interpretação por regras clínicas, tutor interativo, prompts para LLMs |
| **Relatórios** (`reporting/`) | PDF, FHIR R4, internacionalização PT/EN |
| **Datasets** (`datasets/`) | PTB-XL, MIT-BIH (download e visualização via PhysioNet) |
| **Persistência** (`persistence/`) | SQLite thread-safe, autenticação JWT-like |
| **Case Player** (`case_player/`) | Geração e avaliação de casos clínicos interativos |
| **Sinal** (`signal_processing/`) | Filtros digitais, detecção de ruído, pipeline de pré-processamento |

## Interfaces

- **CLI** — `ecgcourse` (Typer + Rich)
- **Web** — Dash interativo com 5 abas (Análise, Educação, Quiz, Simulador, IA)
- **API** — FastAPI MCP Server com 7 endpoints

## Início Rápido

```bash
# Clonar e instalar
git clone https://github.com/Drmcoelho/ECGiga.git
cd ECGiga
pip install -r requirements.txt

# CLI
python -m cli_app.ecgcourse.cli --help

# Web App
python web_app/dash_app/app.py

# API Server
uvicorn mcp_server:app --reload

# Testes
pytest
```

## Deploy em 1 clique

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Drmcoelho/ECGiga)

```bash
# Docker
docker compose up
```

## Arquitetura

```
┌─────────────────────────────────────────────────┐
│                 User Interfaces                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │ CLI App  │  │ Dash Web  │  │ MCP Server   │  │
│  │ (typer)  │  │ (plotly)  │  │ (FastAPI)    │  │
│  └────┬─────┘  └─────┬─────┘  └──────┬───────┘  │
├───────┴──────────────┴───────────────┴───────────┤
│  cv/ │ pathology/ │ education/ │ simulation/      │
│  ai/ │ reporting/ │ datasets/  │ quiz/            │
│  signal_processing/ │ case_player/ │ validation/  │
├──────────────────────────────────────────────────┤
│           persistence/ │ data/                    │
└──────────────────────────────────────────────────┘
```

## Documentação

- [Guia do Desenvolvedor](docs/developer_guide.md)
- [Referência da API](docs/api_reference.md)
- [Guia do Usuário (PT)](docs/user_guide_pt.md)
- [Guia Clínico (PT)](docs/clinical_guide_pt.md)
- [Roadmap](docs/roadmap.md)

## Testes

581 testes cobrindo todos os módulos:

```bash
pytest                          # suite completa
pytest tests/test_mcp_server.py # apenas MCP server
pytest -k "pathology"           # apenas patologias
```

## Contribuindo

Veja o [Guia do Desenvolvedor](docs/developer_guide.md#contributing) para
detalhes sobre setup, estilo de código e como adicionar novos detectores
de patologia ou questões de quiz.

## Licença

Veja [LICENSE](LICENSE) para detalhes.

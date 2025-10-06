# MEGAPROJETO ECG — Parte **0/30** (p0)

[![CI Quality Gates](https://github.com/Drmcoelho/ECGiga/workflows/ci-quality-gates/badge.svg)](https://github.com/Drmcoelho/ECGiga/actions/workflows/ci-quality-gates.yml)
[![Nightly Benchmark](https://github.com/Drmcoelho/ECGiga/workflows/nightly-benchmark/badge.svg)](https://github.com/Drmcoelho/ECGiga/actions/workflows/nightly-benchmark.yml)
[![codecov](https://codecov.io/gh/Drmcoelho/ECGiga/branch/main/graph/badge.svg)](https://codecov.io/gh/Drmcoelho/ECGiga)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Missão:** construir o maior curso open‑source, interativo e clínico de Eletrocardiografia (ECG) para médicos com base sólida — com CLI didática, web dinâmica, IA assistiva (GPT‑5), quizzes MCQ com feedback imediato e simulações fisiológicas.

## 🏆 Quality Gates & Benchmarks

Este projeto mantém altos padrões de qualidade através de gates automatizados:

- **Coverage**: ≥60% (com meta de 70-75% após estabilização)
- **F1 Score**: ≥0.85 para HR 60-90 bpm (benchmark nightly)
- **Schema Validation**: Report schema v0.5 com análise de qualidade
- **Code Quality**: Black formatting + Ruff linting
- **Documentation**: CLI reference auto-gerada

### Nightly Benchmarks

Benchmarks sintéticos executam todas as noites às 2h UTC, validando:
- Performance de detecção de R-peaks
- Consistência de medições de intervalos
- Threshold F1 ≥0.85 para faixa de FC 60-90 bpm
- Métricas de qualidade de imagem e análise

---

## 0) O que é esta parte (p0)?

**p0** entrega a **espinha dorsal** do repositório: estrutura de pastas, guias, convenções, schemas de quiz, _stubs_ de CLI e Web (Dash), _notebooks_ educacionais iniciais (não são a plataforma principal), _prompts_ de IA e automações básicas. É 100% funcional para:
- Clonar, criar venv, instalar deps mínimas e rodar:
  - `ecgcourse` (CLI — modo “esqueleto”)
  - `web_app/dash_app/app.py` (Dash — _hello dashboard_)
- Escrever e validar **quizzes MCQ** via `quiz/schema/mcq.schema.json`.
- Ler a **arquitetura**, **roadmap 0→30** e padrões de contribuição.

> A plataforma principal do curso será **web + CLI**. Notebooks são **complementares** (demonstrações/ensino prático).

---

## 1) Visão — Produto e Público

- **Para quem?** Médicos / profissionais de saúde com base de ECG que querem **aprofundar** e **consolidar** prática.
- **Como?** Conteúdo robusto (fisiologia → fisiopatologia → leitura clínica), **interatividade pesada**, **quizzes MCQ** com explicações robustas, **IA assistiva** (laudos preliminares & tutoria guiada), casos raros e armadilhas diagnósticas.
- **Entrega:** GitHub (open source), deploy gratuito (GitHub Pages + app Dash).

**Pilares**: Precisão clínica, didática pragmática, automações, performance e transparência técnica.

---

## 2) Arquitetura — Macro

```
repo-root/
├─ README.md  (este arquivo)           ──────────────── visão, setup, guias
├─ docs/                                ──────────────── syllabus, arquitetura, roadmap
├─ quiz/                                ──────────────── banco MCQ + schema JSON
├─ cli_app/                             ──────────────── pacote Python “ecgcourse” (Typer + Rich)
│  ├─ ecgcourse/cli.py                  ──────────────── entrypoint CLI
│  └─ ecgcourse/quiz_engine.py          ──────────────── loader/validador de MCQ
├─ web_app/
│  └─ dash_app/app.py                   ──────────────── Dash “hello ECG dashboard”
├─ notebooks/                           ──────────────── cadernos educacionais (complementares)
├─ models/prompts/                      ──────────────── prompts GPT‑5 (laudo, tutor, quiz)
├─ scripts/                             ──────────────── utilidades (setup, run, lint)
├─ requirements.txt / pyproject.toml    ──────────────── deps e build
├─ CONTRIBUTING.md • CODE_OF_CONDUCT.md ──────────────── colaboração
└─ LICENSE • .gitignore • VERSION
```

**Back‑end leve** (FastAPI opcional em fases futuras) para upload/IA; **Front‑end Dash** para interações ricas; **CLI** para treino rápido e off‑grid.

---

## 3) Setup rápido (macOS/Linux)

```bash
git clone <URL_DO_REPO> ecg-megaprojeto
cd ecg-megaprojeto

python3 -m venv .venv && source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3.1 CLI
python -m ecgcourse --help
python -m ecgcourse quiz run quiz/bank/exemplo_arrtimias.json

# 3.2 Dash (dev)
python web_app/dash_app/app.py
# abre http://127.0.0.1:8050
```

> Windows: usar `py -m venv .venv && .venv\Scripts\activate` e ajustar comandos.

---

## 4) Convenções de Quiz (MCQ)

- Arquivos em `quiz/bank/*.json` validados pelo **JSON Schema**: `quiz/schema/mcq.schema.json`.
- Cada questão: `id`, `topic`, `difficulty`, `stem`, `options[]`, `answer_index`, `explanation`.
- **Explicação obrigatória** (robusta e clínica).

Validar:
```bash
python -m ecgcourse quiz validate quiz/bank/exemplo_arrtimias.json
```

---

## 5) CLI — Filosofia

- **Typer** + **Rich** para DX (UX de terminal) elegante.
- Subcomandos: `quiz run|validate`, `analyze image|values` (stubs), `docs open` (atalhos).
- Saída sempre clara, com **feedback imediato** e **racional clínico**.

---

## 6) Web (Dash) — Filosofia

- Dash básico em `web_app/dash_app/app.py` já roda e mostra layout inicial.
- Roadmap p1→p3: múltiplas derivações com zoom, overlays (R‑peaks), _cases_ com “mostrar solução”, sliders de **íons** (K+, Ca2+, Na+) impactando formas de onda simuladas.

---

## 7) Notebooks — Papel Complementar

- Exemplos calculados (p. ex., detecção de picos R, filtros, QTc, simulações de potencial de ação).
- **Não** são a plataforma principal, mas ampliam a compreensão prática.

---

## 8) IA (GPT‑5) — Uso Responsável (stubs p0)

- Prompts em `models/prompts/` para: **laudo preliminar**, **tutor** e **geração de MCQ**.
- _Bindings_/API serão adicionados nas partes p2/p3 com salvaguardas (explicitar limitações, revisão humana).

---

## 9) Roadmap 0→30 (resumo das próximas 6 partes)

- **p0 (esta):** esqueleto + padrões + stubs CLI/Web/Quiz/Notebooks.
- **p1:** CLI “quiz” completo (relatórios locais de desempenho); 50 MCQs validados; Dash com 12 derivações estáticas + zoom.
- **p2:** Análise de valores estruturados (PR/QRS/QT/QTc/eixo) + heurísticas; 150 MCQs; 5 notebooks úteis.
- **p3:** Upload de imagem → pré‑processamento (OpenCV) + chamada IA; cases interativos com feedback; 300 MCQs.
- **p4:** Dash avançado (filtros, overlays, simulação íons); desempenho adaptativo; export PDF de laudo.
- **p5:** FastAPI opcional, contas/offline, empacotamento app macOS/iOS (PWA ou wrapper).

Roadmap completo detalhado em `docs/roadmap.md` (com critérios de aceite).

---

## 10) Qualidade, Ética e Licenças

- **Conteúdo clínico** revisado por especialistas antes de marcar como “estável”.
- **Licenças:** código MIT; conteúdo CC‑BY‑SA 4.0; imagens com crédito/compatibilidade.
- **Aviso:** Ferramentas de IA são **educacionais**; **não** substituem julgamento médico.

---

## 11) Estrutura de Pastas (p0)

```
docs/               guias (síntese, arquitetura, roadmap)
quiz/               banco + schema MCQ
cli_app/            pacote Python “ecgcourse”
web_app/            dash_app (hello)
notebooks/          3 cadernos iniciais (MD/nb)
models/prompts/     prompts GPT‑5 (laudo/tutor/quiz)
scripts/            utilitários (setup/run)
```

---

## 12) Próximos Passos Imediatos (para você)

1. Criar ambiente e instalar deps.
2. Rodar `python -m ecgcourse quiz run quiz/bank/exemplo_arrtimias.json`.
3. Abrir Dash: `python web_app/dash_app/app.py`.
4. Ler `docs/syllabus.md` e `docs/arquitetura.md`.
5. Começar a **escrever MCQs** do seu tema forte (ver `docs/quiz_guide.md`).

**p0 pronto.** Vamos acelerar p1.
---

## 14) **Parte 2/30 (p2)** — Append — ENTREGUE (2025-09-25)

**Foco p2:**
- **CLI `analyze values`** — entrada PR/QRS/QT/RR/FC e I/aVF (mV); saída FC, **QTc (Bazett/Fridericia)**, **eixo** e **flags** (BAV1, QRS largo, QTc ↑/↓, PR curto).
- **Dash p2** — Calculadora QTc interativa.
- **Notebooks (5)** — QTc, eixo, R-peaks & RR, iônicos (demo), artefatos & filtros.
- **Banco MCQs p2** — +110 itens em `quiz/bank/p2/` (total ≥150).

### Uso rápido
```bash
# CLI (via opções)
python -m ecgcourse analyze values --pr 180 --qrs 95 --qt 380 --rr 800 --lead-i 6 --avf 3 --sexo M --report

# CLI (via JSON)
python -m ecgcourse analyze values samples/values/exemplo1.json --report

# Dash
python web_app/dash_app/app.py
```

---

## 15) **Parte 3/30 (p3)** — Append sobre p2 — ENTREGUE (2025-09-25)

**Foco p3: ingerir ECG por imagem + laudo padronizado**

- **CLI `ingest image`**: lê PNG/JPG/PDF(1ª página via Pillow quando suportado) e, se houver, **sidecar META** `<arquivo>.meta.json` com calibração e medidas. Gera **laudo** compatível com `reporting/schema/report.schema.json`, além de `.md` resumido.
- **Schema de laudo**: `reporting/schema/report.schema.json` (versão 0.1) — estável para os próximos MVPs.
- **Dash p3**: `dcc.Upload` para ECG, preview da imagem, leitura de META se existir e cálculo de **QTc** + **eixo** (I/aVF) e **flags** básicas.
- **Amostras**: `samples/ecg_images/synthetic_12lead.{png,meta.json}` com calibração (mm/mV, ms/div, dpi, etc.).
- **Notebooks**: +2 (pré-processamento simples e detecção de grade — conceitos).
- **Banco de MCQs**: +60 itens p3 em `quiz/bank/p3/` (posicionamento, marcapasso, canalopatias, armadilhas).

### Uso rápido (p3)

**Ingestão de imagem → laudo:**
```bash
# arquivo tem sidecar META? (ex.: synthetic_12lead.png.meta.json)
python -m ecgcourse ingest image samples/ecg_images/synthetic_12lead.png --report

# ou forneça META explícito
python -m ecgcourse ingest image samples/ecg_images/synthetic_12lead.png --meta samples/ecg_images/synthetic_12lead.png.meta.json --report
```
Laudos em: `reports/*_ecg_report.json|.md`

**Dash (upload):**
```bash
python web_app/dash_app/app.py
# arraste um PNG/JPG para ver preview e sumarização dos campos
```

---

## 16) **Parte 3b/30 (p3b)** — Manifestos de ECG para automação — ENTREGUE (2025-09-25)

**Objetivo**: agregar **links oficiais** e **datasets** (licenças abertas) para **uso direto na interface web** (exercícios, explicações, features interativas).

- `assets/manifest/ecg_images.v1.jsonl` — imagens (Wikimedia) com `file_url` resolvido via *Special:FilePath*.
- `assets/manifest/ecg_images_index.csv` — índice visual/planilha.
- `assets/manifest/ecg_datasets.v1.jsonl` — bases **PhysioNet** (WFDB) para renderização reprodutível de figuras.
- `scripts/python/download_assets.py` — *downloader* paralelo que grava em `assets/raw/images/`.

### Uso rápido
```bash
python3 scripts/python/download_assets.py
# => assets/raw/images/<id>.<ext>
```

> **Licenças**: respeitar `license` e `license_verified`. Itens `VERIFY_ON_PAGE` precisam de checagem manual antes do deploy público.

---

## 17) **Parte 3c/30 (p3c)** — Verificação de licenças + pré-processamento Web — ENTREGUE (2025-09-25)

- **CLI `assets`**: `download`, `verify`, `preprocess`
- **Verificação**: `scripts/python/verify_licenses.py` → `ecg_images.verified.jsonl` + **créditos** (MD/JSON)
- **Pré-processamento**: `scripts/python/preprocess_images.py` → **WEBP** (sempre) + **AVIF** (quando disponível), tamanhos 320/640/1024/1600, e manifesto `ecg_images.derived.json`
- **CI**: workflow `.github/workflows/assets-pipeline.yml` para rodar a esteira automaticamente

### Uso rápido
```bash
python -m ecgcourse assets download
python -m ecgcourse assets verify
python -m ecgcourse assets preprocess
```

---

## 19) **Parte 5/30 (p5)** — Deskew + Normalização de escala + Layouts 6×2/Ritmo — ENTREGUE (2025-09-25)

**Novidades**
- **CV**: `cv/deskew.py`, `cv/normalize.py`, `cv/segmentation_ext.py`.
- **CLI**: 
  - `python -m ecgcourse cv deskew <img> --save out.png`
  - `python -m ecgcourse cv normalize <img> --pxmm 10 --save out.png`
  - `python -m ecgcourse cv layout-seg <img> --layout 6x2 --json`
  - `python -m ecgcourse ingest image <img> --deskew --normalize --auto-grid --schema-v2 --report`
- **Dash**: opções **Deskew** e **Normalize (px/mm≈10)**, além de **seletor de layout** (3x4, 6x2, 3x4+ritmo).


---

## 20) **Parte 6/30 (p6)** — Detecção de layout/rótulos + R-peaks iniciais — ENTREGUE (2025-09-25)

**Novidades**
- **OCR de rótulos** (I, II, III, aVR, aVL, aVF, V1–V6) via template matching (OpenCV) + OCR opcional (pytesseract) + *fuzzy*.
- **Layout automático** entre `3x4`, `6x2` e `3x4+ritmo` por escore de rótulos previstos.
- **R-peaks a partir da imagem** (traçado 1D por coluna + z-score) → FC média/mediana e RR.

**CLI**
```bash
python -m ecgcourse cv detect-layout samples/ecg_images/synthetic_12lead.png --json
python -m ecgcourse cv detect-leads   samples/ecg_images/synthetic_12lead.png --layout 3x4 --json
python -m ecgcourse cv rpeaks        samples/ecg_images/synthetic_12lead.png --layout 3x4 --lead II --json

python -m ecgcourse ingest image samples/ecg_images/synthetic_12lead.png   --deskew --normalize --auto-grid --auto-leads --rpeaks-lead II --schema-v3 --report
```

---

## 21) **Parte 7/30 (p7)** — R-peaks robustos + Intervalos (PR/QRS/QT/QTc) + Quiz dinâmico — ENTREGUE (2025-09-25)

**Novidades**
- **cv/rpeaks_robust.py**: pipeline Pan‑Tompkins-like (banda limitada → derivada → quadrado → integração → threshold adaptativo).
- **cv/intervals.py**: onsets/offsets e estimativas de **PR/QRS/QT/QTc** (medianas + por batimento).
- **CLI**: `cv rpeaks-robust`, `cv intervals` e flags `--rpeaks-robust/--intervals` no `ingest image`.
- **Schema v0.4**: novo bloco **intervals** no laudo.
- **Quiz**: `quiz/generate_quiz.py` + `python -m ecgcourse quiz build` para gerar MCQs a partir do laudo.
- **Dash**: botões para **R-peaks robustos** e **Intervalos** (sumário textual).



---

## 22) **Parte 8/30 (p8)** — Intervalos refinados + Eixo (I/aVF) + Quiz adaptativo — ENTREGUE (2025-09-26)

**Novidades**
- **cv/intervals_refined.py**: *onset/offset* por **multi‑evidência** (gradiente/energia/estabilidade) e estimativas estáveis de **PR/QRS/QT/QTc**.
- **cv/axis.py**: **eixo frontal** diretamente da imagem (I/aVF), com rótulos clínicos (normal/esquerda/direita/extremo).
- **CLI**: `cv intervals-refined`, `cv axis` e flags `--intervals-refined/--axis` no `ingest image`.
- **Schema v0.5**: blocos `intervals_refined` e `axis` adicionados ao laudo.
- **Quiz adaptativo**: `quiz/engine.py` + `python -m ecgcourse quiz adaptive` apoiado em **lacunas** do laudo.
- **Dash**: botão **Eixo (I/aVF)** exibe ângulo/rotulação no sumário.


---

## 23) **Parte 9/30 (p9)** — Robustez (MAD), Overlay e Export — ENTREGUE (2025-09-26)

**Destaques**
- **Robustez**: seleção de batimentos por **MAD** e recalculo de medianas/QTc (bloco `intervals_refined.median_robust`).
- **Overlay**: `cv overlay` para gerar PNG com R e janelas QRS (lead escolhido).
- **Export**: `report export` → **Markdown/HTML** didáticos + JSON embutido.


---

## 24) **Parte 10/30 (p10)** — Hexaxial, Export (overlay embutido) e Validação — ENTREGUE (2025-09-26)

**Destaques**
- **cv/axis_hexaxial.py**: eixo robusto pelo **sistema hexaxial** (I, II, III, aVR, aVL, aVF) com soma vetorial ponderada.
- **reporting/export.py**: agora aceita `--overlay` e embute imagem **inline** no HTML.
- **reporting/validate_light.py**: `report validate` para checagem leve e contínua.
- **CLI & Dash**: `cv axis-hex` e botão **Eixo (Hexaxial)** na interface.


---

## 25) **Parte 11/30 (p11)** — Ritmo, Transição R/S e HVE — ENTREGUE (2025-09-26)

**Destaques**
- `cv/rhythm.py`: HR/SDNN/CV-RR + rótulo de ritmo com heurística de P.
- `cv/precordial_transition.py`: R/S por precordial e transição V1–V6.
- `cv/lvh_checklist.py`: Sokolow-Lyon e Cornell em mm (grade → px/mm).

**CLI & Dash**
- `rhythm analyze`, `precordials transition`, `checklist lvh`.
- Botões **Ritmo** e **Transição R/S** adicionados no Dash.

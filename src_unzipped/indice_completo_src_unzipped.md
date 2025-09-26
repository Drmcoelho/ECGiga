# Índice Completo do Diretório: src_unzipped

---
  - LICENSE `(Conteúdo não incluído)`

  #### 📄 README.md

  ```md
# MEGAPROJETO ECG — Parte **0/30** (p0)

> **Missão:** construir o maior curso open‑source, interativo e clínico de Eletrocardiografia (ECG) para médicos com base sólida — com CLI didática, web dinâmica, IA assistiva (GPT‑5), quizzes MCQ com feedback imediato e simulações fisiológicas.

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


  ```

  - VERSION `(Conteúdo não incluído)`

  #### 📄 ll.txt

  ```txt
total 88
drwxr-xr-x@ 21 matheuscoelho  wheel   672B 26 set 14:54 .
drwxr-xr-x@  7 matheuscoelho  wheel   224B 26 set 14:54 ..
drwxr-xr-x@  3 matheuscoelho  wheel    96B 26 set 14:53 .github
-rw-r--r--@  1 matheuscoelho  wheel   131B 25 set 19:47 .gitignore
drwxr-xr-x@  3 matheuscoelho  wheel    96B 26 set 14:53 assets
drwxr-xr-x@  4 matheuscoelho  wheel   128B 26 set 14:53 cli_app
drwxr-xr-x@ 11 matheuscoelho  wheel   352B 26 set 14:53 cv
drwxr-xr-x@ 17 matheuscoelho  wheel   544B 26 set 14:53 docs
-rw-r--r--@  1 matheuscoelho  wheel   128B 25 set 19:47 LICENSE
-rw-r--r--@  1 matheuscoelho  wheel     0B 26 set 14:54 ll.txt
drwxr-xr-x@ 22 matheuscoelho  wheel   704B 26 set 14:53 notebooks
-rw-r--r--@  1 matheuscoelho  wheel   463B 25 set 19:47 pyproject.toml
drwxr-xr-x@  5 matheuscoelho  wheel   160B 26 set 14:53 quiz
-rw-r--r--@  1 matheuscoelho  wheel    13K 25 set 21:04 README.md
-rw-r--r--@  1 matheuscoelho  wheel   7,0K 25 set 19:47 readme.me
drwxr-xr-x@  3 matheuscoelho  wheel    96B 26 set 14:53 reporting
-rw-r--r--@  1 matheuscoelho  wheel   837B 25 set 20:56 requirements.txt
drwxr-xr-x@  4 matheuscoelho  wheel   128B 26 set 14:53 samples
drwxr-xr-x@  3 matheuscoelho  wheel    96B 26 set 14:53 scripts
-rw-r--r--@  1 matheuscoelho  wheel     9B 25 set 19:47 VERSION
drwxr-xr-x@  3 matheuscoelho  wheel    96B 26 set 14:53 web_app

  ```

  - pyproject.toml `(Conteúdo não incluído)`

  - readme.me `(Conteúdo não incluído)`

  #### 📄 requirements.txt

  ```txt
typer>=0.12
rich>=13.7
pydantic>=2.7
jsonschema>=4.23
numpy>=1.26
pandas>=2.2
scipy>=1.11
matplotlib>=3.8
plotly>=5.22
dash>=2.17
pillow>=10.2
opencv-python-headless>=4.10
neurokit2>=0.2.9
wfdb>=4.1.2
requests>=2.32
pyyaml>=6.0
toml>=0.10
pytest>=8.3
black>=24.8
ruff>=0.6

# --- p3c additions ---
requests>=2.31.0
beautifulsoup4>=4.12.2
lxml>=4.9.3
pillow-avif-plugin>=1.4.6 ; platform_system != "Windows"  # opcional; será detectado em runtime

# --- p6 additions ---
opencv-python-headless>=4.9.0.80    # template matching e utilidades de imagem
pytesseract>=0.3.10                 # OCR opcional (requer binário tesseract instalado no sistema)
rapidfuzz>=3.6.1                    # fuzzy matching para mapear tokens a rótulos esperados

# --- p6 additions ---
opencv-python-headless>=4.9.0.80
pytesseract>=0.3.10
rapidfuzz>=3.6.1

  ```

  ### 📁 reporting/

    ### 📁 schema/

      #### 📄 report.schema.json

      ```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ECG Report Schema",
  "version": "0.1.0",
  "type": "object",
  "properties": {
    "meta": {
      "type": "object",
      "properties": {
        "source_image": {
          "type": "string"
        },
        "sidecar_meta_used": {
          "type": "boolean"
        },
        "ingest_version": {
          "type": "string"
        },
        "created_at": {
          "type": "string"
        },
        "notes": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "source_image",
        "ingest_version",
        "created_at"
      ]
    },
    "patient_info": {
      "type": "object",
      "properties": {
        "id": {
          "type": [
            "string",
            "null"
          ]
        },
        "age": {
          "type": [
            "integer",
            "null"
          ]
        },
        "sex": {
          "type": [
            "string",
            "null"
          ],
          "enum": [
            "M",
            "F",
            null
          ]
        },
        "context": {
          "type": [
            "string",
            "null"
          ]
        }
      }
    },
    "acquisition": {
      "type": "object",
      "properties": {
        "dpi": {
          "type": [
            "number",
            "null"
          ]
        },
        "mm_per_mV": {
          "type": [
            "number",
            "null"
          ]
        },
        "ms_per_div": {
          "type": [
            "number",
            "null"
          ]
        },
        "leads_layout": {
          "type": [
            "string",
            "null"
          ]
        }
      }
    },
    "measures": {
      "type": "object",
      "properties": {
        "pr_ms": {
          "type": [
            "number",
            "null"
          ]
        },
        "qrs_ms": {
          "type": [
            "number",
            "null"
          ]
        },
        "qt_ms": {
          "type": [
            "number",
            "null"
          ]
        },
        "rr_ms": {
          "type": [
            "number",
            "null"
          ]
        },
        "fc_bpm": {
          "type": [
            "number",
            "null"
          ]
        },
        "axis_angle_deg": {
          "type": [
            "number",
            "null"
          ]
        },
        "axis_label": {
          "type": [
            "string",
            "null"
          ]
        }
      }
    },
    "flags": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "suggested_interpretations": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "meta",
    "measures",
    "version"
  ]
}
      ```

      #### 📄 report.schema.v0.2.json

      ```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ECG Report Schema",
  "version": "0.2.0",
  "type": "object",
  "properties": {
    "meta": {
      "type": "object",
      "properties": {
        "source_image": {
          "type": "string"
        },
        "sidecar_meta_used": {
          "type": "boolean"
        },
        "ingest_version": {
          "type": "string"
        },
        "created_at": {
          "type": "string"
        },
        "notes": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "source_image",
        "ingest_version",
        "created_at"
      ]
    },
    "patient_info": {
      "type": "object",
      "properties": {
        "id": {
          "type": [
            "string",
            "null"
          ]
        },
        "age": {
          "type": [
            "integer",
            "null"
          ]
        },
        "sex": {
          "type": [
            "string",
            "null"
          ],
          "enum": [
            "M",
            "F",
            null
          ]
        },
        "context": {
          "type": [
            "string",
            "null"
          ]
        }
      }
    },
    "acquisition": {
      "type": "object",
      "properties": {
        "dpi": {
          "type": [
            "number",
            "null"
          ]
        },
        "mm_per_mV": {
          "type": [
            "number",
            "null"
          ]
        },
        "ms_per_div": {
          "type": [
            "number",
            "null"
          ]
        },
        "px_per_mm_x": {
          "type": [
            "number",
            "null"
          ]
        },
        "px_per_mm_y": {
          "type": [
            "number",
            "null"
          ]
        },
        "px_small_grid": {
          "type": [
            "number",
            "null"
          ]
        },
        "px_big_grid": {
          "type": [
            "number",
            "null"
          ]
        },
        "grid_confidence": {
          "type": [
            "number",
            "null"
          ]
        },
        "leads_layout": {
          "type": [
            "string",
            "null"
          ]
        }
      }
    },
    "segmentation": {
      "type": "object",
      "properties": {
        "content_bbox": {
          "type": "array",
          "items": {
            "type": "number"
          }
        },
        "leads": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "lead": {
                "type": "string"
              },
              "bbox": {
                "type": "array",
                "items": {
                  "type": "number"
                }
              }
            },
            "required": [
              "lead",
              "bbox"
            ]
          }
        }
      }
    },
    "measures": {
      "type": "object",
      "properties": {
        "pr_ms": {
          "type": [
            "number",
            "null"
          ]
        },
        "qrs_ms": {
          "type": [
            "number",
            "null"
          ]
        },
        "qt_ms": {
          "type": [
            "number",
            "null"
          ]
        },
        "rr_ms": {
          "type": [
            "number",
            "null"
          ]
        },
        "fc_bpm": {
          "type": [
            "number",
            "null"
          ]
        },
        "axis_angle_deg": {
          "type": [
            "number",
            "null"
          ]
        },
        "axis_label": {
          "type": [
            "string",
            "null"
          ]
        }
      }
    },
    "flags": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "suggested_interpretations": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "meta",
    "measures",
    "version"
  ]
}
      ```

      #### 📄 report.schema.v0.3.json

      ```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ECG Report Schema",
  "version": "0.3.0",
  "type": "object",
  "properties": {
    "meta": {
      "type": "object"
    },
    "patient_info": {
      "type": "object"
    },
    "acquisition": {
      "type": "object"
    },
    "segmentation": {
      "type": "object"
    },
    "layout_detection": {
      "type": "object",
      "properties": {
        "layout": {
          "type": "string",
          "enum": [
            "3x4",
            "6x2",
            "3x4+rhythm",
            "unknown"
          ]
        },
        "score": {
          "type": "number"
        },
        "labels": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "bbox": {
                "type": "array"
              },
              "label": {
                "type": [
                  "string",
                  "null"
                ]
              },
              "score": {
                "type": "number"
              }
            }
          }
        }
      }
    },
    "rpeaks": {
      "type": "object",
      "properties": {
        "lead_used": {
          "type": "string"
        },
        "peaks_idx": {
          "type": "array",
          "items": {
            "type": "number"
          }
        },
        "rr_sec": {
          "type": "array",
          "items": {
            "type": "number"
          }
        },
        "hr_bpm_mean": {
          "type": [
            "number",
            "null"
          ]
        },
        "hr_bpm_median": {
          "type": [
            "number",
            "null"
          ]
        }
      }
    },
    "measures": {
      "type": "object"
    },
    "flags": {
      "type": "array"
    },
    "suggested_interpretations": {
      "type": "array"
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "meta",
    "version"
  ]
}
      ```

      #### 📄 report.schema.v0.4.json

      ```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ECG Report Schema",
  "version": "0.4.0",
  "type": "object",
  "properties": {
    "meta": {
      "type": "object"
    },
    "patient_info": {
      "type": "object"
    },
    "acquisition": {
      "type": "object"
    },
    "segmentation": {
      "type": "object"
    },
    "layout_detection": {
      "type": "object"
    },
    "rpeaks": {
      "type": "object"
    },
    "intervals": {
      "type": "object",
      "properties": {
        "lead_used": {
          "type": "string"
        },
        "per_beat": {
          "type": "object"
        },
        "median": {
          "type": "object"
        }
      }
    },
    "measures": {
      "type": "object"
    },
    "flags": {
      "type": "array"
    },
    "suggested_interpretations": {
      "type": "array"
    },
    "version": {
      "type": "string"
    }
  },
  "required": [
    "meta",
    "version"
  ]
}
      ```

  ### 📁 web_app/

    ### 📁 dash_app/

      #### 📄 app.py

      ```py

import dash
from dash import html, dcc, Input, Output, State
import plotly.graph_objs as go
import numpy as np, base64, json
from PIL import Image
from io import BytesIO

app = dash.Dash(__name__)
app.title = "ECG Dash — p4 (upload + overlay + QTc + 12 leads)"

def synth_wave(phase=0.0, n=2000):
    t = np.linspace(0, 1, n)
    base = 0.02*np.sin(2*np.pi*2*t + phase)
    qrs = (np.exp(-((t-0.3)**2)/(2*0.0003)) - 0.25*np.exp(-((t-0.31)**2)/(2*0.00015)))
    p = 0.05*np.exp(-((t-0.2)**2)/(2*0.0012))
    tw = 0.1*np.exp(-((t-0.52)**2)/(2*0.008))
    return base + p + qrs + tw

leads = ["I","II","III","aVR","aVL","aVF","V1","V2","V3","V4","V5","V6"]
series = [synth_wave(phase=i*0.1) for i in range(len(leads))]
traces = [go.Scatter(y=series[i], mode="lines", name=leads[i], visible=True) for i in range(len(leads))]
layout = go.Layout(title="12 derivações sintéticas — zoom habilitado",
                   legend=dict(orientation="h"), xaxis=dict(title="Tempo (s)"),
                   yaxis=dict(title="mV"))
fig_synth = go.Figure(data=traces, layout=layout)

def decode_image(content):
    header, b64 = content.split(",")
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")

def make_overlay_figure(img, seg):
    w, h = img.size
    fig = go.Figure()
    fig.add_layout_image(
        dict(source=img, xref="x", yref="y", x=0, y=h, sizex=w, sizey=h, sizing="stretch", layer="below")
    )
    shapes = []
    annotations = []
    if seg and seg.get("leads"):
        for ld in seg["leads"]:
            x0,y0,x1,y1 = ld["bbox"]
            shapes.append(dict(type="rect", x0=x0, y0=h-y1, x1=x1, y1=h-y0, line=dict(width=2)))
            annotations.append(dict(x=(x0+x1)/2, y=h-y1+15, text=ld["lead"], showarrow=False, bgcolor="rgba(255,255,255,0.4)"))
    fig.update_layout(
        title="Overlay — Segmentação 12 derivações (básica)",
        xaxis=dict(visible=False, range=[0, w]),
        yaxis=dict(visible=False, range=[0, h], scaleanchor="x", scaleratio=1),
        shapes=shapes, annotations=annotations, margin=dict(l=0,r=0,t=30,b=0), height=min(800, int(800*w/h))
    )
    return fig

def qtc_b(qt_ms, rr_ms): return qt_ms/((rr_ms/1000.0)**0.5)
def qtc_f(qt_ms, rr_ms): return qt_ms/((rr_ms/1000.0)**(1/3))
def axis_label_from(I, aVF):
    if I is None or aVF is None: return None
    if I>=0 and aVF>=0: return "Normal"
    if I>=0 and aVF<0: return "Desvio para a esquerda"
    if I<0 and aVF>=0: return "Desvio para a direita"
    return "Desvio extremo (noroeste)"

app.layout = html.Div([
    html.H2("ECG Dashboard (p4) — Upload + Overlay 12D + Calculadora QTc + 12 leads sintéticos"),
    html.Div([
        html.Div([
            html.H3("Upload de ECG (PNG/JPG)"),
            dcc.Upload(
                id='upload-ecg', children=html.Div(['Arraste e solte ou ', html.A('selecione um arquivo')]),
                multiple=False, style={'width':'100%','height':'60px','lineHeight':'60px','borderWidth':'1px','borderStyle':'dashed','borderRadius':'5px','textAlign':'center','marginBottom':'10px'}
            ),
            dcc.Textarea(id="upload-meta", placeholder="Cole o sidecar META (JSON) opcional...", style={"width":"100%","height":"120px"}),
            html.Div([
    dcc.Checklist(id='ops', options=[
        {'label':'Deskew','value':'deskew'},
        {'label':'Normalize (px/mm≈10)','value':'normalize'}
    ], value=[]),
    html.Label('Layout'), dcc.Dropdown(id='layout-select', options=[
        {'label':'3x4','value':'3x4'},
        {'label':'6x2','value':'6x2'},
        {'label':'3x4 + ritmo (II)','value':'3x4+rhythm'}
    ], value='3x4', clearable=False, style={'width':'260px'})
], style={'display':'flex','gap':'16px','alignItems':'center','marginBottom':'8px'}),
html.Button("Processar", id="btn-process", n_clicks=0),
            html.Div(id="upload-summary", style={"marginTop":"10px","whiteSpace":"pre-wrap"}),
html.Div([
  html.Label('Lead para FC (R-peaks)'),
  dcc.Dropdown(id='lead-select', options=[{'label':l,'value':l} for l in ['II','V2','V5']], value='II', clearable=False, style={'width':'200px'}),
  html.Button('R-peaks robustos', id='btn-rrob', n_clicks=0),
  html.Button('Intervalos (PR/QRS/QT/QTc)', id='btn-intervals', n_clicks=0)
], style={'display':'flex','gap':'12px','alignItems':'center','marginTop':'8px'})
            dcc.Graph(id="overlay", figure=go.Figure())
        ], className="card", style={"maxWidth":"900px"})
    ], style={"marginBottom":"16px"}),
    html.Div([
        html.H3("Calculadora QTc (rápida)"),
        html.Label("QT (ms)"), dcc.Input(id="qt-ms", type="number", value=400, step=1),
        html.Label("RR (ms)"), dcc.Input(id="rr-ms", type="number", value=800, step=1),
        html.Div(id="qtc-out", style={"marginTop":"8px","fontWeight":"bold"}),
    ], className="card", style={"maxWidth":"520px","marginBottom":"16px"}),
    dcc.Graph(id="ecg12", figure=fig_synth)
])

@app.callback(
    Output("overlay","figure"),
    Output("upload-summary","children"),
    Input("btn-process","n_clicks"), Input('btn-hr','n_clicks'), Input('btn-rrob','n_clicks'), Input('btn-intervals','n_clicks'),
    State("upload-ecg","contents"),
    State("upload-ecg","filename"),
    State("upload-meta","value"), State('ops','value'), State('layout-select','value'),
    prevent_initial_call=True
)
def process(n, nhr, nrrob, nintv, content, filename, meta_text, ops, layout):
    if not content:
        return go.Figure(), "Nenhuma imagem enviada."
    img = decode_image(content)
    # pré-processo: deskew/normalize
    if ops and 'deskew' in ops:
        from cv.deskew import estimate_rotation_angle, rotate_image
        info = estimate_rotation_angle(img, search_deg=6.0, step=0.5)
        img = rotate_image(img, info['angle_deg'])
    if ops and 'normalize' in ops:
        from cv.normalize import normalize_scale
        img, scale, pxmm = normalize_scale(img, 10.0)
    # META opcional
    meta = None
    if meta_text:
        try: meta = json.loads(meta_text)
        except Exception as e: meta = {"_error": f"Falha lendo META: {e}"}

    # Grid + segmentação básica (servidor)
    from cv.grid_detect import estimate_grid_period_px
    from cv.segmentation import segment_12leads_basic, find_content_bbox
from cv.segmentation_ext import segment_layout
    arr = np.asarray(img.convert("L"))
    grid = estimate_grid_period_px(np.asarray(img))
    bbox = find_content_bbox(arr)
    leads = segment_layout(arr, layout=layout, bbox=bbox)
    from cv.lead_ocr import detect_labels_per_box
    seg = {"content_bbox": bbox, "leads": leads}
    labels = detect_labels_per_box(arr, [d['bbox'] for d in leads])
    summary = [f"Arquivo: {filename}", f"Layout: {layout}", f"Rótulos detectados: {sum(1 for d in labels if d.get('label'))}/{len(labels)}",
               f"Grid small≈{grid.get('px_small_x') or grid.get('px_small_y'):.1f}px, big≈{grid.get('px_big_x') or grid.get('px_big_y'):.1f}px (conf {grid.get('confidence',0):.2f})",
               f"Content bbox: {bbox} | Leads: {len(leads)}"]
    if meta and isinstance(meta, dict):
        m = meta.get("measures", {})
        qt = m.get("qt_ms"); rr = m.get("rr_ms") or (60000.0/(m.get("fc_bpm") or 0) if m.get("fc_bpm") else None)
        if qt and rr:
            summary.append(f"QT: {qt} ms | QTc (B/F): {qtc_b(qt, rr):.1f}/{qtc_f(qt, rr):.1f} ms")
    # Se solicitado Estimar FC, calcula em lead selecionável (II por padrão)
    from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, estimate_px_per_sec
    from cv.rpeaks_robust import pan_tompkins_like
    from cv.intervals import intervals_from_trace
    # estimadores (opcionais, via botões)
    if nrrob or nintv:
        lab = 'II'
        lab2box = {d['lead']: d['bbox'] for d in leads}
        if lab in lab2box:
            x0,y0,x1,y1 = lab2box[lab]
            crop = arr[y0:y1, x0:x1]
            trace = smooth_signal(extract_trace_centerline(crop), win=11)
            from cv.grid_detect import estimate_grid_period_px
            pxmm = (estimate_grid_period_px(np.asarray(img)).get('px_small_x') or estimate_grid_period_px(np.asarray(img)).get('px_small_y'))
            pxsec = estimate_px_per_sec(pxmm, 25.0) or 250.0
            if nrrob:
                rdet = pan_tompkins_like(trace, pxsec)
                summary.append(f"R-peaks robustos: {len(rdet['peaks_idx'])} picos (fs≈{pxsec:.1f} px/s)")
            if nintv:
                rdet = pan_tompkins_like(trace, pxsec)
                iv = intervals_from_trace(trace, rdet['peaks_idx'], pxsec)
                m = iv['median']
                summary.append(f"PR {m.get('PR_ms')} ms | QRS {m.get('QRS_ms')} ms | QT {m.get('QT_ms')} ms | QTcB {m.get('QTc_B')} ms | QTcF {m.get('QTc_F')} ms")
    fig = make_overlay_figure(img, seg)
    return fig, "\n".join(summary)

@app.callback(Output("qtc-out","children"), [Input("qt-ms","value"), Input("rr-ms","value")])
def calc_qtc(qt, rr):
    if not qt or not rr or rr<=0: return "Informe QT e RR em ms."
    return f"QTc Bazett: {qtc_b(qt, rr):.1f} ms | QTc Fridericia: {qtc_f(qt, rr):.1f} ms"

if __name__ == "__main__":
    app.run(debug=True)

      ```

      ### 📁 assets/

        #### 📄 style.css

        ```css
body{font-family: -apple-system, system-ui, Segoe UI, Roboto, sans-serif;}
        ```

  ### 📁 quiz/

    #### 📄 generate_quiz.py

    ```py

import json, random
from typing import Dict, List

def _fmt(val, nd=0):
    return "N/D" if val is None else (f"{val:.{nd}f}" if isinstance(val, (int,float)) else str(val))

def quiz_from_report(report: Dict, seed: int = 42) -> Dict:
    """
    Gera um pequeno conjunto de MCQs com base no laudo analisado (HR/QRS/PR/QT/QTc e bandeiras).
    Saída: {"questions":[{id, prompt, choices:[{id,text,is_correct,explanation}] }]}
    """
    random.seed(seed)
    q = []
    # HR (se disponível via rpeaks)
    hr = None
    if report.get("rpeaks", {}).get("rr_sec"):
        rr = report["rpeaks"]["rr_sec"]
        if rr: hr = 60.0 / (sum(rr)/len(rr))
    # Intervais medianos
    iv = report.get("intervals", {}).get("median", {})
    pr, qrs, qt, qtc = iv.get("PR_ms"), iv.get("QRS_ms"), iv.get("QT_ms"), iv.get("QTc_B")
    # Q1: Ritmo
    if hr:
        prompt = f"Com RR médio ≈ {_fmt(1.0/(hr/60.0), 2)} s, qual a FC aproximada?"
        correct = f"{_fmt(hr,0)} bpm"
        choices = [correct, f"{_fmt(hr*0.5,0)} bpm", f"{_fmt(hr*1.5,0)} bpm", f"{_fmt(hr+30,0)} bpm"]
        random.shuffle(choices)
        expl = f"A FC ≈ 60/RR(s) ≈ {hr:.0f} bpm."
        q.append({"id":"q_hr","prompt":prompt,"choices":[{"id":i,"text":c,"is_correct":(c==correct),"explanation":expl} for i,c in enumerate(choices)]})
    # Q2: QRS largo?
    if qrs is not None:
        prompt = f"O QRS mediano é {_fmt(qrs,0)} ms. Ele é considerado largo?"
        correct = "Sim" if qrs>=120 else "Não"
        expl = "QRS ≥ 120 ms é considerado largo (bloqueio de ramo ou condução intraventricular)."
        choices = ["Sim","Não"]; random.shuffle(choices)
        q.append({"id":"q_qrs","prompt":prompt,"choices":[{"id":i,"text":c,"is_correct":(c==correct),"explanation":expl} for i,c in enumerate(choices)]})
    # Q3: PR prolongado?
    if pr is not None:
        prompt = f"O PR mediano é {_fmt(pr,0)} ms. Há 1º grau AV?"
        correct = "Sim" if pr>200 else "Não"
        expl = "PR > 200 ms define bloqueio AV de 1º grau."
        choices = ["Sim","Não"]; random.shuffle(choices)
        q.append({"id":"q_pr","prompt":prompt,"choices":[{"id":i,"text":c,"is_correct":(c==correct),"explanation":expl} for i,c in enumerate(choices)]})
    # Q4: QT/QTc
    if qt is not None and qtc is not None:
        prompt = f"O QT mediano é {_fmt(qt,0)} ms e QTc(B) {_fmt(qtc,0)} ms. Qual a interpretação?"
        def interp(qtcv):
            if qtcv>480: return "Prolongado (alto risco)"
            if qtcv>440: return "Prolongado (leve/moderado)"
            if qtcv<350: return "Curto"
            return "Normal"
        correct = interp(qtc)
        choices = ["Prolongado (alto risco)","Prolongado (leve/moderado)","Normal","Curto"]; random.shuffle(choices)
        expl = "Limiares típicos: >440–450 ms (prolongado), >480 ms alto risco; <350 ms, curto."
        q.append({"id":"q_qtc","prompt":prompt,"choices":[{"id":i,"text":c,"is_correct":(c==correct),"explanation":expl} for i,c in enumerate(choices)]})
    return {"questions": q}

if __name__ == "__main__":
    import sys, json
    rep = json.load(open(sys.argv[1],"r",encoding="utf-8"))
    print(json.dumps(quiz_from_report(rep), ensure_ascii=False, indent=2))

    ```

    ### 📁 bank/

      #### 📄 exemplo_arrtimias.json

      ```json
{
  "id": "arr-0001",
  "topic": "Arritmias — FA",
  "difficulty": "medium",
  "stem": "Qual achado é mais típico de fibrilação atrial no ECG?",
  "options": [
    "Ondas P serrilhadas regulares com FC ~150 bpm",
    "Intervalos PR progressivamente mais longos até QRS cair",
    "Linha de base fibrilatória sem ondas P discretas e RR irregular",
    "QRS largo regular com dissociação AV"
  ],
  "answer_index": 2,
  "explanation": "FA: ausência de ondas P organizadas e resposta ventricular irregularmente irregular. Flutter tem ondas serrilhadas com padrões de condução, Wenckebach (Mobitz I) tem PR progressivo e TV monomórfica dá QRS largo regular."
}
      ```

      ### 📁 p3/

        #### 📄 chan_0001.json

        ```json
{
  "id": "chan_0001",
  "topic": "Brugada — tipo 1",
  "difficulty": "hard",
  "stem": "Assinatura:",
  "options": [
    "ST côncavo difuso",
    "ST em V1–V2 'coved' + T negativa",
    "Delta",
    "U gigante"
  ],
  "answer_index": 1,
  "explanation": "Tipo 1 clássico."
}
        ```

        #### 📄 chan_0002.json

        ```json
{
  "id": "chan_0002",
  "topic": "QT longo — gatilhos",
  "difficulty": "easy",
  "stem": "Gatilhos comuns:",
  "options": [
    "Hipocalemia/drogas",
    "Hipercalemia",
    "Digitálico",
    "Hipercalcemia"
  ],
  "answer_index": 0,
  "explanation": "Hipocalemia e fármacos prolongadores."
}
        ```

        #### 📄 chan_0003.json

        ```json
{
  "id": "chan_0003",
  "topic": "QT curto — risco",
  "difficulty": "hard",
  "stem": "Associa-se a:",
  "options": [
    "TV polimórfica",
    "FA/Flutter apenas",
    "Pericardite",
    "TEP"
  ],
  "answer_index": 0,
  "explanation": "Risco arrítmico com TV/FV."
}
        ```

        #### 📄 chan_0004.json

        ```json
{
  "id": "chan_0004",
  "topic": "CPVT",
  "difficulty": "hard",
  "stem": "ECG basal geralmente:",
  "options": [
    "Normal",
    "QT muito longo",
    "BRD completo",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "CPVT pode ter ECG basal normal; arritmias adrenérgicas."
}
        ```

        #### 📄 chan_0005.json

        ```json
{
  "id": "chan_0005",
  "topic": "Brugada — desencadeantes",
  "difficulty": "medium",
  "stem": "Podem desmascarar:",
  "options": [
    "Febre, bloqueadores de Na+",
    "Beta-agonistas",
    "Digitálico",
    "Hipocalcemia"
  ],
  "answer_index": 0,
  "explanation": "Clássicos em Brugada."
}
        ```

        #### 📄 lead_pos_0001.json

        ```json
{
  "id": "lead_pos_0001",
  "topic": "Posicionamento — V1/V2 altos",
  "difficulty": "hard",
  "stem": "Colocar V1–V2 um espaço intercostal acima pode mimetizar:",
  "options": [
    "Brugada",
    "HVE",
    "TEP",
    "QT curto"
  ],
  "answer_index": 0,
  "explanation": "Pré-cordiais altas podem gerar morfologia tipo Brugada."
}
        ```

        #### 📄 lead_pos_0002.json

        ```json
{
  "id": "lead_pos_0002",
  "topic": "Posicionamento — V1 errado",
  "difficulty": "medium",
  "stem": "V1 muito lateral tende a:",
  "options": [
    "Reduzir R em V1",
    "Aumentar R em V1",
    "Gerar delta",
    "Inverter P em inferiores"
  ],
  "answer_index": 1,
  "explanation": "Deslocar V1 lateral aumenta R e altera transição."
}
        ```

        #### 📄 lead_pos_0003.json

        ```json
{
  "id": "lead_pos_0003",
  "topic": "Posicionamento — Dextrocardia",
  "difficulty": "hard",
  "stem": "Progresso de R em V1–V6 na dextrocardia usualmente:",
  "options": [
    "Normal",
    "Ausente",
    "Exagerado",
    "Inverso uniforme"
  ],
  "answer_index": 1,
  "explanation": "Pobre progressão de R em precordiais esquerdas."
}
        ```

        #### 📄 lead_pos_0004.json

        ```json
{
  "id": "lead_pos_0004",
  "topic": "Posicionamento — RA/LA invertidos",
  "difficulty": "medium",
  "stem": "Inversão RA/LA produz:",
  "options": [
    "I invertida e troca de aVR/aVL",
    "QRS largo difuso",
    "Delta",
    "QT curto"
  ],
  "answer_index": 0,
  "explanation": "Assinatura clássica de troca de braços."
}
        ```

        #### 📄 lead_pos_0005.json

        ```json
{
  "id": "lead_pos_0005",
  "topic": "Posicionamento — V6 posterior",
  "difficulty": "medium",
  "stem": "V6 muito posterior pode:",
  "options": [
    "Simular infarto lateral",
    "Gerar U proeminente",
    "QRS estreitar",
    "Aumentar PR"
  ],
  "answer_index": 0,
  "explanation": "Posição incorreta pode falsear Q/QRS em laterais."
}
        ```

        #### 📄 p3_auto_015.json

        ```json
{
  "id": "p3_auto_015",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_016.json

        ```json
{
  "id": "p3_auto_016",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_017.json

        ```json
{
  "id": "p3_auto_017",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_018.json

        ```json
{
  "id": "p3_auto_018",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_019.json

        ```json
{
  "id": "p3_auto_019",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_020.json

        ```json
{
  "id": "p3_auto_020",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_021.json

        ```json
{
  "id": "p3_auto_021",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_022.json

        ```json
{
  "id": "p3_auto_022",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_023.json

        ```json
{
  "id": "p3_auto_023",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_024.json

        ```json
{
  "id": "p3_auto_024",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_025.json

        ```json
{
  "id": "p3_auto_025",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_026.json

        ```json
{
  "id": "p3_auto_026",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_027.json

        ```json
{
  "id": "p3_auto_027",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_028.json

        ```json
{
  "id": "p3_auto_028",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_029.json

        ```json
{
  "id": "p3_auto_029",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_030.json

        ```json
{
  "id": "p3_auto_030",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_031.json

        ```json
{
  "id": "p3_auto_031",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_032.json

        ```json
{
  "id": "p3_auto_032",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_033.json

        ```json
{
  "id": "p3_auto_033",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_034.json

        ```json
{
  "id": "p3_auto_034",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_035.json

        ```json
{
  "id": "p3_auto_035",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_036.json

        ```json
{
  "id": "p3_auto_036",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_037.json

        ```json
{
  "id": "p3_auto_037",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_038.json

        ```json
{
  "id": "p3_auto_038",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_039.json

        ```json
{
  "id": "p3_auto_039",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_040.json

        ```json
{
  "id": "p3_auto_040",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_041.json

        ```json
{
  "id": "p3_auto_041",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_042.json

        ```json
{
  "id": "p3_auto_042",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_043.json

        ```json
{
  "id": "p3_auto_043",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_044.json

        ```json
{
  "id": "p3_auto_044",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_045.json

        ```json
{
  "id": "p3_auto_045",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_046.json

        ```json
{
  "id": "p3_auto_046",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_047.json

        ```json
{
  "id": "p3_auto_047",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_048.json

        ```json
{
  "id": "p3_auto_048",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_049.json

        ```json
{
  "id": "p3_auto_049",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_050.json

        ```json
{
  "id": "p3_auto_050",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_051.json

        ```json
{
  "id": "p3_auto_051",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_052.json

        ```json
{
  "id": "p3_auto_052",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_053.json

        ```json
{
  "id": "p3_auto_053",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_054.json

        ```json
{
  "id": "p3_auto_054",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_055.json

        ```json
{
  "id": "p3_auto_055",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 p3_auto_056.json

        ```json
{
  "id": "p3_auto_056",
  "topic": "Artefatos — Tremor",
  "difficulty": "easy",
  "stem": "Tremor gera:",
  "options": [
    "Ruído alta freq.",
    "Baseline wander",
    "Delta",
    "QRS largo fixo"
  ],
  "answer_index": 0,
  "explanation": "Tremor → ruído rápido."
}
        ```

        #### 📄 p3_auto_057.json

        ```json
{
  "id": "p3_auto_057",
  "topic": "Artefatos — Respiração",
  "difficulty": "easy",
  "stem": "Baseline wander é tipicamente:",
  "options": [
    "Baixa freq. oscilante",
    "Alta freq.",
    "Delta",
    "Inversão I"
  ],
  "answer_index": 0,
  "explanation": "Movimento respiratório."
}
        ```

        #### 📄 p3_auto_058.json

        ```json
{
  "id": "p3_auto_058",
  "topic": "Canalopatia — Early rep.",
  "difficulty": "medium",
  "stem": "Repolarização precoce:",
  "options": [
    "Supra difuso com entalhe J",
    "PR deprimido difuso",
    "Delta",
    "Q profunda lateral"
  ],
  "answer_index": 0,
  "explanation": "Entalhe/notch em J."
}
        ```

        #### 📄 p3_auto_059.json

        ```json
{
  "id": "p3_auto_059",
  "topic": "Isquemia — De Winter",
  "difficulty": "hard",
  "stem": "Equivalente de:",
  "options": [
    "STEMI anterior proximal",
    "NSTEMI inferior",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Padrão De Winter."
}
        ```

        #### 📄 ppm_0001.json

        ```json
{
  "id": "ppm_0001",
  "topic": "Marcapasso — captura VD",
  "difficulty": "easy",
  "stem": "Morfologia esperada:",
  "options": [
    "BRE",
    "BRD",
    "QRS estreito",
    "QS em DII"
  ],
  "answer_index": 0,
  "explanation": "Ritmo estimulado VD → BRE."
}
        ```

        #### 📄 ppm_0002.json

        ```json
{
  "id": "ppm_0002",
  "topic": "Marcapasso — falha de captura",
  "difficulty": "medium",
  "stem": "No ECG, falha de captura:",
  "options": [
    "Espícula sem QRS subsequente",
    "QRS sem espícula",
    "RR irregular com F ondas",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "Espícula não seguida de captura."
}
        ```

        #### 📄 ppm_0003.json

        ```json
{
  "id": "ppm_0003",
  "topic": "Marcapasso — sensibilidade baixa",
  "difficulty": "medium",
  "stem": "Pode causar:",
  "options": [
    "Inibição inadequada (undersensing)",
    "Oversensing constante",
    "QT longo",
    "WPW"
  ],
  "answer_index": 0,
  "explanation": "Baixa sensibilidade não detecta atividade intrínseca."
}
        ```

        #### 📄 ppm_0004.json

        ```json
{
  "id": "ppm_0004",
  "topic": "Marcapasso — oversensing",
  "difficulty": "hard",
  "stem": "Pode causar:",
  "options": [
    "Inibição por ruído",
    "Estimulação contínua",
    "QRS estreito",
    "Bloqueio AV"
  ],
  "answer_index": 0,
  "explanation": "Oversensing de ruído impede estímulo."
}
        ```

        #### 📄 ppm_0005.json

        ```json
{
  "id": "ppm_0005",
  "topic": "TRC — biventricular",
  "difficulty": "medium",
  "stem": "TRC eficaz tende a:",
  "options": [
    "Reduzir QRS",
    "Aumentar QRS",
    "Inverter P",
    "Encurtar QT"
  ],
  "answer_index": 0,
  "explanation": "Ressincronização reduz QRS em muitos casos."
}
        ```

      ### 📁 p2/

        #### 📄 p2_0001.json

        ```json
{
  "id": "axis_rule_0001",
  "topic": "Eixo — Quadrantes",
  "difficulty": "easy",
  "stem": "I positivo e aVF negativo sugerem:",
  "options": [
    "Eixo normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo"
  ],
  "answer_index": 1,
  "explanation": "I+, aVF− → desvio para a esquerda."
}
        ```

        #### 📄 p2_0002.json

        ```json
{
  "id": "axis_rule_0002",
  "topic": "Eixo — Quadrantes",
  "difficulty": "easy",
  "stem": "I negativo e aVF positivo sugerem:",
  "options": [
    "Eixo normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo"
  ],
  "answer_index": 2,
  "explanation": "I−, aVF+ → desvio para a direita."
}
        ```

        #### 📄 p2_0003.json

        ```json
{
  "id": "axis_rule_0003",
  "topic": "Eixo — Quadrantes",
  "difficulty": "medium",
  "stem": "I negativo e aVF negativo sugerem:",
  "options": [
    "Eixo normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo"
  ],
  "answer_index": 3,
  "explanation": "I−, aVF− → desvio extremo."
}
        ```

        #### 📄 p2_0004.json

        ```json
{
  "id": "qtc_rule_0001",
  "topic": "Intervalos — QTc",
  "difficulty": "medium",
  "stem": "QT=400 ms, RR=1000 ms. QTc Bazett ≈",
  "options": [
    "320 ms",
    "400 ms",
    "500 ms",
    "600 ms"
  ],
  "answer_index": 1,
  "explanation": "400/√1,0 ≈ 400 ms."
}
        ```

        #### 📄 p2_0005.json

        ```json
{
  "id": "pr_rule_0001",
  "topic": "Intervalos — PR",
  "difficulty": "easy",
  "stem": "PR=220 ms, QRS=90 ms sugere:",
  "options": [
    "BAV 1º grau",
    "Mobitz I",
    "Pré-excitação",
    "BRE"
  ],
  "answer_index": 0,
  "explanation": "PR > 200 ms define BAV 1º."
}
        ```

        #### 📄 p2_0006.json

        ```json
{
  "id": "qrs_rule_0001",
  "topic": "Intervalos — QRS",
  "difficulty": "easy",
  "stem": "QRS=130 ms sugere:",
  "options": [
    "Normal",
    "Bloqueio de ramo completo",
    "BR incompleto",
    "TV garantida"
  ],
  "answer_index": 1,
  "explanation": "≥120 ms compatível com bloqueio completo."
}
        ```

        #### 📄 p2_0007.json

        ```json
{
  "id": "stemi_post_0001",
  "topic": "Isquemia — Posterior",
  "difficulty": "hard",
  "stem": "V1–V3 com R altas e ST deprimido sugerem:",
  "options": [
    "IAM posterior",
    "Pericardite",
    "Brugada",
    "ARVC"
  ],
  "answer_index": 0,
  "explanation": "Sugerem posterior; confirmar V7–V9."
}
        ```

        #### 📄 p2_0008.json

        ```json
{
  "id": "rv_mi_0001",
  "topic": "Isquemia — VD",
  "difficulty": "hard",
  "stem": "Sugerem IAM de VD:",
  "options": [
    "Supra em V3R/V4R",
    "ST difuso côncavo",
    "PR deprimido",
    "U proeminente"
  ],
  "answer_index": 0,
  "explanation": "V4R sensível para VD."
}
        ```

        #### 📄 p2_0009.json

        ```json
{
  "id": "early_t_0001",
  "topic": "Isquemia — T hiperaguda",
  "difficulty": "medium",
  "stem": "T hiperaguda inicial é:",
  "options": [
    "Baixa e larga",
    "Alta e simétrica desproporcional",
    "Negativa simétrica",
    "Com entalhe J"
  ],
  "answer_index": 1,
  "explanation": "Alta/larga e desproporcional."
}
        ```

        #### 📄 p2_0010.json

        ```json
{
  "id": "precordial_misplace_0001",
  "topic": "Técnica — V1–V2 altas",
  "difficulty": "hard",
  "stem": "Pode simular:",
  "options": [
    "Brugada",
    "TEP",
    "Pericardite",
    "HVE"
  ],
  "answer_index": 0,
  "explanation": "Pré-cordiais altas mimetizam Brugada."
}
        ```

        #### 📄 p2_0011.json

        ```json
{
  "id": "paced_bre_0001",
  "topic": "Marcapasso — Morfologia",
  "difficulty": "medium",
  "stem": "Estimulação VD →",
  "options": [
    "BRD",
    "BRE",
    "QRS estreito",
    "QS laterais"
  ],
  "answer_index": 1,
  "explanation": "VD gera padrão de BRE."
}
        ```

        #### 📄 p2_0012.json

        ```json
{
  "id": "hve_strain_0002",
  "topic": "HVE — Strain",
  "difficulty": "easy",
  "stem": "Strain lateral:",
  "options": [
    "ST elevado convexo",
    "ST deprimido + T negativa assimétrica",
    "Delta",
    "QT curto"
  ],
  "answer_index": 1,
  "explanation": "Padrão clássico."
}
        ```

        #### 📄 p2_0013.json

        ```json
{
  "id": "bundle_diff_0001",
  "topic": "BRD vs BRE",
  "difficulty": "easy",
  "stem": "Assinale:",
  "options": [
    "BRD rSR' V1–V2; BRE R larga V5–V6",
    "BRD R larga V6; BRE rSR' V1",
    "Ambos estreitos",
    "Nenhum"
  ],
  "answer_index": 0,
  "explanation": "Correto."
}
        ```

        #### 📄 p2_0014.json

        ```json
{
  "id": "brugada_drugs_0001",
  "topic": "Brugada — Desencadeantes",
  "difficulty": "hard",
  "stem": "Podem desmascarar:",
  "options": [
    "Bloq. canais de Na+",
    "Digitálico",
    "Beta-agonistas",
    "Hipercalemia"
  ],
  "answer_index": 0,
  "explanation": "Na+ e febre desmascaram."
}
        ```

        #### 📄 p2_0015.json

        ```json
{
  "id": "tep_axis_0001",
  "topic": "TEP — Padrões",
  "difficulty": "medium",
  "stem": "Achado possível:",
  "options": [
    "S1Q3T3",
    "Delta",
    "PR curto",
    "QT muito curto"
  ],
  "answer_index": 0,
  "explanation": "Clássico porém inespecífico."
}
        ```

        #### 📄 p2_0016.json

        ```json
{
  "id": "avrt_0001",
  "topic": "AVRT ortodrômica",
  "difficulty": "medium",
  "stem": "QRS costuma ser:",
  "options": [
    "Largo",
    "Estreito",
    "Sempre com delta",
    "Irregular"
  ],
  "answer_index": 1,
  "explanation": "Condução via nó AV ➜ estreito."
}
        ```

        #### 📄 p2_0017.json

        ```json
{
  "id": "af_rate_0001",
  "topic": "FA — Definição",
  "difficulty": "easy",
  "stem": "Característica definidora:",
  "options": [
    "RR irregularmente irregular e ausência de P organizada",
    "RR regular a 150",
    "P com PR progressivo",
    "Dissociação AV"
  ],
  "answer_index": 0,
  "explanation": "FA clássica."
}
        ```

        #### 📄 p2_0018.json

        ```json
{
  "id": "wolff_drugs_0001",
  "topic": "WPW + FA",
  "difficulty": "hard",
  "stem": "Evitar:",
  "options": [
    "AV nodais isolados",
    "Cardioversão elétrica",
    "Procainamida",
    "Manobra vagal"
  ],
  "answer_index": 0,
  "explanation": "Bloquear apenas AV pode piorar."
}
        ```

        #### 📄 p2_0019.json

        ```json
{
  "id": "svt_adenosine_diag_0001",
  "topic": "Adenosina — Diagnóstico",
  "difficulty": "medium",
  "stem": "Pode:",
  "options": [
    "Evidenciar ondas F no flutter",
    "Tratar FA definitivamente",
    "Sempre prolongar QT perigosamente",
    "Induzir bloqueio AV permanente"
  ],
  "answer_index": 0,
  "explanation": "Bloqueio AV momentâneo ajuda diagnóstico."
}
        ```

        #### 📄 p2_0020.json

        ```json
{
  "id": "u_wave_0001",
  "topic": "Onda U",
  "difficulty": "easy",
  "stem": "Mais típica de:",
  "options": [
    "Hipocalemia",
    "Hipercalemia",
    "Hipercalcemia",
    "IAM inferior"
  ],
  "answer_index": 0,
  "explanation": "Clássico."
}
        ```

        #### 📄 p2_0021.json

        ```json
{
  "id": "qt_short_0001",
  "topic": "QT curto",
  "difficulty": "hard",
  "stem": "QTc < 350 ms sugere:",
  "options": [
    "Síndrome QT curto",
    "Digitálico agudo",
    "Hipocalcemia",
    "TEP"
  ],
  "answer_index": 0,
  "explanation": "Risco arrítmico; raro."
}
        ```

        #### 📄 p2_0022.json

        ```json
{
  "id": "pericard_pr_0001",
  "topic": "Pericardite — PR",
  "difficulty": "medium",
  "stem": "Achado comum:",
  "options": [
    "PR deprimido",
    "PR encurtado",
    "PR longo fixo",
    "PR alternante"
  ],
  "answer_index": 0,
  "explanation": "Frequente em pericardite."
}
        ```

        #### 📄 p2_0023.json

        ```json
{
  "id": "osborn_0002",
  "topic": "Hipotermia — Osborn",
  "difficulty": "easy",
  "stem": "Localiza-se:",
  "options": [
    "Ponto J",
    "Início da P",
    "Meio do QRS",
    "Final do T"
  ],
  "answer_index": 0,
  "explanation": "Deflexão no J."
}
        ```

        #### 📄 p2_0024.json

        ```json
{
  "id": "ashman_0002",
  "topic": "Ashman",
  "difficulty": "medium",
  "stem": "Mais visto em:",
  "options": [
    "FA com ciclo longo-curto",
    "Flutter 2:1 fixo",
    "BRD completo",
    "Ritmo idioventricular"
  ],
  "answer_index": 0,
  "explanation": "Aberrância dependente do ciclo."
}
        ```

        #### 📄 p2_0025.json

        ```json
{
  "id": "sgarbossa_mod_0002",
  "topic": "Sgarbossa mod.",
  "difficulty": "hard",
  "stem": "Ênfase:",
  "options": [
    "Discordância proporcional do ST ao QRS",
    "PR curto",
    "QT curto",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "Critério modificado de Smith."
}
        ```

        #### 📄 p2_0026.json

        ```json
{
  "id": "hbae_0001",
  "topic": "HBAE",
  "difficulty": "medium",
  "stem": "Associa-se a:",
  "options": [
    "Eixo esquerdo",
    "Eixo normal",
    "Eixo direito",
    "Eixo extremo"
  ],
  "answer_index": 0,
  "explanation": "Desvia à esquerda."
}
        ```

        #### 📄 p2_0027.json

        ```json
{
  "id": "hbp_0001",
  "topic": "HBPE",
  "difficulty": "hard",
  "stem": "Associa-se a:",
  "options": [
    "Eixo direito",
    "Eixo esquerdo",
    "Eixo normal",
    "Eixo extremo"
  ],
  "answer_index": 0,
  "explanation": "Desvia à direita."
}
        ```

        #### 📄 p2_0028.json

        ```json
{
  "id": "lbbb_stemi_0002",
  "topic": "BRE + IAM",
  "difficulty": "hard",
  "stem": "Mais específico:",
  "options": [
    "ST supra concordante",
    "ST supra discordante leve",
    "PR curto",
    "QRS estreito"
  ],
  "answer_index": 0,
  "explanation": "Sgarbossa clássico."
}
        ```

        #### 📄 p2_0029.json

        ```json
{
  "id": "de_winter_0002",
  "topic": "De Winter",
  "difficulty": "hard",
  "stem": "É equivalente a:",
  "options": [
    "Oclusão proximal da ADA (STEMI anterior)",
    "NSTEMI inferior",
    "Pericardite",
    "Brugada"
  ],
  "answer_index": 0,
  "explanation": "Equivalente de STEMI anterior."
}
        ```

        #### 📄 p2_0030.json

        ```json
{
  "id": "axis_auto_01",
  "topic": "Eixo — I/aVF",
  "difficulty": "easy",
  "stem": "Com I=6 mV e aVF=4 mV, classifique o eixo:",
  "options": [
    "Normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo (noroeste)"
  ],
  "answer_index": 0,
  "explanation": "Quadrante aponta para normal."
}
        ```

        #### 📄 p2_0031.json

        ```json
{
  "id": "axis_auto_02",
  "topic": "Eixo — I/aVF",
  "difficulty": "easy",
  "stem": "Com I=7 mV e aVF=-3 mV, classifique o eixo:",
  "options": [
    "Normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo (noroeste)"
  ],
  "answer_index": 1,
  "explanation": "Quadrante aponta para desvio para a esquerda."
}
        ```

        #### 📄 p2_0032.json

        ```json
{
  "id": "axis_auto_03",
  "topic": "Eixo — I/aVF",
  "difficulty": "easy",
  "stem": "Com I=-5 mV e aVF=6 mV, classifique o eixo:",
  "options": [
    "Normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo (noroeste)"
  ],
  "answer_index": 2,
  "explanation": "Quadrante aponta para desvio para a direita."
}
        ```

        #### 📄 p2_0033.json

        ```json
{
  "id": "axis_auto_04",
  "topic": "Eixo — I/aVF",
  "difficulty": "easy",
  "stem": "Com I=-4 mV e aVF=-5 mV, classifique o eixo:",
  "options": [
    "Normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo (noroeste)"
  ],
  "answer_index": 3,
  "explanation": "Quadrante aponta para desvio extremo (noroeste)."
}
        ```

        #### 📄 p2_0034.json

        ```json
{
  "id": "axis_auto_05",
  "topic": "Eixo — I/aVF",
  "difficulty": "easy",
  "stem": "Com I=2 mV e aVF=0.5 mV, classifique o eixo:",
  "options": [
    "Normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo (noroeste)"
  ],
  "answer_index": 0,
  "explanation": "Quadrante aponta para normal."
}
        ```

        #### 📄 p2_0035.json

        ```json
{
  "id": "axis_auto_06",
  "topic": "Eixo — I/aVF",
  "difficulty": "easy",
  "stem": "Com I=3 mV e aVF=-1 mV, classifique o eixo:",
  "options": [
    "Normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo (noroeste)"
  ],
  "answer_index": 1,
  "explanation": "Quadrante aponta para desvio para a esquerda."
}
        ```

        #### 📄 p2_0036.json

        ```json
{
  "id": "axis_auto_07",
  "topic": "Eixo — I/aVF",
  "difficulty": "easy",
  "stem": "Com I=-2 mV e aVF=3 mV, classifique o eixo:",
  "options": [
    "Normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo (noroeste)"
  ],
  "answer_index": 2,
  "explanation": "Quadrante aponta para desvio para a direita."
}
        ```

        #### 📄 p2_0037.json

        ```json
{
  "id": "axis_auto_08",
  "topic": "Eixo — I/aVF",
  "difficulty": "easy",
  "stem": "Com I=-1 mV e aVF=-1 mV, classifique o eixo:",
  "options": [
    "Normal",
    "Desvio para a esquerda",
    "Desvio para a direita",
    "Desvio extremo (noroeste)"
  ],
  "answer_index": 3,
  "explanation": "Quadrante aponta para desvio extremo (noroeste)."
}
        ```

        #### 📄 p2_0038.json

        ```json
{
  "id": "qtc_auto_01",
  "topic": "QTc — Bazett (aprox)",
  "difficulty": "medium",
  "stem": "QT=380 ms, RR=800 ms. Classifique o QTc:",
  "options": [
    "Normal",
    "Prolongado",
    "Curto",
    "Indefinido"
  ],
  "answer_index": 0,
  "explanation": "QTc≈425 ms."
}
        ```

        #### 📄 p2_0039.json

        ```json
{
  "id": "qtc_auto_02",
  "topic": "QTc — Bazett (aprox)",
  "difficulty": "medium",
  "stem": "QT=440 ms, RR=800 ms. Classifique o QTc:",
  "options": [
    "Normal",
    "Prolongado",
    "Curto",
    "Indefinido"
  ],
  "answer_index": 1,
  "explanation": "QTc≈492 ms."
}
        ```

        #### 📄 p2_0040.json

        ```json
{
  "id": "qtc_auto_03",
  "topic": "QTc — Bazett (aprox)",
  "difficulty": "medium",
  "stem": "QT=460 ms, RR=600 ms. Classifique o QTc:",
  "options": [
    "Normal",
    "Prolongado",
    "Curto",
    "Indefinido"
  ],
  "answer_index": 1,
  "explanation": "QTc≈594 ms."
}
        ```

        #### 📄 p2_0041.json

        ```json
{
  "id": "qtc_auto_04",
  "topic": "QTc — Bazett (aprox)",
  "difficulty": "medium",
  "stem": "QT=500 ms, RR=1000 ms. Classifique o QTc:",
  "options": [
    "Normal",
    "Prolongado",
    "Curto",
    "Indefinido"
  ],
  "answer_index": 1,
  "explanation": "QTc≈500 ms."
}
        ```

        #### 📄 p2_0042.json

        ```json
{
  "id": "qtc_auto_05",
  "topic": "QTc — Bazett (aprox)",
  "difficulty": "medium",
  "stem": "QT=320 ms, RR=700 ms. Classifique o QTc:",
  "options": [
    "Normal",
    "Prolongado",
    "Curto",
    "Indefinido"
  ],
  "answer_index": 0,
  "explanation": "QTc≈382 ms."
}
        ```

        #### 📄 p2_0043.json

        ```json
{
  "id": "qtc_auto_06",
  "topic": "QTc — Bazett (aprox)",
  "difficulty": "medium",
  "stem": "QT=420 ms, RR=1200 ms. Classifique o QTc:",
  "options": [
    "Normal",
    "Prolongado",
    "Curto",
    "Indefinido"
  ],
  "answer_index": 0,
  "explanation": "QTc≈383 ms."
}
        ```

        #### 📄 p2_0044.json

        ```json
{
  "id": "prqrs_auto_01",
  "topic": "Intervalos — PR/QRS",
  "difficulty": "easy",
  "stem": "PR=100 ms, QRS=90 ms. Melhor interpretação:",
  "options": [
    "PR curto (pré-excitação)",
    "BAV 1º",
    "QRS largo (bloqueio de ramo)",
    "QRS 110–119 ms (incompleto)"
  ],
  "answer_index": 0,
  "explanation": "Aplicação direta de faixas normativas."
}
        ```

        #### 📄 p2_0045.json

        ```json
{
  "id": "prqrs_auto_02",
  "topic": "Intervalos — PR/QRS",
  "difficulty": "easy",
  "stem": "PR=220 ms, QRS=90 ms. Melhor interpretação:",
  "options": [
    "PR curto (pré-excitação)",
    "BAV 1º",
    "QRS largo (bloqueio de ramo)",
    "QRS 110–119 ms (incompleto)"
  ],
  "answer_index": 1,
  "explanation": "Aplicação direta de faixas normativas."
}
        ```

        #### 📄 p2_0046.json

        ```json
{
  "id": "prqrs_auto_03",
  "topic": "Intervalos — PR/QRS",
  "difficulty": "easy",
  "stem": "PR=160 ms, QRS=130 ms. Melhor interpretação:",
  "options": [
    "PR curto (pré-excitação)",
    "BAV 1º",
    "QRS largo (bloqueio de ramo)",
    "QRS 110–119 ms (incompleto)"
  ],
  "answer_index": 2,
  "explanation": "Aplicação direta de faixas normativas."
}
        ```

        #### 📄 p2_0047.json

        ```json
{
  "id": "prqrs_auto_04",
  "topic": "Intervalos — PR/QRS",
  "difficulty": "easy",
  "stem": "PR=190 ms, QRS=115 ms. Melhor interpretação:",
  "options": [
    "PR curto (pré-excitação)",
    "BAV 1º",
    "QRS largo (bloqueio de ramo)",
    "QRS 110–119 ms (incompleto)"
  ],
  "answer_index": 3,
  "explanation": "Aplicação direta de faixas normativas."
}
        ```

        #### 📄 p2_0048.json

        ```json
{
  "id": "p2_auto_000",
  "topic": "Artefatos — Tremor",
  "difficulty": "medium",
  "stem": "Tremor muscular tende a gerar:",
  "options": [
    "Ruído de alta frequência",
    "Baseline wander",
    "Ondas F falsas em todas",
    "QRS alargado fixo"
  ],
  "answer_index": 0,
  "explanation": "Ruído rápido."
}
        ```

        #### 📄 p2_0049.json

        ```json
{
  "id": "p2_auto_001",
  "topic": "Técnica — Baseline wander",
  "difficulty": "easy",
  "stem": "Causa comum de baseline wander:",
  "options": [
    "Respiração/posicionamento",
    "Digitálico",
    "Hipercalemia",
    "Marcapasso"
  ],
  "answer_index": 0,
  "explanation": "Respiração e contato."
}
        ```

        #### 📄 p2_0050.json

        ```json
{
  "id": "p2_auto_002",
  "topic": "Derivações — aVR",
  "difficulty": "medium",
  "stem": "Em isquemia inferior, aVR pode mostrar:",
  "options": [
    "Elevação recíproca de ST",
    "Q patológica",
    "Delta",
    "U proeminente"
  ],
  "answer_index": 0,
  "explanation": "Recíproca ocasional."
}
        ```

        #### 📄 p2_0051.json

        ```json
{
  "id": "p2_auto_003",
  "topic": "IAM — Wellens",
  "difficulty": "hard",
  "stem": "Wellens tipo B:",
  "options": [
    "T bifásica V2–V3",
    "T hiperaguda",
    "ST difuso côncavo",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "Padrão clássico."
}
        ```

        #### 📄 p2_0052.json

        ```json
{
  "id": "p2_auto_004",
  "topic": "Eletrólitos — Hipercalemia",
  "difficulty": "medium",
  "stem": "Progressão típica:",
  "options": [
    "T apiculada → QRS largo → desaparece P",
    "PR encurtado → delta",
    "U gigante",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "Clássico."
}
        ```

        #### 📄 p2_0053.json

        ```json
{
  "id": "p2_auto_005",
  "topic": "Eletrólitos — Hipocalemia",
  "difficulty": "easy",
  "stem": "Achado:",
  "options": [
    "U proeminente",
    "T apiculada",
    "Delta",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "U alta é típico."
}
        ```

        #### 📄 p2_0054.json

        ```json
{
  "id": "p2_auto_006",
  "topic": "Ritmos — Flutter 2:1",
  "difficulty": "easy",
  "stem": "FC esperada:",
  "options": [
    "~150 bpm",
    "~75 bpm",
    "~100 bpm",
    "~200 bpm"
  ],
  "answer_index": 0,
  "explanation": "Condução 2:1."
}
        ```

        #### 📄 p2_0055.json

        ```json
{
  "id": "p2_auto_007",
  "topic": "TV vs TSV",
  "difficulty": "hard",
  "stem": "Achado que favorece TV:",
  "options": [
    "Dissociação AV",
    "Resposta universal à adenosina",
    "P retrógrada estreita",
    "RR irregular"
  ],
  "answer_index": 0,
  "explanation": "Sinal forte de TV."
}
        ```

        #### 📄 p2_0056.json

        ```json
{
  "id": "p2_auto_008",
  "topic": "Artefatos — Tremor",
  "difficulty": "medium",
  "stem": "Tremor muscular tende a gerar:",
  "options": [
    "Ruído de alta frequência",
    "Baseline wander",
    "Ondas F falsas em todas",
    "QRS alargado fixo"
  ],
  "answer_index": 0,
  "explanation": "Ruído rápido."
}
        ```

        #### 📄 p2_0057.json

        ```json
{
  "id": "p2_auto_009",
  "topic": "Técnica — Baseline wander",
  "difficulty": "easy",
  "stem": "Causa comum de baseline wander:",
  "options": [
    "Respiração/posicionamento",
    "Digitálico",
    "Hipercalemia",
    "Marcapasso"
  ],
  "answer_index": 0,
  "explanation": "Respiração e contato."
}
        ```

        #### 📄 p2_0058.json

        ```json
{
  "id": "p2_auto_010",
  "topic": "Derivações — aVR",
  "difficulty": "medium",
  "stem": "Em isquemia inferior, aVR pode mostrar:",
  "options": [
    "Elevação recíproca de ST",
    "Q patológica",
    "Delta",
    "U proeminente"
  ],
  "answer_index": 0,
  "explanation": "Recíproca ocasional."
}
        ```

        #### 📄 p2_0059.json

        ```json
{
  "id": "p2_auto_011",
  "topic": "IAM — Wellens",
  "difficulty": "hard",
  "stem": "Wellens tipo B:",
  "options": [
    "T bifásica V2–V3",
    "T hiperaguda",
    "ST difuso côncavo",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "Padrão clássico."
}
        ```

        #### 📄 p2_0060.json

        ```json
{
  "id": "p2_auto_012",
  "topic": "Eletrólitos — Hipercalemia",
  "difficulty": "medium",
  "stem": "Progressão típica:",
  "options": [
    "T apiculada → QRS largo → desaparece P",
    "PR encurtado → delta",
    "U gigante",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "Clássico."
}
        ```

        #### 📄 p2_0061.json

        ```json
{
  "id": "p2_auto_013",
  "topic": "Eletrólitos — Hipocalemia",
  "difficulty": "easy",
  "stem": "Achado:",
  "options": [
    "U proeminente",
    "T apiculada",
    "Delta",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "U alta é típico."
}
        ```

        #### 📄 p2_0062.json

        ```json
{
  "id": "p2_auto_014",
  "topic": "Ritmos — Flutter 2:1",
  "difficulty": "easy",
  "stem": "FC esperada:",
  "options": [
    "~150 bpm",
    "~75 bpm",
    "~100 bpm",
    "~200 bpm"
  ],
  "answer_index": 0,
  "explanation": "Condução 2:1."
}
        ```

        #### 📄 p2_0063.json

        ```json
{
  "id": "p2_auto_015",
  "topic": "TV vs TSV",
  "difficulty": "hard",
  "stem": "Achado que favorece TV:",
  "options": [
    "Dissociação AV",
    "Resposta universal à adenosina",
    "P retrógrada estreita",
    "RR irregular"
  ],
  "answer_index": 0,
  "explanation": "Sinal forte de TV."
}
        ```

        #### 📄 p2_0064.json

        ```json
{
  "id": "p2_auto_016",
  "topic": "Artefatos — Tremor",
  "difficulty": "medium",
  "stem": "Tremor muscular tende a gerar:",
  "options": [
    "Ruído de alta frequência",
    "Baseline wander",
    "Ondas F falsas em todas",
    "QRS alargado fixo"
  ],
  "answer_index": 0,
  "explanation": "Ruído rápido."
}
        ```

        #### 📄 p2_0065.json

        ```json
{
  "id": "p2_auto_017",
  "topic": "Técnica — Baseline wander",
  "difficulty": "easy",
  "stem": "Causa comum de baseline wander:",
  "options": [
    "Respiração/posicionamento",
    "Digitálico",
    "Hipercalemia",
    "Marcapasso"
  ],
  "answer_index": 0,
  "explanation": "Respiração e contato."
}
        ```

        #### 📄 p2_0066.json

        ```json
{
  "id": "p2_auto_018",
  "topic": "Derivações — aVR",
  "difficulty": "medium",
  "stem": "Em isquemia inferior, aVR pode mostrar:",
  "options": [
    "Elevação recíproca de ST",
    "Q patológica",
    "Delta",
    "U proeminente"
  ],
  "answer_index": 0,
  "explanation": "Recíproca ocasional."
}
        ```

        #### 📄 p2_0067.json

        ```json
{
  "id": "p2_auto_019",
  "topic": "IAM — Wellens",
  "difficulty": "hard",
  "stem": "Wellens tipo B:",
  "options": [
    "T bifásica V2–V3",
    "T hiperaguda",
    "ST difuso côncavo",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "Padrão clássico."
}
        ```

        #### 📄 p2_0068.json

        ```json
{
  "id": "p2_auto_020",
  "topic": "Eletrólitos — Hipercalemia",
  "difficulty": "medium",
  "stem": "Progressão típica:",
  "options": [
    "T apiculada → QRS largo → desaparece P",
    "PR encurtado → delta",
    "U gigante",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "Clássico."
}
        ```

        #### 📄 p2_0069.json

        ```json
{
  "id": "p2_auto_021",
  "topic": "Eletrólitos — Hipocalemia",
  "difficulty": "easy",
  "stem": "Achado:",
  "options": [
    "U proeminente",
    "T apiculada",
    "Delta",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "U alta é típico."
}
        ```

        #### 📄 p2_0070.json

        ```json
{
  "id": "p2_auto_022",
  "topic": "Ritmos — Flutter 2:1",
  "difficulty": "easy",
  "stem": "FC esperada:",
  "options": [
    "~150 bpm",
    "~75 bpm",
    "~100 bpm",
    "~200 bpm"
  ],
  "answer_index": 0,
  "explanation": "Condução 2:1."
}
        ```

        #### 📄 p2_0071.json

        ```json
{
  "id": "p2_auto_023",
  "topic": "TV vs TSV",
  "difficulty": "hard",
  "stem": "Achado que favorece TV:",
  "options": [
    "Dissociação AV",
    "Resposta universal à adenosina",
    "P retrógrada estreita",
    "RR irregular"
  ],
  "answer_index": 0,
  "explanation": "Sinal forte de TV."
}
        ```

        #### 📄 p2_0072.json

        ```json
{
  "id": "p2_auto_024",
  "topic": "Artefatos — Tremor",
  "difficulty": "medium",
  "stem": "Tremor muscular tende a gerar:",
  "options": [
    "Ruído de alta frequência",
    "Baseline wander",
    "Ondas F falsas em todas",
    "QRS alargado fixo"
  ],
  "answer_index": 0,
  "explanation": "Ruído rápido."
}
        ```

        #### 📄 p2_0073.json

        ```json
{
  "id": "p2_auto_025",
  "topic": "Técnica — Baseline wander",
  "difficulty": "easy",
  "stem": "Causa comum de baseline wander:",
  "options": [
    "Respiração/posicionamento",
    "Digitálico",
    "Hipercalemia",
    "Marcapasso"
  ],
  "answer_index": 0,
  "explanation": "Respiração e contato."
}
        ```

        #### 📄 p2_0074.json

        ```json
{
  "id": "p2_auto_026",
  "topic": "Derivações — aVR",
  "difficulty": "medium",
  "stem": "Em isquemia inferior, aVR pode mostrar:",
  "options": [
    "Elevação recíproca de ST",
    "Q patológica",
    "Delta",
    "U proeminente"
  ],
  "answer_index": 0,
  "explanation": "Recíproca ocasional."
}
        ```

        #### 📄 p2_0075.json

        ```json
{
  "id": "p2_auto_027",
  "topic": "IAM — Wellens",
  "difficulty": "hard",
  "stem": "Wellens tipo B:",
  "options": [
    "T bifásica V2–V3",
    "T hiperaguda",
    "ST difuso côncavo",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "Padrão clássico."
}
        ```

        #### 📄 p2_0076.json

        ```json
{
  "id": "p2_auto_028",
  "topic": "Eletrólitos — Hipercalemia",
  "difficulty": "medium",
  "stem": "Progressão típica:",
  "options": [
    "T apiculada → QRS largo → desaparece P",
    "PR encurtado → delta",
    "U gigante",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "Clássico."
}
        ```

        #### 📄 p2_0077.json

        ```json
{
  "id": "p2_auto_029",
  "topic": "Eletrólitos — Hipocalemia",
  "difficulty": "easy",
  "stem": "Achado:",
  "options": [
    "U proeminente",
    "T apiculada",
    "Delta",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "U alta é típico."
}
        ```

        #### 📄 p2_0078.json

        ```json
{
  "id": "p2_auto_030",
  "topic": "Ritmos — Flutter 2:1",
  "difficulty": "easy",
  "stem": "FC esperada:",
  "options": [
    "~150 bpm",
    "~75 bpm",
    "~100 bpm",
    "~200 bpm"
  ],
  "answer_index": 0,
  "explanation": "Condução 2:1."
}
        ```

        #### 📄 p2_0079.json

        ```json
{
  "id": "p2_auto_031",
  "topic": "TV vs TSV",
  "difficulty": "hard",
  "stem": "Achado que favorece TV:",
  "options": [
    "Dissociação AV",
    "Resposta universal à adenosina",
    "P retrógrada estreita",
    "RR irregular"
  ],
  "answer_index": 0,
  "explanation": "Sinal forte de TV."
}
        ```

        #### 📄 p2_0080.json

        ```json
{
  "id": "p2_auto_032",
  "topic": "Artefatos — Tremor",
  "difficulty": "medium",
  "stem": "Tremor muscular tende a gerar:",
  "options": [
    "Ruído de alta frequência",
    "Baseline wander",
    "Ondas F falsas em todas",
    "QRS alargado fixo"
  ],
  "answer_index": 0,
  "explanation": "Ruído rápido."
}
        ```

        #### 📄 p2_0081.json

        ```json
{
  "id": "p2_auto_033",
  "topic": "Técnica — Baseline wander",
  "difficulty": "easy",
  "stem": "Causa comum de baseline wander:",
  "options": [
    "Respiração/posicionamento",
    "Digitálico",
    "Hipercalemia",
    "Marcapasso"
  ],
  "answer_index": 0,
  "explanation": "Respiração e contato."
}
        ```

        #### 📄 p2_0082.json

        ```json
{
  "id": "p2_auto_034",
  "topic": "Derivações — aVR",
  "difficulty": "medium",
  "stem": "Em isquemia inferior, aVR pode mostrar:",
  "options": [
    "Elevação recíproca de ST",
    "Q patológica",
    "Delta",
    "U proeminente"
  ],
  "answer_index": 0,
  "explanation": "Recíproca ocasional."
}
        ```

        #### 📄 p2_0083.json

        ```json
{
  "id": "p2_auto_035",
  "topic": "IAM — Wellens",
  "difficulty": "hard",
  "stem": "Wellens tipo B:",
  "options": [
    "T bifásica V2–V3",
    "T hiperaguda",
    "ST difuso côncavo",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "Padrão clássico."
}
        ```

        #### 📄 p2_0084.json

        ```json
{
  "id": "p2_auto_036",
  "topic": "Eletrólitos — Hipercalemia",
  "difficulty": "medium",
  "stem": "Progressão típica:",
  "options": [
    "T apiculada → QRS largo → desaparece P",
    "PR encurtado → delta",
    "U gigante",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "Clássico."
}
        ```

        #### 📄 p2_0085.json

        ```json
{
  "id": "p2_auto_037",
  "topic": "Eletrólitos — Hipocalemia",
  "difficulty": "easy",
  "stem": "Achado:",
  "options": [
    "U proeminente",
    "T apiculada",
    "Delta",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "U alta é típico."
}
        ```

        #### 📄 p2_0086.json

        ```json
{
  "id": "p2_auto_038",
  "topic": "Ritmos — Flutter 2:1",
  "difficulty": "easy",
  "stem": "FC esperada:",
  "options": [
    "~150 bpm",
    "~75 bpm",
    "~100 bpm",
    "~200 bpm"
  ],
  "answer_index": 0,
  "explanation": "Condução 2:1."
}
        ```

        #### 📄 p2_0087.json

        ```json
{
  "id": "p2_auto_039",
  "topic": "TV vs TSV",
  "difficulty": "hard",
  "stem": "Achado que favorece TV:",
  "options": [
    "Dissociação AV",
    "Resposta universal à adenosina",
    "P retrógrada estreita",
    "RR irregular"
  ],
  "answer_index": 0,
  "explanation": "Sinal forte de TV."
}
        ```

        #### 📄 p2_0088.json

        ```json
{
  "id": "p2_auto_040",
  "topic": "Artefatos — Tremor",
  "difficulty": "medium",
  "stem": "Tremor muscular tende a gerar:",
  "options": [
    "Ruído de alta frequência",
    "Baseline wander",
    "Ondas F falsas em todas",
    "QRS alargado fixo"
  ],
  "answer_index": 0,
  "explanation": "Ruído rápido."
}
        ```

        #### 📄 p2_0089.json

        ```json
{
  "id": "p2_auto_041",
  "topic": "Técnica — Baseline wander",
  "difficulty": "easy",
  "stem": "Causa comum de baseline wander:",
  "options": [
    "Respiração/posicionamento",
    "Digitálico",
    "Hipercalemia",
    "Marcapasso"
  ],
  "answer_index": 0,
  "explanation": "Respiração e contato."
}
        ```

        #### 📄 p2_0090.json

        ```json
{
  "id": "p2_auto_042",
  "topic": "Derivações — aVR",
  "difficulty": "medium",
  "stem": "Em isquemia inferior, aVR pode mostrar:",
  "options": [
    "Elevação recíproca de ST",
    "Q patológica",
    "Delta",
    "U proeminente"
  ],
  "answer_index": 0,
  "explanation": "Recíproca ocasional."
}
        ```

        #### 📄 p2_0091.json

        ```json
{
  "id": "p2_auto_043",
  "topic": "IAM — Wellens",
  "difficulty": "hard",
  "stem": "Wellens tipo B:",
  "options": [
    "T bifásica V2–V3",
    "T hiperaguda",
    "ST difuso côncavo",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "Padrão clássico."
}
        ```

        #### 📄 p2_0092.json

        ```json
{
  "id": "p2_auto_044",
  "topic": "Eletrólitos — Hipercalemia",
  "difficulty": "medium",
  "stem": "Progressão típica:",
  "options": [
    "T apiculada → QRS largo → desaparece P",
    "PR encurtado → delta",
    "U gigante",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "Clássico."
}
        ```

        #### 📄 p2_0093.json

        ```json
{
  "id": "p2_auto_045",
  "topic": "Eletrólitos — Hipocalemia",
  "difficulty": "easy",
  "stem": "Achado:",
  "options": [
    "U proeminente",
    "T apiculada",
    "Delta",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "U alta é típico."
}
        ```

        #### 📄 p2_0094.json

        ```json
{
  "id": "p2_auto_046",
  "topic": "Ritmos — Flutter 2:1",
  "difficulty": "easy",
  "stem": "FC esperada:",
  "options": [
    "~150 bpm",
    "~75 bpm",
    "~100 bpm",
    "~200 bpm"
  ],
  "answer_index": 0,
  "explanation": "Condução 2:1."
}
        ```

        #### 📄 p2_0095.json

        ```json
{
  "id": "p2_auto_047",
  "topic": "TV vs TSV",
  "difficulty": "hard",
  "stem": "Achado que favorece TV:",
  "options": [
    "Dissociação AV",
    "Resposta universal à adenosina",
    "P retrógrada estreita",
    "RR irregular"
  ],
  "answer_index": 0,
  "explanation": "Sinal forte de TV."
}
        ```

        #### 📄 p2_0096.json

        ```json
{
  "id": "p2_auto_048",
  "topic": "Artefatos — Tremor",
  "difficulty": "medium",
  "stem": "Tremor muscular tende a gerar:",
  "options": [
    "Ruído de alta frequência",
    "Baseline wander",
    "Ondas F falsas em todas",
    "QRS alargado fixo"
  ],
  "answer_index": 0,
  "explanation": "Ruído rápido."
}
        ```

        #### 📄 p2_0097.json

        ```json
{
  "id": "p2_auto_049",
  "topic": "Técnica — Baseline wander",
  "difficulty": "easy",
  "stem": "Causa comum de baseline wander:",
  "options": [
    "Respiração/posicionamento",
    "Digitálico",
    "Hipercalemia",
    "Marcapasso"
  ],
  "answer_index": 0,
  "explanation": "Respiração e contato."
}
        ```

        #### 📄 p2_0098.json

        ```json
{
  "id": "p2_auto_050",
  "topic": "Derivações — aVR",
  "difficulty": "medium",
  "stem": "Em isquemia inferior, aVR pode mostrar:",
  "options": [
    "Elevação recíproca de ST",
    "Q patológica",
    "Delta",
    "U proeminente"
  ],
  "answer_index": 0,
  "explanation": "Recíproca ocasional."
}
        ```

        #### 📄 p2_0099.json

        ```json
{
  "id": "p2_auto_051",
  "topic": "IAM — Wellens",
  "difficulty": "hard",
  "stem": "Wellens tipo B:",
  "options": [
    "T bifásica V2–V3",
    "T hiperaguda",
    "ST difuso côncavo",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "Padrão clássico."
}
        ```

        #### 📄 p2_0100.json

        ```json
{
  "id": "p2_auto_052",
  "topic": "Eletrólitos — Hipercalemia",
  "difficulty": "medium",
  "stem": "Progressão típica:",
  "options": [
    "T apiculada → QRS largo → desaparece P",
    "PR encurtado → delta",
    "U gigante",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "Clássico."
}
        ```

        #### 📄 p2_0101.json

        ```json
{
  "id": "p2_auto_053",
  "topic": "Eletrólitos — Hipocalemia",
  "difficulty": "easy",
  "stem": "Achado:",
  "options": [
    "U proeminente",
    "T apiculada",
    "Delta",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "U alta é típico."
}
        ```

        #### 📄 p2_0102.json

        ```json
{
  "id": "p2_auto_054",
  "topic": "Ritmos — Flutter 2:1",
  "difficulty": "easy",
  "stem": "FC esperada:",
  "options": [
    "~150 bpm",
    "~75 bpm",
    "~100 bpm",
    "~200 bpm"
  ],
  "answer_index": 0,
  "explanation": "Condução 2:1."
}
        ```

        #### 📄 p2_0103.json

        ```json
{
  "id": "p2_auto_055",
  "topic": "TV vs TSV",
  "difficulty": "hard",
  "stem": "Achado que favorece TV:",
  "options": [
    "Dissociação AV",
    "Resposta universal à adenosina",
    "P retrógrada estreita",
    "RR irregular"
  ],
  "answer_index": 0,
  "explanation": "Sinal forte de TV."
}
        ```

        #### 📄 p2_0104.json

        ```json
{
  "id": "p2_auto_056",
  "topic": "Artefatos — Tremor",
  "difficulty": "medium",
  "stem": "Tremor muscular tende a gerar:",
  "options": [
    "Ruído de alta frequência",
    "Baseline wander",
    "Ondas F falsas em todas",
    "QRS alargado fixo"
  ],
  "answer_index": 0,
  "explanation": "Ruído rápido."
}
        ```

        #### 📄 p2_0105.json

        ```json
{
  "id": "p2_auto_057",
  "topic": "Técnica — Baseline wander",
  "difficulty": "easy",
  "stem": "Causa comum de baseline wander:",
  "options": [
    "Respiração/posicionamento",
    "Digitálico",
    "Hipercalemia",
    "Marcapasso"
  ],
  "answer_index": 0,
  "explanation": "Respiração e contato."
}
        ```

        #### 📄 p2_0106.json

        ```json
{
  "id": "p2_auto_058",
  "topic": "Derivações — aVR",
  "difficulty": "medium",
  "stem": "Em isquemia inferior, aVR pode mostrar:",
  "options": [
    "Elevação recíproca de ST",
    "Q patológica",
    "Delta",
    "U proeminente"
  ],
  "answer_index": 0,
  "explanation": "Recíproca ocasional."
}
        ```

        #### 📄 p2_0107.json

        ```json
{
  "id": "p2_auto_059",
  "topic": "IAM — Wellens",
  "difficulty": "hard",
  "stem": "Wellens tipo B:",
  "options": [
    "T bifásica V2–V3",
    "T hiperaguda",
    "ST difuso côncavo",
    "Delta"
  ],
  "answer_index": 0,
  "explanation": "Padrão clássico."
}
        ```

        #### 📄 p2_0108.json

        ```json
{
  "id": "p2_auto_060",
  "topic": "Eletrólitos — Hipercalemia",
  "difficulty": "medium",
  "stem": "Progressão típica:",
  "options": [
    "T apiculada → QRS largo → desaparece P",
    "PR encurtado → delta",
    "U gigante",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "Clássico."
}
        ```

        #### 📄 p2_0109.json

        ```json
{
  "id": "p2_auto_061",
  "topic": "Eletrólitos — Hipocalemia",
  "difficulty": "easy",
  "stem": "Achado:",
  "options": [
    "U proeminente",
    "T apiculada",
    "Delta",
    "ST difuso"
  ],
  "answer_index": 0,
  "explanation": "U alta é típico."
}
        ```

        #### 📄 p2_0110.json

        ```json
{
  "id": "p2_auto_062",
  "topic": "Ritmos — Flutter 2:1",
  "difficulty": "easy",
  "stem": "FC esperada:",
  "options": [
    "~150 bpm",
    "~75 bpm",
    "~100 bpm",
    "~200 bpm"
  ],
  "answer_index": 0,
  "explanation": "Condução 2:1."
}
        ```

    ### 📁 schema/

      #### 📄 mcq.schema.json

      ```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ECG MCQ",
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "topic": {
      "type": "string"
    },
    "difficulty": {
      "type": "string",
      "enum": [
        "easy",
        "medium",
        "hard"
      ]
    },
    "stem": {
      "type": "string"
    },
    "options": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 2
    },
    "answer_index": {
      "type": "integer",
      "minimum": 0
    },
    "explanation": {
      "type": "string"
    }
  },
  "required": [
    "id",
    "topic",
    "difficulty",
    "stem",
    "options",
    "answer_index",
    "explanation"
  ]
}
      ```

  ### 📁 docs/

    #### 📄 arquitetura.md

    ```md
# Arquitetura — visão p0

- **CLI (Typer/Rich)** para quizzes, utilitários e análises rápidas.
- **Web (Dash)** para gráficos interativos (multi-derivações, zoom, overlays) e casos.
- **Notebooks** complementares (demonstrações/experimentos).
- **Quiz JSON Schema** garante consistência e validação de banco MCQ.
- **IA (GPT‑5)** integrará laudo preliminar e tutoria guiada em p2/p3.

Decisões:
- **Python** centraliza análise/educação; **JS/Dash** cuida do front interativo.
- **Licenças abertas** (MIT/CC‑BY‑SA) para longevidade e colaboração.

    ```

    #### 📄 dados_fontes.md

    ```md
# Dados & Fontes (p0)

- Repositórios educacionais open-source (ex.: LITFL ECG Library), PhysioNet (WFDB).
- Imagens com licença compatível (CC-BY/CC0). Atribua sempre que necessário.
- Em p1–p3 definiremos lista canônica de referências e créditos de imagens.

    ```

    #### 📄 dev_analyze.md

    ```md
# Dev — analyze values (p2)

## Entradas
- `--pr` (ms), `--qrs` (ms), `--qt` (ms), `--rr` (ms) ou `--fc` (bpm)
- `--lead-i` e `--avf` (mV líquidos do QRS; positivos se R>S)
- `--sexo` (M/F) para limiares de QTc (M:450, F:470); se ausente, usa 460 ms

## Saídas
- FC, QTc (Bazett, Fridericia), eixo (rótulo + ângulo aproximado), flags
- Relatórios `reports/*_analyze_values.json|.md`

> Uso educacional.

    ```

    #### 📄 dev_ingest.md

    ```md
# Dev — ingest image (p3)

## Pipeline p3 (MVP)
1. Abrir imagem via Pillow (PNG/JPG). PDF: suportado apenas se backend disponível no Pillow (1ª página).
2. Procurar sidecar META: `<arquivo>.meta.json` ou `--meta path.json`.
3. Se META presente:
   - Ler calibração: dpi, mm/mV, ms/div, layout.
   - Ler medidas provisionadas (educacionais no MVP): PR/QRS/QT/RR/FC, I/aVF.
   - Calcular QTc (Bazett/Fridericia) e eixo.
4. Montar `report` conforme `reporting/schema/report.schema.json` e salvar (`--report`).

> p4–p6: OCR da grade, segmentação das derivações, extração de intervalos com detecção de ondas, calibração automática.

## Limitações (intencionais para MVP p3)
- Sem CV robusta: dependemos de META para escala/medidas confiáveis.
- Upload no Dash não roda análise pesada; serve de preview e teste do contrato de META.

## Contrato de META (exemplo)
```json
{
  "dpi": 300,
  "mm_per_mV": 10,
  "ms_per_div": 200,
  "leads_layout": "3x4",
  "sexo": "M",
  "measures": {
    "pr_ms": 160, "qrs_ms": 100, "qt_ms": 380, "rr_ms": 800, "fc_bpm": 75,
    "lead_i_mv": 6, "avf_mv": 3
  },
  "patient_id": "ID-OPCIONAL",
  "age": 55, "context": "Texto livre."
}
```

    ```

    #### 📄 dev_p5_deskew_scale_layouts.md

    ```md
# Dev — Parte 5/30 (Deskew + Normalização + Layouts) — 2025-09-25

## Novidades
- **Deskew**: `cv.deskew.estimate_rotation_angle` (varredura ±6°; métrica = variância de projeções de gradiente). `rotate_image` aplica correção.
- **Normalização de escala**: `cv.normalize.normalize_scale` estima px/mm via grade e redimensiona para alvo (10 px/mm, *clamped* 0.5–2×).
- **Layouts**: `cv.segmentation_ext.segment_layout` suporta `3x4`, `6x2` e `3x4+rhythm (II)`.

## Integração CLI
- `python -m ecgcourse cv deskew <img> --save out.png`
- `python -m ecgcourse cv normalize <img> --pxmm 10 --save out.png`
- `python -m ecgcourse cv layout-seg <img> --layout 6x2 --json`
- `python -m ecgcourse ingest image <img> --deskew --normalize --auto-grid --schema-v2 --report`

## Considerações técnicas
- A métrica de deskew é robusta para pequenas rotações típicas de scanners; picos de ruído podem afetar o score, mas a busca bruta suaviza.
- A normalização adota **no-upscale agressivo** (máx 2×) para preservar legibilidade e *throughput* no web build.
- Layouts não padronizados ainda dependerão de escolha manual no p5; detecção automática de layout entra no p6 (OCR de rótulos e *template matching*).

    ```

    #### 📄 dev_p6_layout_rpeaks.md

    ```md
# Dev — Parte 6/30 (Layout/Lead OCR + R-peaks) — 2025-09-25


## O que foi adicionado
- **OCR leve de rótulos** (`cv.lead_ocr`): template matching (OpenCV) + fallback **pytesseract** (opcional) + *fuzzy matching* (rapidfuzz).
- **Detecção automática de layout** (`cv.lead_ocr.choose_layout`): avalia candidatos (3x4, 6x2, 3x4+ritmo) comparando rótulos esperados e seleciona o maior escore.
- **R-peaks a partir de imagem** (`cv.rpeaks_from_image`): traçado 1D por coluna (mínimo da banda central), *smoothing* e picos por **z-score** → FC/RR.

## Integração CLI
- `python -m ecgcourse cv detect-layout <img> --json`
- `python -m ecgcourse cv detect-leads <img> --layout 3x4 --json`
- `python -m ecgcourse cv rpeaks <img> --layout 3x4 --lead II --speed 25 --json`
- `python -m ecgcourse ingest image <img> --deskew --normalize --auto-grid --auto-leads --rpeaks-lead II --schema-v3 --report`

## Schema v0.3
- Bloco `layout_detection` com `layout`, `score`, `labels[{{bbox,label,score}}]`.
- Bloco `rpeaks` com `lead_used`, `peaks_idx`, `rr_sec`, `hr_bpm_mean`, `hr_bpm_median`.

## Limitações e roadmap
- OCR depende de *render* simples e/ou Tesseract; para impressões ruidosas, considerar *text spotting* dedicado (p7–p8).
- R-peaks via imagem é uma aproximação; precisão melhora com **normalização de escala**, **deskew** e **contraste**. P7: picos R mais robustos e estimativa de **PR/QRS/QT** (onsets/offsets) validada com grade.

    ```

    #### 📄 dev_p7_rpeaks_intervals_quiz.md

    ```md
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

    ```

    #### 📄 p2_changelog.md

    ```md
# Changelog p2 — 2025-09-25

- CLI: `analyze values` (QTc Bazett/Fridericia, eixo I/aVF, flags educativas).
- Dash: adicionada calculadora QTc.
- Notebooks: 5 cadernos educativos.
- Quiz: +110 MCQs (p2) adicionados.

    ```

    #### 📄 p3_changelog.md

    ```md
# Changelog p3 — 2025-09-25

- CLI: `ingest image` com suporte a META sidecar e geração de laudo no schema v0.1.
- Schema: `reporting/schema/report.schema.json`.
- Dash: upload/preview + sumarização de META (QTc/eixo se fornecidos).
- Amostras: ECG sintético 12-lead + META (calibração/medidas).
- Notebooks: pré-processamento básico e noções de detecção de grade.
- Quiz: +60 MCQs (posicionamento, marcapasso, canalopatias, armadilhas).

    ```

    #### 📄 p3b_assets.md

    ```md

# Assets: ECG Images & Datasets (Manifest v1)

Este diretório contém manifestos **JSONL** para automação de *download* e versionamento dos recursos visuais do curso.

## Por que JSONL?
- Escala: cada linha é um item independente (processamento *streaming*).
- Robustez: fácil "append", *diff* e *merge* via Git.
- Flexibilidade: campos podem evoluir sem quebrar leitores mais antigos.

## Arquivos
- `assets/manifest/ecg_images.v1.jsonl` — imagens (Wikimedia Commons) para uso direto na **interface web** (não-CLI).
- `assets/manifest/ecg_images_index.csv` — índice amigável para planilha/Excel.
- `assets/manifest/ecg_datasets.v1.jsonl` — bases WFDB (PhysioNet) para gerar figuras sob demanda.
- `scripts/python/download_assets.py` — *downloader* paralelo dos itens de `ecg_images.v1.jsonl`.

> **Licenças**: muitos itens estão sob **CC BY‑SA**. Os campos `license` e `license_verified` indicam o status atual. Antes do *deploy* público, execute uma verificação automática e gere créditos no rodapé. Itens com `VERIFY_ON_PAGE` exigem checagem manual e atribuição.

## Uso rápido
```bash
python3 scripts/python/download_assets.py
# Saída: assets/raw/images/<id>.<ext>
```

## Recomendações para a Web (Next.js/Vite)
1. **Pré‑processamento**: otimize e gere *thumbnails* responsivos (AVIF/WEBP) a partir de `assets/raw/images/`.
2. **Acessibilidade**: derive `alt` dinâmico de `condition` e `tags` do manifesto.
3. **Créditos**: exiba `author`, `license` e link `page_url` no *modal* de visualização.

## WFDB (PhysioNet)
Use os *datasets* para renderizar PNG/SVG de traçados específicos por patologia, mantendo reprodutibilidade. Sugestões:
- Python: `wfdb`, `numpy`, `matplotlib` (render neutro), `scipy`.
- Geração *server-side* (celery/worker) ou *build-time* (scripts) para páginas estáticas.


    ```

    #### 📄 p3c_assets_pipeline.md

    ```md
# Parte 3c — Pipeline de Assets (Licenças + Web Derivatives) — 2025-09-25

## Objetivos
1. **Verificar licenças/autor** das imagens listadas em `assets/manifest/ecg_images.v1.jsonl`.
2. **Pré-processar** imagens para formatos/grades **Web-first** (WEBP e opcionalmente AVIF) + diferentes larguras.

## Passos (local ou CI)
```bash
# 1) download
python -m ecgcourse assets download

# 2) verificar licenças + créditos
python -m ecgcourse assets verify
# gera: assets/manifest/ecg_images.verified.jsonl
#       assets/credits/credits.(md|json)

# 3) pré-processar para a web (WEBP/AVIF + manifest)
python -m ecgcourse assets preprocess
# gera: assets/derived/images/<id>/w(320, 640, 1024, 1600)/*.(webp|avif)
#       assets/manifest/ecg_images.derived.json
```

> **Observação:** AVIF depende de `pillow-avif-plugin`. Se indisponível na sua plataforma, o pipeline cai graciosamente para apenas WEBP.

## Integração no Front-end (exemplo)
- Leia `assets/manifest/ecg_images.derived.json` e `ecg_images.verified.jsonl` para montar a galeria:
  - escolha o melhor tamanho por *breakpoint* (320/640/1024/1600).
  - sirva `AVIF` se suportado pelo navegador, caindo para `WEBP`.
- Exiba créditos/atribuição com `assets/credits/credits.md` (ou JSON).

## Limites e próximos incrementos
- A verificação usa heurísticas para Wikimedia; páginas fora desse domínio podem exigir *parsers* dedicados.
- p4/p5 incluirão *hashing* (SHA256) e *integrity checks* além de *thumbnails* responsivos e *LQIP* base64.

    ```

    #### 📄 p5_changelog.md

    ```md
# Changelog p5 — 2025-09-25

- **Deskew**: varredura de ângulo ±6° com maximização da variância de projeções de gradiente.
- **Normalização de escala**: px/mm alvo (10), clamp 0.5–2×.
- **Layouts**: segmentação para 3×4, 6×2 e 3×4+ritmo.
- **CLI**: novos comandos `cv deskew|normalize|layout-seg` e flags `--deskew/--normalize` na ingestão.
- **Dash**: switches para deskew/normalize e seletor de layout.
- **Notebooks**: 19–21 com demonstrações.

    ```

    #### 📄 quiz_guide.md

    ```md
# Guia de Quiz (MCQ)

- Use `quiz/schema/mcq.schema.json` para validar consistência.
- Cada item precisa de **explicação robusta** e referência à seção do curso.
- Dificuldades: `easy|medium|hard`. Evite pegadinhas não clínicas.
- Use imagens quando agregarem (referencie em `images/`).

    ```

    #### 📄 roadmap.md

    ```md
# Roadmap 0→30 (recorte p0–p5)

- **p0**: estrutura, guias, deps, stubs CLI/Web, schema MCQ, 3 notebooks seed.
- **p1**: CLI quiz completa; 50 MCQs validados; Dash 12 derivações estáticas + zoom.
- **p2**: Heurísticas por valores (PR/QRS/QTc/eixo); 150 MCQs; 5 notebooks úteis.
- **p3**: Upload imagem + OpenCV + IA; cases interativos; 300 MCQs; export de laudo.
- **p4**: Dash avançado (filtros, simulação íons); adaptatividade/relatórios.
- **p5**: FastAPI opcional; empacotamento (PWA/app macOS/iOS).
- **p6–p30**: expansão de conteúdo avançado, datasets, validação clínica ampla.

    ```

    #### 📄 syllabus.md

    ```md
# Syllabus (Resumo) — p0

- Fundamentos de bioeletrogênese e potenciais de ação (miócito × marcapasso).
- Sistema de condução: nó SA, AV, His‑Purkinje; períodos refratários.
- Derivações (12 canais), posicionamento e artefatos.
- Ondas/segmentos/intervalos: P, PR, QRS, ST, T, QT/QTc; correlação mecânica.
- Eixo elétrico e hipertrofias; sobrecargas atriais/ventriculares.
- Arritmias supraventriculares e ventriculares; TV/FA/Flutter; WPW/BRD/BRE.
- Isquemia/IAM (STEMI/NSTEMI), pericardite, Brugada, distúrbios iônicos e drogas.
- Casos raros e armadilhas diagnósticas; laudo estruturado e raciocínio clínico.

> **Nota:** Este syllabus será expandido em p1–p5 com objetivos de aprendizagem mensuráveis.

    ```

  ### 📁 samples/

    ### 📁 values/

      #### 📄 exemplo1.json

      ```json
{
  "pr": 180,
  "qrs": 95,
  "qt": 380,
  "rr": 800,
  "lead_i": 6,
  "avf": 3,
  "sexo": "M"
}
      ```

      #### 📄 exemplo2_qtc_longo.json

      ```json
{
  "pr": 160,
  "qrs": 100,
  "qt": 480,
  "fc": 55,
  "lead_i": 5,
  "avf": -2,
  "sexo": "F"
}
      ```

      #### 📄 exemplo3_pre_exc.json

      ```json
{
  "pr": 100,
  "qrs": 110,
  "qt": 340,
  "rr": 700,
  "lead_i": 1,
  "avf": 1,
  "sexo": "M"
}
      ```

    ### 📁 ecg_images/

      - synthetic_12lead.png `(Conteúdo não incluído)`

      #### 📄 synthetic_12lead.png.meta.json

      ```json
{
  "dpi": 300,
  "mm_per_mV": 10,
  "ms_per_div": 200,
  "leads_layout": "3x4",
  "sexo": "M",
  "measures": {
    "pr_ms": 160,
    "qrs_ms": 100,
    "qt_ms": 380,
    "rr_ms": 800,
    "fc_bpm": 75,
    "lead_i_mv": 6,
    "avf_mv": 3
  },
  "patient_id": "SYNTH-001",
  "age": 55,
  "context": "Amostra sintética educacional (p3)."
}
      ```

  ### 📁 scripts/

    ### 📁 python/

      #### 📄 download_assets.py

      ```py
#!/usr/bin/env python3
"""
Download assets listed in assets/manifest/ecg_images.v1.jsonl and datasets manifest.
- Uses Wikimedia "Special:FilePath/<filename>" URLs for original files to avoid resolution pitfalls.
- Verifies SHA1 if provided (not required here).
- Writes images to assets/raw/images/<id>.<ext>
- For datasets, only prints instructions (WFDB download typically requires tarballs and parsing).
"""
import os, sys, json, hashlib, pathlib, urllib.request, urllib.error
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = pathlib.Path(__file__).resolve().parents[2]  # project root
MANIFEST_IMG = BASE / "assets/manifest/ecg_images.v1.jsonl"
OUT_DIR = BASE / "assets/raw/images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def infer_ext_from_url(url: str) -> str:
    path = urlparse(url).path
    ext = os.path.splitext(path)[1] or ".bin"
    # For Special:FilePath the extension is embedded in the file name within the URL
    return ext

def download_one(entry: dict, timeout=60):
    url = entry["file_url"]
    eid = entry["id"]
    ext = infer_ext_from_url(url)
    out_path = OUT_DIR / f"{eid}{ext}"
    if out_path.exists():
        return eid, "exists", out_path
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r, open(out_path, "wb") as f:
            f.write(r.read())
        return eid, "downloaded", out_path
    except urllib.error.HTTPError as e:
        return eid, f"http_error_{e.code}", None
    except Exception as e:
        return eid, f"error_{type(e).__name__}", None

def main():
    entries = []
    with open(MANIFEST_IMG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                print("Skipping bad line:", line[:120], file=sys.stderr)

    print(f"Downloading {len(entries)} images to {OUT_DIR} ...")
    ok = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(download_one, e) for e in entries]
        for fut in as_completed(futs):
            eid, status, path = fut.result()
            if status == "downloaded":
                ok += 1
                print(f"[OK] {eid} -> {path}")
            elif status == "exists":
                print(f"[SKIP] {eid} already exists")
            else:
                print(f"[ERR] {eid}: {status}")
    print(f"Done. {ok} files downloaded.")

if __name__ == "__main__":
    sys.exit(main())

      ```

      #### 📄 preprocess_images.py

      ```py
#!/usr/bin/env python3
"""
Pré-processador de imagens para Web (p3c).
- Lê assets/raw/images/<id>.<ext>
- Gera WEBP (sempre) e AVIF (se pillow-avif-plugin disponível)
- Tamanhos-alvo (larguras): 320, 640, 1024, 1600 (sem upscaling)
- Stripa metadados e garante compressão eficiente
- Emite manifest derivado: assets/manifest/ecg_images.derived.json
"""
import os, sys, json, pathlib
from PIL import Image, ImageOps

# AVIF opcional
try:
    import pillow_avif  # noqa: F401
    AVIF_OK = True
except Exception:
    AVIF_OK = False

BASE = pathlib.Path(__file__).resolve().parents[2]
RAW = BASE / "assets" / "raw" / "images"
DERIVED = BASE / "assets" / "derived" / "images"
DERIVED.mkdir(parents=True, exist_ok=True)
MAN_OUT = BASE / "assets" / "manifest" / "ecg_images.derived.json"

TARGET_WIDTHS = [320, 640, 1024, 1600]

def process_one(path: pathlib.Path, out_dir: pathlib.Path):
    img = Image.open(path).convert("RGB")
    w0, h0 = img.size
    sizes = []
    for tw in TARGET_WIDTHS:
        if tw >= w0:
            tw = w0  # no upscaling
        scale = tw / w0
        th = int(h0 * scale)
        imr = img.resize((tw, th), Image.LANCZOS)
        # WEBP
        webp_dir = out_dir / f"w{tw}"
        webp_dir.mkdir(parents=True, exist_ok=True)
        webp_path = webp_dir / (path.stem + ".webp")
        imr.save(webp_path, "WEBP", quality=85, method=6)
        sizes.append({"format":"webp","width": tw, "height": th, "path": str(webp_path.relative_to(BASE))})
        # AVIF opcional
        if AVIF_OK:
            avif_path = webp_dir / (path.stem + ".avif")
            try:
                imr.save(avif_path, "AVIF", quality=50)
                sizes.append({"format":"avif","width": tw, "height": th, "path": str(avif_path.relative_to(BASE))})
            except Exception:
                pass
    return sizes

def main():
    if not RAW.exists():
        print(f"Nada a fazer: {RAW} não existe.", file=sys.stderr)
        return 1
    manifest = {}
    for fp in sorted(RAW.glob("*")):
        if not fp.is_file(): 
            continue
        eid = fp.stem
        out_dir = DERIVED / eid
        sizes = process_one(fp, out_dir)
        manifest[eid] = {"original": str(fp.relative_to(BASE)), "derived": sizes}
        print(f"[OK] {eid} -> {len(sizes)} derivados")
    with open(MAN_OUT, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"Manifesto derivado salvo em {MAN_OUT}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

      ```

      #### 📄 verify_licenses.py

      ```py
#!/usr/bin/env python3
"""
Verificador de licenças/atribuições para ecg_images JSONL (p3c).
- Lê `assets/manifest/ecg_images.v1.jsonl`
- Faz HTTP GET das `page_url`
- Extrai/license/autor (heurísticas p/ Wikimedia Commons)
- Escreve `ecg_images.verified.jsonl`
- Gera créditos: `assets/credits/credits.md` e `.json`
"""
import os, sys, json, pathlib, re, time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

BASE = pathlib.Path(__file__).resolve().parents[2]
MANIFEST_IN = BASE / "assets" / "manifest" / "ecg_images.v1.jsonl"
MANIFEST_OUT = BASE / "assets" / "manifest" / "ecg_images.verified.jsonl"
CREDITS_DIR = BASE / "assets" / "credits"
CREDITS_DIR.mkdir(parents=True, exist_ok=True)

HDRS = {"User-Agent": "ECGCourseBot/0.1 (+https://example.org; edu)"}

CC_PATTERNS = [
    ("CC BY-SA 4.0", re.compile(r"(CC\s*BY[- ]SA\s*4\.0|creativecommons\.org/licenses/by-sa/4\.0)", re.I)),
    ("CC BY-SA 3.0", re.compile(r"(CC\s*BY[- ]SA\s*3\.0|creativecommons\.org/licenses/by-sa/3\.0)", re.I)),
    ("CC BY 4.0", re.compile(r"(CC\s*BY\s*4\.0|creativecommons\.org/licenses/by/4\.0)", re.I)),
    ("CC BY 3.0", re.compile(r"(CC\s*BY\s*3\.0|creativecommons\.org/licenses/by/3\.0)", re.I)),
    ("CC0", re.compile(r"(CC0|creativecommons\.org/publicdomain/zero/1\.0)", re.I)),
    ("Public Domain", re.compile(r"(public\s*domain|creativecommons\.org/publicdomain/mark/1\.0)", re.I)),
]

def extract_license_and_author(html: str) -> (Optional[str], Optional[str]):
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)

    # License
    license_val = None
    for label, pat in CC_PATTERNS:
        if pat.search(text):
            license_val = label
            break
    if not license_val:
        # Wikimedia sometimes uses explicit "License" field
        licel = soup.find(string=re.compile(r"License", re.I))
        if licel:
            ctx = licel.parent.get_text(" ", strip=True) if hasattr(licel, "parent") else text
            for label, pat in CC_PATTERNS:
                if pat.search(ctx):
                    license_val = label
                    break

    # Author / Artist
    author = None
    for th_name in ["Author", "author", "Artist", "Photographer", "Creator"]:
        th = soup.find("th", string=re.compile(rf"^{th_name}$", re.I))
        if th and th.find_next("td"):
            author = th.find_next("td").get_text(" ", strip=True)
            break
    if not author:
        # fallback: look for "Author" anywhere
        m = re.search(r"Author\s*[:：]\s*(.+?)\s{2,}", text)
        if m:
            author = m.group(1).strip()

    return license_val, author

def verify_one(entry: Dict) -> Dict:
    out = dict(entry)
    url = entry.get("page_url")
    try:
        r = requests.get(url, headers=HDRS, timeout=30)
        r.raise_for_status()
        lic, auth = extract_license_and_author(r.text)
        if lic:
            out["license"] = lic
            out["license_verified"] = True
        if auth:
            out["author"] = auth
        out["verification_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    except Exception as e:
        out["license_verified"] = False
        out["verification_error"] = f"{type(e).__name__}: {e}"
    return out

def iter_jsonl(path: pathlib.Path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: 
                continue
            yield json.loads(line)

def write_jsonl(path: pathlib.Path, items: List[Dict]):
    with open(path, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False)+"\n")

def build_credits(items: List[Dict]):
    data = []
    for it in items:
        data.append({
            "id": it.get("id"),
            "condition": it.get("condition"),
            "author": it.get("author"),
            "license": it.get("license"),
            "page_url": it.get("page_url"),
            "source": it.get("source"),
        })
    # JSON
    with open(CREDITS_DIR / "credits.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Markdown
    lines = ["# Créditos de Imagens — ECG Course", ""]
    for d in data:
        lines.append(f"- **{d['id']}** — {d['condition']} — Autor: {d.get('author') or 'N/D'} — Licença: {d.get('license') or 'N/D'} — Fonte: {d.get('source') or 'N/D'} — [página]({d['page_url']})")
    with open(CREDITS_DIR / "credits.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines)+"\n")

def main(manifest_in=None, manifest_out=None):
    mi = pathlib.Path(manifest_in) if manifest_in else MANIFEST_IN
    mo = pathlib.Path(manifest_out) if manifest_out else MANIFEST_OUT
    items = list(iter_jsonl(mi))
    out = []
    for i, it in enumerate(items, 1):
        out.append(verify_one(it))
        if i % 5 == 0:
            print(f"... verificados {i}/{len(items)}")
    write_jsonl(mo, out)
    build_credits(out)
    print(f"OK — escrito {mo} e créditos em {CREDITS_DIR}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="manifest_in", default=None)
    p.add_argument("--out", dest="manifest_out", default=None)
    args = p.parse_args()
    sys.exit(main(args.manifest_in, args.manifest_out) or 0)

      ```

  ### 📁 cli_app/

    ### 📁 quiz/

      ### 📁 bank/

        #### 📄 exemplo_arrtimias.json

        ```json
{
  "id": "arr-0001",
  "topic": "Arritmias — FA",
  "difficulty": "medium",
  "stem": "Qual achado é mais típico de fibrilação atrial no ECG?",
  "options": [
    "Ondas P serrilhadas regulares com FC ~150 bpm",
    "Intervalos PR progressivamente mais longos até QRS cair",
    "Linha de base fibrilatória sem ondas P discretas e RR irregular",
    "QRS largo regular com dissociação AV"
  ],
  "answer_index": 2,
  "explanation": "FA: ausência de ondas P organizadas e resposta ventricular irregularmente irregular. Flutter tem ondas serrilhadas com padrões de condução, Wenckebach (Mobitz I) tem PR progressivo e TV monomórfica dá QRS largo regular."
}
        ```

      ### 📁 schema/

        #### 📄 mcq.schema.json

        ```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ECG MCQ",
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "topic": {
      "type": "string"
    },
    "difficulty": {
      "type": "string",
      "enum": [
        "easy",
        "medium",
        "hard"
      ]
    },
    "stem": {
      "type": "string"
    },
    "options": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 2
    },
    "answer_index": {
      "type": "integer",
      "minimum": 0
    },
    "explanation": {
      "type": "string"
    }
  },
  "required": [
    "id",
    "topic",
    "difficulty",
    "stem",
    "options",
    "answer_index",
    "explanation"
  ]
}
        ```

    ### 📁 ecgcourse/

      #### 📄 __init__.py

      ```py
__all__ = []

      ```

      #### 📄 cli.py

      ```py

from __future__ import annotations
import json, sys, pathlib, time, random, math
import typer
from rich import print
from rich.panel import Panel
from rich.table import Table
from jsonschema import Draft202012Validator

app = typer.Typer(help="ECGCourse CLI — quizzes, análises e utilitários.")

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_CANDIDATES = [
    REPO_ROOT / "quiz" / "schema" / "mcq.schema.json",
    REPO_ROOT / "cli_app" / "quiz" / "schema" / "mcq.schema.json",
]

def load_schema() -> dict:
    for p in SCHEMA_CANDIDATES:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    typer.echo("Schema mcq.schema.json não encontrado.", err=True)
    raise typer.Exit(code=2)

def validate_item(item: dict, schema: dict):
    Draft202012Validator(schema).validate(item)

def ask_item(item: dict) -> tuple[bool, int]:
    print(Panel.fit(f"[bold cyan]{item['topic']}[/] — dificuldade: {item['difficulty']}"))
    print(f"[bold]Q:[/] {item['stem']}\n")
    for i, opt in enumerate(item["options"]):
        print(f"  [bold]{chr(65+i)}[/]) {opt}")
    ans = input("\nSua resposta (A/B/C/D... ou 'q' para sair): ").strip().upper()
    if ans == 'Q':
        return None, None
    idx = ord(ans) - 65
    correct = idx == item["answer_index"]
    if correct:
        print(Panel.fit("[bold green]Correto![/]"))
    else:
        print(Panel.fit(f"[bold red]Incorreto[/] — correta: {chr(65+item['answer_index'])}"))
    print("\n[bold]Explicação:[/]")
    print(item["explanation"])
    return correct, idx

@app.command()
def quiz(
    action: str = typer.Argument(..., help="run|validate|bank"),
    path: str = typer.Argument(..., help="arquivo .json (run/validate) ou diretório (bank)"),
    report: bool = typer.Option(False, "--report", help="salva relatórios em reports/"),
    shuffle: bool = typer.Option(True, "--shuffle/--no-shuffle", help="embaralhar ordem no modo bank"),
    seed: int = typer.Option(0, "--seed", help="seed para reprodutibilidade (0 = auto)"),
):
    schema = load_schema()
    p = pathlib.Path(path)

    if action in ("run", "validate"):
        if not p.exists():
            typer.echo(f"Arquivo não encontrado: {p}", err=True); raise typer.Exit(code=2)
        with open(p, "r", encoding="utf-8") as f:
            item = json.load(f)
        if action == "validate":
            validate_item(item, schema); print(Panel.fit("[bold green]OK[/] — Schema válido.")); raise typer.Exit(code=0)
        validate_item(item, schema); ask_item(item); raise typer.Exit(code=0)

    if action == "bank":
        if not p.exists() or not p.is_dir():
            typer.echo(f"Diretório inválido: {p}", err=True); raise typer.Exit(code=2)
        items = []
        for fp in sorted(p.glob("*.json")):
            with open(fp, "r", encoding="utf-8") as f:
                it = json.load(f)
            validate_item(it, schema); it["_src"] = str(fp); items.append(it)
        if not items:
            typer.echo("Nenhum .json encontrado.", err=True); raise typer.Exit(code=2)
        if shuffle:
            r = random.Random(seed or time.time_ns()); r.shuffle(items)
        results = []
        for it in items:
            ans = ask_item(it)
            if ans == (None, None): break
            ok, chosen = ans
            results.append({"id": it["id"], "topic": it["topic"], "difficulty": it["difficulty"],
                            "correct": bool(ok), "chosen_index": chosen, "answer_index": it["answer_index"],
                            "src": it["_src"]})
            print("-"*60)
        if not results:
            print(Panel.fit("[bold yellow]Sem respostas registradas.[/]")); raise typer.Exit(code=0)
        total = len(results); acertos = sum(1 for r in results if r["correct"]); pct = 100.0*acertos/total
        tbl = Table(title="Resumo — Banco"); tbl.add_column("Total"); tbl.add_column("Acertos"); tbl.add_column("%")
        tbl.add_row(str(total), str(acertos), f"{pct:.1f}"); print(tbl)
        def agg(key):
            m = {}
            for r in results:
                k = r[key]; m.setdefault(k, {"n":0,"ok":0}); m[k]["n"] += 1; m[k]["ok"] += int(r["correct"])
            return {k: {"n":v["n"], "ok":v["ok"], "pct":(100.0*v["ok"]/v["n"])} for k,v in m.items()}
        by_topic = agg("topic"); by_diff = agg("difficulty")
        print(Panel.fit(f"[bold]Por tópico:[/] {by_topic}"))
        print(Panel.fit(f"[bold]Por dificuldade:[/] {by_diff}"))
        if report:
            reports_dir = (REPO_ROOT / "reports"); reports_dir.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            with open(reports_dir / f"{ts}_summary.json", "w", encoding="utf-8") as f:
                json.dump({"total": total, "correct": acertos, "pct": pct,
                           "by_topic": by_topic, "by_difficulty": by_diff, "results": results},
                          f, ensure_ascii=False, indent=2)
            with open(reports_dir / f"{ts}_summary.md", "w", encoding="utf-8") as f:
                f.write(f"# Relatório de Quiz — {ts}\n\n")
                f.write(f"- Total: {total}\n- Acertos: {acertos}\n- %: {pct:.1f}\n\n")
                f.write("## Por tópico\n\n")
                for k,v in by_topic.items():
                    f.write(f"- {k}: {v['ok']}/{v['n']} ({v['pct']:.1f}%)\n")
                f.write("\n## Por dificuldade\n\n")
                for k,v in by_diff.items():
                    f.write(f"- {k}: {v['ok']}/{v['n']} ({v['pct']:.1f}%)\n")
                f.write("\n## Itens incorretos\n\n")
                for r in results:
                    if not r["correct"]:
                        f.write(f"- {r['id']} [{r['topic']}/{r['difficulty']}] — src: {r['src']}\n")
            print(Panel.fit("[bold green]Relatórios salvos em reports/"))
        raise typer.Exit(code=0)

# Analyze subapp
analyze_app = typer.Typer(help="Análises de valores estruturados de ECG (p2).")

def axis_from_I_aVF(lead_i_mv, avf_mv):
    if lead_i_mv is None or avf_mv is None:
        return None, None
    angle = math.degrees(math.atan2(avf_mv, lead_i_mv))
    # Classificação baseada em sinais (robusta)
    if lead_i_mv >= 0 and avf_mv >= 0:
        label = "Normal"
    elif lead_i_mv >= 0 and avf_mv < 0:
        label = "Desvio para a esquerda"
    elif lead_i_mv < 0 and avf_mv >= 0:
        label = "Desvio para a direita"
    else:
        label = "Desvio extremo (noroeste)"
    return angle, label

@analyze_app.command("values")
def analyze_values(
    path_or_none: str = typer.Argument(None, help="Opcional: arquivo JSON com valores"),
    pr: int = typer.Option(None, "--pr", help="PR (ms)"),
    qrs: int = typer.Option(None, "--qrs", help="QRS (ms)"),
    qt: int = typer.Option(None, "--qt", help="QT (ms)"),
    rr: int = typer.Option(None, "--rr", help="RR (ms)"),
    fc: float = typer.Option(None, "--fc", help="Frequência cardíaca (bpm)"),
    lead_i: float = typer.Option(None, "--lead-i", help="QRS líquido em I (mV)"),
    avf: float = typer.Option(None, "--avf", help="QRS líquido em aVF (mV)"),
    sexo: str = typer.Option(None, "--sexo", help="M/F para limiar QTc"),
    auto_grid: bool = typer.Option(False, "--auto-grid", help="Tentar calibrar grade e segmentar 12D"),
    deskew: bool = typer.Option(False, "--deskew", help="Estimar rotação e deskew antes de processar"),
    normalize: bool = typer.Option(False, "--normalize", help="Normalizar escala para px/mm ~10"),
    schema_v2: bool = typer.Option(True, "--schema-v2/--schema-v1", help="Emitir laudo no schema v0.2"),
    auto_leads: bool = typer.Option(False, "--auto-leads", help="Detectar layout e rótulos automaticamente"),
    rpeaks_lead: str = typer.Option(None, "--rpeaks-lead", help="Derivação para FC (ex.: II, V2)"),
    schema_v3: bool = typer.Option(True, "--schema-v3/--schema-v2-off", help="Emitir laudo no schema v0.3"),
    rpeaks_robust: bool = typer.Option(False, "--rpeaks-robust", help="Usar detecção robusta de R-peaks (Pan‑Tompkins-like)"),
    intervals: bool = typer.Option(False, "--intervals", help="Estimar PR/QRS/QT/QTc a partir do traçado"),
    schema_v4: bool = typer.Option(True, "--schema-v4/--schema-v3-off", help="Emitir laudo no schema v0.4"),
    report: bool = typer.Option(False, "--report", help="Salvar relatório em reports/"),
):
    data = {}
    if path_or_none and path_or_none.lower().endswith(".json"):
        p = pathlib.Path(path_or_none)
        if not p.exists():
            typer.echo(f"Arquivo não encontrado: {p}", err=True); raise typer.Exit(code=2)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    for k, v in {"pr":pr, "qrs":qrs, "qt":qt, "rr":rr, "fc":fc, "lead_i":lead_i, "avf":avf, "sexo":sexo}.items():
        if v is not None: data[k] = v

    if "rr" not in data and "fc" not in data:
        typer.echo("Informe RR (ms) ou FC (bpm).", err=True); raise typer.Exit(code=2)
    if "qt" not in data:
        typer.echo("Informe QT (ms) para cálculo de QTc.", err=True); raise typer.Exit(code=2)

    rr_ms = float(data["rr"]) if "rr" in data else 60000.0/float(data["fc"])
    fc_bpm = 60000.0/rr_ms
    qt_ms = float(data["qt"])
    pr_ms = float(data.get("pr")) if data.get("pr") is not None else None
    qrs_ms = float(data.get("qrs")) if data.get("qrs") is not None else None

    qtcb = qt_ms / ( (rr_ms/1000.0) ** 0.5 )
    qtcfr = qt_ms / ( (rr_ms/1000.0) ** (1.0/3.0) )

    lead_i_mv = float(data.get("lead_i")) if data.get("lead_i") is not None else None
    avf_mv = float(data.get("avf")) if data.get("avf") is not None else None
    angle, axis_label = axis_from_I_aVF(lead_i_mv, avf_mv)

    flags = []
    if pr_ms is not None:
        if pr_ms > 200: flags.append("PR > 200 ms: suspeita de BAV 1º")
        if pr_ms < 120 and (qrs_ms is None or qrs_ms < 120): flags.append("PR < 120 ms: considerar pré-excitação")
    if qrs_ms is not None:
        if qrs_ms >= 120: flags.append("QRS ≥ 120 ms: sugere bloqueio de ramo completo/origem ventricular")
        elif 110 <= qrs_ms < 120: flags.append("QRS 110–119 ms: possível bloqueio de ramo incompleto")
    sexo_s = (data.get("sexo") or "").strip().upper()
    limiar = 450 if sexo_s == "M" else (470 if sexo_s == "F" else 460)
    if qtcb >= limiar or qtcfr >= limiar:
        flags.append(f"QTc prolongado (limiar {limiar} ms)")
    if qtcb < 350 or qtcfr < 350:
        flags.append("QTc possivelmente curto (<350 ms)")

    out = {
        "inputs": {"pr_ms": pr_ms, "qrs_ms": qrs_ms, "qt_ms": qt_ms, "rr_ms": rr_ms, "fc_bpm": fc_bpm,
                   "lead_i_mv": lead_i_mv, "aVF_mv": avf_mv, "sexo": sexo_s or None},
        "derived": {"QTc_Bazett_ms": round(qtcb,1), "QTc_Fridericia_ms": round(qtcfr,1),
                    "axis_angle_deg": round(angle,1) if angle is not None else None,
                    "axis_label": axis_label},
        "flags": flags,
        "notes": [
            "Bazett supercorrige em FC alta e subcorrige em FC baixa; Fridericia é alternativa mais estável.",
            "Classificação de eixo baseada em sinais de I/aVF e ângulo aproximado.",
            "Heurísticas são educacionais e não substituem avaliação clínica completa."
        ]
    }

    print(Panel.fit(f"[bold]FC:[/] {fc_bpm:.1f} bpm | [bold]QTc (Bazett/Fridericia):[/] {out['derived']['QTc_Bazett_ms']:.1f}/{out['derived']['QTc_Fridericia_ms']:.1f} ms"))
    if axis_label:
        print(Panel.fit(f"[bold]Eixo:[/] {axis_label} ({out['derived']['axis_angle_deg']}° aprox)"))
    if flags:
        print(Panel.fit("[bold yellow]Flags:[/]\n- " + "\n- ".join(flags)))
    else:
        print(Panel.fit("[bold green]Sem flags relevantes pelos limiares configurados.[/]"))

    if report:
        reports_dir = (REPO_ROOT / "reports"); reports_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        with open(reports_dir / f"{ts}_analyze_values.json", "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        with open(reports_dir / f"{ts}_analyze_values.md", "w", encoding="utf-8") as f:
            f.write(f"# Relatório analyze values — {ts}\n\n")
            f.write(f"- FC: {fc_bpm:.1f} bpm\n")
            f.write(f"- QTc Bazett: {out['derived']['QTc_Bazett_ms']:.1f} ms\n")
            f.write(f"- QTc Fridericia: {out['derived']['QTc_Fridericia_ms']:.1f} ms\n")
            if axis_label:
                f.write(f"- Eixo: {axis_label} ({out['derived']['axis_angle_deg']}°)\n")
            if flags:
                f.write("\n## Flags\n")
                for fl in flags: f.write(f"- {fl}\n")
        print(Panel.fit("[bold green]Relatórios salvos em reports/"))

app.add_typer(analyze_app, name="analyze")

if __name__ == "__main__":
    app()

# --------------------------
# INGEST commands (p3)
# --------------------------
ingest_app = typer.Typer(help="Ingestão de ECG por imagem (PNG/JPG).")

def _axis_from_I_aVF(lead_i_mv, avf_mv):
    if lead_i_mv is None or avf_mv is None:
        return None, None
    angle = math.degrees(math.atan2(avf_mv, lead_i_mv))
    if lead_i_mv >= 0 and avf_mv >= 0: label = "Normal"
    elif lead_i_mv >= 0 and avf_mv < 0: label = "Desvio para a esquerda"
    elif lead_i_mv < 0 and avf_mv >= 0: label = "Desvio para a direita"
    else: label = "Desvio extremo (noroeste)"
    return angle, label

def _qtc(qt_ms: float, rr_ms: float):
    qb = qt_ms / ((rr_ms/1000.0)**0.5)
    qf = qt_ms / ((rr_ms/1000.0)**(1.0/3.0))
    return round(qb,1), round(qf,1)

@ingest_app.command("image")
def ingest_image(
    image_path: str = typer.Argument(..., help="Arquivo PNG/JPG/PDF(1ª pág.)"),
    meta: str = typer.Option(None, "--meta", help="Sidecar META JSON (se não usar <arquivo>.meta.json)"),
    sexo: str = typer.Option(None, "--sexo", help="M/F para limiar QTc"),
    auto_grid: bool = typer.Option(False, "--auto-grid", help="Tentar calibrar grade e segmentar 12D"),
    deskew: bool = typer.Option(False, "--deskew", help="Estimar rotação e deskew antes de processar"),
    normalize: bool = typer.Option(False, "--normalize", help="Normalizar escala para px/mm ~10"),
    schema_v2: bool = typer.Option(True, "--schema-v2/--schema-v1", help="Emitir laudo no schema v0.2"),
    auto_leads: bool = typer.Option(False, "--auto-leads", help="Detectar layout e rótulos automaticamente"),
    rpeaks_lead: str = typer.Option(None, "--rpeaks-lead", help="Derivação para FC (ex.: II, V2)"),
    schema_v3: bool = typer.Option(True, "--schema-v3/--schema-v2-off", help="Emitir laudo no schema v0.3"),
    rpeaks_robust: bool = typer.Option(False, "--rpeaks-robust", help="Usar detecção robusta de R-peaks (Pan‑Tompkins-like)"),
    intervals: bool = typer.Option(False, "--intervals", help="Estimar PR/QRS/QT/QTc a partir do traçado"),
    schema_v4: bool = typer.Option(True, "--schema-v4/--schema-v3-off", help="Emitir laudo no schema v0.4"),
    report: bool = typer.Option(False, "--report", help="Salvar laudo conforme schema"),
):
    p = pathlib.Path(image_path)
    if not p.exists():
        typer.echo(f"Arquivo não encontrado: {p}", err=True); raise typer.Exit(code=2)

    # Sidecar META
    meta_path = pathlib.Path(meta) if meta else p.with_suffix(p.suffix + ".meta.json")
    # Pré-processamento opcional: deskew + normalize (aplicados sequencialmente sobre arquivo temporário em memória)
    from PIL import Image
    _img = Image.open(_buf).convert("RGB")
    if deskew:
        from cv.deskew import estimate_rotation_angle, rotate_image
        _info = estimate_rotation_angle(_img, search_deg=6.0, step=0.5)
        _img = rotate_image(_img, _info['angle_deg'])
    if normalize:
        from cv.normalize import normalize_scale
        _img, _scale, _pxmm = normalize_scale(_img, target_px_per_mm=10.0)
    # Substitui path por buffer em memória para etapas seguintes que leem a imagem
    import io as _io
    _buf = _io.BytesIO()
    _img.save(_buf, format="PNG")
    _buf.seek(0)
    
    meta_data = {}
    if meta_path.exists():
        try:
            meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception as e:
            typer.echo(f"Falha lendo META: {meta_path} — {e}", err=True)

    # Estratégia p3: se META tiver medidas/params, usamos; senão, placeholder educativo.
    dpi = meta_data.get("dpi")
    mm_per_mV = meta_data.get("mm_per_mV")
    ms_per_div = meta_data.get("ms_per_div")
    layout = meta_data.get("leads_layout", "3x4")
    measures = meta_data.get("measures", {})
    # Auto grid/segmentation if requested or if no calibration present
    seg = None
    grid = None
    layout_det = None
    lead_labels = None
    rpeaks_out = None
    intervals_out = None


    if auto_grid:
        try:
            from PIL import Image
            import numpy as _np
            from cv.grid_detect import estimate_grid_period_px
            from cv.segmentation import segment_12leads_basic, find_content_bbox
            arr = _np.asarray(Image.open(_buf).convert("RGB"))
            grid = estimate_grid_period_px(arr)
            gray = _np.asarray(Image.open(_buf).convert("L"))
            bbox = find_content_bbox(gray)
            seg_leads = segment_12leads_basic(gray, bbox=bbox)
            seg = {"content_bbox": bbox, "leads": seg_leads}
        if auto_leads:
            from cv.lead_ocr import choose_layout
            cand = {"3x4":[d["bbox"] for d in seg_leads]}
            layout_det = choose_layout(_np.asarray(Image.open(p).convert("L")), {"3x4":[d["bbox"] for d in seg_leads]})
            lead_labels = layout_det.get("labels")
        if rpeaks_lead:
            from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, detect_rpeaks_from_trace, estimate_px_per_sec
            # procura bbox do lead requisitado
            _lab2box = {d["lead"]: d["bbox"] for d in seg_leads}
            if rpeaks_lead in _lab2box:
                _x0,_y0,_x1,_y1 = _lab2box[rpeaks_lead]
                _gray = _np.asarray(Image.open(p).convert("L"))
                _crop = _gray[_y0:_y1, _x0:_x1]
                _trace = smooth_signal(extract_trace_centerline(_crop, band=0.8), win=11)
                _pxmm = (grid.get("px_small_x") if grid else None) or (grid.get("px_small_y") if grid else None)
                _pxsec = estimate_px_per_sec(_pxmm, 25.0) or 250.0
                rpeaks_out = detect_rpeaks_from_trace(_trace, px_per_sec=_pxsec, zthr=2.0)
                if rpeaks_robust:
                    from cv.rpeaks_robust import pan_tompkins_like
                    _rob = pan_tompkins_like(_trace, _pxsec)
                    rpeaks_out = {"peaks_idx": _rob["peaks_idx"], "method": "pan_tompkins_like"}
                if intervals:
                    from cv.intervals import intervals_from_trace
                    intervals_out = intervals_from_trace(_trace, rpeaks_out.get("peaks_idx") or [], _pxsec)

                rpeaks_out["lead_used"] = rpeaks_lead
        
        except Exception as e:
            typer.echo(f"Auto-grid falhou: {e}", err=True)
    

    # Derivados
    rr_ms = measures.get("rr_ms")
    fc_bpm = measures.get("fc_bpm") or (60000.0/rr_ms if rr_ms else None)
    qt_ms = measures.get("qt_ms")
    pr_ms = measures.get("pr_ms")
    qrs_ms = measures.get("qrs_ms")
    lead_i = measures.get("lead_i_mv")
    avf = measures.get("avf_mv")

    angle, axis_label = _axis_from_I_aVF(lead_i, avf) if (lead_i is not None and avf is not None) else (None, None)
    qb, qf = (None, None)
    if qt_ms and (rr_ms or fc_bpm):
        rr_calc = rr_ms if rr_ms else 60000.0/float(fc_bpm)
        qb, qf = _qtc(float(qt_ms), float(rr_calc))

    sexo_s = (sexo or meta_data.get("sexo") or "").strip().upper()
    limiar = 450 if sexo_s == "M" else (470 if sexo_s == "F" else 460)

    flags = []
    if pr_ms is not None and pr_ms > 200: flags.append("PR > 200 ms: suspeita de BAV 1º")
    if pr_ms is not None and pr_ms < 120 and (qrs_ms is None or qrs_ms < 120): flags.append("PR < 120 ms: considerar pré-excitação")
    if qrs_ms is not None:
        if qrs_ms >= 120: flags.append("QRS ≥ 120 ms: bloqueio de ramo completo/origem ventricular")
        elif 110 <= qrs_ms < 120: flags.append("QRS 110–119 ms: bloqueio de ramo incompleto")
    if (qb is not None and qb >= limiar) or (qf is not None and qf >= limiar):
        flags.append(f"QTc prolongado (limiar {limiar} ms)")
    if (qb is not None and qb < 350) or (qf is not None and qf < 350):
        flags.append("QTc possivelmente curto (<350 ms)")

    suggested = []
    if flags:
        if any("QTc prolongado" in f for f in flags):
            suggested.append("Investigar causas de QT prolongado (drogas, distúrbios eletrolíticos, canalopatias).")
        if any("PR > 200" in f for f in flags):
            suggested.append("Compatível com BAV de 1º grau em contexto clínico adequado.")
        if any("pré-excitação" in f for f in flags):
            suggested.append("Se houver delta/QRS largo, considerar WPW e ajuste de manejo em taquiarritmias.")
        if any("QRS ≥ 120" in f for f in flags):
            suggested.append("QRS largo: avaliar morfologia BRE/BRD, discordâncias e critérios de isquemia em bloqueios.")
    else:
        suggested.append("Sem flags críticas pelos limiares configurados; correlacionar clinicamente.")

    report_obj = {
        "meta": {
            "source_image": str(p),
            "sidecar_meta_used": bool(meta_data),
            "ingest_version": "p3-0.1",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "notes": ["Este laudo segue schema v0.1 (p3)."]
        },
        "patient_info": {
            "id": meta_data.get("patient_id"),
            "age": meta_data.get("age"),
            "sex": sexo_s or None,
            "context": meta_data.get("context")
        },
        "acquisition": {
            "dpi": dpi, "mm_per_mV": mm_per_mV, "ms_per_div": ms_per_div, "leads_layout": layout,
            "px_per_mm_x": (grid.get("px_small_x") if grid else None),
            "px_per_mm_y": (grid.get("px_small_y") if grid else None),
            "px_small_grid": (grid.get("px_small_x") if grid else None),
            "px_big_grid": (grid.get("px_big_x") if grid else None),
            "grid_confidence": (grid.get("confidence") if grid else None)
        },
        "measures": {
            "pr_ms": pr_ms, "qrs_ms": qrs_ms, "qt_ms": qt_ms, "rr_ms": rr_ms,
            "fc_bpm": fc_bpm, "axis_angle_deg": angle, "axis_label": axis_label
        },
        "flags": flags,
        "suggested_interpretations": suggested,
        "segmentation": (seg if seg else None),
        "layout_detection": (layout_det if auto_leads else None),
        "rpeaks": (rpeaks_out if rpeaks_lead else None),
        "intervals": (intervals_out if intervals else None),
        "version": ("0.4.0" if schema_v4 else ("0.3.0" if schema_v3 else ("0.2.0" if schema_v2 else "0.1.0")))
    }

    # Resumo
    print(Panel.fit("[bold]Ingestão de imagem — resumo[/]"))
    print(f"Arquivo: {p.name}")
    if meta_data: print("META: encontrado e aplicado.")
    if fc_bpm: print(f"FC: {fc_bpm:.1f} bpm")
    if qt_ms: print(f"QT: {qt_ms} ms | QTc (B/F): {qb}/{qf} ms")
    if axis_label: print(f"Eixo: {axis_label} ({angle:.1f}° aprox)")
    if flags: print("Flags: " + "; ".join(flags))

    # Salvar relatórios
    if report:
        reports_dir = (REPO_ROOT / "reports"); reports_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        with open(reports_dir / f"{ts}_ecg_report.json", "w", encoding="utf-8") as f:
            json.dump(report_obj, f, ensure_ascii=False, indent=2)
        with open(reports_dir / f"{ts}_ecg_report.md", "w", encoding="utf-8") as f:
            f.write(f"# Laudo ECG (ingest image) — {ts}\\n\\n")
            f.write(f"- Arquivo: {p.name}\\n")
            if fc_bpm: f.write(f"- FC: {fc_bpm:.1f} bpm\\n")
            if qt_ms: f.write(f"- QT: {qt_ms} ms | QTc (B/F): {qb}/{qf} ms\\n")
            if axis_label: f.write(f"- Eixo: {axis_label} ({angle:.1f}°)\\n")
            if flags:\n                f.write("\\n## Flags\\n"); [f.write(f"- {fl}\\n") for fl in flags]\n            if suggested:\n                f.write("\\n## Sugestões/Observações\\n"); [f.write(f"- {s}\\n") for s in suggested]\n        print(Panel.fit("[bold green]Laudos salvos em reports/"))

app.add_typer(ingest_app, name="ingest")


# --------------------------
# ASSETS commands (p3c)
# --------------------------
assets_app = typer.Typer(help="Automação de assets (download, verificação de licenças, pré-processamento).")

def _import_scripts():
    import sys as _sys, pathlib as _pl
    p = REPO_ROOT / "scripts" / "python"
    if str(p) not in _sys.path:
        _sys.path.append(str(p))

@assets_app.command("download")
def assets_download():
    """Baixa imagens do manifesto para assets/raw/images/"""
    _import_scripts()
    from download_assets import main as _main
    _main()

@assets_app.command("verify")
def assets_verify(manifest_in: str = typer.Option("assets/manifest/ecg_images.v1.jsonl", "--in"),
                  manifest_out: str = typer.Option(None, "--out")):
    """Verifica licenças/autor e gera ecg_images.verified.jsonl + créditos."""
    _import_scripts()
    from verify_licenses import main as _main
    _main(manifest_in, manifest_out)

@assets_app.command("preprocess")
def assets_preprocess():
    """Gera derivados WEBP/AVIF e manifesto ecg_images.derived.json."""
    _import_scripts()
    from preprocess_images import main as _main
    _main()

app.add_typer(assets_app, name="assets")


# --------------------------
# CV commands (p4)
# --------------------------
cv_app = typer.Typer(help="Visão computacional (grade + segmentação 12D).")

def _open_image_to_array(path: pathlib.Path):
    from PIL import Image
    import numpy as np
    img = Image.open(path).convert("RGB")
    return np.asarray(img)

@cv_app.command("calibrate")
def cv_calibrate(image_path: str = typer.Argument(..., help="PNG/JPG"),
                 dump_json: bool = typer.Option(False, "--json", help="Imprime JSON com calibração")):
    """Detecta período de grade (px) e estima px/mm grande/pequena."""
    import json as _json
    import numpy as _np
    from cv.grid_detect import estimate_grid_period_px
    arr = _open_image_to_array(pathlib.Path(image_path))
    info = estimate_grid_period_px(arr)
    # Heurística: px_small ≈ período; px_big ≈ 5*px_small; px/mm ≈ px_small (se small=1mm)
    px_small = float(info.get("px_small_x") or info.get("px_small_y") or 0.0)
    px_big = float(info.get("px_big_x") or info.get("px_big_y") or 0.0)
    out = {
        "px_small_grid": px_small,
        "px_big_grid": px_big,
        "px_per_mm_x": px_small or None,
        "px_per_mm_y": px_small or None,
        "grid_confidence": info.get("confidence", 0.0),
    }
    if dump_json:
        print(_json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(Panel.fit(f"[bold]Grid (px):[/] small≈{px_small:.1f}, big≈{px_big:.1f} | conf {out['grid_confidence']:.2f}"))
    return out

@cv_app.command("segment")
def cv_segment(image_path: str = typer.Argument(..., help="PNG/JPG"),
               layout: str = typer.Option("3x4", "--layout", help="Layout esperado"),
               dump_json: bool = typer.Option(False, "--json", help="Imprime JSON com caixas")):
    """Segmenta a área útil em 12 caixas para as derivações (básico)."""
    import json as _json
    import numpy as _np
    from PIL import Image
    from cv.segmentation import segment_12leads_basic, find_content_bbox
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    leads = segment_12leads_basic(gray, layout=layout, bbox=bbox)
    out = {"content_bbox": bbox, "leads": leads}
    if dump_json:
        print(_json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(Panel.fit(f"[bold]Content bbox:[/] {bbox} — {len(leads)} leads geradas."))
    return out

app.add_typer(cv_app, name="cv")


@cv_app.command("deskew")
def cv_deskew(image_path: str = typer.Argument(..., help="PNG/JPG"),
              save: str = typer.Option(None, "--save", help="Salvar imagem deskew"),
              search_deg: float = typer.Option(6.0, "--range", help="Ângulo máximo (+/-)")):
    """Estima rotação e aplica deskew (busca bruta)."""
    from PIL import Image
    from cv.deskew import estimate_rotation_angle, rotate_image
    p = pathlib.Path(image_path)
    img = Image.open(_buf).convert("RGB")
    info = estimate_rotation_angle(img, search_deg=search_deg, step=0.5)
    print(f"Ângulo estimado: {info['angle_deg']:.2f}° (score {info['score']:.3f} vs {info['score0']:.3f})")
    if save:
        out = rotate_image(img, info['angle_deg'])
        out.save(save)
        print(f"Imagem salva: {save}")

@cv_app.command("normalize")
def cv_normalize(image_path: str = typer.Argument(..., help="PNG/JPG"),
                 target_pxmm: float = typer.Option(10.0, "--pxmm", help="px por mm alvo"),
                 save: str = typer.Option(None, "--save", help="Salvar imagem normalizada")):
    """Normaliza escala para atingir px/mm alvo (sem upscaling >2x)."""
    from PIL import Image
    from cv.normalize import normalize_scale
    p = pathlib.Path(image_path)
    img = Image.open(_buf).convert("RGB")
    im1, scale, pxmm = normalize_scale(img, target_px_per_mm=target_pxmm)
    print(f"px/mm estimado: {pxmm} | scale aplicado: {scale:.3f}")
    if save:
        im1.save(save)
        print(f"Imagem salva: {save}")

@cv_app.command("layout-seg")
def cv_layout_seg(image_path: str = typer.Argument(..., help="PNG/JPG"),
                  layout: str = typer.Option("3x4", "--layout", help="3x4 | 6x2 | 3x4+rhythm"),
                  dump_json: bool = typer.Option(False, "--json", help="Imprime JSON com caixas")):
    """Segmenta conforme layout escolhido (3x4, 6x2 ou 3x4+rhythm)."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation_ext import segment_layout
    gray = _np.asarray(Image.open(image_path).convert("L"))
    seg = segment_layout(gray, layout=layout)
    if dump_json:
        print(_json.dumps({"leads": seg}, ensure_ascii=False, indent=2))
    else:
        print(f"{len(seg)} caixas geradas para layout {layout}.")


@cv_app.command("detect-layout")
def cv_detect_layout(image_path: str = typer.Argument(..., help="PNG/JPG"),
                     layout_hint: str = typer.Option(None, "--hint", help="3x4|6x2|3x4+rhythm"),
                     dump_json: bool = typer.Option(False, "--json")):
    """Detecta layout (3x4/6x2/3x4+ritmo) por rótulos dentro das caixas candidatas."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    from cv.lead_ocr import choose_layout
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    candidates = {
        "3x4": segment_layout(gray, "3x4", bbox=bbox),
        "6x2": segment_layout(gray, "6x2", bbox=bbox),
        "3x4+rhythm": segment_layout(gray, "3x4+rhythm", bbox=bbox),
    }
    best = choose_layout(gray, {k:[d["bbox"] for d in v] for k,v in candidates.items()})
    out = {"layout": best["layout"] or "unknown", "score": best["score"], "labels": best["labels"], "content_bbox": bbox}
    if dump_json:
        print(_json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Layout: {out['layout']} (score {out['score']:.2f})")
    return out

@cv_app.command("detect-leads")
def cv_detect_leads(image_path: str = typer.Argument(..., help="PNG/JPG"),
                    layout: str = typer.Option("3x4", "--layout"),
                    dump_json: bool = typer.Option(False, "--json")):
    """Detecta rótulos por caixa para um layout escolhido, retornando {lead,label,score}."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    from cv.lead_ocr import detect_labels_per_box
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    boxes = [d["bbox"] for d in segment_layout(gray, layout, bbox=bbox)]
    det = detect_labels_per_box(gray, boxes)
    if dump_json:
        print(_json.dumps(det, ensure_ascii=False, indent=2))
    else:
        ok = sum(1 for d in det if d.get("label"))
        print(f"Rótulos detectados em {ok}/{len(det)} caixas.")
    return det

@cv_app.command("rpeaks")
def cv_rpeaks(image_path: str = typer.Argument(..., help="PNG/JPG"),
              layout: str = typer.Option("3x4", "--layout"),
              lead: str = typer.Option("II", "--lead", help="Lead alvo para FC (ex.: II, V2, V5)"),
              speed_mm_s: float = typer.Option(25.0, "--speed", help="Velocidade mm/s"),
              zthr: float = typer.Option(2.0, "--zthr", help="Limiar z-score p/ picos"),
              dump_json: bool = typer.Option(False, "--json")):
    """Extrai traçado 1D da caixa da derivação alvo e estima R-peaks/FC."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    from cv.grid_detect import estimate_grid_period_px
    from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, detect_rpeaks_from_trace, estimate_px_per_sec
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    seg = segment_layout(gray, layout, bbox=bbox)
    # Seleciona caixa pela label esperada
    label2idx = {d["lead"]: i for i,d in enumerate(seg)}
    if lead not in label2idx:
        raise typer.Exit(code=2)
    x0,y0,x1,y1 = seg[label2idx[lead]]["bbox"]
    crop = gray[y0:y1, x0:x1]
    trace = extract_trace_centerline(crop, band=0.8)
    trace = smooth_signal(trace, win=11)
    grid = estimate_grid_period_px(_np.asarray(Image.open(image_path).convert("RGB")))
    pxmm = grid.get("px_small_x") or grid.get("px_small_y")
    pxsec = estimate_px_per_sec(pxmm, speed_mm_per_sec=speed_mm_s)
    res = detect_rpeaks_from_trace(trace, px_per_sec=pxsec or 250.0, zthr=zthr)
    out = {"lead_used": lead, **res}
    if dump_json:
        print(_json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"Lead {lead}: HR média {res['hr_bpm_mean']:.1f} bpm (picos {len(res['peaks_idx'])})" if res['hr_bpm_mean'] else f"Lead {lead}: insuficiente para FC.")
    return out


@cv_app.command("rpeaks-robust")
def cv_rpeaks_robust(image_path: str = typer.Argument(..., help="PNG/JPG"),
                     layout: str = typer.Option("3x4", "--layout"),
                     lead: str = typer.Option("II", "--lead"),
                     speed_mm_s: float = typer.Option(25.0, "--speed"),
                     dump_json: bool = typer.Option(False, "--json")):
    """Detecção robusta de R-peaks (Pan‑Tompkins-like) a partir da imagem recortada da derivação alvo."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    from cv.grid_detect import estimate_grid_period_px
    from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, estimate_px_per_sec
    from cv.rpeaks_robust import pan_tompkins_like
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    seg = segment_layout(gray, layout, bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in seg}
    if lead not in lab2box: raise typer.Exit(code=2)
    x0,y0,x1,y1 = lab2box[lead]
    crop = gray[y0:y1, x0:x1]
    trace = smooth_signal(extract_trace_centerline(crop), win=11)
    pxmm = (estimate_grid_period_px(_np.asarray(Image.open(image_path).convert("RGB"))).get("px_small_x")
            or estimate_grid_period_px(_np.asarray(Image.open(image_path).convert("RGB"))).get("px_small_y"))
    pxsec = estimate_px_per_sec(pxmm, speed_mm_per_sec=speed_mm_s) or 250.0
    res = pan_tompkins_like(trace, pxsec)
    out = {"lead_used": lead, **{k:v for k,v in res.items() if k!='signals'}}
    if dump_json: print(_json.dumps(out, ensure_ascii=False, indent=2))
    else: print(f"Lead {lead}: {len(out['peaks_idx'])} picos detectados | fs≈{pxsec:.1f} px/s")
    return out

@cv_app.command("intervals")
def cv_intervals(image_path: str = typer.Argument(..., help="PNG/JPG"),
                 layout: str = typer.Option("3x4", "--layout"),
                 lead: str = typer.Option("II", "--lead"),
                 speed_mm_s: float = typer.Option(25.0, "--speed"),
                 dump_json: bool = typer.Option(False, "--json")):
    """Onsets/offsets de QRS e estimativas de PR/QRS/QT/QTc a partir de R-peaks robustos."""
    import json as _json, numpy as _np
    from PIL import Image
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    from cv.grid_detect import estimate_grid_period_px
    from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, estimate_px_per_sec
    from cv.rpeaks_robust import pan_tompkins_like
    from cv.intervals import intervals_from_trace
    gray = _np.asarray(Image.open(image_path).convert("L"))
    bbox = find_content_bbox(gray)
    seg = segment_layout(gray, layout, bbox=bbox)
    lab2box = {d["lead"]: d["bbox"] for d in seg}
    if lead not in lab2box: raise typer.Exit(code=2)
    x0,y0,x1,y1 = lab2box[lead]
    crop = gray[y0:y1, x0:x1]
    trace = smooth_signal(extract_trace_centerline(crop), win=11)
    pxmm = (estimate_grid_period_px(_np.asarray(Image.open(image_path).convert("RGB"))).get("px_small_x")
            or estimate_grid_period_px(_np.asarray(Image.open(image_path).convert("RGB"))).get("px_small_y"))
    pxsec = estimate_px_per_sec(pxmm, speed_mm_per_sec=speed_mm_s) or 250.0
    rdet = pan_tompkins_like(trace, pxsec)
    iv = intervals_from_trace(trace, rdet["peaks_idx"], pxsec)
    out = {"lead_used": lead, "rpeaks": {"peaks_idx": rdet["peaks_idx"]}, "intervals": iv}
    if dump_json: print(_json.dumps(out, ensure_ascii=False, indent=2))
    else: 
        m = iv["median"]
        print(f"PR {m.get('PR_ms')} ms | QRS {m.get('QRS_ms')} ms | QT {m.get('QT_ms')} ms | QTcB {m.get('QTc_B')} ms | QTcF {m.get('QTc_F')} ms")
    return out


quiz_app = typer.Typer(help="Geração de quizzes MCQ a partir de laudos.")

@quiz_app.command("build")
def quiz_build(report_json: str = typer.Argument(..., help="Arquivo de laudo JSON"),
               out_json: str = typer.Option(None, "--out", help="Arquivo de saída (JSON)")):
    """Gera MCQs automaticamente com base em PR/QRS/QT/QTc/HR do laudo."""
    import json as _json
    from quiz.generate_quiz import quiz_from_report
    with open(report_json,"r",encoding="utf-8") as f:
        rep = _json.load(f)
    q = quiz_from_report(rep)
    if out_json:
        with open(out_json,"w",encoding="utf-8") as f: _json.dump(q,f,ensure_ascii=False,indent=2)
        print(f"Quiz salvo em {out_json}")
    else:
        print(_json.dumps(q, ensure_ascii=False, indent=2))

app.add_typer(quiz_app, name="quiz")

      ```

  ### 📁 cv/

    #### 📄 deskew.py

    ```py

import numpy as np
from PIL import Image, ImageOps

def _to_gray(img_or_arr):
    if isinstance(img_or_arr, Image.Image):
        return np.asarray(img_or_arr.convert("L"))
    arr = np.asarray(img_or_arr)
    if arr.ndim==3:
        r,g,b = arr[...,0],arr[...,1],arr[...,2]
        arr = (0.2989*r + 0.5870*g + 0.1140*b).astype(np.float32)
    return arr

def _proj_score(gray):
    # usa gradientes simples para salientar linhas de grade e calcula variância das projeções
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))
    sx = gx.mean(axis=0)
    sy = gy.mean(axis=1)
    # maior variância indica linhas mais alinhadas ao eixo
    return float(np.var(sx) + np.var(sy))

def estimate_rotation_angle(img: Image.Image, search_deg=6.0, step=0.5):
    """
    Busca bruta de ângulo em [-search_deg, +search_deg] (deg) maximizando a variância
    das projeções dos gradientes (proxy para alinhamento com a grade).
    Retorna: {'angle_deg': best, 'score': best_score, 'score0': score_sem_rotacao}
    """
    gray0 = _to_gray(img)
    score0 = _proj_score(gray0)
    best_angle = 0.0
    best_score = score0
    # varre ângulos
    n = int(2*search_deg/step)+1
    for k in range(n):
        ang = -search_deg + k*step
        if abs(ang) < 1e-6: 
            continue
        gr = img.rotate(ang, resample=Image.BILINEAR, expand=True, fillcolor=(255,255,255))
        score = _proj_score(_to_gray(gr))
        if score > best_score:
            best_score, best_angle = score, ang
    return {"angle_deg": float(best_angle), "score": float(best_score), "score0": float(score0)}

def rotate_image(img: Image.Image, angle_deg: float) -> Image.Image:
    return img.rotate(float(angle_deg), resample=Image.BILINEAR, expand=True, fillcolor=(255,255,255))

    ```

    #### 📄 grid_detect.py

    ```py

import numpy as np
from PIL import Image, ImageOps

def _to_gray(arr_or_img):
    if isinstance(arr_or_img, Image.Image):
        img = arr_or_img.convert("L")
        return np.asarray(img).astype(np.float32)
    if arr_or_img.ndim==3:
        # assume RGB
        r,g,b = arr_or_img[...,0], arr_or_img[...,1], arr_or_img[...,2]
        return (0.2989*r + 0.5870*g + 0.1140*b).astype(np.float32)
    return arr_or_img.astype(np.float32)

def _autocorr_1d(x):
    x = (x - x.mean()) / (x.std() + 1e-6)
    ac = np.correlate(x, x, mode="full")[len(x)-1:]
    ac /= (ac[0] + 1e-6)
    return ac

def _dominant_period(ac, min_p=4, max_p=200):
    # encontra melhor pico em [min_p, max_p]
    seg = ac[min_p:max_p]
    if seg.size==0:
        return None, 0.0
    k = int(np.argmax(seg))
    p = k + min_p
    conf = float(seg[k])
    return p, conf

def estimate_grid_period_px(img_or_array):
    """
    Estima período da grade (em pixels) nas direções X e Y.
    Heurística: projeção de derivada (diferença) -> autocorrelação -> pico dominante.
    Retorna: dict { 'px_small_x','px_small_y','px_big_x','px_big_y','confidence' }
    """
    arr = _to_gray(img_or_array)
    # borda: ignora 2% em cada lado para reduzir bordas
    h, w = arr.shape
    x0, x1 = int(0.02*w), int(0.98*w)
    y0, y1 = int(0.02*h), int(0.98*h)
    roi = arr[y0:y1, x0:x1]

    # gradientes simples
    gx = np.abs(np.diff(roi, axis=1))
    gy = np.abs(np.diff(roi, axis=0))

    # projeções
    proj_x = gx.mean(axis=0)
    proj_y = gy.mean(axis=1)

    acx = _autocorr_1d(proj_x)
    acy = _autocorr_1d(proj_y)
    px_x, cfx = _dominant_period(acx, 4, 200)
    px_y, cfy = _dominant_period(acy, 4, 200)

    # small grid ~ px_x, px_y ; big grid = 5*small (aprox), arredonda
    res = {}
    if px_x:
        res["px_small_x"] = float(px_x)
        res["px_big_x"] = float(px_x*5.0)
    if px_y:
        res["px_small_y"] = float(px_y)
        res["px_big_y"] = float(px_y*5.0)
    res["confidence"] = float(0.5*(cfx + cfy))
    return res

    ```

    #### 📄 intervals.py

    ```py

import numpy as np
from typing import Dict, List, Optional, Tuple

def _grad_abs(x: np.ndarray) -> np.ndarray:
    g = np.diff(x, prepend=x[:1])
    return np.abs(g)

def _find_onset_offset(sig: np.ndarray, center: int, fs: float, max_pre_ms=120.0, max_post_ms=120.0, th_rel=0.2) -> Tuple[int,int]:
    """
    Encontra início/fim do QRS em torno do pico usando gradiente absoluto.
    th_rel: fração do pico de gradiente para limiar.
    """
    g = _grad_abs(sig)
    g = (g - g.min())/(g.ptp()+1e-6)
    # janelas
    pre = int(max_pre_ms*fs/1000.0)
    pos = int(max_post_ms*fs/1000.0)
    i0 = max(0, center-pre); i1 = min(len(sig)-1, center+pos)
    gi = g[i0:i1+1]
    # limiares
    gpk = gi.max()
    thr = th_rel * gpk
    # onset: último ponto antes do centro onde g < thr por 15 ms
    hold = int(0.015*fs)
    onset = i0
    for i in range(center-i0, -1, -1):
        if np.all(gi[max(0,i-hold):i+1] < thr):
            onset = i0 + i; break
    # offset: primeiro ponto depois onde g < thr por 15 ms
    offset = i1
    for i in range(center-i0, len(gi)):
        if np.all(gi[i:min(len(gi), i+hold)] < thr):
            offset = i0 + i; break
    return onset, offset

def _t_end(sig: np.ndarray, qrs_off: int, fs: float, max_ms=520.0) -> Optional[int]:
    """
    Fim da onda T: após QRS, onde o gradiente retorna estável a ~0 por 30 ms.
    """
    g = _grad_abs(sig); g = (g - g.min())/(g.ptp()+1e-6)
    end_win = int(0.03*fs)
    max_samp = int(max_ms*fs/1000.0)
    i0 = qrs_off
    i1 = min(len(sig)-1, qrs_off + max_samp)
    for i in range(i0, i1-end_win):
        if np.all(g[i:i+end_win] < 0.08):
            return i
    return None

def _p_onset(sig: np.ndarray, qrs_on: int, fs: float, max_ms=280.0) -> Optional[int]:
    """
    Início da P: antes do QRS, procura pequeno aumento de energia sustentado por 20 ms.
    """
    g = _grad_abs(sig); g = (g - g.min())/(g.ptp()+1e-6)
    start_win = int(0.02*fs)
    max_samp = int(max_ms*fs/1000.0)
    i0 = max(0, qrs_on - max_samp)
    for i in range(qrs_on, i0, -1):
        if np.all(g[max(i-start_win,0):i] > 0.05):
            return i-start_win
    return None

def intervals_from_trace(y_px: np.ndarray, r_peaks: List[int], px_per_sec: float) -> Dict:
    """
    Calcula PR, QRS, QT e QTc (Bazett/Fridericia) a partir de traçado 1D e R-peaks.
    Usa medianas por batimento.
    """
    fs = float(px_per_sec)
    # centraliza para baseline
    y = y_px - np.median(y_px)
    onsets=[]; offsets=[]; Ts=[]; Ps=[]
    for r in r_peaks:
        on, off = _find_onset_offset(y, r, fs)
        onsets.append(on); offsets.append(off)
        t_end = _t_end(y, off, fs)
        Ts.append(t_end)
        p_on = _p_onset(y, on, fs)
        Ps.append(p_on)
    # RR
    rr = [ (b-a)/fs for a,b in zip(r_peaks, r_peaks[1:]) ]
    rr_med = float(np.median(rr)) if rr else None
    # PR, QRS, QT (em ms) por batimento
    PR = []; QRS = []; QT = []
    for i in range(len(r_peaks)):
        p = Ps[i]; on = onsets[i]; off = offsets[i]; t = Ts[i]
        if p is not None and on is not None:
            PR.append( (on - p) * 1000.0/fs )
        if on is not None and off is not None:
            QRS.append( (off - on) * 1000.0/fs )
        if on is not None and t is not None:
            QT.append( (t - on) * 1000.0/fs )
    med = lambda arr: float(np.median(arr)) if arr else None
    pr_ms, qrs_ms, qt_ms = med(PR), med(QRS), med(QT)
    qtc_b = (qt_ms / (rr_med**0.5)) if (qt_ms and rr_med) else None
    qtc_f = (qt_ms / (rr_med**(1/3))) if (qt_ms and rr_med) else None
    return {
        "per_beat": {"PR_ms": PR, "QRS_ms": QRS, "QT_ms": QT},
        "median": {"PR_ms": pr_ms, "QRS_ms": qrs_ms, "QT_ms": qt_ms, "QTc_B": qtc_b, "QTc_F": qtc_f, "RR_s": rr_med}
    }

    ```

    #### 📄 lead_ocr.py

    ```py

import numpy as np
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageOps

# OCR opcional
try:
    import pytesseract
    TESS_OK = True
except Exception:
    TESS_OK = False

# OpenCV opcional (template matching)
try:
    import cv2
    CV2_OK = True
except Exception:
    CV2_OK = False

LABELS = ["I","II","III","aVR","aVL","aVF","V1","V2","V3","V4","V5","V6"]
LABELS_SET = set(LABELS)

def _pil_to_gray(arr_or_img) -> np.ndarray:
    if isinstance(arr_or_img, Image.Image):
        return np.asarray(arr_or_img.convert("L"))
    arr = np.asarray(arr_or_img)
    if arr.ndim == 3:
        r,g,b = arr[...,0],arr[...,1],arr[...,2]
        arr = (0.2989*r + 0.5870*g + 0.1140*b).astype(np.float32)
        return arr.astype(np.uint8)
    return arr

def _render_templates(font: Optional[ImageFont.ImageFont]=None, sizes=(18,22,26)) -> Dict[str, List[np.ndarray]]:
    """Gera templates PIL simples para cada rótulo em múltiplos tamanhos."""
    if font is None:
        font = ImageFont.load_default()
    out = {k: [] for k in LABELS}
    for sz in sizes:
        try:
            font = ImageFont.load_default()
        except Exception:
            pass
        for lab in LABELS:
            # render básico em preto sobre branco
            bbox = font.getbbox(lab)
            w = max(12, bbox[2]-bbox[0]+6); h = max(12, bbox[3]-bbox[1]+6)
            im = Image.new("L", (w,h), 255)
            d = ImageDraw.Draw(im)
            d.text((3,3), lab, fill=0, font=font)
            out[lab].append(np.asarray(im))
    return out

def _match_template(gray: np.ndarray, templ: np.ndarray) -> float:
    """Score simples por normalised cross-correlation (via OpenCV se disponível; caso contrário, correlação manual)."""
    if gray is None or templ is None: return 0.0
    if gray.ndim != 2: gray = _pil_to_gray(gray)
    if templ.ndim != 2: templ = _pil_to_gray(templ)
    gh, gw = gray.shape; th, tw = templ.shape
    if gh<th or gw<tw: return 0.0
    if CV2_OK:
        res = cv2.matchTemplate(gray, templ, cv2.TM_CCOEFF_NORMED)
        return float(np.max(res))
    # fallback pobre: correlação em amostras centrais
    y0 = gh//4; y1 = min(gh, y0+th+8); x0 = 4; x1 = min(gw, x0+tw+8)
    crop = gray[y0:y1, x0:x1]
    crop = crop[:th, :tw]
    if crop.size != templ.size: return 0.0
    g = (crop - crop.mean())/(crop.std()+1e-6)
    t = (templ - templ.mean())/(templ.std()+1e-6)
    return float(np.mean(g*t))

def _ocr_text(gray_crop: np.ndarray) -> str:
    if not TESS_OK: return ""
    try:
        txt = pytesseract.image_to_string(gray_crop, config="--psm 7 -c tessedit_char_whitelist=IVaLRF123456")
        return (txt or "").strip()
    except Exception:
        return ""

def _normalize_token(t: str) -> str:
    t = (t or "").strip()
    repl = {"l":"I","|":"I","!":"I"}  # confusões comuns
    t = "".join(repl.get(ch, ch) for ch in t)
    t = t.replace(" ", "").replace("\n","").replace("\t","")
    return t

def _fuzzy_map(token: str, candidates=LABELS) -> Optional[str]:
    try:
        from rapidfuzz import process, fuzz
        res = process.extractOne(token, candidates, scorer=fuzz.WRatio)
        if res and res[1] >= 80:
            return res[0]
    except Exception:
        pass
    return token if token in candidates else None

def detect_labels_per_box(gray: np.ndarray, boxes: List[Tuple[int,int,int,int]]) -> List[Dict]:
    """
    Para cada bbox, tenta identificar o rótulo na área superior-esquerda.
    Retorna [{ 'bbox':(x0,y0,x1,y1), 'label': <str or None>, 'score': float }]
    """
    TEMPL = _render_templates()
    out = []
    for (x0,y0,x1,y1) in boxes:
        bw, bh = x1-x0, y1-y0
        # região de rótulo: 25% largura x 25% altura
        rx1 = x0 + int(bw*0.35); ry1 = y0 + int(bh*0.35)
        crop = gray[y0:ry1, x0:rx1]
        if crop.size == 0:
            out.append({"bbox": (x0,y0,x1,y1), "label": None, "score": 0.0}); continue
        crop_g = crop if crop.ndim==2 else _pil_to_gray(crop)
        # template matching
        best_lab, best_score = None, 0.0
        for lab, templs in TEMPL.items():
            for templ in templs:
                sc = _match_template(crop_g, templ)
                if sc > best_score:
                    best_score, best_lab = sc, lab
        # OCR + fuzzy (opcional)
        tok = _normalize_token(_ocr_text(crop_g))
        if tok:
            cand = _fuzzy_map(tok, LABELS)
            if cand and (best_score < 0.6):  # aceita OCR quando TM fraco
                best_lab, best_score = cand, max(best_score, 0.6)
        out.append({"bbox": (x0,y0,x1,y1), "label": best_lab, "score": float(best_score)})
    return out

def score_layout(labels_detected: List[Dict], expected_sequence: List[str]) -> float:
    """Compara labels detectados com sequência esperada p/ o layout; linear na ordem de boxes."""
    if not labels_detected: return 0.0
    labs = [d.get("label") for d in labels_detected]
    ok = 0; total = min(len(labs), len(expected_sequence))
    for i in range(total):
        if labs[i] == expected_sequence[i]:
            ok += 1
    return ok / max(1,total)

def choose_layout(gray: np.ndarray, candidates: Dict[str, List[Tuple[int,int,int,int]]]) -> Dict:
    """
    Recebe um dicionário {layout: boxes} e retorna melhor layout por escore de rótulos.
    Sequências esperadas:
      - 3x4: I,II,III,aVR,aVL,aVF,V1,V2,V3,V4,V5,V6
      - 6x2: I,II,III,aVR,aVL,aVF,V1,V2,V3,V4,V5,V6  (mesma ordem, linhas diferentes)
      - 3x4+rhythm: mesma sequência + 'II_rhythm' no fim (ignorado na pontuação)
    """
    seq = ["I","II","III","aVR","aVL","aVF","V1","V2","V3","V4","V5","V6"]
    best = {"layout": None, "score": -1.0, "labels": None}
    for name, boxes in candidates.items():
        det = detect_labels_per_box(gray, boxes[:12])  # avalia 12 principais
        sc = score_layout(det, seq)
        if sc > best["score"]:
            best = {"layout": name, "score": sc, "labels": det}
    return best

    ```

    #### 📄 normalize.py

    ```py

import numpy as np
from PIL import Image
from .grid_detect import estimate_grid_period_px

def estimate_px_per_mm(img_rgb) -> float:
    """Assume small grid ~= 1 mm; retorna px/mm estimado (ou None)."""
    info = estimate_grid_period_px(img_rgb)
    px_small = info.get("px_small_x") or info.get("px_small_y")
    return float(px_small) if px_small else None

def normalize_scale(img: Image.Image, target_px_per_mm: float = 10.0):
    """
    Redimensiona para atingir target_px_per_mm (sem upscaling excessivo >2x; clamped).
    Retorna (img_resized, scale_factor_aplicado, px_per_mm_estimado).
    """
    pxmm = estimate_px_per_mm(img.convert("RGB"))
    if not pxmm:
        return img, 1.0, None
    scale = target_px_per_mm / pxmm
    scale = max(0.5, min(2.0, scale))  # clamp
    w0, h0 = img.size
    w1, h1 = int(w0*scale), int(h0*scale)
    im1 = img.resize((w1, h1), Image.LANCZOS)
    return im1, scale, pxmm

    ```

    #### 📄 rpeaks_from_image.py

    ```py

import numpy as np
from typing import Dict, List, Tuple, Optional

def extract_trace_centerline(gray_crop: np.ndarray, band: float = 0.8) -> np.ndarray:
    """
    Constrói uma série 1D y(x) a partir do recorte da derivação:
    para cada coluna x, pega a posição do pixel mais escuro (mínimo) dentro de uma banda vertical central.
    'band' define a fração da altura considerada ao redor do meio (default 80%).
    Retorna vetor float com coordenadas y (em pixels, origem topo).
    """
    if gray_crop.ndim != 2:
        raise ValueError("Esperado gray 2D")
    h, w = gray_crop.shape
    cy0 = int((1-band)*0.5*h)
    cy1 = int(h - cy0)
    center = []
    for x in range(w):
        col = gray_crop[cy0:cy1, x]
        y_local = int(np.argmin(col))
        center.append(cy0 + y_local)
    return np.array(center, dtype=float)

def smooth_signal(y: np.ndarray, win: int = 9) -> np.ndarray:
    win = max(3, int(win) | 1)  # ímpar
    ker = np.ones(win)/win
    return np.convolve(y, ker, mode="same")

def detect_rpeaks_from_trace(y: np.ndarray, px_per_sec: float, zthr: float = 2.0,
                             min_bpm: float = 30.0, max_bpm: float = 220.0) -> Dict:
    """
    Detecção simples de R-peaks:
    - sinal invertido (picos para cima)
    - z-score e threshold (zthr)
    - distância mínima entre picos baseada em max_bpm
    Retorna dict com 'peaks_idx', 'rr_sec', 'hr_bpm_mean', 'hr_bpm_median'.
    """
    # converte posição (pixels) para "amplitude" invertida para destacar picos
    y_inv = -(y - np.median(y))
    # z-score
    z = (y_inv - np.mean(y_inv)) / (np.std(y_inv) + 1e-6)
    # distância mínima entre picos (em pixels)
    min_dist_sec = 60.0 / max_bpm
    min_dist_px = int(px_per_sec * min_dist_sec)
    if min_dist_px < 1: min_dist_px = 1
    # detecção: pico local com z > zthr e distância mínima
    peaks = []
    last = -1e9
    for i in range(1, len(z)-1):
        if z[i] > zthr and z[i] >= z[i-1] and z[i] >= z[i+1]:
            if i - last >= min_dist_px:
                peaks.append(i); last = i
    # RR e FC
    rr_sec = []
    for a,b in zip(peaks, peaks[1:]):
        rr_sec.append((b-a)/px_per_sec)
    hr = [60.0/r for r in rr_sec if r>1e-6]
    hr_mean = float(np.mean(hr)) if hr else None
    hr_median = float(np.median(hr)) if hr else None
    return {"peaks_idx": peaks, "rr_sec": rr_sec, "hr_bpm_mean": hr_mean, "hr_bpm_median": hr_median}

def estimate_px_per_sec(px_per_mm: Optional[float], speed_mm_per_sec: float = 25.0) -> Optional[float]:
    return (px_per_mm * speed_mm_per_sec) if px_per_mm else None

    ```

    #### 📄 rpeaks_robust.py

    ```py

import numpy as np
from typing import Dict, List, Tuple, Optional

def _moving_avg(x: np.ndarray, win: int) -> np.ndarray:
    win = max(1, int(win))
    ker = np.ones(win, dtype=float) / win
    return np.convolve(x, ker, mode="same")

def _diff_ma_bandpass(x: np.ndarray, lo_win: int, hi_win: int) -> np.ndarray:
    """
    Filtro banda limitada usando diferença de médias móveis (hi-pass + low-pass simples).
    lo_win: janela curta (passa altas)  ~ 5-15 ms
    hi_win: janela longa (remove DC)    ~ 150-200 ms
    """
    lo = _moving_avg(x, lo_win)
    hi = _moving_avg(x, hi_win)
    return lo - hi

def _normalize(x: np.ndarray) -> np.ndarray:
    x = x - np.median(x)
    s = np.std(x) + 1e-6
    return x / s

def _integrator(y: np.ndarray, win: int) -> np.ndarray:
    # Integração por janela deslizante (média) — etapa final do Pan‑Tompkins
    return _moving_avg(y, win)

def pan_tompkins_like(y_px: np.ndarray, px_per_sec: float,
                      lo_ms: float = 12.0, hi_ms: float = 180.0,
                      deriv_ms: float = 8.0, integ_ms: float = 150.0,
                      refractory_ms: float = 200.0,
                      learn_sec: float = 2.0) -> Dict:
    """
    Pipeline Pan‑Tompkins-like sobre traçado 1D (posição em pixels ao longo do tempo em "colunas").
    Retorna picos R robustos e intermediários (sinais) para debug.
    """
    # 1) Sinal: inverter para que picos positivos representem complexos QRS
    y = -(y_px - np.median(y_px))
    fs = float(px_per_sec)
    # 2) Banda limitada (diferença de MAs)
    lo_win = max(1, int(lo_ms * fs / 1000.0))
    hi_win = max(lo_win+1, int(hi_ms * fs / 1000.0))
    yb = _diff_ma_bandpass(y, lo_win, hi_win)
    # 3) Derivada e quadrado
    d_win = max(1, int(deriv_ms * fs / 1000.0))
    dy = np.diff(yb, prepend=yb[:1])
    dy = _moving_avg(dy, d_win)
    sq = dy * dy
    # 4) Integração janela
    i_win = max(1, int(integ_ms * fs / 1000.0))
    yi = _integrator(sq, i_win)
    yi = _normalize(yi)

    # 5) Threshold adaptativo estilo Pan‑Tompkins
    thr_spki = 0.0  # nível sinal
    thr_npki = 0.0  # nível ruído
    peaks = []
    rp = int(refractory_ms * fs / 1000.0)
    last_peak = -10**9

    # fase de aprendizado
    n_learn = int(learn_sec * fs)
    base = yi[:max(10, n_learn)]
    thr_npki = float(np.median(base))
    thr_spki = float(np.percentile(base, 95))
    THR1 = thr_npki + 0.25*(thr_spki - thr_npki)

    for i in range(len(yi)):
        if yi[i] > THR1 and (i - last_peak) >= rp:
            # candidato a R: pico local
            if yi[i] >= yi[i-1] and yi[i] >= yi[min(i+1, len(yi)-1)]:
                peaks.append(i)
                last_peak = i
                # atualiza níveis
                thr_spki = 0.875*thr_spki + 0.125*yi[i]
                THR1 = thr_npki + 0.25*(thr_spki - thr_npki)
        else:
            # atualiza ruído lentamente
            thr_npki = 0.875*thr_npki + 0.125*yi[i]
            THR1 = thr_npki + 0.25*(thr_spki - thr_npki)

    return {
        "peaks_idx": peaks,
        "fs_px": fs,
        "signals": {"yb": yb, "dy": dy, "sq": sq, "yi": yi},
        "params": {"lo_win": lo_win, "hi_win": hi_win, "d_win": d_win, "i_win": i_win, "rp": rp}
    }

    ```

    #### 📄 segmentation.py

    ```py

import numpy as np

def find_content_bbox(gray, tol=250):
    """Retorna bbox (x0,y0,x1,y1) da área não-branca (heurística)."""
    mask = gray < tol
    ys, xs = np.where(mask)
    if len(xs)==0 or len(ys)==0:
        h, w = gray.shape
        return (0,0,w,h)
    return (int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1))

def segment_12leads_basic(gray, layout="3x4", bbox=None, margin=0.02):
    """
    Segmentação simplificada: divide retângulo de conteúdo em 3 linhas x 4 colunas.
    Retorna lista de dicts: {lead, bbox:(x0,y0,x1,y1)}
    """
    h, w = gray.shape
    if bbox is None:
        bbox = find_content_bbox(gray)
    x0,y0,x1,y1 = bbox
    W = x1-x0; H = y1-y0
    rows, cols = 3, 4
    mx = int(margin*W); my = int(margin*H)
    labels = ["I","II","III","aVR","aVL","aVF","V1","V2","V3","V4","V5","V6"]
    out = []
    k = 0
    for r in range(rows):
        for c in range(cols):
            cx0 = x0 + c*W//cols + mx
            cx1 = x0 + (c+1)*W//cols - mx
            cy0 = y0 + r*H//rows + my
            cy1 = y0 + (r+1)*H//rows - my
            out.append({"lead": labels[k], "bbox": (int(cx0),int(cy0),int(cx1),int(cy1))})
            k += 1
    return out

    ```

    #### 📄 segmentation_ext.py

    ```py

from typing import List, Dict, Tuple
import numpy as np

def _grid_boxes(bbox, rows, cols, margin=0.02):
    x0,y0,x1,y1 = bbox
    W = x1-x0; H = y1-y0
    mx = int(margin*W); my = int(margin*H)
    boxes = []
    for r in range(rows):
        for c in range(cols):
            cx0 = x0 + c*W//cols + mx
            cx1 = x0 + (c+1)*W//cols - mx
            cy0 = y0 + r*H//rows + my
            cy1 = y0 + (r+1)*H//rows - my
            boxes.append((int(cx0),int(cy0),int(cx1),int(cy1)))
    return boxes

def segment_layout(gray, layout="3x4", bbox=None, margin=0.02):
    """
    Suporta: '3x4', '6x2', '3x4+rhythm' (lead II longo inferior).
    Retorna lista de dicts {lead, bbox}.
    """
    from .segmentation import find_content_bbox
    if bbox is None:
        bbox = find_content_bbox(gray)
    x0,y0,x1,y1 = bbox
    if layout == "3x4":
        labels = ["I","II","III","aVR","aVL","aVF","V1","V2","V3","V4","V5","V6"]
        boxes = _grid_boxes(bbox, 3, 4, margin)
        return [{"lead": lab, "bbox": box} for lab, box in zip(labels, boxes)]
    elif layout == "6x2":
        # linha 1: I, II, III, aVR, aVL, aVF  |  linha 2: V1..V6
        top_h = (y1-y0)//2
        top_bbox = (x0,y0,x1,y0+top_h)
        bot_bbox = (x0,y0+top_h,x1,y1)
        labs_top = ["I","II","III","aVR","aVL","aVF"]
        labs_bot = ["V1","V2","V3","V4","V5","V6"]
        boxes = []
        boxes += _grid_boxes(top_bbox, 1, 6, margin)
        boxes += _grid_boxes(bot_bbox, 1, 6, margin)
        return [{"lead": lab, "bbox": box} for lab, box in zip(labs_top+labs_bot, boxes)]
    elif layout == "3x4+rhythm":
        # 3x4 clássico + tira longa (II) em faixa inferior de 15% da altura
        base_h = int((y1-y0)*0.85)
        base_bbox = (x0,y0,x1,y0+base_h)
        rhythm_bbox = (x0,y0+base_h,x1,y1)
        labels = ["I","II","III","aVR","aVL","aVF","V1","V2","V3","V4","V5","V6"]
        boxes = _grid_boxes(base_bbox, 3, 4, margin)
        out = [{"lead": lab, "bbox": box} for lab, box in zip(labels, boxes)]
        out.append({"lead":"II_rhythm","bbox":(x0,y0+base_h,x1,y1)})
        return out
    else:
        raise ValueError(f"Layout não suportado: {layout}")

    ```

  ### 📁 assets/

    ### 📁 manifest/

      - ecg_datasets.v1.jsonl `(Conteúdo não incluído)`

      - ecg_images.v1.jsonl `(Conteúdo não incluído)`

      - ecg_images_index.csv `(Conteúdo não incluído)`

  ### 📁 notebooks/

    - 00_seed.ipynb `(Conteúdo não incluído)`

    - 01_seed.ipynb `(Conteúdo não incluído)`

    - 02_seed.ipynb `(Conteúdo não incluído)`

    - 10_QTc_formulas_e_armadilhas.ipynb `(Conteúdo não incluído)`

    - 11_Eixo_I_aVF_vetor.ipynb `(Conteúdo não incluído)`

    - 12_Rpeaks_e_RR.ipynb `(Conteúdo não incluído)`

    - 13_Ions_e_STT_demo.ipynb `(Conteúdo não incluído)`

    - 14_Artefatos_e_Filtros.ipynb `(Conteúdo não incluído)`

    - 15_Imagem_Preprocess_basico.ipynb `(Conteúdo não incluído)`

    - 16_Grid_detect_nocoes.ipynb `(Conteúdo não incluído)`

    - 17_Calibracao_Autocorrelacao.ipynb `(Conteúdo não incluído)`

    - 18_Segmentacao_12Derivacoes_Basica.ipynb `(Conteúdo não incluído)`

    - 19_Deskew_BuscaBruta.ipynb `(Conteúdo não incluído)`

    - 20_Normalizacao_Escala.ipynb `(Conteúdo não incluído)`

    - 21_Segmentacao_Layouts.ipynb `(Conteúdo não incluído)`

    - 22_Deteccao_Layout_Rotulos.ipynb `(Conteúdo não incluído)`

    - 23_RPeaks_Inicial.ipynb `(Conteúdo não incluído)`

    - 24_RPeaks_Robustos.ipynb `(Conteúdo não incluído)`

    - 25_Intervalos_OnsetsOffsets.ipynb `(Conteúdo não incluído)`

    - 26_Quiz_Dinamico.ipynb `(Conteúdo não incluído)`


## Context rápido

Este repositório é o "ECGiga" — um megaprojeto Python para análise e ensino de ECGs. As peças principais estão em

- `cli_app/` — CLI Typer baseada em `ecgcourse` (utilitários, ingestão, quizzes). Veja `cli_app/ecgcourse/cli.py` para exemplos de comandos.
- `cv/` — processamento de imagens de ECG (deskew, grid detect, lead OCR, rpeaks, intervals). Exemplos: `cv/grid_detect.py`, `cv/lead_ocr.py`, `cv/rpeaks_from_image.py`.
- `web_app/` — front interativo (Dash) usado para visualizações interativas e casos.
- `notebooks/` — notebooks didáticos e experimentos; úteis para reproduzir heurísticas.
- `quiz/` — schema e geradores de MCQ; schema principal: `quiz/schema/mcq.schema.json`.

## Objetivo para agentes de codificação

Seja conciso e focado: melhorias devem preservar heurísticas existentes (não substitua sem testes). Priorize:

- clareza das transformações em `cv/` (imagem → traço → picos → intervalos);
- estabilidade das saídas JSON/schema (`quiz/schema/*`, `reports/`);
- compatibilidade com a CLI (`cli_app/ecgcourse/cli.py`) — mantenha assinaturas de opções.

## Comandos e fluxos de desenvolvedor (descobertos no repositório)

- Rodar CLI (exemplos):
  - `python -m ecgcourse quiz run quizzes/sample.json`
  - `python -m ecgcourse ingest image samples/img001.png --deskew --normalize --auto-grid --auto-leads --rpeaks-lead II --schema-v3 --report`
  - `python -m ecgcourse analyze values --qt 360 --rr 800 --sexo M`

- Web app (Dash interativo):
  - `cd ECG_Curso_Megaprojeto_p16_append/web_app/dash_app && python app.py`
  - Abre em `http://localhost:8050` por padrão (modo debug).
  - Usa páginas multi-page Dash (arquitetura: `dash.page_registry`, callbacks em arquivos separados).

- Tests / linting: dependências listadas em `ECG_Curso_Megaprojeto_p16_append/requirements.txt`. Projeto usa `black` e `ruff` (configs em `pyproject.toml`). Use `pytest` para testes.

- Dependências nativas opcionais:
  - **Tesseract OCR**: requerido apenas se usar `pytesseract` para OCR de rótulos (fallback em `cv/lead_ocr.py`). Template matching funciona sem ele.
  - **AVIF plugin (Pillow)**: listado em `requirements.txt` mas opcional; detectado em runtime.

## Padrões e decisões específicas do projeto

- Entradas/saídas são frequentemente JSON sidecars (ex.: `<img>.meta.json`) — preserve esse formato quando criar novas rotinas de ingestão.
- Heurísticas são preferidas a modelos complexos em módulos CV (funções com nomes como `estimate_grid_period_px`, `segment_12leads_basic`, `detect_rpeaks_from_trace`). Prefira refatorar com testes ao invés de substituição total.
- Interoperabilidade entre módulos via dicionários/JSON: muitos pontos esperam chaves como `rpeaks.peaks_idx`, `layout.labels`, `measures.qrs_ms` — siga esses nomes ao emitir relatórios.
- Pipelines de processamento de imagem são compostos e sequenciais: `deskew` → `normalize` → `grid_detect` → `segmentation` → `lead_ocr` → `rpeaks` → `intervals`. Cada etapa emite dict/JSON que alimenta a próxima.

### Exemplos de funções-chave em `cv/`:

- `cv/rpeaks_from_image.py::extract_trace_centerline(gray_crop, band=0.8)`: Extrai série 1D y(x) do traçado pegando pixel mais escuro (mínimo) em cada coluna dentro de uma banda vertical central. Retorna array NumPy com coordenadas y.
- `cv/rpeaks_from_image.py::detect_rpeaks_from_trace(y, px_per_sec, zthr=2.0)`: Detecta R-peaks por z-score invertido (picos para cima) com threshold e distância mínima entre picos. Retorna `{'peaks_idx': [...], 'rr_sec': [...], 'hr_bpm_mean': float, 'hr_bpm_median': float}`.
- `cv/grid_detect.py::estimate_grid_period_px(arr)`: Estima período da grade (em pixels) por autocorrelação ou FFT. Retorna dict com `px_small_x`, `px_small_y` (1 mm), `px_large_x`, `px_large_y` (5 mm).
- `cv/segmentation.py::segment_12leads_basic(gray, bbox)`: Segmenta 12 derivações em layout 3×4 ou 6×2. Retorna lista de dicts `[{'lead': 'I', 'bbox': (x0,y0,x1,y1)}, ...]`.

## Arquivos-chave a revisar antes de alterar comportamento crítico

- `cli_app/ecgcourse/cli.py` — define a superfície pública da CLI (parâmetros, formatos de saída).
- `cv/rpeaks_from_image.py`, `cv/rpeaks_robust.py`, `cv/intervals.py`, `cv/intervals_refined.py` — algoritmos de sinais.
- `quiz/schema/mcq.schema.json` — validação dos itens MCQ (use `jsonschema` como no CLI).
- `docs/` — várias notas de design (ex.: `docs/arquitetura.md`, `docs/dev_p6_layout_rpeaks.md`, `docs/dev_p7_rpeaks_intervals_quiz.md`) que explicam formato e limitações.

## Do's e Don'ts para o agente

- Do: Cite e link (caminho) para os arquivos que você altera. Ex.: "Editei `cv/rpeaks_from_image.py` — modifiquei `detect_rpeaks_from_trace`".
- Do: Sempre manter compatibilidade com a CLI — preserve nomes de opções e formatos JSON de saída.
- Do: Adicionar/atualizar testes mínimos quando mudar heurísticas (use `pytest`).
- Don't: Não remover shortcuts heurísticos sem fornecer comparações (ex.: antes/depois em notebooks ou testes).
- Don't: Não assumir bibliotecas de sistema (ex.: tesseract) estarão presentes — a base usa `pytesseract` apenas como opcional; documente dependências nativas quando necessário.

## Exemplos rápidos para o agente

- Para adicionar um modo mais robusto de detecção de picos, estenda `cv/rpeaks_robust.py` e garanta que o CLI aceite `--rpeaks-robust` (veja `cli.py:ingest_image`).
- Para emitir novo campo no laudo JSON, adicione a chave em `cli_app` antes de salvar em `reports/` e atualize `docs/` para explicitar o novo campo.

## Quando pedir esclarecimentos ao mantenedor

- Se alterar schema de saída JSON.
- Se precisar instalar binários (tesseract, etc.) para recursos opcionais.

---

Se algo aqui ficou vago ou você quer que eu destaque exemplos adicionais (ex.: funções dentro de `cv/` para link direto), diga quais áreas priorizar e eu itero.

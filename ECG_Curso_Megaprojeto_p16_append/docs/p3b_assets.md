
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


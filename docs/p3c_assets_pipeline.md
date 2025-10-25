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

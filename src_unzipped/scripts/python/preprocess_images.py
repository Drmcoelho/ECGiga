#!/usr/bin/env python3
"""
Pré-processador de imagens para Web (p3c).
- Lê assets/raw/images/<id>.<ext>
- Gera WEBP (sempre) e AVIF (se pillow-avif-plugin disponível)
- Tamanhos-alvo (larguras): 320, 640, 1024, 1600 (sem upscaling)
- Stripa metadados e garante compressão eficiente
- Emite manifest derivado: assets/manifest/ecg_images.derived.json
"""
import json
import pathlib
import sys

from PIL import Image

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
        sizes.append(
            {"format": "webp", "width": tw, "height": th, "path": str(webp_path.relative_to(BASE))}
        )
        # AVIF opcional
        if AVIF_OK:
            avif_path = webp_dir / (path.stem + ".avif")
            try:
                imr.save(avif_path, "AVIF", quality=50)
                sizes.append(
                    {
                        "format": "avif",
                        "width": tw,
                        "height": th,
                        "path": str(avif_path.relative_to(BASE)),
                    }
                )
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

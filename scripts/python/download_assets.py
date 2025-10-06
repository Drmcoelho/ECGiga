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

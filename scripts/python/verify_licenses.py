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


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


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

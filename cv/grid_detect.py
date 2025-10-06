
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

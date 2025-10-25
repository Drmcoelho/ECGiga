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
    w1, h1 = int(w0 * scale), int(h0 * scale)
    im1 = img.resize((w1, h1), Image.LANCZOS)
    return im1, scale, pxmm

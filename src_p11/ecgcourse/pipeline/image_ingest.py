"""
Pure function image processing pipeline extracted from CLI ingest logic.
Provides process_image() function that takes image data and parameters,
returns structured report without filesystem side effects.
"""

import json
import time
import io
from datetime import datetime
from typing import Dict, Any, Optional, Union, BinaryIO
from PIL import Image
from pathlib import Path

def _axis_from_I_aVF(lead_i_mv: float, avf_mv: float) -> tuple[Optional[float], Optional[str]]:
    """Calculate axis from lead I and aVF values."""
    if lead_i_mv is None or avf_mv is None:
        return None, None
    
    # Simplified axis calculation
    if lead_i_mv > 0 and avf_mv > 0:
        angle = 60.0
        label = "Normal"
    elif lead_i_mv > 0 and avf_mv < 0:
        angle = -30.0
        label = "LAD"
    elif lead_i_mv < 0 and avf_mv > 0:
        angle = 120.0
        label = "RAD"
    else:
        angle = -120.0
        label = "Extrema"
    
    return angle, label

def _qtc(qt_ms: float, rr_ms: float) -> tuple[Optional[float], Optional[float]]:
    """Calculate QTc using Bazett and Fridericia formulas."""
    if qt_ms is None or rr_ms is None:
        return None, None
    
    rr_sec = rr_ms / 1000.0
    qtc_bazett = qt_ms / (rr_sec ** 0.5)
    qtc_fridericia = qt_ms / (rr_sec ** (1/3))
    
    return qtc_bazett, qtc_fridericia

def process_image(
    image_data: Union[bytes, BinaryIO],
    deskew: bool = False,
    normalize: bool = False,
    auto_grid: bool = False,
    rpeaks_lead: Optional[str] = None,
    rpeaks_robust: bool = False,
    intervals: bool = False,
    sexo: Optional[str] = None,
    meta_data: Optional[Dict[str, Any]] = None,
    schema_version: str = "0.4.0"
) -> Dict[str, Any]:
    """
    Process ECG image and return structured report.
    
    This is a pure function extracted from CLI ingest logic.
    No filesystem writes except reading source image data.
    
    Args:
        image_data: Image bytes or BytesIO object
        deskew: Apply rotation correction
        normalize: Normalize scale to target px/mm
        auto_grid: Enable automatic grid detection and segmentation
        rpeaks_lead: Lead name for R-peak detection (e.g., "II", "V2")
        rpeaks_robust: Use robust R-peak detection algorithm
        intervals: Calculate PR/QRS/QT intervals
        sexo: Patient sex ("M"/"F") for QTc thresholds
        meta_data: Optional metadata dict with calibration/patient info
        schema_version: Report schema version
        
    Returns:
        Structured report dict compatible with schema v0.4/v0.5
    """
    # Handle image data input
    if isinstance(image_data, bytes):
        image_buffer = io.BytesIO(image_data)
    else:
        image_buffer = image_data
        image_buffer.seek(0)
    
    # Initialize metadata
    meta_data = meta_data or {}
    created_at = datetime.now().isoformat()
    
    # Track processing capabilities
    capabilities = []
    flags = []
    
    try:
        # Load and process image
        img = Image.open(image_buffer).convert("RGB")
        
        # Pre-processing pipeline
        if deskew:
            try:
                from cv.deskew import estimate_rotation_angle, rotate_image
                info = estimate_rotation_angle(img, search_deg=6.0, step=0.5)
                img = rotate_image(img, info['angle_deg'])
                capabilities.append("deskew")
            except ImportError:
                flags.append("deskew_unavailable")
            except Exception as e:
                flags.append(f"deskew_failed: {str(e)[:100]}")
        
        if normalize:
            try:
                from cv.normalize import normalize_scale
                img, scale, pxmm = normalize_scale(img, target_px_per_mm=10.0)
                capabilities.append("normalize")
            except ImportError:
                flags.append("normalize_unavailable")
            except Exception as e:
                flags.append(f"normalize_failed: {str(e)[:100]}")
        
        # Convert processed image back to buffer for further analysis
        processed_buffer = io.BytesIO()
        img.save(processed_buffer, format="PNG")
        processed_buffer.seek(0)
        
        # Initialize analysis results
        grid = None
        seg = None
        layout_det = None
        rpeaks_out = None
        intervals_out = None
        intervals_refined_out = None
        axis_out = None
        
        # Auto grid detection and segmentation
        if auto_grid:
            try:
                import numpy as np
                from cv.grid_detect import estimate_grid_period_px
                from cv.segmentation import segment_12leads_basic, find_content_bbox
                
                arr = np.asarray(img)
                grid = estimate_grid_period_px(arr)
                
                gray = np.asarray(img.convert("L"))
                bbox = find_content_bbox(gray)
                seg_leads = segment_12leads_basic(gray, bbox=bbox)
                seg = {"content_bbox": bbox.tolist() if hasattr(bbox, 'tolist') else bbox, "leads": seg_leads}
                
                capabilities.append("segmentation")
                
                # R-peaks detection if requested
                if rpeaks_lead and seg_leads:
                    try:
                        from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, detect_rpeaks_from_trace, estimate_px_per_sec
                        
                        # Find bbox for requested lead
                        lab2box = {d["lead"]: d["bbox"] for d in seg_leads}
                        if rpeaks_lead in lab2box:
                            x0, y0, x1, y1 = lab2box[rpeaks_lead]
                            crop = gray[y0:y1, x0:x1]
                            trace = smooth_signal(extract_trace_centerline(crop, band=0.8), win=11)
                            
                            pxmm = grid.get("px_small_x") if grid else 10.0
                            pxsec = estimate_px_per_sec(pxmm, 25.0) or 250.0
                            
                            if rpeaks_robust:
                                try:
                                    from cv.rpeaks_robust import pan_tompkins_like
                                    rob = pan_tompkins_like(trace, pxsec)
                                    rpeaks_out = {"peaks_idx": rob["peaks_idx"], "method": "pan_tompkins_like", "lead_used": rpeaks_lead}
                                    capabilities.append("rpeaks_robust")
                                except ImportError:
                                    flags.append("rpeaks_robust_unavailable")
                            else:
                                rpeaks_out = detect_rpeaks_from_trace(trace, px_per_sec=pxsec, zthr=2.0)
                                rpeaks_out["lead_used"] = rpeaks_lead
                                rpeaks_out["method"] = "basic"
                            
                            capabilities.append("rpeaks")
                            
                            # Intervals calculation
                            if intervals and rpeaks_out.get("peaks_idx"):
                                try:
                                    from cv.intervals import intervals_from_trace
                                    intervals_out = intervals_from_trace(trace, rpeaks_out["peaks_idx"], pxsec)
                                    capabilities.append("intervals")
                                except ImportError:
                                    flags.append("intervals_unavailable")
                                except Exception as e:
                                    flags.append(f"intervals_failed: {str(e)[:100]}")
                    
                    except ImportError:
                        flags.append("rpeaks_unavailable")
                    except Exception as e:
                        flags.append(f"rpeaks_failed: {str(e)[:100]}")
                        
            except ImportError:
                flags.append("cv_modules_unavailable")
            except Exception as e:
                flags.append(f"segmentation_failed: {str(e)[:100]}")
        
        # Extract measurements from metadata or analysis results  
        measures = meta_data.get("measures", {})
        rr_ms = measures.get("rr_ms")
        fc_bpm = measures.get("fc_bpm") or (60000.0/rr_ms if rr_ms else None)
        qt_ms = measures.get("qt_ms") 
        pr_ms = measures.get("pr_ms")
        qrs_ms = measures.get("qrs_ms")
        lead_i = measures.get("lead_i_mv")
        avf = measures.get("avf_mv")
        
        # Calculate derived values
        angle, axis_label = _axis_from_I_aVF(lead_i, avf) if (lead_i is not None and avf is not None) else (None, None)
        qb, qf = (None, None)
        if qt_ms and (rr_ms or fc_bpm):
            rr_calc = rr_ms if rr_ms else 60000.0/float(fc_bpm)
            qb, qf = _qtc(float(qt_ms), float(rr_calc))
        
        # Clinical interpretation flags
        sexo_s = (sexo or meta_data.get("sexo", "")).strip().upper()
        limiar = 450 if sexo_s == "M" else (470 if sexo_s == "F" else 460)
        
        clinical_flags = []
        if pr_ms is not None and pr_ms > 200:
            clinical_flags.append("PR > 200 ms: suspeita de BAV 1º")
        if pr_ms is not None and pr_ms < 120 and (qrs_ms is None or qrs_ms < 120):
            clinical_flags.append("PR < 120 ms: considerar pré-excitação") 
        if qrs_ms is not None:
            if qrs_ms >= 120:
                clinical_flags.append("QRS ≥ 120 ms: bloqueio de ramo completo/origem ventricular")
            elif 110 <= qrs_ms < 120:
                clinical_flags.append("QRS 110–119 ms: bloqueio de ramo incompleto")
        if (qb is not None and qb >= limiar) or (qf is not None and qf >= limiar):
            clinical_flags.append(f"QTc prolongado (limiar {limiar} ms)")
        if (qb is not None and qb < 350) or (qf is not None and qf < 350):
            clinical_flags.append("QTc possivelmente curto (<350 ms)")
        
        # Clinical suggestions
        suggested = []
        if clinical_flags:
            if any("QTc prolongado" in f for f in clinical_flags):
                suggested.append("Investigar causas de QT prolongado (drogas, distúrbios eletrolíticos, canalopatias).")
            if any("PR > 200" in f for f in clinical_flags):
                suggested.append("Compatível com BAV de 1º grau em contexto clínico adequado.")
            if any("pré-excitação" in f for f in clinical_flags):
                suggested.append("Se houver delta/QRS largo, considerar WPW e ajuste de manejo em taquiarritmias.")
            if any("QRS ≥ 120" in f for f in clinical_flags):
                suggested.append("QRS largo: avaliar morfologia BRE/BRD, discordâncias e critérios de isquemia em bloqueios.")
        else:
            suggested.append("Sem flags críticas pelos limiares configurados; correlacionar clinicamente.")
        
        # Combine all flags
        all_flags = flags + clinical_flags
        
    except Exception as e:
        # Fallback for when CV modules are unavailable or processing fails
        capabilities = []
        all_flags = ["pipeline_unavailable", f"error: {str(e)[:200]}"]
        
        # Minimal report structure
        seg = None
        grid = None
        rpeaks_out = None
        intervals_out = None
        axis_out = None
        layout_det = None
        
        # Basic metadata extraction
        measures = meta_data.get("measures", {})
        fc_bpm = measures.get("fc_bpm") 
        qt_ms = measures.get("qt_ms")
        pr_ms = measures.get("pr_ms") 
        qrs_ms = measures.get("qrs_ms")
        angle = None
        axis_label = None
        qb, qf = None, None
        suggested = ["Processamento de imagem indisponível - apenas metadados exibidos"]
    
    # Build final report object
    report_obj = {
        "meta": {
            "source": "api_ingest",
            "ingest_version": "p4-0.1",
            "created_at": created_at,
            "processing_flags": flags,
            "notes": [f"Schema version: {schema_version}"]
        },
        "patient_info": {
            "id": meta_data.get("patient_id"),
            "age": meta_data.get("age"),
            "sex": sexo_s or meta_data.get("sexo") or None,
            "context": meta_data.get("context")
        },
        "acquisition": {
            "dpi": meta_data.get("dpi"),
            "mm_per_mV": meta_data.get("mm_per_mV"),
            "ms_per_div": meta_data.get("ms_per_div"),
            "leads_layout": meta_data.get("leads_layout", "3x4"),
            "px_per_mm_x": grid.get("px_small_x") if grid else None,
            "px_per_mm_y": grid.get("px_small_y") if grid else None,
            "grid_confidence": grid.get("confidence") if grid else None
        },
        "measures": {
            "pr_ms": pr_ms,
            "qrs_ms": qrs_ms, 
            "qt_ms": qt_ms,
            "rr_ms": rr_ms,
            "fc_bpm": fc_bpm,
            "axis_angle_deg": angle,
            "axis_label": axis_label,
            "qtc_bazett_ms": qb,
            "qtc_fridericia_ms": qf
        },
        "flags": all_flags,
        "suggested_interpretations": suggested,
        "segmentation": seg,
        "layout_detection": layout_det,
        "rpeaks": rpeaks_out,
        "intervals": intervals_out,
        "intervals_refined": intervals_refined_out,
        "axis": axis_out,
        "capabilities": capabilities,
        "version": schema_version
    }
    
    return report_obj
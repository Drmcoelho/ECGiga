"""
Phase 20 – Pulmonary Embolism (TEP) Detection
===============================================
Detection of ECG patterns associated with acute pulmonary embolism:
S1Q3T3, right heart strain, and overall PE scoring.

Camera analogy:
    A massive PE suddenly overloads the right ventricle.  The cameras
    pointing at the right heart (V1-V4, III) see the strain, while
    the left-facing cameras (I, aVL, V5-V6) lose their normal dominance.
    S1Q3T3 is like camera I seeing the left ventricle "shrink" (S wave),
    camera III seeing the right ventricle "push forward" (Q wave + inverted T).
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np


# ---------------------------------------------------------------------------
# S1Q3T3 Detection
# ---------------------------------------------------------------------------

def detect_s1q3t3(leads_data: Dict[str, Dict]) -> Dict:
    """Detect the classic S1Q3T3 pattern of acute right heart strain.

    Parameters
    ----------
    leads_data : dict
        Keys are lead names. Each value is a dict with optional keys:
        - ``s_wave_mv`` (float): S-wave amplitude in mV (negative value indicates depth)
        - ``q_wave_mv`` (float): Q-wave amplitude in mV (negative value)
        - ``t_wave_polarity`` (str): ``"positive"``, ``"negative"``, or ``"biphasic"``
        - ``s_wave_present`` (bool): explicit S-wave presence flag
        - ``q_wave_present`` (bool): explicit Q-wave presence flag

    Returns
    -------
    dict
        ``s1`` (bool), ``q3`` (bool), ``t3_inverted`` (bool),
        ``pattern_complete`` (bool), ``confidence`` (float), ``details`` (str).
    """
    # --- S wave in lead I ---
    lead_i = leads_data.get("I", {})
    s1 = False
    s1_detail = ""
    if lead_i.get("s_wave_present", False):
        s1 = True
        s1_detail = "Onda S presente em DI"
    elif "s_wave_mv" in lead_i:
        # S wave deeper than -0.15 mV (1.5 mm) is significant
        if lead_i["s_wave_mv"] < -0.10:
            s1 = True
            s1_detail = f"Onda S em DI = {lead_i['s_wave_mv']:.2f} mV"

    # --- Q wave in lead III ---
    lead_iii = leads_data.get("III", {})
    q3 = False
    q3_detail = ""
    if lead_iii.get("q_wave_present", False):
        q3 = True
        q3_detail = "Onda Q presente em DIII"
    elif "q_wave_mv" in lead_iii:
        if lead_iii["q_wave_mv"] < -0.10:
            q3 = True
            q3_detail = f"Onda Q em DIII = {lead_iii['q_wave_mv']:.2f} mV"

    # --- Inverted T in lead III ---
    t3_inverted = False
    t3_detail = ""
    t_pol = lead_iii.get("t_wave_polarity", "")
    if t_pol == "negative":
        t3_inverted = True
        t3_detail = "Onda T invertida em DIII"
    elif "t_wave_mv" in lead_iii:
        if lead_iii["t_wave_mv"] < -0.05:
            t3_inverted = True
            t3_detail = f"Onda T negativa em DIII = {lead_iii['t_wave_mv']:.2f} mV"

    pattern_complete = s1 and q3 and t3_inverted
    components_present = sum([s1, q3, t3_inverted])

    # Confidence based on how many components found
    if pattern_complete:
        confidence = 0.75
    elif components_present == 2:
        confidence = 0.4
    elif components_present == 1:
        confidence = 0.15
    else:
        confidence = 0.0

    details_parts = [d for d in [s1_detail, q3_detail, t3_detail] if d]
    details = "; ".join(details_parts) if details_parts else "Nenhum componente de S1Q3T3 detectado"

    return {
        "s1": s1,
        "q3": q3,
        "t3_inverted": t3_inverted,
        "pattern_complete": pattern_complete,
        "confidence": round(confidence, 2),
        "details": details,
    }


# ---------------------------------------------------------------------------
# Right Heart Strain
# ---------------------------------------------------------------------------

def detect_right_heart_strain(leads_data: Dict[str, Dict]) -> Dict:
    """Detect signs of right heart strain on ECG.

    Signs evaluated:
    * Right axis deviation (axis > 90 degrees)
    * New RBBB (incomplete or complete)
    * T-wave inversion in V1-V4 (right precordial strain)
    * Sinus tachycardia (HR > 100)
    * S1Q3T3 pattern (delegated to :func:`detect_s1q3t3`)

    Parameters
    ----------
    leads_data : dict
        Keys are lead names.  Each value is a dict with:
        - ``t_wave_polarity`` (str): "positive", "negative", "biphasic"
        - ``axis_degrees`` (float): in the top-level or lead-I sub-dict
        - ``rbbb`` (bool): in top-level
        - ``heart_rate`` (float): in top-level
        - Plus any keys used by :func:`detect_s1q3t3`.

    Returns
    -------
    dict
        ``right_axis`` (bool), ``rbbb`` (bool), ``t_inversion_v1v4`` (list),
        ``tachycardia`` (bool), ``s1q3t3`` (dict), ``strain_score`` (int 0-5),
        ``interpretation`` (str).
    """
    # Top-level metadata (can be stored in a "__meta__" key or directly)
    meta = leads_data.get("__meta__", {})

    # Right axis deviation
    axis = meta.get("axis_degrees", leads_data.get("axis_degrees", None))
    right_axis = False
    if axis is not None:
        right_axis = axis > 90

    # RBBB
    rbbb = meta.get("rbbb", leads_data.get("rbbb", False))

    # T-wave inversion in V1-V4
    t_inv_leads: List[str] = []
    for lead_name in ["V1", "V2", "V3", "V4"]:
        ld = leads_data.get(lead_name, {})
        if ld.get("t_wave_polarity") == "negative":
            t_inv_leads.append(lead_name)

    # Tachycardia
    hr = meta.get("heart_rate", leads_data.get("heart_rate", None))
    tachycardia = False
    if hr is not None:
        tachycardia = hr > 100

    # S1Q3T3
    s1q3t3_result = detect_s1q3t3(leads_data)

    # Strain score (0-5)
    score = 0
    if right_axis:
        score += 1
    if rbbb:
        score += 1
    if len(t_inv_leads) >= 2:
        score += 1
    if tachycardia:
        score += 1
    if s1q3t3_result["pattern_complete"]:
        score += 1

    # Interpretation
    if score >= 4:
        interpretation = "Alta probabilidade de sobrecarga aguda de VD"
    elif score >= 2:
        interpretation = "Moderada probabilidade de sobrecarga de VD"
    elif score >= 1:
        interpretation = "Sinais isolados; baixa especificidade para TEP"
    else:
        interpretation = "Sem sinais eletrocardiográficos de sobrecarga de VD"

    return {
        "right_axis": right_axis,
        "rbbb": rbbb,
        "t_inversion_v1v4": t_inv_leads,
        "tachycardia": tachycardia,
        "s1q3t3": s1q3t3_result,
        "strain_score": score,
        "interpretation": interpretation,
    }


# ---------------------------------------------------------------------------
# Overall PE score
# ---------------------------------------------------------------------------

def pe_score(features: Dict) -> Dict:
    """Compute an overall ECG-based PE likelihood score.

    This is NOT a clinical decision tool (Wells/Geneva scores use clinical
    data).  It summarises ECG findings only.

    Parameters
    ----------
    features : dict
        Keys (all optional):
        - ``s1q3t3`` (bool)
        - ``right_axis`` (bool)
        - ``rbbb`` (bool)
        - ``t_inversion_right_precordial`` (bool)
        - ``sinus_tachycardia`` (bool)
        - ``atrial_fibrillation`` (bool)
        - ``st_depression_lateral`` (bool)

    Returns
    -------
    dict
        ``ecg_score`` (int 0-7), ``category`` (str), ``note`` (str).
    """
    score_map = {
        "s1q3t3": 2,
        "right_axis": 1,
        "rbbb": 1,
        "t_inversion_right_precordial": 1,
        "sinus_tachycardia": 1,
        "atrial_fibrillation": 1,
        "st_depression_lateral": 0,  # non-specific but recorded
    }

    total = 0
    present: List[str] = []
    for key, weight in score_map.items():
        if features.get(key, False):
            total += weight
            present.append(key)

    if total >= 4:
        category = "Alta suspeita eletrocardiográfica de TEP"
    elif total >= 2:
        category = "Moderada suspeita eletrocardiográfica de TEP"
    elif total >= 1:
        category = "Baixa suspeita — achados inespecíficos"
    else:
        category = "ECG sem sinais sugestivos de TEP"

    note = (
        "ATENÇÃO: o ECG tem baixa sensibilidade para TEP. "
        "Um ECG normal NÃO exclui embolia pulmonar. "
        "Sempre correlacionar com clínica, D-dímero e angiotomografia."
    )

    return {
        "ecg_score": total,
        "category": category,
        "findings_present": present,
        "note": note,
    }


def explain_pe_cameras() -> str:
    """Camera-analogy explanation of PE ECG findings.

    Returns
    -------
    str
        Educational explanation in Portuguese.
    """
    return (
        "Analogia das Câmeras — Tromboembolismo Pulmonar (TEP)\n"
        "=" * 55 + "\n\n"
        "Quando um grande coágulo obstrui a artéria pulmonar, o ventrículo "
        "direito (VD) precisa empurrar sangue contra uma resistência enorme. "
        "Isso sobrecarrega agudamente o VD.\n\n"
        "As câmeras que apontam para o lado direito do coração — V1 a V4, "
        "e DIII — captam essa sobrecarga:\n\n"
        "• Câmera DIII vê o VD dilatado empurrando para baixo → onda Q em DIII\n"
        "• Câmera DI vê o VD 'roubando' espaço do VE → onda S em DI\n"
        "• Câmera DIII vê isquemia do VD → T invertida em DIII\n"
        "→ Juntas: padrão S1Q3T3\n\n"
        "• Câmeras V1-V4 veem o VD sofrendo → inversão de T em V1-V4\n"
        "• O eixo elétrico desvia para a direita (câmeras da direita "
        "ficam dominantes)\n"
        "• RBBB pode surgir pela dilatação aguda do VD (estica o feixe "
        "de condução direito)\n\n"
        "Taquicardia sinusal é o achado MAIS COMUM (a câmera do nó sinusal "
        "dispara mais rápido tentando compensar).\n\n"
        "⚠ Lembre-se: até 25 % dos TEP têm ECG completamente normal. "
        "O ECG ajuda a suspeitar, mas nunca exclui!"
    )

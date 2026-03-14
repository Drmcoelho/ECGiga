"""Conduction abnormality detection.

Detects:
- Brugada pattern (Type 1, 2, 3) in right precordial leads
- Digitalis effect (ST "scooping", PR prolongation)
- Bundle branch block classification (RBBB, LBBB, fascicular blocks)

References:
- Brugada et al., "Present status of Brugada syndrome", JACC, 2018.
- Surawicz & Knilans, "Chou's Electrocardiography in Clinical Practice", 6th ed.
"""

from __future__ import annotations

from typing import Any


def detect_brugada_pattern(
    st_morphology_v1: str | None = None,
    st_morphology_v2: str | None = None,
    st_elevation_v1_mv: float | None = None,
    st_elevation_v2_mv: float | None = None,
    t_wave_v1: str | None = None,
    t_wave_v2: str | None = None,
    rbbb_pattern: bool = False,
    fever: bool = False,
    family_history_scd: bool = False,
) -> dict[str, Any]:
    """Detect Brugada pattern in right precordial leads.

    Brugada types:
    - Type 1 (coved): ST elevation >=2mm with coved morphology and T inversion in V1-V2
      → Diagnostic (pathognomonic)
    - Type 2 (saddleback): ST elevation >=2mm with saddleback morphology in V1-V2
      → Suggestive (needs provocation test)
    - Type 3: ST elevation <1mm with saddleback morphology
      → Non-diagnostic alone

    Parameters
    ----------
    st_morphology_v1, st_morphology_v2 : str, optional
        'coved', 'saddleback', 'normal', or None.
    st_elevation_v1_mv, st_elevation_v2_mv : float, optional
        ST elevation in millivolts.
    t_wave_v1, t_wave_v2 : str, optional
        T wave description ('inverted', 'positive', 'biphasic').
    rbbb_pattern : bool
        Whether RBBB-like pattern is present (common in Brugada).
    fever : bool
        Fever can unmask or worsen Brugada pattern.
    family_history_scd : bool
        Family history of sudden cardiac death.

    Returns
    -------
    dict
        - detected: bool
        - brugada_type: str ('1', '2', '3', 'none')
        - confidence: float (0-1)
        - findings: list[str]
        - recommendations: list[str]
        - details: str
    """
    findings: list[str] = []
    recommendations: list[str] = []

    st_v1 = st_elevation_v1_mv or 0.0
    st_v2 = st_elevation_v2_mv or 0.0
    max_st = max(st_v1, st_v2)

    morph_v1 = (st_morphology_v1 or "").lower()
    morph_v2 = (st_morphology_v2 or "").lower()
    t_v1 = (t_wave_v1 or "").lower()
    t_v2 = (t_wave_v2 or "").lower()

    brugada_type = "none"
    score = 0.0

    # Type 1: Coved ST >= 2mm (0.2 mV) with T inversion
    if ("coved" in morph_v1 or "coved" in morph_v2) and max_st >= 0.2:
        if "invert" in t_v1 or "invert" in t_v2:
            brugada_type = "1"
            score = 0.9
            findings.append(
                "Padrão Brugada Tipo 1 (coved): ST coved ≥2mm com T invertida em V1/V2"
            )
            findings.append("PADRÃO DIAGNÓSTICO — não necessita teste provocativo")

    # Type 2: Saddleback ST >= 2mm
    elif ("saddleback" in morph_v1 or "saddleback" in morph_v2) and max_st >= 0.2:
        brugada_type = "2"
        score = 0.5
        findings.append(
            "Padrão Brugada Tipo 2 (saddleback): ST saddleback ≥2mm em V1/V2"
        )
        findings.append("Padrão sugestivo — requer teste provocativo (ajmalina/flecainida)")

    # Type 3: Saddleback ST < 1mm
    elif ("saddleback" in morph_v1 or "saddleback" in morph_v2) and max_st < 0.1:
        brugada_type = "3"
        score = 0.2
        findings.append("Padrão Brugada Tipo 3: saddleback com ST < 1mm")

    # ST elevation without clear morphology description
    elif max_st >= 0.2 and (rbbb_pattern or "invert" in t_v1 or "invert" in t_v2):
        score = 0.3
        findings.append(f"ST elevado em V1/V2 ({max_st:.1f} mV) com padrão atípico")

    # Modifiers
    if fever and brugada_type != "none":
        score = min(1.0, score + 0.1)
        findings.append("Febre pode desmascarar/agravar padrão de Brugada")

    if family_history_scd:
        score = min(1.0, score + 0.1)
        findings.append("História familiar de morte súbita — aumenta risco")

    if rbbb_pattern:
        score = min(1.0, score + 0.05)
        findings.append("Padrão tipo BRD associado (comum em Brugada)")

    detected = brugada_type in ("1", "2") and score > 0.3

    # Recommendations
    if brugada_type == "1":
        recommendations = [
            "Encaminhar para eletrofisiologista",
            "Avaliar indicação de CDI (cardioversor-desfibrilador implantável)",
            "Evitar drogas que agravam Brugada (lista em brugadadrugs.org)",
            "Triagem familiar (ECG em parentes de 1° grau)",
        ]
    elif brugada_type == "2":
        recommendations = [
            "Teste provocativo com ajmalina ou flecainida",
            "Encaminhar para avaliação eletrofisiológica",
            "Evitar drogas da lista Brugada até esclarecimento",
        ]
    elif brugada_type == "3":
        recommendations = [
            "Monitorar. Considerar teste provocativo se contexto clínico suspeito.",
        ]

    details = (
        f"Brugada {'Tipo ' + brugada_type if brugada_type != 'none' else 'não detectado'}. "
        f"Confiança: {score:.0%}."
    )

    return {
        "detected": detected,
        "brugada_type": brugada_type,
        "confidence": round(score, 3),
        "findings": findings,
        "recommendations": recommendations,
        "details": details,
    }


def detect_digitalis_effect(
    report: dict,
    st_morphology: dict[str, str] | None = None,
    medication_digitalis: bool = False,
) -> dict[str, Any]:
    """Detect digitalis (digoxin) effect on ECG.

    Digitalis effect (NOT toxicity):
    - ST depression with "reverse tick" / scooping morphology
    - Short QTc
    - T wave flattening or inversion
    - PR prolongation (vagal effect)
    - Possible U waves

    Digitalis toxicity:
    - All of the above plus arrhythmias
    - Atrial tachycardia with block
    - Bidirectional VT
    - Regularized AF

    Parameters
    ----------
    report : dict
        ECG report.
    st_morphology : dict, optional
        Lead -> ST morphology description.
    medication_digitalis : bool
        Whether patient is known to be on digoxin.

    Returns
    -------
    dict
        - detected: bool
        - pattern: str ('effect', 'possible_toxicity', 'none')
        - confidence: float
        - findings: list[str]
        - details: str
    """
    iv = (report.get("intervals_refined") or report.get("intervals") or {}).get("median", {})
    flags = [f.lower() for f in report.get("flags", [])]

    findings: list[str] = []
    score = 0.0

    pr_ms = iv.get("PR_ms")
    qtc = iv.get("QTc_B")

    # ST "scooping" / reverse tick pattern
    if st_morphology:
        scooped_leads = [
            lead for lead, morph in st_morphology.items()
            if "scoop" in morph.lower() or "colher" in morph.lower()
            or "salvador dali" in morph.lower() or "reverse tick" in morph.lower()
        ]
        if scooped_leads:
            findings.append(f"ST em colher (scooping) em {', '.join(scooped_leads)}")
            score += 0.35

    # Short QTc
    if qtc and qtc < 360:
        findings.append(f"QTc encurtado ({qtc:.0f} ms)")
        score += 0.15

    # PR prolongation
    if pr_ms and pr_ms > 200:
        findings.append(f"PR prolongado ({pr_ms:.0f} ms) — efeito vagotônico")
        score += 0.15

    # Known medication
    if medication_digitalis:
        score += 0.25
        findings.append("Uso conhecido de digitálico")

    # Flags
    if any("digital" in f or "digoxin" in f for f in flags):
        score += 0.2
    if any("colher" in f or "scoop" in f for f in flags):
        score += 0.2

    score = min(1.0, score)

    # Check for toxicity signs
    toxicity_signs = []
    hr = 60.0 / iv.get("RR_s", 1) if iv.get("RR_s") else None
    if hr and hr > 100 and pr_ms and pr_ms > 200:
        toxicity_signs.append("Taquicardia com BAV — possível TAM com bloqueio")
    if any("bidirecional" in f or "bidirectional" in f for f in flags):
        toxicity_signs.append("TV bidirecional — sinal de toxicidade digitálica!")

    if toxicity_signs:
        pattern = "possible_toxicity"
        findings.extend(toxicity_signs)
        score = min(1.0, score + 0.2)
    elif score > 0.3:
        pattern = "effect"
    else:
        pattern = "none"

    detected = pattern != "none"

    details = (
        f"{'Efeito digitálico detectado' if pattern == 'effect' else 'Possível TOXICIDADE digitálica!' if pattern == 'possible_toxicity' else 'Sem padrão de digitálico'}. "
        f"Confiança: {score:.0%}."
    )

    return {
        "detected": detected,
        "pattern": pattern,
        "confidence": round(score, 3),
        "findings": findings,
        "details": details,
    }


def classify_bundle_branch_block(
    qrs_duration_ms: float,
    morphology_v1: str | None = None,
    morphology_v6: str | None = None,
    axis_deg: float | None = None,
    septal_q_absent: bool = False,
    broad_notched_r_lateral: bool = False,
) -> dict[str, Any]:
    """Classify bundle branch blocks and fascicular blocks.

    Classifications:
    - Complete RBBB: QRS ≥120ms + rSR'/rsR' in V1 + wide S in V6/I
    - Complete LBBB: QRS ≥120ms + broad R in V6 + QS/rS in V1 + no septal Q
    - Incomplete RBBB/LBBB: QRS 100-119ms with morphological criteria
    - LAFB: Left axis (-45° to -90°) + qR in I/aVL + rS in II/III
    - LPFB: Right axis (>90°) + rS in I/aVL + qR in III + no RVH

    Parameters
    ----------
    qrs_duration_ms : float
        QRS duration in ms.
    morphology_v1 : str, optional
        QRS morphology in V1: 'rsR', 'rSR', 'RSR', 'QS', 'rS', 'R', etc.
    morphology_v6 : str, optional
        QRS morphology in V6: 'qRs', 'R', 'RS', 'rS', 'QS', etc.
    axis_deg : float, optional
        QRS axis in degrees.
    septal_q_absent : bool
        Whether septal Q waves are absent in V5/V6 (LBBB criterion).
    broad_notched_r_lateral : bool
        Whether broad/notched R in lateral leads (LBBB).

    Returns
    -------
    dict
        - classification: str (e.g., 'RBBB', 'LBBB', 'LAFB', etc.)
        - complete: bool (True for complete, False for incomplete)
        - confidence: float (0-1)
        - criteria_met: list[str]
        - clinical_significance: str
        - details: str
    """
    v1 = (morphology_v1 or "").upper()
    v6 = (morphology_v6 or "").upper()

    criteria_met: list[str] = []

    if qrs_duration_ms < 100:
        return {
            "classification": "normal_conduction",
            "complete": False,
            "confidence": 0.9,
            "criteria_met": ["QRS < 100 ms — condução normal"],
            "clinical_significance": "Sem significado patológico",
            "details": "QRS estreito — condução intraventricular normal.",
        }

    complete = qrs_duration_ms >= 120

    # --- RBBB detection ---
    rbbb_score = 0.0
    if "RSR" in v1 or "RSR'" in v1 or v1 in ("RSR", "RSRP"):
        rbbb_score += 0.4
        criteria_met.append(f"RSR' em V1 ({v1})")
    elif v1 == "R" and qrs_duration_ms >= 120:
        rbbb_score += 0.2
        criteria_met.append("R puro em V1")

    if "S" in v6 and v6 not in ("RSR",):
        rbbb_score += 0.2
        criteria_met.append(f"S amplo em V6 ({v6})")

    if complete:
        rbbb_score += 0.2
        criteria_met.append(f"QRS ≥ 120 ms ({qrs_duration_ms:.0f} ms)")

    # --- LBBB detection ---
    lbbb_score = 0.0
    if v1 in ("QS", "RS") or "RS" in v1.lower():
        lbbb_score += 0.2
    if v1 == "QS":
        lbbb_score += 0.2
        criteria_met.append("QS em V1")

    if "R" in v6 and "S" not in v6 and v6 != "":
        lbbb_score += 0.2
        criteria_met.append(f"R amplo em V6 ({v6})")

    if septal_q_absent:
        lbbb_score += 0.15
        criteria_met.append("Ausência de Q septal em V5/V6")

    if broad_notched_r_lateral:
        lbbb_score += 0.2
        criteria_met.append("R alargado/entalhado em derivações laterais")

    if complete:
        lbbb_score += 0.2

    # --- Fascicular blocks ---
    lafb_score = 0.0
    lpfb_score = 0.0

    if axis_deg is not None:
        if -90 <= axis_deg <= -45:
            lafb_score += 0.6
            criteria_met.append(f"Desvio do eixo para esquerda ({axis_deg:.0f}°)")
        elif axis_deg > 90:
            lpfb_score += 0.4
            criteria_met.append(f"Desvio do eixo para direita ({axis_deg:.0f}°)")

    # --- Determine winner ---
    classifications = {
        "RBBB": rbbb_score,
        "LBBB": lbbb_score,
        "LAFB": lafb_score,
        "LPFB": lpfb_score,
    }

    best = max(classifications, key=classifications.get)
    best_score = classifications[best]

    # Bifascicular block detection
    if rbbb_score > 0.3 and lafb_score > 0.3:
        best = "RBBB + LAFB (bifascicular)"
        best_score = (rbbb_score + lafb_score) / 2
        criteria_met.append("Padrão bifascicular: BRD + BDAS")
    elif rbbb_score > 0.3 and lpfb_score > 0.3:
        best = "RBBB + LPFB (bifascicular)"
        best_score = (rbbb_score + lpfb_score) / 2
        criteria_met.append("Padrão bifascicular: BRD + BDPI")

    if best_score < 0.2:
        best = "nonspecific_IVCD"
        criteria_met.append("Atraso de condução intraventricular inespecífico")

    # Clinical significance
    if "LBBB" in best:
        significance = (
            "BRE novo pode indicar IAM. BRE crônico: avaliar cardiomiopatia, "
            "insuficiência cardíaca, doença degenerativa. "
            "Critérios de Sgarbossa/Smith se suspeita de SCA."
        )
    elif "RBBB" in best and "LAFB" in best:
        significance = (
            "Bloqueio bifascicular: risco de progressão para BAVT. "
            "Avaliar necessidade de marcapasso se síncope."
        )
    elif "RBBB" in best:
        significance = (
            "BRD isolado pode ser benigno em jovens. "
            "Considerar: TEP, CIA, sobrecarga VD, Brugada."
        )
    elif "LAFB" in best:
        significance = (
            "BDAS isolado: geralmente benigno. "
            "Comum em hipertensão, doença coronariana, envelhecimento."
        )
    else:
        significance = "Avaliar no contexto clínico."

    details = (
        f"Classificação: {best} ({'completo' if complete else 'incompleto'}). "
        f"QRS: {qrs_duration_ms:.0f} ms. Confiança: {best_score:.0%}."
    )

    return {
        "classification": best,
        "complete": complete,
        "confidence": round(best_score, 3),
        "criteria_met": criteria_met,
        "clinical_significance": significance,
        "details": details,
    }


from __future__ import annotations
from typing import Dict, List

def _mk_question(prompt: str, correct: str, wrong: List[str], exp: str) -> Dict:
    choices = [{"text": correct, "is_correct": True, "explanation": exp}]
    for w in wrong:
        choices.append({"text": w, "is_correct": False, "explanation": "Alternativa incorreta dadas as evidências do laudo."})
    return {"prompt": prompt, "choices": choices}

def quiz_from_report(rep: Dict, n_max: int = 10) -> Dict:
    qs: List[Dict] = []
    # Intervalos
    m = (rep.get("intervals_refined") or {}).get("median") or {}
    if m:
        qrs = m.get("QRS_ms"); qt = m.get("QT_ms"); qtc = m.get("QTc_B")
        if qrs is not None:
            qs.append(_mk_question(
                "Qual a interpretação correta para o QRS mediano?",
                f"QRS ≈ {qrs:.0f} ms (largo se ≥ 120 ms).",
                ["QRS estreito por definição (≤ 90 ms).","QRS não pode ser estimado a partir de laudos automáticos."],
                "Laudos confiáveis trazem a duração mediana; cortes usuais: 120 ms para bloqueios completos."
            ))
        if qtc is not None:
            qs.append(_mk_question(
                "Sobre o QTc, qual afirmação é verdadeira?",
                f"QTc ≈ {qtc:.0f} ms; risco alto costuma ser > 480 ms (contexto clínico importa).",
                ["QTc ≤ 360 ms é sempre patológico.","QTc > 500 ms só ocorre em taquiarritmias ventriculares."],
                "Cortes comuns: 440–460 ms (limítrofes) e > 480–500 ms (alto risco), a depender do contexto."
            ))
    # Eixo
    ax = rep.get("axis_hex") or rep.get("axis")
    if ax:
        ang = ax.get("angle_deg"); lab = ax.get("label","")
        if ang is not None:
            qs.append(_mk_question(
                "Qual a melhor descrição do eixo elétrico frontal?",
                f"Eixo ≈ {ang:.0f}° — {lab}.",
                ["Eixo indeterminável por ECG de 12 derivações.","Eixo depende apenas de V1 e V6."],
                "O sistema hexaxial usa I, II, III, aVR, aVL e aVF."
            ))
    # Bloqueios
    bl = rep.get("conduction") or {}
    if bl:
        lab = bl.get("label","Sem bloqueio maior evidente")
        qrs_ms = bl.get("qrs_ms")
        qs.append(_mk_question(
            "Quanto à condução intraventricular, o laudo sugere:",
            lab + (f" (QRS {qrs_ms:.0f} ms)" if isinstance(qrs_ms,(int,float)) else ""),
            ["Bloqueio AV de 2º grau Mobitz II.","Wolf-Parkinson-White."],
            "Heurística com morfologia precordial e duração do QRS."
        ))
    # HVE
    hv = rep.get("hypertrophy_extended") or rep.get("hypertrophy") or {}
    if hv:
        sok = hv.get("sokolow_lyon_mm"); corn = hv.get("cornell_product_mm_ms") or hv.get("cornell_mV")
        qs.append(_mk_question(
            "Sobre hipertrofia ventricular esquerda (HVE):",
            f"Sokolow-Lyon ≈ {sok:.1f} mm e Cornell product ≈ {corn} (ver thresholds).",
            ["Critérios de HVE não podem ser estimados a partir do ECG.","Cornell product usa apenas V5/V6."],
            "Sokolow: S(V1)+max(R(V5,V6)); Cornell product: (RaVL+SV3)×QRSd (mm·ms)."
        ))
    # Limitar e ordenar
    return {"questions": qs[:n_max]}

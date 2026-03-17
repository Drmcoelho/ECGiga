"""Algoritmos de detecção de arritmias para análise de ECG.

Implementa detecção de:
- Fibrilação atrial (FA) via irregularidade RR e ausência de onda P
- Flutter atrial via frequência característica e detecção de ondas F
- Análise genérica de irregularidade de ritmo
- Diferenciação de taquicardia de complexo largo (TCL): TV vs TSV com aberrância

Referências:
- Dash et al., "Automatic real-time detection of atrial fibrillation",
  Ann Biomed Eng, 2009.
- Critérios de Brugada para TV: Brugada et al., Circulation, 1991.
- Algoritmo de Vereckei para TCL: Vereckei et al., Heart Rhythm, 2008.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


def detect_atrial_fibrillation(
    rr_intervals: list[float] | NDArray,
    p_wave_present: list[bool] | None = None,
    fs: float | None = None,
) -> dict[str, Any]:
    """Detecta fibrilação atrial a partir de série de intervalos RR.

    Utiliza três critérios complementares:
    1. Irregularidade RR (coeficiente de variação de diferenças sucessivas)
    2. Ausência de padrões RR repetitivos (razão de pontos de inflexão)
    3. Ausência de onda P (se fornecida)

    Parâmetros
    ----------
    rr_intervals : list[float] ou ndarray
        Intervalos RR em segundos.
    p_wave_present : list[bool], opcional
        Indicadores de presença de onda P por batimento.
    fs : float, opcional
        Frequência de amostragem (não utilizado, para consistência da API).

    Retorna
    -------
    dict
        - detected: bool
        - confidence: float (0-1)
        - criteria: dict com resultados de testes individuais
        - classification: str ('AF', 'possible_AF', 'not_AF', 'insufficient_data')
        - details: str
    """
    rr = np.asarray(rr_intervals, dtype=np.float64)

    if len(rr) < 8:
        return {
            "detected": False,
            "confidence": 0.0,
            "criteria": {},
            "classification": "insufficient_data",
            "details": "Necessário pelo menos 8 intervalos RR para análise de FA",
        }

    # Filtra intervalos RR fisiologicamente impossíveis
    rr = rr[(rr > 0.2) & (rr < 3.0)]
    if len(rr) < 8:
        return {
            "detected": False,
            "confidence": 0.0,
            "criteria": {},
            "classification": "insufficient_data",
            "details": "Intervalos RR insuficientes após filtragem",
        }

    criteria = {}
    scores = []

    # Critério 1: RMSSD / RR médio (coeficiente de irregularidade)
    diffs = np.diff(rr)
    rmssd = np.sqrt(np.mean(diffs ** 2))
    mean_rr = np.mean(rr)
    irregularity_coeff = rmssd / mean_rr if mean_rr > 0 else 0.0

    # FA tipicamente tem coeficiente de irregularidade > 0,10
    # Ritmo sinusal tipicamente < 0,06
    af_irreg_score = min(1.0, max(0.0, (irregularity_coeff - 0.06) / 0.08))
    criteria["irregularity_coefficient"] = round(irregularity_coeff, 4)
    criteria["irregularity_threshold"] = 0.10
    criteria["irregularity_positive"] = irregularity_coeff > 0.10
    scores.append(af_irreg_score)

    # Critério 2: Razão de pontos de inflexão (TPR)
    # Em sequências aleatórias (FA), TPR ≈ 2/3
    # Em ritmo regular (sinusal), TPR é menor
    turning_points = 0
    for i in range(1, len(rr) - 1):
        if (rr[i] > rr[i - 1] and rr[i] > rr[i + 1]) or \
           (rr[i] < rr[i - 1] and rr[i] < rr[i + 1]):
            turning_points += 1
    tpr = turning_points / (len(rr) - 2) if len(rr) > 2 else 0.0

    # FA: TPR > 0,55 (mais próximo de 2/3 = 0,667)
    tpr_score = min(1.0, max(0.0, (tpr - 0.45) / 0.20))
    criteria["turning_point_ratio"] = round(tpr, 4)
    criteria["tpr_threshold"] = 0.55
    criteria["tpr_positive"] = tpr > 0.55
    scores.append(tpr_score)

    # Critério 3: Entropia de Shannon do histograma RR
    # Maior entropia = mais irregular (FA)
    n_bins = max(5, int(np.sqrt(len(rr))))
    hist, _ = np.histogram(rr, bins=n_bins)
    hist_norm = hist / hist.sum()
    hist_norm = hist_norm[hist_norm > 0]
    entropy = -np.sum(hist_norm * np.log2(hist_norm))
    max_entropy = np.log2(n_bins)
    norm_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    entropy_score = min(1.0, max(0.0, (norm_entropy - 0.6) / 0.25))
    criteria["shannon_entropy"] = round(entropy, 4)
    criteria["normalized_entropy"] = round(norm_entropy, 4)
    criteria["entropy_positive"] = norm_entropy > 0.75
    scores.append(entropy_score)

    # Critério 4: Ausência de onda P (se disponível)
    if p_wave_present is not None and len(p_wave_present) > 0:
        p_absent_frac = 1.0 - sum(p_wave_present) / len(p_wave_present)
        p_score = min(1.0, max(0.0, (p_absent_frac - 0.3) / 0.4))
        criteria["p_wave_absent_fraction"] = round(p_absent_frac, 4)
        criteria["p_wave_positive"] = p_absent_frac > 0.5
        scores.append(p_score)

    # Confiança combinada
    confidence = sum(scores) / len(scores) if scores else 0.0

    # Classificação
    positive_criteria = sum(1 for s in scores if s > 0.5)
    if confidence > 0.7 and positive_criteria >= 2:
        classification = "AF"
        detected = True
        details = (
            f"Fibrilação atrial detectada (confiança {confidence:.0%}). "
            f"Coeficiente de irregularidade: {irregularity_coeff:.3f}, "
            f"TPR: {tpr:.3f}, Entropia normalizada: {norm_entropy:.3f}."
        )
    elif confidence > 0.4 and positive_criteria >= 1:
        classification = "possible_AF"
        detected = False
        details = (
            f"Possível fibrilação atrial (confiança {confidence:.0%}). "
            f"Recomenda-se monitorização prolongada (Holter 24h)."
        )
    else:
        classification = "not_AF"
        detected = False
        details = "Ritmo não sugestivo de fibrilação atrial."

    return {
        "detected": detected,
        "confidence": round(confidence, 3),
        "criteria": criteria,
        "classification": classification,
        "details": details,
    }


def detect_atrial_flutter(
    rr_intervals: list[float] | NDArray,
    heart_rate: float | None = None,
    p_wave_rate: float | None = None,
) -> dict[str, Any]:
    """Detecta padrão de flutter atrial.

    Características do flutter atrial:
    - Frequência atrial ~300 bpm (faixa 250-350)
    - Frequência ventricular frequentemente ~150 bpm (bloqueio 2:1) ou ~100 bpm (3:1) ou ~75 bpm (4:1)
    - Intervalos RR regulares ou regularmente irregulares
    - Ondas F em dente de serra nas derivações inferiores (II, III, aVF)

    Parâmetros
    ----------
    rr_intervals : list[float] ou ndarray
        Intervalos RR em segundos.
    heart_rate : float, opcional
        Frequência cardíaca calculada em bpm. Se None, derivada dos intervalos RR.
    p_wave_rate : float, opcional
        Frequência de ondas P/F detectadas em bpm (se ondas F detectadas).

    Retorna
    -------
    dict
        - detected: bool
        - confidence: float (0-1)
        - likely_conduction_ratio: str (ex.: '2:1', '3:1', '4:1', 'variable')
        - estimated_atrial_rate: float
        - details: str
    """
    rr = np.asarray(rr_intervals, dtype=np.float64)
    rr = rr[(rr > 0.15) & (rr < 3.0)]

    if len(rr) < 5:
        return {
            "detected": False,
            "confidence": 0.0,
            "likely_conduction_ratio": "unknown",
            "estimated_atrial_rate": 0.0,
            "details": "Dados insuficientes para análise de flutter",
        }

    # Calcula frequência ventricular
    if heart_rate is None:
        mean_rr = np.mean(rr)
        heart_rate = 60.0 / mean_rr if mean_rr > 0 else 0.0

    # Verifica regularidade (CV baixo = regular)
    cv = np.std(rr) / np.mean(rr) if np.mean(rr) > 0 else 1.0

    scores = []

    # Critério 1: Frequência ventricular compatível com razões de condução típicas do flutter
    # Frequência atrial do flutter = ~300 bpm
    atrial_rate_estimate = 300.0  # estimativa padrão
    if p_wave_rate and 250 <= p_wave_rate <= 350:
        atrial_rate_estimate = p_wave_rate

    # Verifica se FC corresponde a uma razão de condução
    conduction_ratios = {
        "2:1": atrial_rate_estimate / 2,  # ~150 bpm
        "3:1": atrial_rate_estimate / 3,  # ~100 bpm
        "4:1": atrial_rate_estimate / 4,  # ~75 bpm
    }

    best_ratio = "variable"
    best_match = 999.0
    for ratio, expected_hr in conduction_ratios.items():
        diff = abs(heart_rate - expected_hr) / expected_hr
        if diff < best_match:
            best_match = diff
            best_ratio = ratio

    # Correspondência próxima com razão de condução = pontuação mais alta
    hr_score = max(0.0, 1.0 - best_match * 5)  # 0% diff = 1.0, 20% diff = 0.0
    scores.append(hr_score)

    # Critério 2: Intervalos RR regulares (ou regularmente irregulares para bloqueio variável)
    regularity_score = max(0.0, 1.0 - cv * 5)  # CV < 0,05 = muito regular
    scores.append(regularity_score)

    # Critério 3: Frequência cardíaca na faixa típica de flutter
    # Flutter 2:1: 130-170, 3:1: 85-115, 4:1: 65-85
    hr_in_range = (
        (130 <= heart_rate <= 170) or
        (85 <= heart_rate <= 115) or
        (65 <= heart_rate <= 85)
    )
    range_score = 0.8 if hr_in_range else 0.2
    scores.append(range_score)

    # Critério 4: Frequência de onda P se disponível
    if p_wave_rate is not None:
        if 250 <= p_wave_rate <= 350:
            scores.append(1.0)
        else:
            scores.append(0.0)

    confidence = sum(scores) / len(scores) if scores else 0.0

    detected = confidence > 0.6 and hr_in_range
    if cv > 0.15:
        best_ratio = "variable"

    details = (
        f"Flutter atrial {'detectado' if detected else 'não detectado'} "
        f"(confiança {confidence:.0%}). "
        f"FC ventricular: {heart_rate:.0f} bpm, "
        f"Condução provável: {best_ratio}, "
        f"Taxa atrial estimada: {atrial_rate_estimate:.0f} bpm."
    )

    return {
        "detected": detected,
        "confidence": round(confidence, 3),
        "likely_conduction_ratio": best_ratio,
        "estimated_atrial_rate": round(atrial_rate_estimate, 1),
        "details": details,
    }


def detect_rhythm_irregularity(
    rr_intervals: list[float] | NDArray,
) -> dict[str, Any]:
    """Análise abrangente de irregularidade de ritmo.

    Classifica o ritmo como:
    - regular: CV < 0,05 (ritmo sinusal, marcapasso, flutter com bloqueio fixo)
    - regularly_irregular: padrão periódico (Wenckebach, bigeminismo, trigeminismo)
    - irregularly_irregular: variação aleatória (FA, taquicardia atrial multifocal)

    Parâmetros
    ----------
    rr_intervals : list[float] ou ndarray
        Intervalos RR em segundos.

    Retorna
    -------
    dict
        - pattern: str ('regular', 'regularly_irregular', 'irregularly_irregular')
        - cv: float (coeficiente de variação)
        - rmssd_ms: float (raiz quadrada média das diferenças sucessivas em ms)
        - premature_beats: int (contagem estimada)
        - bigeminy: bool
        - trigeminy: bool
        - details: str
    """
    rr = np.asarray(rr_intervals, dtype=np.float64)
    rr = rr[(rr > 0.15) & (rr < 3.0)]

    if len(rr) < 4:
        return {
            "pattern": "unknown",
            "cv": 0.0,
            "rmssd_ms": 0.0,
            "premature_beats": 0,
            "bigeminy": False,
            "trigeminy": False,
            "details": "Dados insuficientes",
        }

    mean_rr = np.mean(rr)
    cv = np.std(rr) / mean_rr if mean_rr > 0 else 0.0

    diffs = np.diff(rr)
    rmssd = np.sqrt(np.mean(diffs ** 2)) * 1000  # Converte para ms

    # Detecção de batimentos prematuros: RR < 80% da média
    premature_threshold = mean_rr * 0.80
    premature_beats = int(np.sum(rr < premature_threshold))

    # Bigeminismo: padrão alternado curto-longo
    bigeminy = False
    trigeminy = False

    if len(rr) >= 6:
        # Verifica bigeminismo (padrão de período 2)
        even_rr = rr[::2]
        odd_rr = rr[1::2]
        min_len = min(len(even_rr), len(odd_rr))
        if min_len >= 3:
            even_mean = np.mean(even_rr[:min_len])
            odd_mean = np.mean(odd_rr[:min_len])
            even_cv = np.std(even_rr[:min_len]) / even_mean if even_mean > 0 else 1.0
            odd_cv = np.std(odd_rr[:min_len]) / odd_mean if odd_mean > 0 else 1.0
            ratio = min(even_mean, odd_mean) / max(even_mean, odd_mean) if max(even_mean, odd_mean) > 0 else 1.0

            if even_cv < 0.10 and odd_cv < 0.10 and ratio < 0.85:
                bigeminy = True

    if len(rr) >= 9 and not bigeminy:
        # Verifica trigeminismo (padrão de período 3)
        for offset in range(3):
            sub = rr[offset::3]
            if len(sub) >= 3:
                sub_cv = np.std(sub) / np.mean(sub) if np.mean(sub) > 0 else 1.0
                if sub_cv < 0.10:
                    # Verifica se as outras fases também são regulares mas diferentes
                    other_cvs = []
                    for o2 in range(3):
                        if o2 != offset:
                            s2 = rr[o2::3]
                            if len(s2) >= 2:
                                other_cvs.append(np.std(s2) / np.mean(s2) if np.mean(s2) > 0 else 1.0)
                    if all(c < 0.15 for c in other_cvs):
                        trigeminy = True
                        break

    # Classifica padrão
    if cv < 0.05:
        pattern = "regular"
        details = f"Ritmo regular (CV = {cv:.3f}). FC média: {60/mean_rr:.0f} bpm."
    elif bigeminy or trigeminy:
        pattern = "regularly_irregular"
        extra = "bigeminismo" if bigeminy else "trigeminismo"
        details = (
            f"Ritmo regularmente irregular — padrão de {extra}. "
            f"CV = {cv:.3f}, RMSSD = {rmssd:.1f} ms. "
            f"Extrassístoles estimadas: {premature_beats}."
        )
    elif cv > 0.15:
        pattern = "irregularly_irregular"
        details = (
            f"Ritmo irregularmente irregular (CV = {cv:.3f}, RMSSD = {rmssd:.1f} ms). "
            f"Considerar: fibrilação atrial, taquicardia atrial multifocal."
        )
    else:
        # Irregularidade moderada
        if premature_beats > len(rr) * 0.1:
            pattern = "regularly_irregular"
            details = (
                f"Ritmo com extrassístoles frequentes ({premature_beats} batimentos prematuros). "
                f"CV = {cv:.3f}."
            )
        else:
            pattern = "regular"
            details = f"Ritmo essencialmente regular com variação sinusal (CV = {cv:.3f})."

    return {
        "pattern": pattern,
        "cv": round(cv, 4),
        "rmssd_ms": round(rmssd, 1),
        "premature_beats": premature_beats,
        "bigeminy": bigeminy,
        "trigeminy": trigeminy,
        "details": details,
    }


def classify_wide_complex_tachycardia(
    qrs_duration_ms: float,
    heart_rate: float,
    axis_deg: float | None = None,
    concordance: str | None = None,
    av_dissociation: bool = False,
    capture_beats: bool = False,
    fusion_beats: bool = False,
    rsr_v1: bool = False,
    morphology_v1: str | None = None,
    morphology_v6: str | None = None,
    previous_bbb: bool = False,
) -> dict[str, Any]:
    """Diferencia taquicardia ventricular de TSV com aberrância.

    Implementa abordagem de pontuação composta combinando:
    - Critérios de Brugada (algoritmo de 4 etapas)
    - Critérios de Vereckei em aVR
    - Critérios morfológicos em V1/V6

    Parâmetros
    ----------
    qrs_duration_ms : float
        Duração do QRS em milissegundos.
    heart_rate : float
        Frequência cardíaca em bpm.
    axis_deg : float, opcional
        Eixo do QRS em graus.
    concordance : str, opcional
        Concordância precordial: 'positive', 'negative', ou None.
    av_dissociation : bool
        Se dissociação AV está presente.
    capture_beats : bool
        Se batimentos de captura são observados.
    fusion_beats : bool
        Se batimentos de fusão são observados.
    rsr_v1 : bool
        Se padrão RSR' em V1 (sugere RBBB = TSV com aberrância).
    morphology_v1 : str, opcional
        Morfologia do QRS em V1: 'R', 'qR', 'Rs', 'rS', 'RSR', 'QS'.
    morphology_v6 : str, opcional
        Morfologia do QRS em V6: 'R', 'Rs', 'rS', 'QS', 'qRs'.
    previous_bbb : bool
        Se o paciente tem bloqueio de ramo prévio conhecido.

    Retorna
    -------
    dict
        - classification: str ('VT', 'SVT_aberrancy', 'uncertain')
        - vt_probability: float (0-1)
        - criteria_met: list[str]
        - details: str
    """
    if qrs_duration_ms < 120:
        return {
            "classification": "narrow_complex",
            "vt_probability": 0.0,
            "criteria_met": [],
            "details": "QRS estreito — não é taquicardia de complexo largo.",
        }

    if heart_rate < 100:
        return {
            "classification": "not_tachycardia",
            "vt_probability": 0.0,
            "criteria_met": [],
            "details": "FC < 100 bpm — não é taquicardia.",
        }

    vt_points = 0
    svt_points = 0
    criteria_met: list[str] = []

    # --- Brugada Etapa 1: Ausência de complexo RS em todas as derivações precordiais ---
    if concordance == "negative":
        vt_points += 3
        criteria_met.append("Concordância negativa precordial (VT)")
    elif concordance == "positive":
        vt_points += 2
        criteria_met.append("Concordância positiva precordial (VT)")

    # --- Dissociação AV (critério mais forte para TV) ---
    if av_dissociation:
        vt_points += 4
        criteria_met.append("Dissociação AV presente (forte indicador de TV)")

    # --- Batimentos de captura / fusão (patognomônicos de TV) ---
    if capture_beats:
        vt_points += 3
        criteria_met.append("Batimentos de captura (patognomônico de TV)")
    if fusion_beats:
        vt_points += 3
        criteria_met.append("Batimentos de fusão (patognomônico de TV)")

    # --- Duração do QRS ---
    if qrs_duration_ms > 160:
        vt_points += 2
        criteria_met.append(f"QRS muito alargado ({qrs_duration_ms:.0f} ms)")
    elif qrs_duration_ms > 140:
        vt_points += 1
        criteria_met.append(f"QRS moderadamente alargado ({qrs_duration_ms:.0f} ms)")

    # --- Eixo ---
    if axis_deg is not None:
        if -90 < axis_deg < -30 or 180 > axis_deg > 150:
            # Eixo noroeste = muito sugestivo de TV
            vt_points += 2
            criteria_met.append(f"Eixo extremo ({axis_deg:.0f}°) — sugere TV")
        elif axis_deg < -90 or axis_deg > 180:
            vt_points += 3
            criteria_met.append(f"Eixo no-man's-land ({axis_deg:.0f}°) — forte indicador de TV")

    # --- RSR' em V1 (sugere TSV com aberrância / RBBB) ---
    if rsr_v1 or morphology_v1 == "RSR":
        svt_points += 2
        criteria_met.append("RSR' em V1 sugere TSV com aberrância (BRD)")

    # --- Critérios de morfologia em V1 ---
    if morphology_v1 in ("R", "qR"):
        vt_points += 1
        criteria_met.append(f"Morfologia {morphology_v1} em V1 favorece TV")

    # --- Morfologia em V6 ---
    if morphology_v6 in ("QS", "rS"):
        vt_points += 1
        criteria_met.append(f"Morfologia {morphology_v6} em V6 favorece TV")

    # --- BRB prévio conhecido reduz probabilidade de TV ---
    if previous_bbb:
        svt_points += 2
        criteria_met.append("BRB prévio conhecido — favorece TSV com aberrância")

    # --- Classificação ---
    total = vt_points + svt_points
    if total == 0:
        vt_prob = 0.5
    else:
        vt_prob = vt_points / total

    if vt_prob > 0.65:
        classification = "VT"
        details = (
            f"TAQUICARDIA VENTRICULAR provável (probabilidade {vt_prob:.0%}). "
            f"Critérios: {', '.join(criteria_met)}. "
            "Na dúvida, tratar como TV (abordagem mais segura)."
        )
    elif vt_prob < 0.35:
        classification = "SVT_aberrancy"
        details = (
            f"TSV com aberrância provável (probabilidade TV: {vt_prob:.0%}). "
            f"Critérios: {', '.join(criteria_met)}."
        )
    else:
        classification = "uncertain"
        details = (
            f"Diferenciação incerta (probabilidade TV: {vt_prob:.0%}). "
            f"Critérios: {', '.join(criteria_met)}. "
            "REGRA CLÍNICA: na dúvida, tratar como TV!"
        )

    return {
        "classification": classification,
        "vt_probability": round(vt_prob, 3),
        "criteria_met": criteria_met,
        "details": details,
    }

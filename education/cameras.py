"""
education/cameras.py — Módulo "Câmeras Cardíacas"

Conceito central: cada derivação do ECG é uma CÂMERA que filma o coração
de um ângulo específico.  Quando o vetor elétrico se aproxima do polo
positivo da derivação, a câmera registra deflexão positiva (imagem nítida).
Quando se afasta, deflexão negativa.  Quando perpendicular, registro
isoelétrico/bifásico (câmera não resolve).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Mnemônico CAFÉ
# ---------------------------------------------------------------------------

MNEMONIC_CAFE: Dict[str, str] = {
    "C": "Câmera = polo positivo da derivação",
    "A": "Aproximando = deflexão positiva (onda para cima)",
    "F": "Fugindo = deflexão negativa (onda para baixo)",
    "E": "Esquece quando perpendicular = registro bifásico / isoelétrico",
    "resumo": (
        "CAFÉ — Lembre: a Câmera é o polo positivo. "
        "Se o vetor se Aproxima, a deflexão é positiva. "
        "Se Foge, negativa. "
        "E se está perpendicular? Esquece — fica bifásico!"
    ),
}

# ---------------------------------------------------------------------------
# LEAD_CAMERAS — As 12 câmeras cardíacas
# ---------------------------------------------------------------------------

LEAD_CAMERAS: Dict[str, Dict[str, Any]] = {
    # === Derivações dos membros (plano frontal) ===
    "I": {
        "angle_deg": 0,
        "plane": "frontal",
        "description_pt": (
            "Derivação I: câmera posicionada no braço esquerdo (0°). "
            "Filma o coração da direita para a esquerda."
        ),
        "camera_analogy_pt": (
            "Imagine uma câmera no seu ombro esquerdo, apontando "
            "horizontalmente para o coração. Tudo que se move em "
            "direção ao braço esquerdo aparece 'positivo' na tela."
        ),
    },
    "II": {
        "angle_deg": 60,
        "plane": "frontal",
        "description_pt": (
            "Derivação II: câmera posicionada na perna esquerda (60°). "
            "Alinhada com o eixo normal do coração — por isso geralmente "
            "registra as maiores deflexões positivas."
        ),
        "camera_analogy_pt": (
            "Câmera na sua perna esquerda, olhando para cima e para a "
            "direita. Como o vetor cardíaco normal (~60°) aponta "
            "diretamente para ela, a imagem é a mais nítida e positiva."
        ),
    },
    "III": {
        "angle_deg": 120,
        "plane": "frontal",
        "description_pt": (
            "Derivação III: câmera posicionada a 120°, filmando a "
            "parede inferior do coração de um ângulo mais lateral."
        ),
        "camera_analogy_pt": (
            "Câmera na perna esquerda, mas com angulação diferente de "
            "DII. Quando o vetor se desvia para a direita, esta câmera "
            "capta melhor."
        ),
    },
    "aVR": {
        "angle_deg": -150,
        "plane": "frontal",
        "description_pt": (
            "Derivação aVR: câmera posicionada no braço direito (-150°). "
            "Olha o coração 'de costas' — por isso quase tudo é negativo."
        ),
        "camera_analogy_pt": (
            "A câmera rebelde! Está posicionada no ombro direito, "
            "olhando na direção oposta ao fluxo normal da "
            "despolarização. Resultado: quase tudo aparece invertido, "
            "como filmar pelo espelho retrovisor."
        ),
    },
    "aVL": {
        "angle_deg": -30,
        "plane": "frontal",
        "description_pt": (
            "Derivação aVL: câmera a -30°, filmando a parede lateral "
            "alta do ventrículo esquerdo."
        ),
        "camera_analogy_pt": (
            "Câmera no ombro esquerdo, apontada ligeiramente para "
            "baixo. Capta bem eventos da parede lateral alta. "
            "Quando o eixo é normal (~60°), o vetor faz ~90° com ela, "
            "então o QRS pode ser bifásico — a câmera 'não decide'."
        ),
    },
    "aVF": {
        "angle_deg": 90,
        "plane": "frontal",
        "description_pt": (
            "Derivação aVF: câmera a 90° (polo positivo no pé). "
            "Filma diretamente a parede inferior do coração."
        ),
        "camera_analogy_pt": (
            "Câmera embaixo do coração, olhando para cima. "
            "Qualquer vetor que desce aparece positivo. "
            "É a câmera principal da parede inferior."
        ),
    },
    # === Derivações precordiais (plano horizontal) ===
    "V1": {
        "angle_deg": 0,
        "plane": "horizontal",
        "description_pt": (
            "V1: câmera no 4º espaço intercostal, borda esternal "
            "direita. Vê o septo e o ventrículo direito de perto."
        ),
        "camera_analogy_pt": (
            "Câmera colada no peito à direita do esterno. "
            "O septo se despolariza em sua direção (r pequeno), "
            "mas depois a grande massa do VE se afasta (S profundo). "
            "Padrão normal: rS."
        ),
    },
    "V2": {
        "angle_deg": 15,
        "plane": "horizontal",
        "description_pt": (
            "V2: câmera no 4º espaço intercostal, borda esternal "
            "esquerda. Transição entre VD e VE."
        ),
        "camera_analogy_pt": (
            "Câmera um pouco mais à esquerda que V1. "
            "Ainda vê bastante do septo, mas começa a captar "
            "mais do VE. Padrão normal: rS (R pode ser um pouco maior)."
        ),
    },
    "V3": {
        "angle_deg": 45,
        "plane": "horizontal",
        "description_pt": (
            "V3: câmera na zona de transição — entre V2 e V4. "
            "Aqui o R e o S costumam ter amplitude semelhante."
        ),
        "camera_analogy_pt": (
            "A câmera da transição! Está no ponto em que o vetor "
            "começa a 'se virar' na direção da câmera. "
            "R ≈ S — é a zona de transição elétrica."
        ),
    },
    "V4": {
        "angle_deg": 70,
        "plane": "horizontal",
        "description_pt": (
            "V4: câmera no ápice do coração, 5º espaço intercostal "
            "na linha hemiclavicular esquerda."
        ),
        "camera_analogy_pt": (
            "Câmera no ápice! Aqui o vetor principal já aponta "
            "na sua direção. O R começa a dominar sobre o S. "
            "É a câmera que melhor registra a atividade apical."
        ),
    },
    "V5": {
        "angle_deg": 90,
        "plane": "horizontal",
        "description_pt": (
            "V5: câmera na linha axilar anterior, filmando a "
            "parede lateral do ventrículo esquerdo."
        ),
        "camera_analogy_pt": (
            "Câmera na lateral do tórax. O vetor de despolarização "
            "do VE se dirige em sua direção — R alto com s pequeno. "
            "Boa câmera para ver a parede lateral."
        ),
    },
    "V6": {
        "angle_deg": 110,
        "plane": "horizontal",
        "description_pt": (
            "V6: câmera na linha axilar média, a mais lateral "
            "das precordiais. Filma a parede lateral do VE."
        ),
        "camera_analogy_pt": (
            "A câmera mais lateral de todas! Vê o VE de lado. "
            "R dominante com s pequeno ou ausente. "
            "Se o R aqui é muito alto, pode indicar HVE."
        ),
    },
}

# ---------------------------------------------------------------------------
# Constantes auxiliares
# ---------------------------------------------------------------------------

_FRONTAL_LEADS = ["I", "II", "III", "aVR", "aVL", "aVF"]
_HORIZONTAL_LEADS = ["V1", "V2", "V3", "V4", "V5", "V6"]
_ALL_LEADS = _FRONTAL_LEADS + _HORIZONTAL_LEADS


def _normalize_angle(deg: float) -> float:
    """Normaliza ângulo para o intervalo (-180, 180]."""
    deg = deg % 360
    if deg > 180:
        deg -= 360
    return deg


def _angle_difference(a: float, b: float) -> float:
    """Retorna a diferença angular absoluta em graus (0-180)."""
    diff = abs(_normalize_angle(a) - _normalize_angle(b))
    if diff > 180:
        diff = 360 - diff
    return diff


# ---------------------------------------------------------------------------
# explain_lead
# ---------------------------------------------------------------------------

def explain_lead(lead_name: str) -> Dict[str, Any]:
    """
    Retorna explicação educacional completa de uma derivação usando
    a analogia de câmeras.

    Parameters
    ----------
    lead_name : str
        Nome da derivação (e.g. "II", "V1", "aVR").

    Returns
    -------
    dict com chaves:
        lead, angle_deg, plane, description_pt, camera_analogy_pt,
        mnemonic_cafe, clinical_tip_pt
    """
    key = lead_name.strip()
    if key not in LEAD_CAMERAS:
        raise ValueError(
            f"Derivação '{key}' não encontrada. "
            f"Derivações válidas: {', '.join(_ALL_LEADS)}"
        )
    info = LEAD_CAMERAS[key]

    # Dica clínica contextual
    clinical_tips: Dict[str, str] = {
        "I": "DI é referência para o eixo: se QRS positivo → vetor aponta para a esquerda.",
        "II": "DII costuma ter o maior QRS positivo — é a derivação de monitorização padrão.",
        "III": "DIII complementa DII para avaliar a parede inferior.",
        "aVR": "aVR normalmente é toda negativa. Se positiva, pense em dextrocardia ou troca de eletrodos!",
        "aVL": "aVL vê a parede lateral alta. Supra de ST aqui sugere oclusão de ramo diagonal.",
        "aVF": "aVF é a câmera inferior. Supra de ST aqui = IAM inferior (coronária direita ou circunflexa).",
        "V1": "V1 é a janela do VD e do septo. R' aqui = BRD. R alto = HVD ou IAM posterior.",
        "V2": "V2 junto com V1 ajuda a detectar BRD e Brugada.",
        "V3": "V3 é a zona de transição. Se R > S aqui, transição precoce.",
        "V4": "V4 no ápice. Supra de ST aqui com DII/DIII/aVF = IAM extenso.",
        "V5": "V5 avalia parede lateral. R alto pode indicar HVE.",
        "V6": "V6 é a câmera mais lateral. qRs normal; R alto = HVE (critério de Sokolow: SV1 + RV5/V6 ≥ 35mm).",
    }

    return {
        "lead": key,
        "angle_deg": info["angle_deg"],
        "plane": info["plane"],
        "description_pt": info["description_pt"],
        "camera_analogy_pt": info["camera_analogy_pt"],
        "mnemonic_cafe": MNEMONIC_CAFE["resumo"],
        "clinical_tip_pt": clinical_tips.get(key, ""),
    }


# ---------------------------------------------------------------------------
# explain_deflection
# ---------------------------------------------------------------------------

def explain_deflection(lead_name: str, vector_direction_deg: float) -> Dict[str, Any]:
    """
    Explica por que uma onda é positiva, negativa ou bifásica em
    determinada derivação, dado o ângulo do vetor elétrico.

    Parameters
    ----------
    lead_name : str
    vector_direction_deg : float  — ângulo do vetor no plano (em graus)

    Returns
    -------
    dict com: lead, lead_angle_deg, vector_deg, angle_diff,
              deflection ("positiva" | "negativa" | "bifásica"),
              explanation_pt
    """
    key = lead_name.strip()
    if key not in LEAD_CAMERAS:
        raise ValueError(f"Derivação '{key}' não encontrada.")

    lead_angle = LEAD_CAMERAS[key]["angle_deg"]
    diff = _angle_difference(lead_angle, vector_direction_deg)

    if diff <= 80:
        deflection = "positiva"
        explanation = (
            f"O vetor elétrico ({vector_direction_deg}°) está se APROXIMANDO "
            f"da câmera {key} ({lead_angle}°). "
            f"Diferença angular: {diff:.0f}° (< 90°). "
            "Pela regra do CAFÉ: Aproximando → deflexão positiva. "
            "A câmera vê o vetor vindo em sua direção — imagem nítida, "
            "onda para cima."
        )
    elif diff >= 100:
        deflection = "negativa"
        explanation = (
            f"O vetor elétrico ({vector_direction_deg}°) está FUGINDO "
            f"da câmera {key} ({lead_angle}°). "
            f"Diferença angular: {diff:.0f}° (> 90°). "
            "Pela regra do CAFÉ: Fugindo → deflexão negativa. "
            "A câmera vê o vetor se afastando — imagem desfocada, "
            "onda para baixo."
        )
    else:
        deflection = "bifásica"
        explanation = (
            f"O vetor elétrico ({vector_direction_deg}°) está praticamente "
            f"PERPENDICULAR à câmera {key} ({lead_angle}°). "
            f"Diferença angular: {diff:.0f}° (≈ 90°). "
            "Pela regra do CAFÉ: Esquece quando perpendicular → bifásico. "
            "A câmera não consegue resolver — o vetor cruza seu campo "
            "de visão sem se aproximar nem se afastar de verdade."
        )

    return {
        "lead": key,
        "lead_angle_deg": lead_angle,
        "vector_deg": vector_direction_deg,
        "angle_diff": diff,
        "deflection": deflection,
        "explanation_pt": explanation,
    }


# ---------------------------------------------------------------------------
# explain_axis
# ---------------------------------------------------------------------------

def explain_axis(angle_deg: float) -> Dict[str, Any]:
    """
    Explica o eixo cardíaco usando a analogia de câmeras.

    Parameters
    ----------
    angle_deg : float — eixo cardíaco em graus

    Returns
    -------
    dict com: axis_deg, classification, best_cameras, worst_cameras,
              perpendicular_cameras, explanation_pt
    """
    angle = _normalize_angle(angle_deg)

    # Classificação do eixo
    if -30 <= angle <= 90:
        classification = "normal"
        class_text = "Eixo normal (-30° a +90°)"
    elif -90 <= angle < -30:
        classification = "desvio_esquerda"
        class_text = "Desvio do eixo para a esquerda (-90° a -30°)"
    elif 90 < angle <= 180:
        classification = "desvio_direita"
        class_text = "Desvio do eixo para a direita (+90° a +180°)"
    else:
        classification = "desvio_extremo"
        class_text = "Desvio extremo do eixo (-90° a -180° / +180°)"

    # Classificar cada câmera frontal
    best: List[str] = []
    worst: List[str] = []
    perpendicular: List[str] = []
    for lead in _FRONTAL_LEADS:
        diff = _angle_difference(LEAD_CAMERAS[lead]["angle_deg"], angle)
        if diff <= 30:
            best.append(lead)
        elif diff >= 150:
            worst.append(lead)
        elif 80 <= diff <= 100:
            perpendicular.append(lead)

    explanation = (
        f"Com eixo em {angle:.0f}° ({class_text}):\n"
        f"• Câmeras com melhor visão (vetor vem direto): {', '.join(best) if best else 'nenhuma alinhada perfeitamente'}\n"
        f"• Câmeras cegas (vetor foge): {', '.join(worst) if worst else 'nenhuma totalmente oposta'}\n"
        f"• Câmeras perpendiculares (bifásico): {', '.join(perpendicular) if perpendicular else 'nenhuma exatamente perpendicular'}\n\n"
        "Dica: a derivação com maior R positivo é a câmera mais alinhada "
        "com o eixo. A derivação com QRS bifásico é perpendicular ao eixo."
    )

    return {
        "axis_deg": angle,
        "classification": classification,
        "classification_text": class_text,
        "best_cameras": best,
        "worst_cameras": worst,
        "perpendicular_cameras": perpendicular,
        "explanation_pt": explanation,
    }


# ---------------------------------------------------------------------------
# get_camera_story
# ---------------------------------------------------------------------------

def get_camera_story(report: Dict[str, Any]) -> str:
    """
    Gera narrativa educacional completa de um laudo ECG usando a
    analogia de câmeras cardíacas.

    Parameters
    ----------
    report : dict
        Dicionário com campos opcionais:
        - axis_deg (float)
        - rhythm (str)
        - rate_bpm (int)
        - findings (list[str])
        - st_changes (dict[str, str])  — e.g. {"II": "supra", "V1": "infra"}
        - intervals (dict)

    Returns
    -------
    str — texto narrativo em português
    """
    parts: List[str] = []

    parts.append("=" * 60)
    parts.append("🎬 RELATÓRIO ECG — VISÃO PELAS CÂMERAS CARDÍACAS")
    parts.append("=" * 60)
    parts.append("")

    # --- Ritmo e FC ---
    rhythm = report.get("rhythm", "sinusal")
    rate = report.get("rate_bpm")
    if rate:
        parts.append(f"RITMO: {rhythm} | FC: {rate} bpm")
        if rhythm.lower() == "sinusal":
            parts.append(
                "  → A câmera DII (que tem a melhor visão do nó sinusal) "
                "registra ondas P positivas antes de cada QRS. "
                "O 'diretor' (nó sinusal) está no comando."
            )
    parts.append("")

    # --- Eixo ---
    axis = report.get("axis_deg")
    if axis is not None:
        axis_info = explain_axis(axis)
        parts.append(f"EIXO CARDÍACO: {axis:.0f}° — {axis_info['classification_text']}")
        if axis_info["best_cameras"]:
            parts.append(
                f"  → As câmeras {', '.join(axis_info['best_cameras'])} têm a "
                "melhor visão: o vetor vem direto na direção delas."
            )
        if axis_info["perpendicular_cameras"]:
            parts.append(
                f"  → As câmeras {', '.join(axis_info['perpendicular_cameras'])} "
                "estão perpendiculares: registram QRS bifásico."
            )
        parts.append("")

    # --- Alterações de ST ---
    st_changes = report.get("st_changes", {})
    if st_changes:
        parts.append("ALTERAÇÕES DE ST (lesão/isquemia):")
        for lead, change in st_changes.items():
            lead_info = LEAD_CAMERAS.get(lead, {})
            if change.lower() == "supra":
                parts.append(
                    f"  → Câmera {lead}: SUPRADESNIVELAMENTO de ST. "
                    f"Esta câmera está vendo lesão diretamente! "
                    f"({lead_info.get('description_pt', '')})"
                )
            elif change.lower() == "infra":
                parts.append(
                    f"  → Câmera {lead}: infradesnivelamento de ST. "
                    "Pode ser imagem recíproca (espelho) de uma lesão "
                    "vista por câmeras do lado oposto, ou isquemia subendocárdica."
                )
        parts.append("")

    # --- Achados gerais ---
    findings = report.get("findings", [])
    if findings:
        parts.append("ACHADOS:")
        for f in findings:
            parts.append(f"  • {f}")
        parts.append("")

    # --- Intervalos ---
    intervals = report.get("intervals", {})
    if intervals:
        parts.append("INTERVALOS:")
        pr = intervals.get("PR_ms")
        if pr:
            parts.append(
                f"  PR: {pr} ms"
                + (" (prolongado → o sinal demora a passar do átrio para o ventrículo)"
                   if pr > 200 else " (normal)")
            )
        qrs = intervals.get("QRS_ms")
        if qrs:
            parts.append(
                f"  QRS: {qrs} ms"
                + (" (alargado → condução lenta nos ventrículos, possível bloqueio de ramo)"
                   if qrs > 120 else " (normal)")
            )
        qt = intervals.get("QTc_ms")
        if qt:
            parts.append(
                f"  QTc: {qt} ms"
                + (" (prolongado → risco de arritmias)" if qt > 460 else " (normal)")
            )
        parts.append("")

    # --- Rodapé CAFÉ ---
    parts.append("-" * 60)
    parts.append("LEMBRE DO MNEMÔNICO CAFÉ:")
    parts.append(MNEMONIC_CAFE["resumo"])
    parts.append("-" * 60)

    return "\n".join(parts)

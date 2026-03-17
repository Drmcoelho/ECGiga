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
# Territory mapping constants
# ---------------------------------------------------------------------------

TERRITORY_LEADS: Dict[str, List[str]] = {
    "inferior": ["II", "III", "aVF"],
    "anterior": ["V1", "V2", "V3", "V4"],
    "lateral": ["I", "aVL", "V5", "V6"],
    "septal": ["V1", "V2"],
    "lateral_alto": ["I", "aVL"],
    "posterior": [],  # reciprocal in V1-V3
}

RECIPROCAL_MAP: Dict[str, List[str]] = {
    "inferior": ["I", "aVL"],
    "anterior": ["II", "III", "aVF"],
    "lateral": ["III", "aVF"],
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

    # Dica clínica contextual — expanded to 3-4 sentences each
    clinical_tips: Dict[str, str] = {
        "I": (
            "DI é referência para o eixo: se QRS positivo → vetor aponta para a esquerda. "
            "Anatomicamente, DI filma a parede lateral alta do ventrículo esquerdo, "
            "território da artéria descendente anterior (ramo diagonal) e da circunflexa. "
            "Procure inversão de onda T ou infradesnivelamento de ST como sinais de isquemia lateral. "
            "Cuidado: em dextrocardia ou troca de eletrodos, DI pode apresentar complexos invertidos — "
            "sempre confira se a onda P é positiva em DI antes de interpretar o eixo."
        ),
        "II": (
            "DII costuma ter o maior QRS positivo — é a derivação de monitorização padrão. "
            "Vê a parede inferior do coração, território da artéria coronária direita (ACD) "
            "ou circunflexa dominante. Supradesnivelamento de ST em DII, junto com DIII e aVF, "
            "configura padrão de IAMCSST inferior — uma emergência médica. "
            "Cuidado: DII é a melhor derivação para avaliar a onda P e ritmo, mas pode "
            "apresentar artefatos de movimento por estar alinhada com a linha muscular da perna."
        ),
        "III": (
            "DIII complementa DII para avaliar a parede inferior do coração. "
            "Junto com DII e aVF, forma o trio de câmeras inferiores — território da ACD. "
            "Supra de ST em DIII maior que em DII sugere oclusão da ACD (vs. circunflexa). "
            "Cuidado: DIII é a derivação mais variável com a respiração; ondas Q isoladas "
            "em DIII podem ser normais e desaparecem com a inspiração profunda."
        ),
        "aVR": (
            "aVR normalmente é toda negativa. Se positiva, pense em dextrocardia ou troca de eletrodos! "
            "Anatomicamente, aVR olha para a base do coração e o septo basal, refletindo a cavidade "
            "do ventrículo esquerdo. Supra de ST em aVR com infra difuso sugere oclusão de tronco da "
            "coronária esquerda ou doença triarterial — situação de altíssimo risco. "
            "Cuidado: não ignore aVR; é a derivação mais subestimada, mas pode ser a mais importante "
            "em contextos de isquemia grave."
        ),
        "aVL": (
            "aVL vê a parede lateral alta. Supra de ST aqui sugere oclusão de ramo diagonal. "
            "É a câmera da parede lateral alta do ventrículo esquerdo, território do ramo diagonal "
            "da descendente anterior ou da circunflexa marginal. Supra de ST em aVL com reciprocidade "
            "em DIII e aVF indica IAM lateral alto. "
            "Cuidado: com eixo normal (~60°), aVL pode ter QRS bifásico — isso é normal e não deve "
            "ser confundido com patologia."
        ),
        "aVF": (
            "aVF é a câmera inferior. Supra de ST aqui = IAM inferior (coronária direita ou circunflexa). "
            "Filma diretamente a parede inferior, sendo a derivação principal para detectar IAM inferior. "
            "Combinada com DII e DIII, forma o tripé diagnóstico para isquemia do território da ACD. "
            "Cuidado: ondas Q patológicas em aVF podem indicar infarto inferior antigo; sempre compare "
            "com ECGs prévios quando disponíveis."
        ),
        "V1": (
            "V1 é a janela do VD e do septo. R' aqui = BRD. R alto = HVD ou IAM posterior. "
            "Anatomicamente, V1 vê o ventrículo direito e o septo interventricular de muito perto, "
            "sendo essencial para detectar bloqueio de ramo direito (rsR'), padrão de Brugada e "
            "sinais de hipertrofia ventricular direita. Infra de ST com R alto em V1-V3 pode ser "
            "imagem especular de IAM posterior — solicite derivações posteriores (V7-V9). "
            "Cuidado: a posição do eletrodo V1 é crítica; um espaço intercostal acima ou abaixo "
            "pode mimetizar ou mascarar padrões patológicos como Brugada."
        ),
        "V2": (
            "V2 junto com V1 ajuda a detectar BRD e Brugada. "
            "Vê a transição entre ventrículo direito e septo, sendo sensível para padrões de "
            "repolarização precoce e elevação do ponto J. Supra de ST côncavo em V2 com "
            "morfologia em 'sela' ou 'tenda' deve levantar suspeita de síndrome de Brugada. "
            "Cuidado: em mulheres, os critérios de supra de ST para IAMCSST anterior são "
            "diferentes (≥1,5mm vs. ≥2mm em homens) — não aplique os mesmos limiares."
        ),
        "V3": (
            "V3 é a zona de transição. Se R > S aqui, transição precoce. "
            "Esta câmera marca o ponto onde a despolarização ventricular muda de direção — "
            "o vetor começa a apontar para a câmera. Supra de ST em V1-V3 configura padrão "
            "anterosseptal, sugerindo oclusão da descendente anterior proximal. "
            "Cuidado: a transição elétrica normal (R = S) ocorre entre V3 e V4; se ocorrer em "
            "V1-V2, investigue HVD, IAM posterior ou pré-excitação (Wolff-Parkinson-White)."
        ),
        "V4": (
            "V4 no ápice. Supra de ST aqui com DII/DIII/aVF = IAM extenso. "
            "Câmera posicionada sobre o ápice do coração, território da descendente anterior "
            "distal. É a derivação com maior amplitude normal de QRS e onde a onda T deve ser "
            "sempre positiva. Inversão de onda T em V4 (com V1-V3 normais) sugere isquemia apical. "
            "Cuidado: supra de ST persistente em V4 em pacientes jovens pode ser variante normal "
            "(repolarização precoce), mas sempre exclua SCA no contexto clínico adequado."
        ),
        "V5": (
            "V5 avalia parede lateral. R alto pode indicar HVE. "
            "Câmera na parede lateral do ventrículo esquerdo, território da artéria circunflexa "
            "ou ramos diagonais. R alto em V5 (>26mm) ou soma SV1 + RV5 ≥ 35mm satisfaz "
            "critério de Sokolow-Lyon para hipertrofia ventricular esquerda. "
            "Cuidado: em atletas e jovens magros, voltagens altas em V5 podem ser fisiológicas — "
            "correlacione com sinais de sobrecarga (strain) como infra de ST e T invertida."
        ),
        "V6": (
            "V6 é a câmera mais lateral. qRs normal; R alto = HVE (critério de Sokolow: SV1 + RV5/V6 ≥ 35mm). "
            "Filma a parede lateral do ventrículo esquerdo de perfil, sendo sensível para "
            "detectar hipertrofia e padrões de bloqueio de ramo esquerdo (ausência de q septal, "
            "R alargado). Inversão de T em V5-V6 com R dominante sugere sobrecarga ventricular esquerda. "
            "Cuidado: a ausência de onda q septal em V6 (normalmente presente) pode indicar BRE, "
            "IAM septal prévio ou pré-excitação — investigue o contexto."
        ),
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
              amplitude (float, -1 to 1),
              strength (str),
              explanation_pt
    """
    key = lead_name.strip()
    if key not in LEAD_CAMERAS:
        raise ValueError(f"Derivação '{key}' não encontrada.")

    lead_angle = LEAD_CAMERAS[key]["angle_deg"]
    diff = _angle_difference(lead_angle, vector_direction_deg)

    # Gradient system using cosine for amplitude
    amplitude = math.cos(math.radians(diff))

    # Strength classification based on angle difference thresholds
    if diff <= 45:
        strength = "forte"
        strength_text = "fortemente positiva"
    elif diff <= 75:
        strength = "moderada"
        strength_text = "moderadamente positiva"
    elif diff <= 105:
        strength = "isoelétrica"
        strength_text = "bifásica"
    elif diff <= 135:
        strength = "moderada"
        strength_text = "moderadamente negativa"
    else:
        strength = "forte"
        strength_text = "fortemente negativa"

    # Backward-compatible three-way classification using original thresholds
    if diff <= 80:
        deflection = "positiva"
        explanation = (
            f"O vetor elétrico ({vector_direction_deg}°) está se APROXIMANDO "
            f"da câmera {key} ({lead_angle}°). "
            f"Diferença angular: {diff:.0f}° (< 90°). "
            "Pela regra do CAFÉ: Aproximando → deflexão positiva. "
            "A câmera vê o vetor vindo em sua direção — imagem nítida, "
            f"onda para cima. Intensidade: {strength_text} "
            f"(amplitude relativa: {amplitude:+.2f})."
        )
    elif diff >= 100:
        deflection = "negativa"
        explanation = (
            f"O vetor elétrico ({vector_direction_deg}°) está FUGINDO "
            f"da câmera {key} ({lead_angle}°). "
            f"Diferença angular: {diff:.0f}° (> 90°). "
            "Pela regra do CAFÉ: Fugindo → deflexão negativa. "
            "A câmera vê o vetor se afastando — imagem desfocada, "
            f"onda para baixo. Intensidade: {strength_text} "
            f"(amplitude relativa: {amplitude:+.2f})."
        )
    else:
        deflection = "bifásica"
        explanation = (
            f"O vetor elétrico ({vector_direction_deg}°) está praticamente "
            f"PERPENDICULAR à câmera {key} ({lead_angle}°). "
            f"Diferença angular: {diff:.0f}° (≈ 90°). "
            "Pela regra do CAFÉ: Esquece quando perpendicular → bifásico. "
            "A câmera não consegue resolver — o vetor cruza seu campo "
            f"de visão sem se aproximar nem se afastar de verdade. "
            f"Intensidade: {strength_text} "
            f"(amplitude relativa: {amplitude:+.2f})."
        )

    return {
        "lead": key,
        "lead_angle_deg": lead_angle,
        "vector_deg": vector_direction_deg,
        "angle_diff": diff,
        "deflection": deflection,
        "amplitude": round(amplitude, 4),
        "strength": strength,
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
# predict_qrs_morphology
# ---------------------------------------------------------------------------

def predict_qrs_morphology(lead: str, vector_angle: float) -> Dict[str, Any]:
    """
    Prediz a morfologia esperada do QRS em uma derivação, dado o ângulo
    do vetor principal de despolarização ventricular.

    A câmera (derivação) registra R quando o vetor se aproxima e S
    quando o vetor se afasta. A amplitude relativa depende do cosseno
    da diferença angular.

    Parameters
    ----------
    lead : str
        Nome da derivação (e.g. "V1", "II").
    vector_angle : float
        Ângulo do vetor QRS principal em graus.

    Returns
    -------
    dict com:
        lead, vector_angle, lead_angle, r_amplitude (float -1 to 1),
        s_amplitude (float -1 to 1), pattern (str),
        explanation_pt (str)
    """
    key = lead.strip()
    if key not in LEAD_CAMERAS:
        raise ValueError(f"Derivação '{key}' não encontrada.")

    lead_angle = LEAD_CAMERAS[key]["angle_deg"]
    diff = _angle_difference(lead_angle, vector_angle)
    cos_val = math.cos(math.radians(diff))

    # R amplitude: positive projection (how much vector approaches camera)
    # S amplitude: negative projection (how much vector moves away)
    # These represent the relative sizes of R and S waves
    r_amplitude = max(0.0, cos_val)
    s_amplitude = max(0.0, -cos_val)

    # Determine QRS morphology pattern based on R/S ratio
    if diff <= 15:
        # Vector almost directly toward camera: tall R, no S
        pattern = "R"
        r_amplitude = round(cos_val, 4)
        s_amplitude = 0.0
    elif diff <= 35:
        # Vector mostly toward camera: small q, tall R, small s
        pattern = "qRs"
        r_amplitude = round(cos_val, 4)
        s_amplitude = round(1.0 - cos_val, 4)
    elif diff <= 55:
        # Vector approaching but with angle: R dominant with S
        pattern = "Rs"
        r_amplitude = round(cos_val, 4)
        s_amplitude = round(abs(math.sin(math.radians(diff))) * 0.5, 4)
    elif diff <= 75:
        # Transition zone: R and S similar
        pattern = "RS"
        r_amplitude = round(cos_val, 4)
        s_amplitude = round(abs(math.sin(math.radians(diff))) * 0.7, 4)
    elif diff <= 105:
        # Near perpendicular: biphasic
        pattern = "RS" if cos_val >= 0 else "rS"
        r_amplitude = round(max(0.0, cos_val), 4)
        s_amplitude = round(max(0.0, -cos_val), 4)
    elif diff <= 125:
        # Vector mostly away: small r, deep S
        pattern = "rS"
        r_amplitude = round(abs(math.sin(math.radians(diff))) * 0.5, 4)
        s_amplitude = round(abs(cos_val), 4)
    elif diff <= 145:
        # Vector strongly away: tiny r, dominant S
        pattern = "rS"
        r_amplitude = round(abs(math.sin(math.radians(diff))) * 0.3, 4)
        s_amplitude = round(abs(cos_val), 4)
    elif diff <= 165:
        # Vector almost opposite: Qr or QS
        pattern = "Qr"
        r_amplitude = round(1.0 + cos_val, 4)  # small positive
        s_amplitude = round(abs(cos_val), 4)
    else:
        # Vector directly away: QS
        pattern = "QS"
        r_amplitude = 0.0
        s_amplitude = round(abs(cos_val), 4)

    # Build explanation using camera analogy
    if diff <= 55:
        direction_text = "se APROXIMA"
        image_text = (
            f"a câmera {key} vê o vetor vindo em sua direção, "
            f"registrando uma onda R dominante (padrão {pattern})"
        )
    elif diff <= 105:
        direction_text = "CRUZA PERPENDICULARMENTE"
        image_text = (
            f"a câmera {key} está quase perpendicular ao vetor — "
            f"parte se aproxima (R) e parte se afasta (S), gerando padrão {pattern}"
        )
    else:
        direction_text = "FOGE"
        image_text = (
            f"a câmera {key} vê o vetor se afastando, "
            f"registrando uma onda S dominante (padrão {pattern})"
        )

    explanation = (
        f"Com o vetor QRS a {vector_angle}° e a câmera {key} a {lead_angle}° "
        f"(diferença: {diff:.0f}°), o vetor {direction_text} da câmera. "
        f"Resultado: {image_text}. "
        f"Pense na câmera como um fotógrafo: quando o ator (vetor) caminha "
        f"em sua direção, a imagem cresce na tela (onda R positiva); quando "
        f"se afasta, a imagem diminui (onda S negativa). "
        f"Amplitude R relativa: {r_amplitude:+.2f}, S relativa: {s_amplitude:.2f}."
    )

    return {
        "lead": key,
        "vector_angle": vector_angle,
        "lead_angle": lead_angle,
        "r_amplitude": r_amplitude,
        "s_amplitude": s_amplitude,
        "pattern": pattern,
        "explanation_pt": explanation,
    }


# ---------------------------------------------------------------------------
# get_camera_story — with clinical pattern synthesis
# ---------------------------------------------------------------------------

def _detect_stemi_territories(st_changes: Dict[str, str]) -> List[Dict[str, Any]]:
    """Detect STEMI territories from ST changes."""
    detected = []
    for territory, leads in TERRITORY_LEADS.items():
        if not leads:
            continue
        supra_leads = [l for l in leads if st_changes.get(l, "").lower() == "supra"]
        if len(supra_leads) >= 2:
            # Check for reciprocal changes
            reciprocal_leads = RECIPROCAL_MAP.get(territory, [])
            reciprocal_found = [
                l for l in reciprocal_leads
                if st_changes.get(l, "").lower() == "infra"
            ]
            detected.append({
                "territory": territory,
                "supra_leads": supra_leads,
                "reciprocal_leads": reciprocal_found,
                "has_reciprocal": len(reciprocal_found) > 0,
            })
    return detected


def _detect_hve(findings: List[str]) -> bool:
    """Detect HVE from findings list."""
    hve_keywords = ["hve", "hipertrofia ventricular esquerda", "sokolow",
                    "cornell", "voltagem", "voltage"]
    for f in findings:
        f_lower = f.lower()
        if any(kw in f_lower for kw in hve_keywords):
            return True
    return False


def _detect_bundle_branch_block(
    findings: List[str], intervals: Dict[str, Any]
) -> Optional[str]:
    """Detect bundle branch block from findings and intervals."""
    qrs = intervals.get("QRS_ms", 0)
    if qrs <= 120:
        return None
    findings_lower = " ".join(f.lower() for f in findings)
    if "brd" in findings_lower or "bloqueio de ramo direito" in findings_lower:
        return "BRD"
    if "bre" in findings_lower or "bloqueio de ramo esquerdo" in findings_lower:
        return "BRE"
    # If QRS wide but no specific morphology mentioned
    if qrs > 120:
        return "bloqueio_indeterminado"
    return None


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

    # Collect alerts for risk assessment
    alerts: List[str] = []
    clinical_patterns: List[str] = []

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

        # --- STEMI territory detection ---
        stemi_territories = _detect_stemi_territories(st_changes)
        if stemi_territories:
            parts.append("⚠ PADRÕES TERRITORIAIS DETECTADOS:")
            for st in stemi_territories:
                territory_names = {
                    "inferior": "IAMCSST inferior",
                    "anterior": "IAMCSST anterior",
                    "lateral": "IAMCSST lateral",
                    "septal": "IAMCSST septal",
                    "lateral_alto": "IAMCSST lateral alto",
                }
                territory_label = territory_names.get(
                    st["territory"], f"IAMCSST {st['territory']}"
                )
                parts.append(
                    f"  🔴 Padrão de {territory_label} — "
                    f"Supra em: {', '.join(st['supra_leads'])}"
                )
                if st["has_reciprocal"]:
                    parts.append(
                        f"     ✓ Alterações recíprocas confirmadas em: "
                        f"{', '.join(st['reciprocal_leads'])} — "
                        "aumenta especificidade para IAMCSST."
                    )
                alerts.append("URGENTE")
                clinical_patterns.append(f"Padrão de {territory_label}")
            parts.append("")

    # --- Achados gerais ---
    findings = report.get("findings", [])
    if findings:
        parts.append("ACHADOS:")
        for f in findings:
            parts.append(f"  • {f}")
        parts.append("")

    # --- HVE detection ---
    if _detect_hve(findings):
        clinical_patterns.append("Hipertrofia ventricular esquerda (HVE)")
        parts.append("PADRÃO DE HVE DETECTADO:")
        parts.append(
            "  As câmeras laterais (V5, V6, I, aVL) registram voltagens "
            "aumentadas porque a massa ventricular esquerda hipertrofiada "
            "gera vetores de maior amplitude em sua direção. "
            "V1 pode mostrar S profundo (o vetor se afasta desta câmera). "
            "Procure sinais de sobrecarga (strain): infradesnivelamento de ST "
            "com T invertida assimétrica nas derivações laterais."
        )
        parts.append("")

    # --- Bundle branch block detection ---
    intervals = report.get("intervals", {})
    bbb = _detect_bundle_branch_block(findings, intervals)
    if bbb:
        if bbb == "BRD":
            clinical_patterns.append("Bloqueio de ramo direito (BRD)")
            parts.append("PADRÃO DE BRD DETECTADO:")
            parts.append(
                "  A câmera V1 registra rsR' (dupla positividade) porque a "
                "despolarização tardia do ventrículo direito se dirige em sua "
                "direção. As câmeras laterais (I, V6) mostram S empastado — "
                "o vetor tardio do VD se afasta delas."
            )
            parts.append("")
        elif bbb == "BRE":
            clinical_patterns.append("Bloqueio de ramo esquerdo (BRE)")
            parts.append("PADRÃO DE BRE DETECTADO:")
            parts.append(
                "  As câmeras laterais (V5, V6, I) registram R alargado "
                "e entalhado porque toda a despolarização do VE ocorre por "
                "condução muscular lenta. V1 mostra QS ou rS largo — "
                "o vetor se afasta desta câmera durante todo o QRS."
            )
            parts.append("")
        elif bbb == "bloqueio_indeterminado":
            clinical_patterns.append("QRS alargado (possível bloqueio de ramo)")
            parts.append("QRS ALARGADO — POSSÍVEL BLOQUEIO DE RAMO:")
            parts.append(
                "  O QRS alargado indica condução intraventricular lenta. "
                "Analise V1 e V6 para definir se é BRD (rsR' em V1) "
                "ou BRE (R largo em V6 sem q septal)."
            )
            parts.append("")

    # --- Intervalos ---
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
            if qt > 500:
                alerts.append("ATENÇÃO")
                clinical_patterns.append(
                    f"QTc prolongado ({qt} ms > 500 ms) — risco de Torsades de Pointes"
                )
        parts.append("")

    # --- Risk assessment ---
    if alerts:
        parts.append("=" * 60)
        if "URGENTE" in alerts:
            parts.append(
                "🚨 ALERTA URGENTE — Padrão sugestivo de IAMCSST detectado. "
                "Correlacionar com clínica e considerar ativação de "
                "protocolo de reperfusão imediata."
            )
        if "ATENÇÃO" in alerts:
            parts.append(
                "⚠ ATENÇÃO — QTc > 500 ms detectado. Risco elevado de "
                "arritmia ventricular (Torsades de Pointes). "
                "Revisar medicações e eletrólitos."
            )
        parts.append("=" * 60)
        parts.append("")

    # --- Clinical summary paragraph (integrated assessment) ---
    summary_sentences: List[str] = []
    if rhythm and rate:
        summary_sentences.append(
            f"Trata-se de um ECG com ritmo {rhythm} a {rate} bpm"
        )
    elif rhythm:
        summary_sentences.append(f"Trata-se de um ECG com ritmo {rhythm}")

    if axis is not None:
        axis_info = explain_axis(axis)
        if axis_info["classification"] != "normal":
            summary_sentences.append(
                f"com {axis_info['classification_text'].lower()}"
            )
        else:
            summary_sentences.append("com eixo normal")

    if clinical_patterns:
        summary_sentences.append(
            "Os principais achados incluem: " + "; ".join(clinical_patterns)
        )

    # Correlate axis + ST + rhythm
    if axis is not None and st_changes and stemi_territories if st_changes else False:
        axis_info = explain_axis(axis)
        if axis_info["classification"] == "desvio_direita" and any(
            t["territory"] == "inferior" for t in stemi_territories
        ):
            summary_sentences.append(
                "O desvio do eixo para a direita combinado com supra de ST "
                "inferior sugere comprometimento do ventrículo direito — "
                "considerar derivações direitas (V3R, V4R)"
            )
        if axis_info["classification"] == "desvio_esquerda" and any(
            t["territory"] == "anterior" for t in stemi_territories
        ):
            summary_sentences.append(
                "O desvio do eixo para a esquerda com padrão anterior sugere "
                "oclusão proximal da descendente anterior com envolvimento "
                "do fascículo anterossuperior"
            )

    if not summary_sentences:
        summary_sentences.append(
            "ECG sem alterações significativas identificadas pela análise automática"
        )

    if summary_sentences:
        parts.append("RESUMO CLÍNICO INTEGRADO:")
        parts.append(". ".join(summary_sentences) + ".")
        if "URGENTE" in alerts:
            parts.append(
                "Este padrão exige correlação clínica imediata e consideração "
                "de intervenção urgente. As câmeras cardíacas que detectam "
                "lesão direta fornecem evidência objetiva de injúria miocárdica "
                "em território coronariano específico."
            )
        parts.append("")

    # --- Rodapé CAFÉ ---
    parts.append("-" * 60)
    parts.append("LEMBRE DO MNEMÔNICO CAFÉ:")
    parts.append(MNEMONIC_CAFE["resumo"])
    parts.append("-" * 60)

    return "\n".join(parts)

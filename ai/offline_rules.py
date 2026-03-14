"""
Rule-based ECG interpretation that works without any API.

Phase 22 (p22) - Offline fallback for AI/LLM integration.
All output is in Portuguese with camera analogies where appropriate.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Interpretation rules: each rule has a condition function and a conclusion
# ---------------------------------------------------------------------------

INTERPRETATION_RULES: list[dict[str, Any]] = [
    # --- PR interval ---
    {
        "id": "pr_prolonged",
        "category": "intervals",
        "condition": lambda med: med.get("PR_ms", 0) and med["PR_ms"] > 200,
        "conclusion": "Intervalo PR prolongado (>{val:.0f} ms) — sugere bloqueio AV de 1.° grau.",
        "camera": (
            "O atraso entre o flash (onda P) e o disparo do obturador (QRS) está "
            "maior que o normal — a câmera demora mais para disparar após o flash."
        ),
        "val_key": "PR_ms",
    },
    {
        "id": "pr_short",
        "category": "intervals",
        "condition": lambda med: med.get("PR_ms", 999) < 120 and med.get("PR_ms", 0) > 0,
        "conclusion": "Intervalo PR curto (<120 ms) — considerar pré-excitação (ex: Wolff-Parkinson-White).",
        "camera": (
            "O flash e o obturador disparam quase simultaneamente — como se houvesse "
            "um atalho no mecanismo da câmera."
        ),
        "val_key": "PR_ms",
    },
    # --- QRS duration ---
    {
        "id": "qrs_wide",
        "category": "intervals",
        "condition": lambda med: med.get("QRS_ms", 0) and med["QRS_ms"] > 120,
        "conclusion": "QRS alargado (>{val:.0f} ms) — possível bloqueio de ramo ou ritmo ventricular.",
        "camera": (
            "O obturador da câmera está demorando mais para abrir e fechar — a captura "
            "da imagem fica borrada e mais larga que o normal."
        ),
        "val_key": "QRS_ms",
    },
    {
        "id": "qrs_borderline",
        "category": "intervals",
        "condition": lambda med: 110 <= med.get("QRS_ms", 0) <= 120,
        "conclusion": "QRS limítrofe (110-120 ms) — bloqueio de ramo incompleto possível.",
        "camera": (
            "O obturador está ligeiramente mais lento que o ideal — a câmera ainda "
            "funciona, mas a imagem pode ficar levemente desfocada."
        ),
        "val_key": "QRS_ms",
    },
    # --- QTc ---
    {
        "id": "qtc_prolonged",
        "category": "intervals",
        "condition": lambda med: med.get("QTc_B", 0) and med["QTc_B"] > 460,
        "conclusion": "QTc prolongado (>{val:.0f} ms, Bazett) — risco de arritmias ventriculares.",
        "camera": (
            "O ciclo completo da câmera (do disparo ao reset) está muito longo — "
            "a câmera pode não estar pronta para a próxima foto a tempo."
        ),
        "val_key": "QTc_B",
    },
    {
        "id": "qtc_short",
        "category": "intervals",
        "condition": lambda med: med.get("QTc_B", 999) < 340 and med.get("QTc_B", 0) > 0,
        "conclusion": "QTc curto (<340 ms) — síndrome do QT curto, risco arritmogênico.",
        "camera": (
            "O ciclo da câmera está rápido demais — o reset ocorre antes que a "
            "captura esteja completa."
        ),
        "val_key": "QTc_B",
    },
    # --- Heart rate (from RR) ---
    {
        "id": "tachycardia",
        "category": "rhythm",
        "condition": lambda med: med.get("RR_s", 0) and med["RR_s"] > 0 and (60.0 / med["RR_s"]) > 100,
        "conclusion": "Taquicardia (FC >{val:.0f} bpm).",
        "camera": (
            "A câmera está disparando muito rápido — como um fotógrafo em modo burst, "
            "tirando mais de 100 fotos por minuto."
        ),
        "val_key": "RR_s",
        "val_transform": lambda rr: 60.0 / rr if rr > 0 else 0,
    },
    {
        "id": "bradycardia",
        "category": "rhythm",
        "condition": lambda med: med.get("RR_s", 0) and med["RR_s"] > 0 and (60.0 / med["RR_s"]) < 60,
        "conclusion": "Bradicardia (FC <{val:.0f} bpm).",
        "camera": (
            "A câmera está disparando muito devagar — como um fotógrafo que tira "
            "menos de 60 fotos por minuto."
        ),
        "val_key": "RR_s",
        "val_transform": lambda rr: 60.0 / rr if rr > 0 else 0,
    },
    # --- Axis ---
    {
        "id": "axis_left_deviation",
        "category": "axis",
        "condition": lambda med: False,  # handled separately via axis dict
        "conclusion": "Desvio do eixo para a esquerda.",
        "camera": (
            "As câmeras frontais mostram que a atividade elétrica principal está "
            "apontando mais para a esquerda do que o esperado."
        ),
    },
    {
        "id": "axis_right_deviation",
        "category": "axis",
        "condition": lambda med: False,
        "conclusion": "Desvio do eixo para a direita.",
        "camera": (
            "As câmeras frontais mostram que a atividade elétrica principal está "
            "apontando mais para a direita do que o esperado."
        ),
    },
    {
        "id": "axis_extreme",
        "category": "axis",
        "condition": lambda med: False,
        "conclusion": "Eixo extremo (terra de ninguém).",
        "camera": (
            "Nenhuma câmera frontal consegue capturar bem a atividade elétrica — "
            "como se o coração estivesse de costas para todas as câmeras."
        ),
    },
]

# Mapping from flag text patterns to differential diagnoses
_FLAG_DIFFERENTIAL_MAP: dict[str, list[dict[str, str]]] = {
    "bloqueio": [
        {"diagnosis": "Bloqueio de ramo direito", "support": "QRS alargado com padrão RSR' em V1"},
        {"diagnosis": "Bloqueio de ramo esquerdo", "support": "QRS alargado com ausência de R em V1"},
        {"diagnosis": "Bloqueio AV", "support": "PR prolongado ou dissociação AV"},
    ],
    "taquicardia": [
        {"diagnosis": "Taquicardia sinusal", "support": "FC >100 bpm com ondas P normais"},
        {"diagnosis": "Taquicardia supraventricular", "support": "FC >150 bpm com QRS estreito"},
        {"diagnosis": "Taquicardia ventricular", "support": "FC >100 bpm com QRS alargado"},
    ],
    "bradicardia": [
        {"diagnosis": "Bradicardia sinusal", "support": "FC <60 bpm com ondas P normais"},
        {"diagnosis": "Bloqueio AV de 2.° ou 3.° grau", "support": "Dissociação P-QRS"},
        {"diagnosis": "Disfunção do nó sinusal", "support": "Pausas sinusais prolongadas"},
    ],
    "qt prolongado": [
        {"diagnosis": "Síndrome do QT longo congênito", "support": "QTc >460 ms sem causa secundária"},
        {"diagnosis": "QT longo induzido por drogas", "support": "Uso de medicamentos que prolongam QT"},
        {"diagnosis": "Distúrbio eletrolítico", "support": "Hipocalemia, hipocalcemia, hipomagnesemia"},
    ],
    "hipertrofia": [
        {"diagnosis": "Hipertrofia ventricular esquerda", "support": "Critérios de voltagem em V5-V6"},
        {"diagnosis": "Hipertrofia ventricular direita", "support": "Desvio de eixo para direita, R alto em V1"},
        {"diagnosis": "Cardiomiopatia hipertrófica", "support": "HVE com ondas Q septais profundas"},
    ],
    "isquemia": [
        {"diagnosis": "Síndrome coronariana aguda", "support": "Alterações de ST-T agudas"},
        {"diagnosis": "Angina estável", "support": "Alterações transitórias com esforço"},
        {"diagnosis": "Infarto prévio", "support": "Ondas Q patológicas estabelecidas"},
    ],
    "fibrilação": [
        {"diagnosis": "Fibrilação atrial", "support": "Ritmo irregularmente irregular, ausência de ondas P"},
        {"diagnosis": "Flutter atrial", "support": "Ondas F em dente de serra"},
        {"diagnosis": "Fibrilação atrial paroxística", "support": "Episódios intermitentes"},
    ],
    "supra": [
        {"diagnosis": "Infarto agudo com supra de ST (IAMCSST)", "support": "Supradesnivelamento de ST >1mm em 2+ derivações contíguas"},
        {"diagnosis": "Pericardite aguda", "support": "Supradesnivelamento difuso e côncavo de ST"},
        {"diagnosis": "Repolarização precoce benigna", "support": "Supra de ST com concavidade superior em jovens"},
    ],
    "infra": [
        {"diagnosis": "Isquemia subendocárdica", "support": "Infradesnivelamento de ST horizontal ou descendente"},
        {"diagnosis": "Efeito digitálico", "support": "ST em colher (concavidade superior)"},
        {"diagnosis": "Sobrecarga ventricular", "support": "Infradesnivelamento com HVE/HVD"},
    ],
    "onda t invertida": [
        {"diagnosis": "Isquemia miocárdica", "support": "Inversão de T simétrica e profunda"},
        {"diagnosis": "Sobrecarga ventricular (strain)", "support": "T invertida assimétrica com HVE"},
        {"diagnosis": "Embolia pulmonar", "support": "T invertida em V1-V4 com S1Q3T3"},
    ],
}


# ---------------------------------------------------------------------------
# Core interpretation function
# ---------------------------------------------------------------------------

def interpret_report(report: dict) -> dict:
    """Full rule-based interpretation of an ECG report.

    Analyzes intervals (PR, QRS, QT/QTc), axis, rhythm, and pathology flags.
    Generates structured interpretation text in Portuguese using camera analogies.

    Parameters
    ----------
    report : dict
        ECG report dictionary (ECGiga schema).

    Returns
    -------
    dict
        ``{"interpretation": str, "differentials": list, "recommendations": list, "confidence": str}``
    """
    findings: list[str] = []
    camera_notes: list[str] = []
    differentials: list[str] = []
    recommendations: list[str] = []

    # --- Extract intervals ---
    iv = report.get("intervals_refined") or report.get("intervals") or {}
    med = iv.get("median", {})

    # Apply interval / rhythm rules
    for rule in INTERPRETATION_RULES:
        if rule["category"] in ("intervals", "rhythm"):
            try:
                if rule["condition"](med):
                    val_key = rule.get("val_key", "")
                    val = med.get(val_key, 0)
                    transform = rule.get("val_transform")
                    if transform:
                        val = transform(val)
                    conclusion = rule["conclusion"].format(val=val)
                    findings.append(conclusion)
                    camera_notes.append(rule["camera"])
            except (TypeError, ZeroDivisionError, KeyError):
                continue

    # --- Axis analysis ---
    axis = report.get("axis") or report.get("axis_hex") or {}
    angle = axis.get("angle_deg")
    label = axis.get("label", "")

    if angle is not None:
        if -30 <= angle <= 90:
            findings.append(f"Eixo elétrico normal ({angle:.0f}°).")
        elif -90 <= angle < -30:
            findings.append(f"Desvio do eixo para a esquerda ({angle:.0f}°).")
            camera_notes.append(
                "As câmeras frontais mostram que a atividade elétrica principal "
                "está apontando mais para a esquerda do que o esperado."
            )
            differentials.append("Considerar: bloqueio divisional anterossuperior esquerdo, HVE")
        elif 90 < angle <= 180:
            findings.append(f"Desvio do eixo para a direita ({angle:.0f}°).")
            camera_notes.append(
                "As câmeras frontais mostram que a atividade elétrica principal "
                "está apontando mais para a direita do que o esperado."
            )
            differentials.append("Considerar: HVD, bloqueio divisional posteroinferior, TEP")
        else:
            findings.append(f"Eixo extremo ({angle:.0f}°) — eixo indeterminado.")
            camera_notes.append(
                "Nenhuma câmera frontal consegue capturar bem a atividade elétrica — "
                "como se o coração estivesse de costas para todas as câmeras."
            )
            differentials.append("Eixo extremo: considerar ritmo ventricular, hipercalemia grave")

    # --- Heart rate ---
    rr_s = med.get("RR_s", 0)
    if rr_s and rr_s > 0:
        hr = 60.0 / rr_s
        findings.append(f"Frequência cardíaca estimada: ~{hr:.0f} bpm.")
        if hr > 100:
            recommendations.append("Investigar causa da taquicardia (febre, dor, ansiedade, hipertireoidismo, etc.).")
        elif hr < 60:
            recommendations.append("Avaliar se bradicardia é fisiológica (atleta) ou patológica.")
    else:
        # Try rpeaks
        rpeaks = report.get("rpeaks", {})
        rr_list = rpeaks.get("rr_sec", [])
        if rr_list:
            avg_rr = sum(rr_list) / len(rr_list)
            if avg_rr > 0:
                hr = 60.0 / avg_rr
                findings.append(f"Frequência cardíaca estimada: ~{hr:.0f} bpm.")

    # --- Flags ---
    flags = report.get("flags", [])
    for flag in flags:
        fl = flag.lower()
        if fl in ("sem flags relevantes", "nenhum", "normal"):
            continue
        findings.append(f"Flag: {flag}")
        # Match flag to differentials
        for pattern, diffs in _FLAG_DIFFERENTIAL_MAP.items():
            if pattern in fl:
                for d in diffs:
                    differentials.append(f"{d['diagnosis']} — {d['support']}")

    # --- Normal ECG check ---
    has_abnormal = any(
        kw in f.lower()
        for f in findings
        for kw in (
            "prolongado", "curto", "alargado", "limítrofe", "desvio",
            "taquicardia", "bradicardia", "extremo", "flag",
        )
    )

    if not has_abnormal:
        findings.append("ECG dentro dos limites da normalidade.")
        camera_notes.append(
            "Todas as câmeras estão funcionando corretamente — cada uma captura "
            "a atividade elétrica exatamente como esperado."
        )

    # --- Build interpretation text ---
    interpretation_parts = ["## Interpretação do ECG\n"]
    interpretation_parts.append("### Achados")
    for f in findings:
        interpretation_parts.append(f"- {f}")

    if camera_notes:
        interpretation_parts.append("\n### Analogias com Câmera")
        for c in camera_notes:
            interpretation_parts.append(f"- {c}")

    if not differentials:
        differentials.append("Sem diagnósticos diferenciais relevantes — ECG compatível com normalidade.")

    if not recommendations:
        recommendations.append("Correlacionar com quadro clínico.")
        recommendations.append("Repetir ECG se houver alteração clínica.")

    # Confidence
    if has_abnormal and differentials:
        confidence = "moderada"
    elif not has_abnormal:
        confidence = "alta"
    else:
        confidence = "baixa"

    interpretation_text = "\n".join(interpretation_parts)

    return {
        "interpretation": interpretation_text,
        "differentials": differentials,
        "recommendations": recommendations,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# Rule-based differential diagnosis
# ---------------------------------------------------------------------------

def generate_differential(findings: list[str]) -> list[dict]:
    """Generate rule-based differential diagnoses from a list of ECG findings.

    Parameters
    ----------
    findings : list[str]
        List of ECG findings/abnormalities as free-text strings.

    Returns
    -------
    list[dict]
        Each dict has ``{"diagnosis": str, "support": str, "camera_analogy": str}``.
    """
    results: list[dict] = []
    seen: set[str] = set()

    for finding in findings:
        fl = finding.lower()

        # PR interval
        if "pr" in fl and ("prolongado" in fl or "longo" in fl or "> 200" in fl or ">200" in fl):
            _add_differential(results, seen, {
                "diagnosis": "Bloqueio AV de 1.° grau",
                "support": "Intervalo PR prolongado (>200 ms)",
                "camera_analogy": "O atraso entre o flash e o obturador está maior que o normal.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Efeito medicamentoso (betabloqueador, digital)",
                "support": "PR prolongado pode ser efeito de drogas cronotrópicas negativas",
                "camera_analogy": "Alguém ajustou o timer da câmera para demorar mais entre o flash e a foto.",
            })

        if "pr" in fl and ("curto" in fl or "< 120" in fl or "<120" in fl):
            _add_differential(results, seen, {
                "diagnosis": "Síndrome de Wolff-Parkinson-White",
                "support": "PR curto com possível onda delta",
                "camera_analogy": "Existe um atalho no mecanismo — o obturador dispara quase junto com o flash.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Síndrome de Lown-Ganong-Levine",
                "support": "PR curto sem onda delta",
                "camera_analogy": "O timer da câmera foi encurtado, mas o obturador funciona normalmente.",
            })

        # QRS
        if "qrs" in fl and ("alargado" in fl or "largo" in fl or "> 120" in fl or ">120" in fl):
            _add_differential(results, seen, {
                "diagnosis": "Bloqueio de ramo direito",
                "support": "QRS alargado com morfologia RSR' em V1",
                "camera_analogy": "O obturador está abrindo em duas etapas — primeiro rápido, depois lento.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Bloqueio de ramo esquerdo",
                "support": "QRS alargado com QS ou rS em V1",
                "camera_analogy": "O obturador está preso e demora mais para completar o ciclo.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Ritmo ventricular / Marca-passo",
                "support": "QRS alargado com morfologia bizarra",
                "camera_analogy": "A câmera está sendo acionada manualmente em vez do mecanismo automático.",
            })

        # QTc
        if "qtc" in fl and ("prolongado" in fl or "longo" in fl or "> 460" in fl or ">460" in fl):
            _add_differential(results, seen, {
                "diagnosis": "Síndrome do QT longo congênito",
                "support": "QTc prolongado sem causa secundária identificável",
                "camera_analogy": "O ciclo completo da câmera é geneticamente mais longo.",
            })
            _add_differential(results, seen, {
                "diagnosis": "QT longo adquirido (medicamentoso/eletrolítico)",
                "support": "QTc prolongado com uso de fármacos ou distúrbio iônico",
                "camera_analogy": "Algo externo está fazendo a câmera demorar mais para resetar.",
            })

        # Tachycardia
        if "taquicardia" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Taquicardia sinusal",
                "support": "FC >100 bpm com ondas P normais precedendo cada QRS",
                "camera_analogy": "O fotógrafo está disparando mais rápido, mas cada foto é normal.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Taquicardia supraventricular paroxística",
                "support": "FC 150-250 bpm, QRS estreito, início/fim súbitos",
                "camera_analogy": "A câmera entrou em modo burst — disparo automático ultrarrápido.",
            })

        # Bradycardia
        if "bradicardia" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Bradicardia sinusal fisiológica",
                "support": "FC <60 bpm em atleta ou durante sono, ondas P normais",
                "camera_analogy": "O fotógrafo profissional tira menos fotos — cada uma com mais qualidade.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Bloqueio AV de alto grau",
                "support": "Dissociação entre ondas P e complexos QRS",
                "camera_analogy": "O flash dispara mas o obturador nem sempre responde.",
            })

        # Axis deviation
        if "eixo" in fl and "esquerda" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Bloqueio divisional anterossuperior esquerdo (BDAS)",
                "support": "Desvio do eixo para esquerda (-30° a -90°)",
                "camera_analogy": "As câmeras do lado esquerdo capturam sinais mais fortes.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Hipertrofia ventricular esquerda",
                "support": "Eixo desviado com critérios de voltagem aumentada",
                "camera_analogy": "O lado esquerdo do cenário está tão grande que domina todas as fotos das câmeras esquerdas.",
            })

        if "eixo" in fl and "direita" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Hipertrofia ventricular direita",
                "support": "Desvio do eixo para direita (>90°) com R alto em V1",
                "camera_analogy": "As câmeras do lado direito estão captando sinais desproporcionalmente fortes.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Tromboembolismo pulmonar",
                "support": "Desvio de eixo agudo com padrão S1Q3T3",
                "camera_analogy": "Uma obstrução súbita fez o lado direito inchar e dominar as câmeras.",
            })

        # ST changes
        if "supra" in fl or "st" in fl and "elev" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Infarto agudo do miocárdio com supra de ST",
                "support": "Supradesnivelamento >1mm em derivações contíguas",
                "camera_analogy": "Algumas câmeras mostram uma área brilhante demais — sinal de lesão aguda.",
            })
            _add_differential(results, seen, {
                "diagnosis": "Pericardite aguda",
                "support": "Supradesnivelamento difuso e côncavo",
                "camera_analogy": "Todas as câmeras mostram brilho difuso — inflamação ao redor do coração.",
            })

        # Fibrilação
        if "fibrilação" in fl or "fa" == fl.strip() or "irregular" in fl:
            _add_differential(results, seen, {
                "diagnosis": "Fibrilação atrial",
                "support": "Ritmo irregularmente irregular, sem ondas P definidas",
                "camera_analogy": "O flash está disparando caoticamente — sem ritmo ou padrão definido.",
            })

    # Fallback if no matches
    if not results:
        results.append({
            "diagnosis": "Sem diagnóstico diferencial específico identificado",
            "support": "Os achados não correspondem a padrões patológicos conhecidos nas regras offline",
            "camera_analogy": "Todas as câmeras parecem estar funcionando dentro do esperado.",
        })

    return results


def _add_differential(
    results: list[dict], seen: set[str], entry: dict
) -> None:
    """Add a differential if not already present."""
    if entry["diagnosis"] not in seen:
        seen.add(entry["diagnosis"])
        results.append(entry)

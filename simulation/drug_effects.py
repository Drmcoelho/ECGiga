"""
Drug effects on ECG simulation.

Models how common medications and substances alter ECG morphology.
Each drug entry includes its known ECG effects and a Portuguese
description using the camera analogy.
"""

from __future__ import annotations

import copy
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Drug database — at least 15 entries
# ---------------------------------------------------------------------------

DRUG_DATABASE: dict[str, dict[str, Any]] = {
    "amiodarona": {
        "qt_prolongation": True,
        "pr_prolongation": True,
        "hr_decrease": True,
        "qt_delta_ms": 60,
        "pr_delta_ms": 30,
        "hr_delta_bpm": -15,
        "description_pt": (
            "Amiodarona: antiarrítmico classe III. Bloqueia múltiplos canais iônicos. "
            "Na analogia da câmera, é como colocar vários filtros ao mesmo tempo — "
            "a imagem (ECG) fica mais lenta (bradicardia, PR longo) e a exposição "
            "aumenta (QT prolongado). Pode causar Torsades de Pointes."
        ),
        "camera_analogy": (
            "Múltiplos filtros na lente: a câmera captura mais devagar "
            "(bradicardia) e com exposição prolongada (QT longo)."
        ),
    },
    "digoxina": {
        "st_depression": True,
        "qt_shortening": True,
        "pr_prolongation": True,
        "qt_delta_ms": -30,
        "pr_delta_ms": 20,
        "st_delta_mv": -0.15,
        "description_pt": (
            "Digoxina: glicosídeo cardíaco que inibe a Na⁺/K⁺-ATPase. "
            "Na câmera, é como ajustar o contraste manualmente — o segmento ST "
            "ganha uma curvatura característica ('pá de Salvador Dalí'), o QT "
            "encurta e a condução AV fica mais lenta (PR longo)."
        ),
        "camera_analogy": (
            "Ajuste de contraste manual: ST em 'bigode de Dalí', "
            "velocidade reduzida (PR longo), exposição curta (QT curto)."
        ),
    },
    "betabloqueador": {
        "hr_decrease": True,
        "pr_prolongation": True,
        "hr_delta_bpm": -20,
        "pr_delta_ms": 20,
        "description_pt": (
            "Betabloqueadores (propranolol, atenolol, metoprolol): bloqueiam "
            "receptores β-adrenérgicos. Na câmera, é como reduzir o frame rate — "
            "a frequência cardíaca diminui e a condução AV fica mais lenta."
        ),
        "camera_analogy": (
            "Frame rate reduzido: a câmera captura menos imagens por segundo "
            "(bradicardia) e o atraso entre disparos aumenta (PR longo)."
        ),
    },
    "verapamil": {
        "hr_decrease": True,
        "pr_prolongation": True,
        "hr_delta_bpm": -15,
        "pr_delta_ms": 25,
        "description_pt": (
            "Verapamil: bloqueador de canal de cálcio. Na câmera, é como "
            "fechar parcialmente o obturador — menos cálcio entra nas células "
            "do nó AV, atrasando a condução (PR longo) e reduzindo a FC."
        ),
        "camera_analogy": (
            "Obturador parcialmente fechado: menos luz (Ca²⁺) entra, "
            "a velocidade cai (bradicardia, PR longo)."
        ),
    },
    "antidepressivo_triciclico": {
        "qt_prolongation": True,
        "qrs_widening": True,
        "qt_delta_ms": 50,
        "qrs_delta_ms": 30,
        "description_pt": (
            "Antidepressivos tricíclicos (amitriptilina, nortriptilina): "
            "bloqueiam canais de Na⁺ (tipo IA). Na câmera, é como desfocar "
            "a lente — a despolarização fica mais lenta (QRS largo) e a "
            "repolarização se prolonga (QT longo). Em intoxicação, "
            "padrão de Brugada tipo 1 possível."
        ),
        "camera_analogy": (
            "Lente desfocada: a imagem fica borrada (QRS largo) "
            "e a exposição prolongada (QT longo)."
        ),
    },
    "fluoroquinolona": {
        "qt_prolongation": True,
        "qt_delta_ms": 30,
        "description_pt": (
            "Fluoroquinolonas (levofloxacina, moxifloxacina): antibióticos "
            "que bloqueiam canais hERG de K⁺. Na câmera, é como aumentar "
            "o tempo de exposição — QT fica mais longo, com risco de arritmias."
        ),
        "camera_analogy": (
            "Tempo de exposição aumentado: a foto fica com rastro "
            "(QT prolongado), especialmente com moxifloxacina."
        ),
    },
    "cocaina": {
        "st_elevation": True,
        "tachycardia": True,
        "hr_delta_bpm": 30,
        "st_delta_mv": 0.2,
        "description_pt": (
            "Cocaína: simpatomimético e bloqueador de canais de Na⁺. "
            "Na câmera, é como colocar em modo burst com flash — a FC "
            "dispara (taquicardia), vasoespasmo coronário causa elevação "
            "do ST (infarto), e o QRS pode alargar."
        ),
        "camera_analogy": (
            "Modo burst + flash: a câmera dispara rápido demais "
            "(taquicardia) e o flash queima a imagem (ST elevado)."
        ),
    },
    "metadona": {
        "qt_prolongation": True,
        "qt_delta_ms": 50,
        "description_pt": (
            "Metadona: opioide sintético que bloqueia canais hERG. "
            "Na câmera, exposição muito longa — QT significativamente "
            "prolongado, risco elevado de Torsades de Pointes."
        ),
        "camera_analogy": (
            "Exposição ultra-longa: alto risco de imagem tremida (TdP)."
        ),
    },
    "sotalol": {
        "qt_prolongation": True,
        "hr_decrease": True,
        "qt_delta_ms": 50,
        "hr_delta_bpm": -15,
        "description_pt": (
            "Sotalol: betabloqueador com propriedade classe III. "
            "Combina redução da FC com prolongamento do QT. Na câmera, "
            "frame rate baixo + exposição longa — duplo efeito."
        ),
        "camera_analogy": (
            "Frame rate baixo + exposição longa: bradicardia + QT prolongado."
        ),
    },
    "flecainida": {
        "qrs_widening": True,
        "pr_prolongation": True,
        "qrs_delta_ms": 25,
        "pr_delta_ms": 20,
        "description_pt": (
            "Flecainida: antiarrítmico classe IC, potente bloqueador de Na⁺. "
            "Na câmera, é como reduzir a resolução — QRS alarga significativamente. "
            "Contraindicada em doença cardíaca estrutural."
        ),
        "camera_analogy": (
            "Resolução reduzida: a imagem fica borrada (QRS largo), "
            "especialmente durante esforço."
        ),
    },
    "haloperidol": {
        "qt_prolongation": True,
        "qt_delta_ms": 40,
        "description_pt": (
            "Haloperidol: antipsicótico típico que bloqueia canais hERG. "
            "Na câmera, exposição prolongada — QT longo, especialmente "
            "em doses IV altas."
        ),
        "camera_analogy": (
            "Exposição prolongada em modo automático: QT se estende."
        ),
    },
    "ondansetrona": {
        "qt_prolongation": True,
        "qt_delta_ms": 20,
        "description_pt": (
            "Ondansetrona (Zofran): antiemético que pode prolongar o QT "
            "em doses > 16 mg IV. Na câmera, leve aumento de exposição."
        ),
        "camera_analogy": (
            "Leve aumento de exposição: QT levemente prolongado em doses altas."
        ),
    },
    "adenosina": {
        "hr_decrease": True,
        "pr_prolongation": True,
        "hr_delta_bpm": -40,
        "pr_delta_ms": 80,
        "description_pt": (
            "Adenosina: ativa receptores A1, hiperpolariza o nó AV. "
            "Na câmera, é como congelar a imagem por um instante — "
            "pausa sinusal transitória, usada para diagnóstico/tratamento de TSV."
        ),
        "camera_analogy": (
            "Pause/freeze: a câmera congela por alguns segundos "
            "(bloqueio AV transitório)."
        ),
    },
    "atropina": {
        "hr_increase": True,
        "hr_delta_bpm": 25,
        "description_pt": (
            "Atropina: anticolinérgico que bloqueia o nervo vago. "
            "Na câmera, é como acelerar o frame rate — a FC aumenta "
            "rapidamente. Usada para bradicardia sintomática."
        ),
        "camera_analogy": (
            "Frame rate acelerado: a câmera dispara mais rápido (taquicardia)."
        ),
    },
    "epinefrina": {
        "tachycardia": True,
        "hr_increase": True,
        "st_elevation": False,
        "hr_delta_bpm": 40,
        "description_pt": (
            "Epinefrina (adrenalina): agonista α e β-adrenérgico. "
            "Na câmera, modo burst máximo — FC muito elevada, "
            "aumento de contratilidade. Pode causar arritmias."
        ),
        "camera_analogy": (
            "Modo burst máximo: câmera dispara o mais rápido possível."
        ),
    },
    "diltiazem": {
        "hr_decrease": True,
        "pr_prolongation": True,
        "hr_delta_bpm": -15,
        "pr_delta_ms": 25,
        "description_pt": (
            "Diltiazem: bloqueador de canal de cálcio (não-diidropiridínico). "
            "Semelhante ao verapamil — obturador parcialmente fechado, "
            "condução AV mais lenta, bradicardia."
        ),
        "camera_analogy": (
            "Obturador semi-fechado: FC e condução AV diminuem."
        ),
    },
    "procainamida": {
        "qt_prolongation": True,
        "qrs_widening": True,
        "qt_delta_ms": 45,
        "qrs_delta_ms": 15,
        "description_pt": (
            "Procainamida: antiarrítmico classe IA, bloqueia Na⁺ e K⁺. "
            "Na câmera, resolução reduzida + exposição longa — "
            "QRS alarga e QT prolonga."
        ),
        "camera_analogy": (
            "Resolução e exposição alteradas: QRS largo + QT longo."
        ),
    },
    "lidocaina": {
        "qrs_widening": False,
        "description_pt": (
            "Lidocaína: antiarrítmico classe IB, bloqueia Na⁺ em tecido "
            "isquêmico. Na câmera, correção seletiva de foco — age "
            "preferencialmente em células danificadas, com mínimo efeito "
            "no ECG normal."
        ),
        "camera_analogy": (
            "Correção seletiva: foco ajustado apenas nas áreas danificadas."
        ),
    },
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def simulate_drug_effect(baseline_waveform: np.ndarray, drug_name: str) -> np.ndarray:
    """Apply a drug's ECG effect to a baseline waveform.

    Parameters
    ----------
    baseline_waveform : np.ndarray
        1-D ECG-like signal (single lead).
    drug_name : str
        Key from ``DRUG_DATABASE``.

    Returns
    -------
    np.ndarray
        Modified waveform of the same length.
    """
    drug = DRUG_DATABASE.get(drug_name.lower())
    if drug is None:
        raise ValueError(
            f"Drug '{drug_name}' not found. Available: {list(DRUG_DATABASE.keys())}"
        )

    waveform = baseline_waveform.astype(np.float64).copy()
    n = len(waveform)

    # --- QT prolongation / shortening: stretch or compress the repolarization ---
    qt_delta = drug.get("qt_delta_ms", 0)
    if qt_delta != 0:
        # Stretch the second half of the waveform (T-wave region)
        mid = n // 2
        second_half = waveform[mid:]
        factor = 1.0 + qt_delta / 400.0  # rough scaling
        new_len = max(int(len(second_half) * factor), 1)
        x_old = np.linspace(0, 1, len(second_half))
        x_new = np.linspace(0, 1, new_len)
        stretched = np.interp(x_new, x_old, second_half)
        # Fit back to original length
        if new_len >= n - mid:
            waveform[mid:] = stretched[: n - mid]
        else:
            waveform[mid : mid + new_len] = stretched
            waveform[mid + new_len :] = stretched[-1]

    # --- QRS widening ---
    qrs_delta = drug.get("qrs_delta_ms", 0)
    if qrs_delta > 0:
        # Smooth the QRS region (first quarter) to simulate widening
        kernel_size = max(3, int(qrs_delta / 2))
        if kernel_size % 2 == 0:
            kernel_size += 1
        quarter = n // 4
        segment = waveform[:quarter]
        kernel = np.ones(kernel_size) / kernel_size
        padded = np.pad(segment, kernel_size // 2, mode="edge")
        smoothed = np.convolve(padded, kernel, mode="valid")[: len(segment)]
        waveform[:quarter] = smoothed

    # --- ST depression ---
    st_delta_mv = drug.get("st_delta_mv", 0.0)
    if st_delta_mv != 0:
        # Shift the ST segment region
        st_start = int(n * 0.35)
        st_end = int(n * 0.55)
        taper = np.ones(st_end - st_start)
        taper[:10] = np.linspace(0, 1, min(10, len(taper)))
        taper[-10:] = np.linspace(1, 0, min(10, len(taper)))
        waveform[st_start:st_end] += st_delta_mv * taper[: st_end - st_start]

    # --- ST elevation ---
    if drug.get("st_elevation"):
        st_start = int(n * 0.35)
        st_end = int(n * 0.50)
        amount = drug.get("st_delta_mv", 0.2)
        if amount <= 0:
            amount = 0.2
        seg_len = st_end - st_start
        taper = np.ones(seg_len)
        ramp = min(10, seg_len)
        taper[:ramp] = np.linspace(0, 1, ramp)
        taper[-ramp:] = np.linspace(1, 0, ramp)
        waveform[st_start:st_end] += amount * taper

    # --- Heart rate effects (simulate by scaling amplitude slightly) ---
    hr_delta = drug.get("hr_delta_bpm", 0)
    if hr_delta != 0:
        # Subtle amplitude modulation to indicate rate change
        rate_factor = 1.0 + hr_delta / 200.0
        waveform *= rate_factor

    # --- PR prolongation ---
    pr_delta = drug.get("pr_delta_ms", 0)
    if pr_delta > 0:
        # Flatten a region before QRS to simulate longer PR
        pr_region = int(n * 0.08)
        shift = min(int(pr_delta / 5), pr_region)
        if shift > 0:
            # Insert isoelectric segment
            baseline_val = waveform[0]
            insert = np.full(shift, baseline_val)
            waveform = np.concatenate([waveform[:pr_region], insert, waveform[pr_region:]])
            waveform = waveform[:n]  # trim to original length

    return waveform


def get_drug_info(drug_name: str) -> dict:
    """Get drug information including camera analogy explanation.

    Parameters
    ----------
    drug_name : str
        Drug name (key from DRUG_DATABASE).

    Returns
    -------
    dict
        Drug entry with all fields, or error dict.
    """
    drug = DRUG_DATABASE.get(drug_name.lower())
    if drug is None:
        return {
            "error": f"Drug '{drug_name}' not found",
            "available_drugs": sorted(DRUG_DATABASE.keys()),
        }
    result = copy.deepcopy(drug)
    result["name"] = drug_name.lower()
    return result


def check_drug_interactions(drug_list: list[str]) -> list[str]:
    """Check for dangerous QT-prolonging drug interactions.

    Parameters
    ----------
    drug_list : list[str]
        List of drug names currently in use.

    Returns
    -------
    list[str]
        List of warning messages (empty if no interactions found).
    """
    warnings: list[str] = []
    qt_prolongers: list[str] = []
    pr_prolongers: list[str] = []
    bradycardics: list[str] = []
    qrs_wideners: list[str] = []

    for name in drug_list:
        drug = DRUG_DATABASE.get(name.lower())
        if drug is None:
            warnings.append(f"Droga '{name}' não encontrada no banco de dados.")
            continue

        if drug.get("qt_prolongation"):
            qt_prolongers.append(name)
        if drug.get("pr_prolongation"):
            pr_prolongers.append(name)
        if drug.get("hr_decrease"):
            bradycardics.append(name)
        if drug.get("qrs_widening"):
            qrs_wideners.append(name)

    # Multiple QT prolongers = high risk
    if len(qt_prolongers) >= 2:
        warnings.append(
            f"⚠ ALTO RISCO: Múltiplas drogas que prolongam o QT em uso simultâneo: "
            f"{', '.join(qt_prolongers)}. Risco elevado de Torsades de Pointes. "
            f"Monitorar ECG e eletrólitos (K⁺, Mg²⁺)."
        )

    # Multiple PR prolongers = risk of complete heart block
    if len(pr_prolongers) >= 2:
        warnings.append(
            f"⚠ Risco de bloqueio AV avançado: Múltiplas drogas que prolongam "
            f"o PR em uso: {', '.join(pr_prolongers)}. "
            f"Monitorar intervalo PR e sintomas de bradicardia."
        )

    # Multiple bradycardic agents
    if len(bradycardics) >= 2:
        warnings.append(
            f"⚠ Risco de bradicardia severa: Múltiplos agentes bradicárdicos: "
            f"{', '.join(bradycardics)}. Monitorar FC e sintomas."
        )

    # QRS widening + QT prolongation
    if qrs_wideners and qt_prolongers:
        combined = set(qrs_wideners) | set(qt_prolongers)
        warnings.append(
            f"⚠ Combinação de alargamento do QRS + prolongamento do QT: "
            f"{', '.join(combined)}. Risco de arritmia ventricular."
        )

    # Specific dangerous combinations
    drug_set = {d.lower() for d in drug_list}
    if "cocaina" in drug_set and "betabloqueador" in drug_set:
        warnings.append(
            "⚠ CONTRAINDICAÇÃO: Betabloqueador + cocaína = risco de "
            "vasoespasmo coronário paradoxal e hipertensão não controlada. "
            "Use benzodiazepínico em vez de betabloqueador."
        )

    if "digoxina" in drug_set and "verapamil" in drug_set:
        warnings.append(
            "⚠ Digoxina + Verapamil: o verapamil aumenta os níveis séricos "
            "de digoxina. Risco de intoxicação digitálica. Ajustar dose."
        )

    if "digoxina" in drug_set and "amiodarona" in drug_set:
        warnings.append(
            "⚠ Digoxina + Amiodarona: a amiodarona aumenta os níveis de "
            "digoxina em 70-100%. Reduzir dose de digoxina pela metade."
        )

    if "flecainida" in drug_set and any(
        d in drug_set for d in ("betabloqueador", "verapamil", "diltiazem")
    ):
        warnings.append(
            "⚠ Flecainida + bloqueador nodal: risco de bradicardia severa "
            "e depressão miocárdica. Usar com cautela extrema."
        )

    return warnings

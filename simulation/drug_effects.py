"""
Drug effects on ECG simulation.

Models how common medications and substances alter ECG morphology using
pharmacodynamic principles:

- Vaughan-Williams classification for antiarrhythmic agents
- Hill equation dose-response: effect = Emax * C / (EC50 + C)
- Ion-channel-target-based waveform modification (INa, IKr, ICaL, β-adrenergic)
- RR interval resampling (not amplitude scaling) for heart rate effects
- CYP450-aware drug interaction checking with severity levels

Each drug entry includes its known ECG effects and a Portuguese
description using the camera analogy.
"""

from __future__ import annotations

import copy
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Pharmacodynamic helpers
# ---------------------------------------------------------------------------


def _hill_equation(concentration: float, emax: float, ec50: float,
                   n: float = 1.0) -> float:
    """Hill equation for dose-response relationship.

    effect = Emax * C^n / (EC50^n + C^n)

    Parameters
    ----------
    concentration : float
        Drug concentration (arbitrary units, 0-1 normalized by default).
    emax : float
        Maximum effect.
    ec50 : float
        Concentration producing 50% of Emax.
    n : float
        Hill coefficient (steepness).
    """
    if concentration <= 0:
        return 0.0
    cn = concentration ** n
    return emax * cn / (ec50 ** n + cn)


# ---------------------------------------------------------------------------
# Drug database — with Vaughan-Williams classification and ion channel targets
# ---------------------------------------------------------------------------

DRUG_DATABASE: dict[str, dict[str, Any]] = {
    "amiodarona": {
        "vaughan_williams_class": "III",
        "ion_channel_targets": {"IKr": 0.6, "INa": 0.2, "ICaL": 0.15, "beta": 0.1},
        "ec50": 0.4,
        "hill_n": 1.2,
        "qt_prolongation": True,
        "pr_prolongation": True,
        "hr_decrease": True,
        "qt_delta_ms": 60,
        "pr_delta_ms": 30,
        "hr_delta_bpm": -15,
        "cyp_inhibits": ["CYP3A4", "CYP2D6", "CYP2C9"],
        "cyp_substrate": ["CYP3A4"],
        "description_pt": (
            "Amiodarona: antiarrítmico classe III (Vaughan-Williams). Bloqueia "
            "predominantemente IKr (repolarização), com efeitos adicionais em INa, "
            "ICaL e receptores β-adrenérgicos. Na analogia da câmera, é como "
            "colocar vários filtros ao mesmo tempo — a imagem (ECG) fica mais "
            "lenta (bradicardia, PR longo) e a exposição aumenta (QT prolongado "
            "por bloqueio de IKr). Pode causar Torsades de Pointes."
        ),
        "camera_analogy": (
            "Múltiplos filtros na lente: a câmera captura mais devagar "
            "(bradicardia) e com exposição prolongada (QT longo)."
        ),
    },
    "digoxina": {
        "vaughan_williams_class": None,
        "mechanism": "Na+/K+-ATPase inhibitor → increased intracellular Ca2+",
        "ion_channel_targets": {"IKr": 0.1},
        "ec50": 0.3,
        "hill_n": 1.5,
        "st_depression": True,
        "qt_shortening": True,
        "pr_prolongation": True,
        "qt_delta_ms": -30,
        "pr_delta_ms": 20,
        "st_delta_mv": -0.15,
        "cyp_substrate": [],
        "cyp_inhibits": [],
        "transporter": "P-glycoprotein",
        "description_pt": (
            "Digoxina: glicosídeo cardíaco que inibe a Na⁺/K⁺-ATPase, "
            "aumentando o Ca²⁺ intracelular via trocador Na⁺/Ca²⁺. Na câmera, "
            "é como ajustar o contraste manualmente — o segmento ST ganha uma "
            "curvatura característica ('pá de Salvador Dalí'), o QT encurta e a "
            "condução AV fica mais lenta (PR longo) por aumento do tônus vagal."
        ),
        "camera_analogy": (
            "Ajuste de contraste manual: ST em 'bigode de Dalí', "
            "velocidade reduzida (PR longo), exposição curta (QT curto)."
        ),
    },
    "betabloqueador": {
        "vaughan_williams_class": "II",
        "ion_channel_targets": {"beta": 0.8},
        "ec50": 0.3,
        "hill_n": 1.0,
        "hr_decrease": True,
        "pr_prolongation": True,
        "hr_delta_bpm": -20,
        "pr_delta_ms": 20,
        "cyp_substrate": ["CYP2D6"],
        "cyp_inhibits": [],
        "description_pt": (
            "Betabloqueadores (propranolol, atenolol, metoprolol): classe II "
            "(Vaughan-Williams), bloqueiam receptores β₁-adrenérgicos no nó "
            "sinusal e AV. Na câmera, é como reduzir o frame rate — a frequência "
            "cardíaca diminui (menor automatismo do nó SA) e a condução AV fica "
            "mais lenta (PR prolongado)."
        ),
        "camera_analogy": (
            "Frame rate reduzido: a câmera captura menos imagens por segundo "
            "(bradicardia) e o atraso entre disparos aumenta (PR longo)."
        ),
    },
    "verapamil": {
        "vaughan_williams_class": "IV",
        "ion_channel_targets": {"ICaL": 0.7, "beta": 0.1},
        "ec50": 0.35,
        "hill_n": 1.0,
        "hr_decrease": True,
        "pr_prolongation": True,
        "hr_delta_bpm": -15,
        "pr_delta_ms": 25,
        "cyp_substrate": ["CYP3A4"],
        "cyp_inhibits": ["CYP3A4"],
        "description_pt": (
            "Verapamil: bloqueador de canal de cálcio classe IV (Vaughan-Williams). "
            "Bloqueia ICaL no nó AV e miocárdio, reduzindo a condução AV e "
            "contratilidade. Na câmera, é como fechar parcialmente o obturador — "
            "menos Ca²⁺ entra nas células do nó AV, atrasando a condução (PR longo) "
            "e reduzindo a FC."
        ),
        "camera_analogy": (
            "Obturador parcialmente fechado: menos luz (Ca²⁺) entra, "
            "a velocidade cai (bradicardia, PR longo)."
        ),
    },
    "antidepressivo_triciclico": {
        "vaughan_williams_class": "IA-like",
        "ion_channel_targets": {"INa": 0.5, "IKr": 0.3},
        "ec50": 0.3,
        "hill_n": 1.3,
        "qt_prolongation": True,
        "qrs_widening": True,
        "qt_delta_ms": 50,
        "qrs_delta_ms": 30,
        "cyp_substrate": ["CYP2D6", "CYP3A4"],
        "cyp_inhibits": ["CYP2D6"],
        "description_pt": (
            "Antidepressivos tricíclicos (amitriptilina, nortriptilina): "
            "bloqueiam canais de Na⁺ (efeito tipo classe IA) e IKr. Na câmera, "
            "é como desfocar a lente — o bloqueio de INa reduz a velocidade de "
            "condução (QRS largo) e o bloqueio de IKr prolonga a repolarização "
            "(QT longo). Em intoxicação, padrão de Brugada tipo 1 possível."
        ),
        "camera_analogy": (
            "Lente desfocada: a imagem fica borrada (QRS largo) "
            "e a exposição prolongada (QT longo)."
        ),
    },
    "fluoroquinolona": {
        "vaughan_williams_class": None,
        "mechanism": "hERG/IKr channel blocker",
        "ion_channel_targets": {"IKr": 0.4},
        "ec50": 0.5,
        "hill_n": 1.0,
        "qt_prolongation": True,
        "qt_delta_ms": 30,
        "cyp_substrate": [],
        "cyp_inhibits": ["CYP1A2"],
        "description_pt": (
            "Fluoroquinolonas (levofloxacina, moxifloxacina): antibióticos "
            "que bloqueiam canais hERG (IKr), prolongando a repolarização. "
            "Na câmera, é como aumentar o tempo de exposição — QT fica mais "
            "longo, com risco de arritmias ventriculares."
        ),
        "camera_analogy": (
            "Tempo de exposição aumentado: a foto fica com rastro "
            "(QT prolongado), especialmente com moxifloxacina."
        ),
    },
    "cocaina": {
        "vaughan_williams_class": "IC-like",
        "mechanism": "Na+ channel blocker + sympathomimetic (NE reuptake inhibitor)",
        "ion_channel_targets": {"INa": 0.4, "beta": -0.5},
        "ec50": 0.3,
        "hill_n": 1.2,
        "st_elevation": True,
        "tachycardia": True,
        "hr_delta_bpm": 30,
        "st_delta_mv": 0.2,
        "cyp_substrate": ["CYP3A4"],
        "cyp_inhibits": [],
        "description_pt": (
            "Cocaína: bloqueador de canais de Na⁺ (efeito classe IC) e "
            "simpatomimético potente (inibe recaptação de norepinefrina). "
            "Na câmera, é como colocar em modo burst com flash — a FC dispara "
            "(ativação simpática), vasoespasmo coronário causa elevação do ST "
            "(infarto), e o QRS pode alargar (bloqueio de INa)."
        ),
        "camera_analogy": (
            "Modo burst + flash: a câmera dispara rápido demais "
            "(taquicardia) e o flash queima a imagem (ST elevado)."
        ),
    },
    "metadona": {
        "vaughan_williams_class": None,
        "mechanism": "hERG/IKr channel blocker (potent)",
        "ion_channel_targets": {"IKr": 0.7},
        "ec50": 0.3,
        "hill_n": 1.5,
        "qt_prolongation": True,
        "qt_delta_ms": 50,
        "cyp_substrate": ["CYP3A4", "CYP2D6"],
        "cyp_inhibits": [],
        "description_pt": (
            "Metadona: opioide sintético que é um potente bloqueador de "
            "canais hERG (IKr), prolongando significativamente a repolarização. "
            "Na câmera, exposição muito longa — QT significativamente "
            "prolongado, risco elevado de Torsades de Pointes."
        ),
        "camera_analogy": (
            "Exposição ultra-longa: alto risco de imagem tremida (TdP)."
        ),
    },
    "sotalol": {
        "vaughan_williams_class": "III + II",
        "ion_channel_targets": {"IKr": 0.6, "beta": 0.5},
        "ec50": 0.35,
        "hill_n": 1.0,
        "qt_prolongation": True,
        "hr_decrease": True,
        "qt_delta_ms": 50,
        "hr_delta_bpm": -15,
        "cyp_substrate": [],
        "cyp_inhibits": [],
        "description_pt": (
            "Sotalol: betabloqueador com propriedade classe III (bloqueio de IKr). "
            "Combina redução da FC (classe II, bloqueio β) com prolongamento "
            "do QT (classe III, bloqueio IKr). Na câmera, frame rate baixo + "
            "exposição longa — duplo efeito."
        ),
        "camera_analogy": (
            "Frame rate baixo + exposição longa: bradicardia + QT prolongado."
        ),
    },
    "flecainida": {
        "vaughan_williams_class": "IC",
        "ion_channel_targets": {"INa": 0.7, "IKr": 0.1},
        "ec50": 0.3,
        "hill_n": 1.2,
        "qrs_widening": True,
        "pr_prolongation": True,
        "qrs_delta_ms": 25,
        "pr_delta_ms": 20,
        "cyp_substrate": ["CYP2D6"],
        "cyp_inhibits": [],
        "description_pt": (
            "Flecainida: antiarrítmico classe IC (Vaughan-Williams), potente "
            "bloqueador de INa com cinética de dissociação lenta. Na câmera, "
            "é como reduzir a resolução — QRS alarga significativamente "
            "(velocidade de condução reduzida). Contraindicada em doença "
            "cardíaca estrutural (estudo CAST)."
        ),
        "camera_analogy": (
            "Resolução reduzida: a imagem fica borrada (QRS largo), "
            "especialmente durante esforço."
        ),
    },
    "haloperidol": {
        "vaughan_williams_class": None,
        "mechanism": "hERG/IKr channel blocker (D2 antagonist)",
        "ion_channel_targets": {"IKr": 0.5},
        "ec50": 0.4,
        "hill_n": 1.0,
        "qt_prolongation": True,
        "qt_delta_ms": 40,
        "cyp_substrate": ["CYP3A4", "CYP2D6"],
        "cyp_inhibits": ["CYP2D6"],
        "description_pt": (
            "Haloperidol: antipsicótico típico que bloqueia canais hERG (IKr), "
            "prolongando a repolarização ventricular. Na câmera, exposição "
            "prolongada — QT longo, especialmente em doses IV altas."
        ),
        "camera_analogy": (
            "Exposição prolongada em modo automático: QT se estende."
        ),
    },
    "ondansetrona": {
        "vaughan_williams_class": None,
        "mechanism": "5-HT3 antagonist + mild hERG/IKr blocker",
        "ion_channel_targets": {"IKr": 0.2},
        "ec50": 0.6,
        "hill_n": 1.0,
        "qt_prolongation": True,
        "qt_delta_ms": 20,
        "cyp_substrate": ["CYP3A4", "CYP1A2"],
        "cyp_inhibits": [],
        "description_pt": (
            "Ondansetrona (Zofran): antiemético que pode prolongar o QT "
            "em doses > 16 mg IV por bloqueio leve de IKr. Na câmera, "
            "leve aumento de exposição."
        ),
        "camera_analogy": (
            "Leve aumento de exposição: QT levemente prolongado em doses altas."
        ),
    },
    "adenosina": {
        "vaughan_williams_class": None,
        "mechanism": "A1 receptor agonist → IKAdo activation, AV node depression",
        "ion_channel_targets": {"beta": 0.0},
        "ec50": 0.2,
        "hill_n": 2.0,
        "hr_decrease": True,
        "pr_prolongation": True,
        "hr_delta_bpm": -40,
        "pr_delta_ms": 80,
        "cyp_substrate": [],
        "cyp_inhibits": [],
        "description_pt": (
            "Adenosina: ativa receptores A1, hiperpolariza o nó AV via "
            "ativação de IKAdo (corrente de K⁺ dependente de adenosina). "
            "Na câmera, é como congelar a imagem por um instante — "
            "pausa sinusal transitória, usada para diagnóstico/tratamento de TSV."
        ),
        "camera_analogy": (
            "Pause/freeze: a câmera congela por alguns segundos "
            "(bloqueio AV transitório)."
        ),
    },
    "atropina": {
        "vaughan_williams_class": None,
        "mechanism": "Muscarinic antagonist → removes vagal tone",
        "ion_channel_targets": {"beta": -0.3},
        "ec50": 0.25,
        "hill_n": 1.0,
        "hr_increase": True,
        "hr_delta_bpm": 25,
        "cyp_substrate": [],
        "cyp_inhibits": [],
        "description_pt": (
            "Atropina: anticolinérgico que bloqueia receptores muscarínicos, "
            "removendo o tônus vagal sobre o nó SA. Na câmera, é como "
            "acelerar o frame rate — a FC aumenta rapidamente. "
            "Usada para bradicardia sintomática."
        ),
        "camera_analogy": (
            "Frame rate acelerado: a câmera dispara mais rápido (taquicardia)."
        ),
    },
    "epinefrina": {
        "vaughan_williams_class": None,
        "mechanism": "α + β adrenergic agonist → chronotropic/inotropic",
        "ion_channel_targets": {"beta": -0.8},
        "ec50": 0.2,
        "hill_n": 1.5,
        "tachycardia": True,
        "hr_increase": True,
        "st_elevation": False,
        "hr_delta_bpm": 40,
        "cyp_substrate": [],
        "cyp_inhibits": [],
        "description_pt": (
            "Epinefrina (adrenalina): agonista α e β-adrenérgico potente. "
            "Aumenta a corrente If no nó SA (cronotropismo positivo) e ICaL "
            "no miocárdio (inotropismo positivo). Na câmera, modo burst "
            "máximo — FC muito elevada. Pode causar arritmias."
        ),
        "camera_analogy": (
            "Modo burst máximo: câmera dispara o mais rápido possível."
        ),
    },
    "diltiazem": {
        "vaughan_williams_class": "IV",
        "ion_channel_targets": {"ICaL": 0.6, "beta": 0.1},
        "ec50": 0.35,
        "hill_n": 1.0,
        "hr_decrease": True,
        "pr_prolongation": True,
        "hr_delta_bpm": -15,
        "pr_delta_ms": 25,
        "cyp_substrate": ["CYP3A4"],
        "cyp_inhibits": ["CYP3A4"],
        "description_pt": (
            "Diltiazem: bloqueador de canal de cálcio classe IV (Vaughan-Williams), "
            "não-diidropiridínico. Bloqueia ICaL no nó AV. Semelhante ao "
            "verapamil — obturador parcialmente fechado, condução AV mais lenta, "
            "bradicardia."
        ),
        "camera_analogy": (
            "Obturador semi-fechado: FC e condução AV diminuem."
        ),
    },
    "procainamida": {
        "vaughan_williams_class": "IA",
        "ion_channel_targets": {"INa": 0.4, "IKr": 0.4},
        "ec50": 0.35,
        "hill_n": 1.0,
        "qt_prolongation": True,
        "qrs_widening": True,
        "qt_delta_ms": 45,
        "qrs_delta_ms": 15,
        "cyp_substrate": ["CYP2D6"],
        "cyp_inhibits": [],
        "description_pt": (
            "Procainamida: antiarrítmico classe IA (Vaughan-Williams), bloqueia "
            "INa (fase 0, reduz velocidade de condução → QRS largo) e IKr "
            "(fase 3, prolonga repolarização → QT longo). Na câmera, "
            "resolução reduzida + exposição longa."
        ),
        "camera_analogy": (
            "Resolução e exposição alteradas: QRS largo + QT longo."
        ),
    },
    "lidocaina": {
        "vaughan_williams_class": "IB",
        "ion_channel_targets": {"INa": 0.3},
        "ec50": 0.5,
        "hill_n": 1.0,
        "qrs_widening": False,
        "cyp_substrate": ["CYP3A4", "CYP1A2"],
        "cyp_inhibits": [],
        "description_pt": (
            "Lidocaína: antiarrítmico classe IB (Vaughan-Williams), bloqueia "
            "INa com cinética de dissociação rápida — age preferencialmente em "
            "tecido isquêmico (células parcialmente despolarizadas) com mínimo "
            "efeito no tecido saudável. Na câmera, correção seletiva de foco."
        ),
        "camera_analogy": (
            "Correção seletiva: foco ajustado apenas nas áreas danificadas."
        ),
    },
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _apply_rr_resampling(waveform: np.ndarray, hr_delta_bpm: int) -> np.ndarray:
    """Modify heart rate by resampling the RR interval, not amplitude scaling.

    Positive hr_delta → shorter RR → compress waveform (tachycardia).
    Negative hr_delta → longer RR → stretch waveform (bradycardia).

    The output is always the same length as input; the RR-modified
    waveform is placed at the start and the remainder is filled with
    the baseline value (resting potential).
    """
    if hr_delta_bpm == 0:
        return waveform.copy()

    n = len(waveform)
    # Assume baseline HR ~70 bpm → one beat occupies most of the waveform
    baseline_hr = 70.0
    new_hr = baseline_hr + hr_delta_bpm
    new_hr = max(new_hr, 20.0)  # physiological floor
    new_hr = min(new_hr, 220.0)  # physiological ceiling

    # Ratio determines stretch/compress factor for one beat
    ratio = baseline_hr / new_hr  # >1 = stretch (slower), <1 = compress (faster)

    new_beat_len = max(int(n * ratio), 10)

    # Resample the original beat to the new duration
    x_old = np.linspace(0, 1, n)
    x_new = np.linspace(0, 1, new_beat_len)
    resampled = np.interp(x_new, x_old, waveform)

    # Place into output array
    output = np.full(n, waveform[0], dtype=np.float64)  # fill with baseline
    copy_len = min(new_beat_len, n)
    output[:copy_len] = resampled[:copy_len]

    return output


def _apply_ion_channel_effects(waveform: np.ndarray, drug: dict,
                               concentration: float = 1.0) -> np.ndarray:
    """Apply waveform modifications based on ion channel targets using
    the Hill equation for dose-response.

    Ion channel targets and their ECG effects:
    - INa block → QRS widening (reduced conduction velocity)
    - IKr block → QT prolongation (delayed repolarization)
    - ICaL block → PR prolongation + reduced amplitude
    - beta effect → HR change (handled separately via RR resampling)
    """
    targets = drug.get("ion_channel_targets", {})
    ec50 = drug.get("ec50", 0.5)
    hill_n = drug.get("hill_n", 1.0)
    n = len(waveform)

    # INa block → QRS widening via convolution (conduction velocity decrease)
    ina_block = targets.get("INa", 0.0)
    if ina_block > 0:
        block_fraction = _hill_equation(concentration, ina_block, ec50, hill_n)
        qrs_delta = drug.get("qrs_delta_ms", int(block_fraction * 40))
        if qrs_delta > 0:
            kernel_size = max(3, int(qrs_delta / 2))
            if kernel_size % 2 == 0:
                kernel_size += 1
            quarter = n // 4
            segment = waveform[:quarter]
            kernel = np.ones(kernel_size) / kernel_size
            padded = np.pad(segment, kernel_size // 2, mode="edge")
            smoothed = np.convolve(padded, kernel, mode="valid")[: len(segment)]
            waveform[:quarter] = smoothed

    # IKr block → QT prolongation (repolarization delay)
    ikr_block = targets.get("IKr", 0.0)
    if ikr_block > 0:
        block_fraction = _hill_equation(concentration, ikr_block, ec50, hill_n)
        qt_delta = drug.get("qt_delta_ms", int(block_fraction * 80))
        if qt_delta > 0:
            mid = n // 2
            second_half = waveform[mid:]
            factor = 1.0 + qt_delta / 400.0
            new_len = max(int(len(second_half) * factor), 1)
            x_old = np.linspace(0, 1, len(second_half))
            x_new = np.linspace(0, 1, new_len)
            stretched = np.interp(x_new, x_old, second_half)
            if new_len >= n - mid:
                waveform[mid:] = stretched[: n - mid]
            else:
                waveform[mid: mid + new_len] = stretched
                waveform[mid + new_len:] = stretched[-1]

    # ICaL block → PR prolongation + decreased contractility (amplitude)
    ical_block = targets.get("ICaL", 0.0)
    if ical_block > 0:
        block_fraction = _hill_equation(concentration, ical_block, ec50, hill_n)
        # Reduced contractility: slight amplitude reduction
        amplitude_factor = 1.0 - 0.15 * block_fraction
        waveform *= amplitude_factor

    return waveform


def simulate_drug_effect(baseline_waveform: np.ndarray, drug_name: str,
                         concentration: float = 1.0) -> np.ndarray:
    """Apply a drug's ECG effect to a baseline waveform.

    Uses pharmacodynamic modeling based on the drug's ion channel targets
    and the Hill equation for dose-response relationships.

    Parameters
    ----------
    baseline_waveform : np.ndarray
        1-D ECG-like signal (single lead).
    drug_name : str
        Key from ``DRUG_DATABASE``.
    concentration : float
        Normalized drug concentration (0 to 1+). Default 1.0 = therapeutic.

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

    # --- Ion-channel-target-based effects ---
    waveform = _apply_ion_channel_effects(waveform, drug, concentration)

    # --- QT shortening (e.g. digoxin) ---
    qt_delta = drug.get("qt_delta_ms", 0)
    if qt_delta < 0:
        # Compress the second half for QT shortening
        mid = n // 2
        second_half = waveform[mid:]
        factor = 1.0 + qt_delta / 400.0
        new_len = max(int(len(second_half) * factor), 1)
        x_old = np.linspace(0, 1, len(second_half))
        x_new = np.linspace(0, 1, new_len)
        stretched = np.interp(x_new, x_old, second_half)
        if new_len >= n - mid:
            waveform[mid:] = stretched[: n - mid]
        else:
            waveform[mid: mid + new_len] = stretched
            waveform[mid + new_len:] = stretched[-1]

    # --- ST depression ---
    st_delta_mv = drug.get("st_delta_mv", 0.0)
    if st_delta_mv != 0:
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

    # --- Heart rate effects: RR interval resampling (not amplitude scaling) ---
    hr_delta = drug.get("hr_delta_bpm", 0)
    if hr_delta != 0:
        waveform = _apply_rr_resampling(waveform, hr_delta)

    # --- PR prolongation (insert isoelectric segment) ---
    pr_delta = drug.get("pr_delta_ms", 0)
    if pr_delta > 0:
        pr_region = int(n * 0.08)
        shift = min(int(pr_delta / 5), pr_region)
        if shift > 0:
            baseline_val = waveform[0]
            insert = np.full(shift, baseline_val)
            waveform = np.concatenate([waveform[:pr_region], insert,
                                       waveform[pr_region:]])
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


# ---------------------------------------------------------------------------
# QT risk scoring
# ---------------------------------------------------------------------------

def _compute_qt_risk_score(drug_list: list[str]) -> tuple[float, list[str]]:
    """Compute additive QT prolongation risk score.

    Each drug contributes its IKr block fraction to the total risk.
    Score thresholds:
        < 0.3: low risk
        0.3-0.6: moderate risk
        > 0.6: high risk

    Returns (score, list of contributing drugs).
    """
    score = 0.0
    contributors = []
    for name in drug_list:
        drug = DRUG_DATABASE.get(name.lower())
        if drug is None:
            continue
        targets = drug.get("ion_channel_targets", {})
        ikr = targets.get("IKr", 0.0)
        qt_delta = drug.get("qt_delta_ms", 0)
        if ikr > 0 or qt_delta > 0:
            contribution = ikr + (qt_delta / 200.0 if qt_delta > 0 else 0)
            score += contribution
            contributors.append(name)
    return score, contributors


def _check_cyp450_interactions(drug_list: list[str]) -> list[str]:
    """Check for CYP450-mediated pharmacokinetic interactions.

    If drug A inhibits a CYP enzyme that drug B is a substrate of,
    drug B's levels may increase, potentiating its effects.
    """
    warnings = []
    drugs_info = {}
    for name in drug_list:
        drug = DRUG_DATABASE.get(name.lower())
        if drug is not None:
            drugs_info[name.lower()] = drug

    for name_a, drug_a in drugs_info.items():
        inhibits = set(drug_a.get("cyp_inhibits", []))
        if not inhibits:
            continue
        for name_b, drug_b in drugs_info.items():
            if name_a == name_b:
                continue
            substrates = set(drug_b.get("cyp_substrate", []))
            overlap = inhibits & substrates
            if overlap:
                enzymes = ", ".join(sorted(overlap))
                warnings.append(
                    f"⚠ Interação CYP450: {name_a} inibe {enzymes}, que "
                    f"metaboliza {name_b}. Níveis séricos de {name_b} podem "
                    f"aumentar significativamente. Considerar ajuste de dose."
                )
    return warnings


# ---------------------------------------------------------------------------
# Contraindicated combinations
# ---------------------------------------------------------------------------

_CONTRAINDICATED_PAIRS: list[tuple[set[str], str, str]] = [
    (
        {"cocaina", "betabloqueador"},
        "CONTRAINDICAÇÃO",
        "⚠ CONTRAINDICAÇÃO: Betabloqueador + cocaína = bloqueio β sem oposição "
        "permite estimulação α irrestrita → vasoespasmo coronário paradoxal e "
        "hipertensão não controlada. Use benzodiazepínico em vez de betabloqueador.",
    ),
    (
        {"digoxina", "verapamil"},
        "ALTO RISCO",
        "⚠ Digoxina + Verapamil: o verapamil inibe a P-glicoproteína, "
        "aumentando os níveis séricos de digoxina em 70-100%. "
        "Risco de intoxicação digitálica. Ajustar dose.",
    ),
    (
        {"digoxina", "amiodarona"},
        "ALTO RISCO",
        "⚠ Digoxina + Amiodarona: a amiodarona inibe CYP3A4 e P-glicoproteína, "
        "aumentando os níveis de digoxina em 70-100%. Reduzir dose de digoxina "
        "pela metade.",
    ),
]


def check_drug_interactions(drug_list: list[str]) -> list[str]:
    """Check for dangerous drug interactions with pharmacological reasoning.

    Includes:
    - Additive QT prolongation risk scoring
    - CYP450-mediated interaction warnings
    - Contraindicated combinations with severity levels
    - Pharmacodynamic interaction analysis

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

    # --- Additive QT prolongation risk scoring ---
    qt_score, qt_contributors = _compute_qt_risk_score(drug_list)
    if len(qt_prolongers) >= 2:
        severity = "ALTO RISCO" if qt_score > 0.6 else "RISCO MODERADO"
        warnings.append(
            f"⚠ {severity}: Múltiplas drogas que prolongam o QT em uso "
            f"simultâneo: {', '.join(qt_prolongers)}. Score de risco QT "
            f"aditivo: {qt_score:.2f}. Risco elevado de Torsades de Pointes. "
            f"Monitorar ECG e eletrólitos (K⁺, Mg²⁺)."
        )

    # --- Multiple PR prolongers → risk of AV block ---
    if len(pr_prolongers) >= 2:
        warnings.append(
            f"⚠ Risco de bloqueio AV avançado: Múltiplas drogas que prolongam "
            f"o PR em uso: {', '.join(pr_prolongers)}. "
            f"Monitorar intervalo PR e sintomas de bradicardia."
        )

    # --- Multiple bradycardic agents ---
    if len(bradycardics) >= 2:
        warnings.append(
            f"⚠ Risco de bradicardia severa: Múltiplos agentes bradicárdicos: "
            f"{', '.join(bradycardics)}. Monitorar FC e sintomas."
        )

    # --- QRS widening + QT prolongation ---
    if qrs_wideners and qt_prolongers:
        combined = set(qrs_wideners) | set(qt_prolongers)
        warnings.append(
            f"⚠ Combinação de alargamento do QRS + prolongamento do QT: "
            f"{', '.join(combined)}. Risco de arritmia ventricular."
        )

    # --- Contraindicated combinations ---
    drug_set = {d.lower() for d in drug_list}
    for pair, _severity, message in _CONTRAINDICATED_PAIRS:
        if pair.issubset(drug_set):
            warnings.append(message)

    # --- Flecainide + nodal blockers ---
    if "flecainida" in drug_set and any(
        d in drug_set for d in ("betabloqueador", "verapamil", "diltiazem")
    ):
        warnings.append(
            "⚠ Flecainida + bloqueador nodal: risco de bradicardia severa "
            "e depressão miocárdica. Usar com cautela extrema."
        )

    # --- CYP450 interaction analysis ---
    cyp_warnings = _check_cyp450_interactions(drug_list)
    warnings.extend(cyp_warnings)

    return warnings

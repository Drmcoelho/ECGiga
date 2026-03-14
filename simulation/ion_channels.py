"""
Ion channel simulation for ECG waveform modification.

Models the effect of extracellular ion concentration changes on cardiac
action potentials and the resulting ECG waveform.  The core metaphor used
throughout ECGiga is the "camera analogy" — the heart's electrical system
is likened to a camera capturing snapshots, and ion channel disturbances
change the exposure, focus, and shutter speed of that camera.
"""

from __future__ import annotations

import numpy as np


class ActionPotentialModel:
    """Simulate a ventricular action potential and derive ECG-like effects.

    Default extracellular concentrations (mEq/L):
        K+  = 4.0   (normal 3.5–5.0)
        Ca2+ = 2.2  (normal 2.1–2.6)
        Na+ = 140.0 (normal 136–145)
    """

    # Normal reference ranges
    _K_NORMAL = 4.0
    _CA_NORMAL = 2.2
    _NA_NORMAL = 140.0

    def __init__(
        self,
        k_extra: float = 4.0,
        ca_extra: float = 2.2,
        na_extra: float = 140.0,
    ) -> None:
        self.k_extra = k_extra
        self.ca_extra = ca_extra
        self.na_extra = na_extra

        # Derived baseline intervals (ms) — will be modified by ion changes
        self._qt_base = 380.0
        self._qrs_base = 90.0
        self._pr_base = 160.0

    # ------------------------------------------------------------------
    # Public helpers to set abnormal concentrations
    # ------------------------------------------------------------------

    def apply_hyperkalemia(self, level: str = "mild") -> None:
        """Raise extracellular K+.

        * mild:     5.5–6.0 mEq/L
        * moderate: 6.0–7.0 mEq/L
        * severe:   > 7.0 mEq/L
        """
        mapping = {"mild": 5.7, "moderate": 6.5, "severe": 7.5}
        self.k_extra = mapping.get(level, 5.7)

    def apply_hypokalemia(self, level: str = "mild") -> None:
        """Lower extracellular K+.

        * mild:     3.0–3.5 mEq/L
        * moderate: 2.5–3.0 mEq/L
        * severe:   < 2.5 mEq/L
        """
        mapping = {"mild": 3.2, "moderate": 2.7, "severe": 2.2}
        self.k_extra = mapping.get(level, 3.2)

    def apply_hypercalcemia(self) -> None:
        """Raise extracellular Ca2+ (> 2.6 mEq/L)."""
        self.ca_extra = 3.5

    def apply_hypocalcemia(self) -> None:
        """Lower extracellular Ca2+ (< 2.1 mEq/L)."""
        self.ca_extra = 1.5

    # ------------------------------------------------------------------
    # Waveform generation
    # ------------------------------------------------------------------

    def compute_waveform(self, duration_ms: int = 1000, fs: int = 1000) -> np.ndarray:
        """Generate an action-potential-shaped waveform.

        The waveform has five classical phases (0–4) and is modulated by
        the current ion concentrations.

        Parameters
        ----------
        duration_ms : int
            Duration of the generated waveform in milliseconds.
        fs : int
            Sampling frequency in Hz (samples per second).

        Returns
        -------
        np.ndarray
            1-D array of voltage values (mV-like units).
        """
        n_samples = int(duration_ms * fs / 1000)
        t = np.linspace(0, duration_ms, n_samples, endpoint=False)

        # Resting potential shifts with K+
        v_rest = -90.0 + 20.0 * np.log(self.k_extra / self._K_NORMAL)

        # Phase 0: rapid depolarization (Na+ dependent)
        na_factor = self.na_extra / self._NA_NORMAL
        v_peak = 20.0 * na_factor

        # Phase 2 plateau duration affected by Ca2+
        ca_factor = self.ca_extra / self._CA_NORMAL
        plateau_duration = 200.0 * ca_factor  # ms

        # Phase 3 repolarization affected by K+
        k_factor = self.k_extra / self._K_NORMAL
        repol_rate = 0.5 / k_factor  # higher K+ → faster repol

        waveform = np.full(n_samples, v_rest)

        # Depolarization onset at 50 ms
        t_onset = 50.0
        for i, ti in enumerate(t):
            dt = ti - t_onset
            if dt < 0:
                continue
            elif dt < 5:
                # Phase 0: rapid upstroke
                waveform[i] = v_rest + (v_peak - v_rest) * (dt / 5.0)
            elif dt < 5 + 10:
                # Phase 1: partial repolarization notch
                notch_depth = 10.0
                frac = (dt - 5) / 10.0
                waveform[i] = v_peak - notch_depth * np.sin(np.pi * frac)
            elif dt < 5 + 10 + plateau_duration:
                # Phase 2: plateau
                plateau_v = v_peak - 10.0
                decay = 0.02 * (dt - 15)
                waveform[i] = plateau_v - decay
            elif dt < 5 + 10 + plateau_duration + 150:
                # Phase 3: repolarization
                start_v = v_peak - 10.0 - 0.02 * plateau_duration
                frac = (dt - 15 - plateau_duration) / 150.0
                frac = min(frac, 1.0)
                waveform[i] = start_v + (v_rest - start_v) * (frac ** repol_rate)
            else:
                # Phase 4: resting
                waveform[i] = v_rest

        return waveform

    # ------------------------------------------------------------------
    # ECG-level effects summary
    # ------------------------------------------------------------------

    def get_ecg_effects(self) -> dict:
        """Return a dict describing the ECG-level consequences of the
        current ion concentrations.

        Keys:
            qt_change   – description of QT interval change
            t_wave_change – description of T-wave morphology change
            st_change   – description of ST segment change
            qrs_change  – description of QRS complex change
            description_pt – Portuguese explanation using camera analogy
        """
        effects: dict[str, str] = {
            "qt_change": "Sem alteração",
            "t_wave_change": "Sem alteração",
            "st_change": "Sem alteração",
            "qrs_change": "Sem alteração",
            "description_pt": "",
        }

        k = self.k_extra
        ca = self.ca_extra

        descriptions: list[str] = []

        # --- Potassium effects ---
        if k > 7.0:
            effects["qt_change"] = "QT encurtado"
            effects["t_wave_change"] = "Ondas T apiculadas (tall peaked T waves)"
            effects["qrs_change"] = "QRS alargado (>120 ms), padrão sinusoidal possível"
            effects["st_change"] = "Depressão do ST possível"
            descriptions.append(
                "Hipercalemia severa (K⁺ > 7.0 mEq/L): Na analogia da câmera, "
                "é como se o obturador estivesse tão rápido que a imagem fica "
                "distorcida — a repolarização é acelerada (T apiculada) e a "
                "despolarização fica lenta (QRS largo). Risco de fibrilação ventricular."
            )
        elif k > 6.0:
            effects["qt_change"] = "QT pode estar encurtado"
            effects["t_wave_change"] = "Ondas T apiculadas"
            effects["qrs_change"] = "QRS levemente alargado"
            descriptions.append(
                "Hipercalemia moderada (K⁺ 6.0–7.0 mEq/L): A câmera começa "
                "a perder resolução — as ondas T ficam pontiagudas e estreitas, "
                "indicando repolarização acelerada. O QRS pode começar a alargar."
            )
        elif k > 5.0:
            effects["t_wave_change"] = "Ondas T levemente apiculadas"
            descriptions.append(
                "Hipercalemia leve (K⁺ 5.0–6.0 mEq/L): Pequena alteração no "
                "'foco' da câmera — ondas T mais pontiagudas que o habitual."
            )
        elif k < 2.5:
            effects["qt_change"] = "QT prolongado"
            effects["t_wave_change"] = "Ondas T achatadas/invertidas, onda U proeminente"
            effects["st_change"] = "Depressão do ST"
            descriptions.append(
                "Hipocalemia severa (K⁺ < 2.5 mEq/L): A câmera está com "
                "exposição excessiva — a repolarização fica prolongada (QT longo), "
                "as ondas T desaparecem e surge a onda U. Alto risco de Torsades de Pointes."
            )
        elif k < 3.0:
            effects["qt_change"] = "QT prolongado"
            effects["t_wave_change"] = "Ondas T achatadas, onda U presente"
            effects["st_change"] = "Depressão leve do ST"
            descriptions.append(
                "Hipocalemia moderada (K⁺ 2.5–3.0 mEq/L): A exposição da câmera "
                "está alta — ondas T achatadas e aparecimento de onda U."
            )
        elif k < 3.5:
            effects["t_wave_change"] = "Ondas T levemente achatadas"
            descriptions.append(
                "Hipocalemia leve (K⁺ 3.0–3.5 mEq/L): Leve desajuste de exposição "
                "— ondas T um pouco mais baixas."
            )

        # --- Calcium effects ---
        if ca > 2.6:
            effects["qt_change"] = "QT encurtado"
            descriptions.append(
                "Hipercalcemia (Ca²⁺ > 2.6 mEq/L): Na câmera, o obturador "
                "está mais rápido — o plateau da fase 2 encurta, resultando "
                "em QT curto. O segmento ST pode parecer quase ausente."
            )
        elif ca < 2.1:
            effects["qt_change"] = "QT prolongado"
            descriptions.append(
                "Hipocalcemia (Ca²⁺ < 2.1 mEq/L): O obturador está lento — "
                "o plateau da fase 2 se prolonga, resultando em QT longo com "
                "segmento ST esticado."
            )

        effects["description_pt"] = " ".join(descriptions) if descriptions else (
            "Concentrações iônicas dentro da normalidade. A 'câmera' cardíaca "
            "está funcionando com configurações padrão — sem distorções esperadas no ECG."
        )

        return effects

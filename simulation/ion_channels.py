"""
Ion channel simulation for ECG waveform modification.

Models the effect of extracellular ion concentration changes on cardiac
action potentials and the resulting ECG waveform.  Uses a simplified
Luo-Rudy phase model with physiologically grounded ion current
representations and the Goldman-Hodgkin-Katz (GHK) equation for resting
membrane potential.

The core metaphor used throughout ECGiga is the "camera analogy" — the
heart's electrical system is likened to a camera capturing snapshots, and
ion channel disturbances change the exposure, focus, and shutter speed
of that camera.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------

_R = 8314.0  # Universal gas constant, mJ/(mol*K)
_T = 310.0   # Body temperature, K (37 °C)
_F = 96485.0  # Faraday constant, C/mol
_RT_F = _R * _T / _F  # ≈ 26.73 mV at 37 °C


# ---------------------------------------------------------------------------
# GHK resting potential
# ---------------------------------------------------------------------------

def _ghk_resting_potential(
    k_out: float, na_out: float, cl_out: float = 110.0,
    k_in: float = 140.0, na_in: float = 12.0, cl_in: float = 4.0,
    p_k: float = 1.0, p_na: float = 0.04, p_cl: float = 0.45,
) -> float:
    """Goldman-Hodgkin-Katz voltage equation.

    Vm = (RT/F) * ln((PK*Ko + PNa*Nao + PCl*Cli) / (PK*Ki + PNa*Nai + PCl*Clo))

    Default permeability ratios approximate ventricular myocyte at rest.
    """
    numerator = p_k * k_out + p_na * na_out + p_cl * cl_in
    denominator = p_k * k_in + p_na * na_in + p_cl * cl_out
    if denominator <= 0 or numerator <= 0:
        return -90.0
    return _RT_F * np.log(numerator / denominator)


# ---------------------------------------------------------------------------
# Simplified ion current models
# ---------------------------------------------------------------------------

def _ina_availability(v_rest: float, v_half_inact: float = -70.0,
                      slope: float = 6.0) -> float:
    """Fraction of Na+ channels available (h∞ steady-state inactivation).

    As resting potential depolarizes (e.g. hyperkalemia), more Na+ channels
    are in the inactivated state, reducing INa availability.  This is a
    Boltzmann sigmoid: h∞ = 1 / (1 + exp((Vm - V_half) / slope)).
    """
    return 1.0 / (1.0 + np.exp((v_rest - v_half_inact) / slope))


def _ito_current(dt_phase1: float, tau: float = 8.0,
                 g_to: float = 10.0) -> float:
    """Transient outward K+ current (Ito) – phase 1 notch.

    Modeled as a decaying exponential during early repolarization.
    """
    return g_to * np.exp(-dt_phase1 / tau)


def _ical_plateau(dt_phase2: float, tau_inact: float = 80.0,
                  g_cal: float = 1.0, ca_factor: float = 1.0) -> float:
    """L-type Ca2+ current (ICaL) – maintains phase 2 plateau.

    The plateau voltage is sustained by the balance between inward ICaL
    and outward IKr.  Ca2+ factor modulates channel conductance.
    """
    return g_cal * ca_factor * np.exp(-dt_phase2 / tau_inact)


def _ikr_current(dt: float, tau_act: float = 50.0,
                 g_kr: float = 0.8, k_factor: float = 1.0) -> float:
    """Rapid delayed rectifier K+ current (IKr) – phase 2/3.

    Activates during plateau and drives terminal repolarization together
    with IKs.
    """
    activation = 1.0 - np.exp(-dt / tau_act)
    return g_kr * k_factor * activation


def _iks_current(dt: float, tau_act: float = 200.0,
                 g_ks: float = 0.3, k_factor: float = 1.0) -> float:
    """Slow delayed rectifier K+ current (IKs) – phase 3.

    Slowly activating K+ current that completes repolarization.
    """
    activation = 1.0 - np.exp(-dt / tau_act)
    return g_ks * k_factor * activation


def _ik1_current(v: float, k_out: float, k_normal: float = 4.0) -> float:
    """Inward rectifier K+ current (IK1) – phase 4 resting potential.

    Conductance scales with sqrt(Ko/Ko_normal) per GHK rectification.
    Maintains the resting membrane potential.
    """
    g_k1 = 0.5 * np.sqrt(k_out / k_normal)
    v_k = _RT_F * np.log(k_out / 140.0)  # EK via Nernst
    return g_k1 * (v - v_k) / (1.0 + np.exp(0.07 * (v + 80.0)))


class ActionPotentialModel:
    """Simulate a ventricular action potential and derive ECG-like effects.

    Uses a simplified Luo-Rudy phase model with physiologically grounded
    ion channel representations:
      - Phase 0: Fast INa (rapid depolarization)
      - Phase 1: Ito (transient outward K+, early repolarization notch)
      - Phase 2: ICaL balanced by IKr (plateau)
      - Phase 3: IKr + IKs (delayed rectifier repolarization)
      - Phase 4: IK1 (inward rectifier, resting potential maintenance)

    Resting potential computed via Goldman-Hodgkin-Katz equation.

    Default extracellular concentrations (mEq/L):
        K+  = 4.0   (normal 3.5–5.0)
        Ca2+ = 2.2  (normal 2.1–2.6)
        Na+ = 140.0 (normal 136–145)
    """

    # Normal reference ranges
    _K_NORMAL = 4.0
    _CA_NORMAL = 2.2
    _NA_NORMAL = 140.0

    # Intracellular concentrations (mEq/L)
    _K_IN = 140.0
    _NA_IN = 12.0
    _CL_IN = 4.0
    _CL_OUT = 110.0

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
    # Internal physiological computations
    # ------------------------------------------------------------------

    def _compute_resting_potential(self) -> float:
        """Compute resting membrane potential via GHK equation."""
        return _ghk_resting_potential(
            k_out=self.k_extra, na_out=self.na_extra, cl_out=self._CL_OUT,
            k_in=self._K_IN, na_in=self._NA_IN, cl_in=self._CL_IN,
        )

    def _compute_ina_availability(self) -> float:
        """Fraction of Na+ channels available at resting potential.

        Hyperkalemia depolarizes RMP → more Na+ channel inactivation →
        decreased INa → slower upstroke → wider QRS.
        """
        v_rest = self._compute_resting_potential()
        return _ina_availability(v_rest)

    def _compute_ca_factor(self) -> float:
        """Ca2+ modulation factor for ICaL plateau duration.

        Hypercalcemia → increased ICaL inactivation rate → shortened plateau.
        Hypocalcemia → decreased ICaL → prolonged plateau.
        """
        return self.ca_extra / self._CA_NORMAL

    def _compute_k_repol_factor(self) -> float:
        """K+ modulation of repolarizing currents (IKr, IKs).

        Hyperkalemia → increased IK conductance → faster repolarization.
        Hypokalemia → decreased IK conductance → slower repolarization.
        """
        return np.sqrt(self.k_extra / self._K_NORMAL)

    # ------------------------------------------------------------------
    # Waveform generation
    # ------------------------------------------------------------------

    def compute_waveform(self, duration_ms: int = 1000, fs: int = 1000) -> np.ndarray:
        """Generate an action-potential-shaped waveform using simplified
        Luo-Rudy phase model.

        The waveform has five classical phases (0–4), each driven by the
        dominant ion current for that phase, modulated by the current
        extracellular ion concentrations.

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

        # --- Physiological parameters ---
        v_rest = self._compute_resting_potential()
        h_inf = self._compute_ina_availability()
        ca_factor = self._compute_ca_factor()
        k_repol = self._compute_k_repol_factor()

        # Na+ channel availability determines upstroke velocity and peak
        # Reduced availability → lower peak, slower upstroke → wider QRS
        na_factor = self.na_extra / self._NA_NORMAL
        v_peak = 20.0 * na_factor * h_inf  # INa-dependent overshoot
        upstroke_speed = 5.0 / max(h_inf, 0.1)  # ms for phase 0

        # Phase 1: Ito notch depth (relatively constant)
        notch_depth = 10.0

        # Phase 2: ICaL plateau duration modulated by Ca2+
        # Hypercalcemia → faster ICaL inactivation → shorter plateau
        # Hypocalcemia → slower inactivation → longer plateau
        ical_tau = 80.0 / max(ca_factor, 0.3)  # inactivation time constant
        plateau_duration = 150.0 + 50.0 / max(ca_factor, 0.3)

        # Phase 3: IKr + IKs repolarization rate modulated by K+
        # Hyperkalemia → increased K+ conductance → faster repolarization
        # Hypokalemia → decreased conductance → slower repolarization
        repol_duration = 150.0 / max(k_repol, 0.3)

        waveform = np.full(n_samples, v_rest)

        # Depolarization onset at 50 ms
        t_onset = 50.0

        # Phase boundaries (ms relative to onset)
        phase0_end = upstroke_speed
        phase1_end = phase0_end + 10.0
        phase2_end = phase1_end + plateau_duration
        phase3_end = phase2_end + repol_duration

        for i, ti in enumerate(t):
            dt = ti - t_onset
            if dt < 0:
                # Phase 4 (pre-depolarization): IK1 maintains resting potential
                continue
            elif dt < phase0_end:
                # Phase 0: Fast INa rapid depolarization
                # Voltage-gated Na+ channels open at threshold (~-70 mV)
                frac = dt / phase0_end
                # Sigmoidal upstroke shape
                waveform[i] = v_rest + (v_peak - v_rest) * (
                    3 * frac ** 2 - 2 * frac ** 3  # smooth step
                )
            elif dt < phase1_end:
                # Phase 1: Ito transient outward K+ current
                dt1 = dt - phase0_end
                ito = _ito_current(dt1, tau=8.0, g_to=notch_depth)
                waveform[i] = v_peak - ito * (dt1 / 10.0)
            elif dt < phase2_end:
                # Phase 2: ICaL vs IKr plateau balance
                dt2 = dt - phase1_end
                plateau_start_v = v_peak - notch_depth * 0.5

                # ICaL provides inward (depolarizing) current
                i_cal = _ical_plateau(dt2, tau_inact=ical_tau,
                                      ca_factor=ca_factor)
                # IKr provides outward (repolarizing) current
                i_kr = _ikr_current(dt2, tau_act=50.0, k_factor=k_repol)

                # Net current determines plateau drift
                net_current = i_cal - i_kr
                plateau_decay = 0.03 * dt2 * (1.0 - net_current / 2.0)
                waveform[i] = plateau_start_v - plateau_decay
            elif dt < phase3_end:
                # Phase 3: IKr + IKs drive repolarization
                dt3 = dt - phase2_end
                # Voltage at start of phase 3
                dt2_total = plateau_duration
                i_cal_end = _ical_plateau(dt2_total, tau_inact=ical_tau,
                                          ca_factor=ca_factor)
                i_kr_end = _ikr_current(dt2_total, tau_act=50.0,
                                        k_factor=k_repol)
                net_end = i_cal_end - i_kr_end
                plateau_start_v = v_peak - notch_depth * 0.5
                start_v = plateau_start_v - 0.03 * dt2_total * (
                    1.0 - net_end / 2.0)

                frac = dt3 / repol_duration
                frac = min(frac, 1.0)

                # Combined IKr + IKs repolarization with power-law shape
                # IKs slowly activating component gives characteristic shape
                iks_component = _iks_current(dt3, tau_act=repol_duration * 0.6,
                                             k_factor=k_repol)
                repol_shape = frac ** (0.8 + 0.4 * iks_component)
                waveform[i] = start_v + (v_rest - start_v) * repol_shape
            else:
                # Phase 4: IK1 maintains resting potential
                waveform[i] = v_rest

        return waveform

    # ------------------------------------------------------------------
    # ECG-level effects summary
    # ------------------------------------------------------------------

    def get_ecg_effects(self) -> dict:
        """Return a dict describing the ECG-level consequences of the
        current ion concentrations.

        Effects are derived mechanistically from the ion channel model:
        - Hyperkalemia: depolarized RMP (GHK) → decreased INa availability
          (Boltzmann inactivation) → wide QRS; increased IK → peaked T waves
        - Hypokalemia: hyperpolarized RMP → prolonged repolarization
          (decreased IKr/IKs) → U waves, flat T
        - Hypercalcemia: shortened ICaL plateau → short QT
        - Hypocalcemia: prolonged ICaL plateau → long QT

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

        # Compute mechanistic values for effect determination
        v_rest = self._compute_resting_potential()
        h_inf = self._compute_ina_availability()
        k_repol = self._compute_k_repol_factor()

        descriptions: list[str] = []

        # --- Potassium effects (mechanistically derived) ---
        if k > 7.0:
            # Severe hyperkalemia: V_rest depolarized ~-75mV, h∞ < 0.5
            # → marked INa reduction → very wide QRS, sinusoidal pattern
            # Increased IK1/IKr → accelerated repolarization → peaked T
            effects["qt_change"] = "QT encurtado"
            effects["t_wave_change"] = "Ondas T apiculadas (tall peaked T waves)"
            effects["qrs_change"] = "QRS alargado (>120 ms), padrão sinusoidal possível"
            effects["st_change"] = "Depressão do ST possível"
            descriptions.append(
                f"Hipercalemia severa (K⁺ > 7.0 mEq/L): O potencial de repouso está "
                f"despolarizado para ~{v_rest:.0f} mV (GHK), reduzindo a disponibilidade "
                f"de canais de Na⁺ para {h_inf:.0%} (inativação Boltzmann). "
                f"Na analogia da câmera, é como se o obturador estivesse tão rápido "
                f"que a imagem fica distorcida — a repolarização é acelerada por aumento "
                f"de IKr/IK1 (T apiculada) e a despolarização fica lenta por redução de "
                f"INa (QRS largo). Risco de fibrilação ventricular."
            )
        elif k > 6.0:
            # Moderate hyperkalemia
            effects["qt_change"] = "QT pode estar encurtado"
            effects["t_wave_change"] = "Ondas T apiculadas"
            effects["qrs_change"] = "QRS levemente alargado"
            descriptions.append(
                f"Hipercalemia moderada (K⁺ 6.0–7.0 mEq/L): Potencial de repouso "
                f"despolarizado para ~{v_rest:.0f} mV, disponibilidade de INa {h_inf:.0%}. "
                f"A câmera começa a perder resolução — as ondas T ficam pontiagudas "
                f"(IKr aumentado) e o QRS pode alargar (INa reduzido)."
            )
        elif k > 5.0:
            # Mild hyperkalemia: mainly IKr effect → peaked T
            effects["t_wave_change"] = "Ondas T levemente apiculadas"
            descriptions.append(
                "Hipercalemia leve (K⁺ 5.0–6.0 mEq/L): Pequena alteração no "
                "'foco' da câmera — ondas T mais pontiagudas que o habitual "
                "por discreto aumento da condutância de IKr."
            )
        elif k < 2.5:
            # Severe hypokalemia: hyperpolarized RMP, markedly reduced IKr/IKs
            effects["qt_change"] = "QT prolongado"
            effects["t_wave_change"] = "Ondas T achatadas/invertidas, onda U proeminente"
            effects["st_change"] = "Depressão do ST"
            descriptions.append(
                f"Hipocalemia severa (K⁺ < 2.5 mEq/L): O potencial de repouso está "
                f"hiperpolarizado (~{v_rest:.0f} mV) pela equação GHK. A condutância de "
                f"IKr/IKs está reduzida ({k_repol:.0%} do normal), prolongando a "
                f"repolarização (QT longo). Ondas U proeminentes por repolarização "
                f"tardia das fibras de Purkinje. A câmera está com exposição "
                f"excessiva. Alto risco de Torsades de Pointes."
            )
        elif k < 3.0:
            # Moderate hypokalemia
            effects["qt_change"] = "QT prolongado"
            effects["t_wave_change"] = "Ondas T achatadas, onda U presente"
            effects["st_change"] = "Depressão leve do ST"
            descriptions.append(
                "Hipocalemia moderada (K⁺ 2.5–3.0 mEq/L): A exposição da câmera "
                "está alta — ondas T achatadas e aparecimento de onda U. "
                "Repolarização prolongada por redução de IKr/IKs."
            )
        elif k < 3.5:
            effects["t_wave_change"] = "Ondas T levemente achatadas"
            descriptions.append(
                "Hipocalemia leve (K⁺ 3.0–3.5 mEq/L): Leve desajuste de exposição "
                "— ondas T um pouco mais baixas por discreta redução de IKr."
            )

        # --- Calcium effects (ICaL plateau mechanism) ---
        if ca > 2.6:
            # Hypercalcemia: increased ICaL inactivation rate → shorter plateau
            effects["qt_change"] = "QT encurtado"
            descriptions.append(
                "Hipercalcemia (Ca²⁺ > 2.6 mEq/L): A cinética de inativação do "
                "ICaL é acelerada pelo Ca²⁺ extracelular elevado, encurtando o "
                "plateau da fase 2 e resultando em QT curto. Na câmera, o obturador "
                "está mais rápido. O segmento ST pode parecer quase ausente."
            )
        elif ca < 2.1:
            # Hypocalcemia: decreased ICaL → prolonged plateau
            effects["qt_change"] = "QT prolongado"
            descriptions.append(
                "Hipocalcemia (Ca²⁺ < 2.1 mEq/L): A corrente ICaL reduzida prolonga "
                "o plateau da fase 2, resultando em QT longo com segmento ST "
                "esticado. O obturador está lento."
            )

        effects["description_pt"] = " ".join(descriptions) if descriptions else (
            "Concentrações iônicas dentro da normalidade. A 'câmera' cardíaca "
            "está funcionando com configurações padrão — sem distorções esperadas no ECG."
        )

        return effects

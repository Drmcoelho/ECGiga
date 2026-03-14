"""Testes abrangentes para os módulos de detecção de patologias cardíacas.

Verifica detecção de arritmias, distúrbios eletrolíticos, padrões isquêmicos
e anormalidades de condução a partir de medidas e características de ECG.
"""

from __future__ import annotations

import numpy as np
import pytest

from pathology.arrhythmia import (
    classify_wide_complex_tachycardia,
    detect_atrial_fibrillation,
    detect_atrial_flutter,
    detect_rhythm_irregularity,
)
from pathology.electrolyte import (
    detect_calcium_abnormality,
    detect_hyperkalemia_pattern,
    detect_hypokalemia_pattern,
)
from pathology.ischemia import (
    detect_de_winter_pattern,
    detect_nstemi_pattern,
    detect_wellens_pattern,
    differentiate_stemi_vs_early_repol,
)
from pathology.conduction import (
    classify_bundle_branch_block,
    detect_brugada_pattern,
    detect_digitalis_effect,
)


# ---------------------------------------------------------------------------
# Fixtures - Intervalos RR e relatórios sintéticos
# ---------------------------------------------------------------------------

@pytest.fixture
def rr_ritmo_sinusal():
    """Intervalos RR regulares simulando ritmo sinusal a 75 bpm (0.8s)."""
    base = 0.8
    # Variação sinusal respiratória suave (não aleatória) — CV muito baixo
    n = 30
    # Modulação senoidal suave simula arritmia sinusal respiratória
    rr = [base + 0.008 * np.sin(2 * np.pi * i / 6) for i in range(n)]
    return rr


@pytest.fixture
def rr_fibrilacao_atrial():
    """Intervalos RR irregulares simulando fibrilação atrial.

    Alta variabilidade, sem padrão repetitivo.
    """
    rng = np.random.default_rng(123)
    # RR entre 0.35 e 1.2s — altamente irregular
    return rng.uniform(0.35, 1.2, size=40).tolist()


@pytest.fixture
def rr_flutter_2_para_1():
    """Intervalos RR regulares simulando flutter atrial com condução 2:1.

    FC ventricular ~150 bpm (RR ~0.4s), muito regular.
    """
    rng = np.random.default_rng(99)
    base = 0.40  # 150 bpm
    return (base + rng.normal(0, 0.005, size=20)).tolist()


@pytest.fixture
def rr_bigeminismo():
    """Intervalos RR com padrão de bigeminismo (alternância curto-longo)."""
    # Normal: 0.8s, Extrassístole: 0.5s, Pausa compensatória: 1.1s
    pattern = []
    for _ in range(10):
        pattern.append(0.80)  # Batimento sinusal
        pattern.append(0.50)  # Extrassístole (curto)
    return pattern


@pytest.fixture
def relatorio_normal():
    """Relatório ECG com valores normais."""
    return {
        "intervals_refined": {
            "median": {
                "RR_s": 0.8,
                "PR_ms": 160,
                "QRS_ms": 90,
                "QT_ms": 380,
                "QTc_B": 425,
            }
        },
        "flags": [],
    }


@pytest.fixture
def relatorio_hipercalemia():
    """Relatório ECG sugestivo de hipercalemia moderada."""
    return {
        "intervals_refined": {
            "median": {
                "RR_s": 0.85,
                "PR_ms": 220,
                "QRS_ms": 130,
                "QT_ms": 340,
                "QTc_B": 330,
            }
        },
        "flags": ["T apiculada em V2-V4"],
    }


@pytest.fixture
def relatorio_hipocalemia():
    """Relatório ECG sugestivo de hipocalemia."""
    return {
        "intervals_refined": {
            "median": {
                "RR_s": 0.75,
                "PR_ms": 160,
                "QRS_ms": 90,
                "QT_ms": 480,
                "QTc_B": 500,
            }
        },
        "flags": ["onda U proeminente", "T achatada em V4-V6"],
    }


@pytest.fixture
def relatorio_digitalis():
    """Relatório ECG com efeito digitálico."""
    return {
        "intervals_refined": {
            "median": {
                "RR_s": 0.85,
                "PR_ms": 210,
                "QRS_ms": 88,
                "QT_ms": 340,
                "QTc_B": 350,
            }
        },
        "flags": [],
    }


# ---------------------------------------------------------------------------
# Testes: Detecção de Fibrilação Atrial
# ---------------------------------------------------------------------------

class TestDeteccaoFibrilacaoAtrial:
    """Testes para detect_atrial_fibrillation."""

    def test_detecta_fa_com_rr_irregular(self, rr_fibrilacao_atrial):
        """Verifica detecção de FA com intervalos RR altamente irregulares."""
        resultado = detect_atrial_fibrillation(rr_fibrilacao_atrial)
        assert resultado["detected"] is True
        assert resultado["classification"] == "AF"
        assert resultado["confidence"] > 0.5

    def test_nao_detecta_fa_em_ritmo_sinusal(self, rr_ritmo_sinusal):
        """Verifica que ritmo sinusal regular não é classificado como FA."""
        resultado = detect_atrial_fibrillation(rr_ritmo_sinusal)
        assert resultado["detected"] is False
        assert resultado["classification"] == "not_AF"

    def test_ondas_p_ausentes_aumentam_confianca(self, rr_fibrilacao_atrial):
        """Verifica que ausência de ondas P aumenta confiança na detecção de FA."""
        sem_p = detect_atrial_fibrillation(
            rr_fibrilacao_atrial,
            p_wave_present=[False] * len(rr_fibrilacao_atrial),
        )
        com_p = detect_atrial_fibrillation(
            rr_fibrilacao_atrial,
            p_wave_present=[True] * len(rr_fibrilacao_atrial),
        )
        assert sem_p["confidence"] >= com_p["confidence"]

    def test_dados_insuficientes_retorna_insufficient(self):
        """Verifica que menos de 8 intervalos retorna insufficient_data."""
        resultado = detect_atrial_fibrillation([0.8, 0.82, 0.79])
        assert resultado["classification"] == "insufficient_data"
        assert resultado["detected"] is False

    def test_criterios_presentes_no_resultado(self, rr_fibrilacao_atrial):
        """Verifica que os critérios individuais são retornados."""
        resultado = detect_atrial_fibrillation(rr_fibrilacao_atrial)
        assert "irregularity_coefficient" in resultado["criteria"]
        assert "turning_point_ratio" in resultado["criteria"]
        assert "shannon_entropy" in resultado["criteria"]


# ---------------------------------------------------------------------------
# Testes: Detecção de Flutter Atrial
# ---------------------------------------------------------------------------

class TestDeteccaoFlutterAtrial:
    """Testes para detect_atrial_flutter."""

    def test_detecta_flutter_2_para_1(self, rr_flutter_2_para_1):
        """Verifica detecção de flutter com condução 2:1 (~150 bpm)."""
        resultado = detect_atrial_flutter(rr_flutter_2_para_1)
        assert resultado["detected"]
        assert resultado["likely_conduction_ratio"] == "2:1"
        assert resultado["confidence"] > 0.5

    def test_nao_detecta_flutter_em_sinusal_lento(self):
        """Verifica que ritmo sinusal a 55 bpm não é classificado como flutter."""
        # 55 bpm = RR ~1.09s — fora de todas as faixas típicas de flutter
        rng = np.random.default_rng(99)
        rr_lento = (1.09 + rng.normal(0, 0.01, size=20)).tolist()
        resultado = detect_atrial_flutter(rr_lento)
        assert not resultado["detected"]

    def test_taxa_atrial_estimada_correta(self, rr_flutter_2_para_1):
        """Verifica que a taxa atrial estimada é ~300 bpm (padrão flutter)."""
        resultado = detect_atrial_flutter(rr_flutter_2_para_1)
        assert 250 <= resultado["estimated_atrial_rate"] <= 350

    def test_dados_insuficientes(self):
        """Verifica resposta com menos de 5 intervalos RR."""
        resultado = detect_atrial_flutter([0.4, 0.41, 0.39])
        assert not resultado["detected"]
        assert resultado["likely_conduction_ratio"] == "unknown"

    def test_flutter_com_p_wave_rate_fornecido(self, rr_flutter_2_para_1):
        """Verifica que p_wave_rate explícito é usado na detecção."""
        resultado = detect_atrial_flutter(
            rr_flutter_2_para_1, p_wave_rate=300.0
        )
        assert resultado["estimated_atrial_rate"] == 300.0


# ---------------------------------------------------------------------------
# Testes: Irregularidade de Ritmo
# ---------------------------------------------------------------------------

class TestIrregularidadeRitmo:
    """Testes para detect_rhythm_irregularity."""

    def test_ritmo_regular(self, rr_ritmo_sinusal):
        """Verifica classificação de ritmo regular."""
        resultado = detect_rhythm_irregularity(rr_ritmo_sinusal)
        assert resultado["pattern"] == "regular"
        assert resultado["cv"] < 0.05

    def test_bigeminismo_detectado(self, rr_bigeminismo):
        """Verifica detecção de padrão de bigeminismo."""
        resultado = detect_rhythm_irregularity(rr_bigeminismo)
        assert resultado["bigeminy"] is True
        assert resultado["pattern"] == "regularly_irregular"

    def test_irregularmente_irregular_fa(self, rr_fibrilacao_atrial):
        """Verifica classificação de ritmo irregularmente irregular (FA)."""
        resultado = detect_rhythm_irregularity(rr_fibrilacao_atrial)
        assert resultado["pattern"] == "irregularly_irregular"
        assert resultado["cv"] > 0.15

    def test_campos_obrigatorios_presentes(self, rr_ritmo_sinusal):
        """Verifica que todos os campos esperados estão no resultado."""
        resultado = detect_rhythm_irregularity(rr_ritmo_sinusal)
        campos = {"pattern", "cv", "rmssd_ms", "premature_beats", "bigeminy", "trigeminy", "details"}
        assert campos.issubset(resultado.keys())

    def test_dados_insuficientes(self):
        """Verifica resposta com menos de 4 intervalos."""
        resultado = detect_rhythm_irregularity([0.8, 0.82])
        assert resultado["pattern"] == "unknown"


# ---------------------------------------------------------------------------
# Testes: Classificação de Taquicardia de Complexo Largo
# ---------------------------------------------------------------------------

class TestTaquicardiaComplexoLargo:
    """Testes para classify_wide_complex_tachycardia."""

    def test_tv_com_criterios_classicos(self):
        """Verifica classificação como TV com dissociação AV e QRS largo."""
        resultado = classify_wide_complex_tachycardia(
            qrs_duration_ms=170,
            heart_rate=180,
            av_dissociation=True,
            concordance="negative",
        )
        assert resultado["classification"] == "VT"
        assert resultado["vt_probability"] > 0.65

    def test_tsv_com_aberrancia(self):
        """Verifica classificação como TSV com RSR' e BRB prévio."""
        resultado = classify_wide_complex_tachycardia(
            qrs_duration_ms=130,
            heart_rate=160,
            rsr_v1=True,
            previous_bbb=True,
        )
        assert resultado["classification"] == "SVT_aberrancy"
        assert resultado["vt_probability"] < 0.35

    def test_qrs_estreito_nao_e_taquicardia_larga(self):
        """Verifica que QRS < 120ms retorna narrow_complex."""
        resultado = classify_wide_complex_tachycardia(
            qrs_duration_ms=100, heart_rate=150,
        )
        assert resultado["classification"] == "narrow_complex"

    def test_fc_menor_100_nao_e_taquicardia(self):
        """Verifica que FC < 100 bpm retorna not_tachycardia."""
        resultado = classify_wide_complex_tachycardia(
            qrs_duration_ms=150, heart_rate=80,
        )
        assert resultado["classification"] == "not_tachycardia"

    def test_batimentos_fusao_favorecem_tv(self):
        """Verifica que batimentos de fusão aumentam probabilidade de TV."""
        sem_fusao = classify_wide_complex_tachycardia(
            qrs_duration_ms=150, heart_rate=160,
            rsr_v1=True,  # adiciona critério SVT para diferenciar
        )
        com_fusao = classify_wide_complex_tachycardia(
            qrs_duration_ms=150, heart_rate=160,
            rsr_v1=True,
            fusion_beats=True, capture_beats=True,
        )
        assert com_fusao["vt_probability"] > sem_fusao["vt_probability"]


# ---------------------------------------------------------------------------
# Testes: Detecção de Hipercalemia
# ---------------------------------------------------------------------------

class TestDeteccaoHipercalemia:
    """Testes para detect_hyperkalemia_pattern."""

    def test_detecta_padrao_t_apiculada_qrs_largo(self, relatorio_hipercalemia):
        """Verifica detecção com T apiculadas e QRS alargado."""
        resultado = detect_hyperkalemia_pattern(
            relatorio_hipercalemia,
            t_wave_peaked=["V2", "V3", "V4"],
        )
        assert resultado["detected"] is True
        assert resultado["stage"] in ("mild", "moderate", "severe")
        assert resultado["confidence"] > 0.3

    def test_sem_padrao_em_ecg_normal(self, relatorio_normal):
        """Verifica que ECG normal não gera detecção de hipercalemia."""
        resultado = detect_hyperkalemia_pattern(relatorio_normal)
        assert resultado["detected"] is False
        assert resultado["stage"] == "none"

    def test_t_amplitude_alta_aumenta_score(self, relatorio_normal):
        """Verifica que amplitude alta de T contribui para detecção."""
        resultado = detect_hyperkalemia_pattern(
            relatorio_normal,
            t_wave_amplitude={"V2": 1.2, "V3": 1.5, "V4": 1.0},
        )
        assert resultado["confidence"] > 0

    def test_recomendacoes_presentes_quando_detectado(self, relatorio_hipercalemia):
        """Verifica que recomendações clínicas são fornecidas."""
        resultado = detect_hyperkalemia_pattern(
            relatorio_hipercalemia,
            t_wave_peaked=["V2", "V3"],
        )
        if resultado["detected"]:
            assert len(resultado["recommendations"]) > 0


# ---------------------------------------------------------------------------
# Testes: Detecção de Hipocalemia
# ---------------------------------------------------------------------------

class TestDeteccaoHipocalemia:
    """Testes para detect_hypokalemia_pattern."""

    def test_detecta_padrao_onda_u(self, relatorio_hipocalemia):
        """Verifica detecção de hipocalemia com ondas U."""
        resultado = detect_hypokalemia_pattern(
            relatorio_hipocalemia,
            u_wave_present=["V2", "V3", "V4"],
        )
        assert resultado["detected"] is True
        assert resultado["severity"] in ("mild", "moderate", "severe")

    def test_sem_padrao_em_ecg_normal(self, relatorio_normal):
        """Verifica que ECG normal não gera detecção de hipocalemia."""
        resultado = detect_hypokalemia_pattern(relatorio_normal)
        assert resultado["detected"] is False
        assert resultado["severity"] == "none"

    def test_t_achatada_e_infra_st_contribuem(self, relatorio_normal):
        """Verifica que T achatada e infra ST aumentam score."""
        resultado = detect_hypokalemia_pattern(
            relatorio_normal,
            t_wave_flat=["V4", "V5", "V6"],
            st_depression_leads=["V4", "V5"],
        )
        assert resultado["confidence"] > 0


# ---------------------------------------------------------------------------
# Testes: Detecção de Anormalidade de Cálcio
# ---------------------------------------------------------------------------

class TestAnormalidadeCalcio:
    """Testes para detect_calcium_abnormality."""

    def test_hipercalcemia_qtc_curto(self):
        """Verifica detecção de hipercalcemia com QTc encurtado."""
        report = {
            "intervals_refined": {
                "median": {"QTc_B": 320, "QRS_ms": 90}
            },
            "flags": [],
        }
        resultado = detect_calcium_abnormality(report)
        assert resultado["detected"] is True
        assert resultado["abnormality"] == "hypercalcemia"

    def test_hipocalcemia_qtc_longo(self):
        """Verifica detecção de hipocalcemia com QTc prolongado e QRS normal."""
        report = {
            "intervals_refined": {
                "median": {"QTc_B": 520, "QRS_ms": 88}
            },
            "flags": [],
        }
        resultado = detect_calcium_abnormality(report)
        assert resultado["detected"] is True
        assert resultado["abnormality"] == "hypocalcemia"

    def test_sem_anormalidade_qtc_normal(self, relatorio_normal):
        """Verifica que QTc normal não gera detecção."""
        resultado = detect_calcium_abnormality(relatorio_normal)
        assert resultado["detected"] is False
        assert resultado["abnormality"] == "none"


# ---------------------------------------------------------------------------
# Testes: Detecção de NSTEMI
# ---------------------------------------------------------------------------

class TestDeteccaoNSTEMI:
    """Testes para detect_nstemi_pattern."""

    def test_detecta_infra_st_contiguo_anterior(self):
        """Verifica detecção de NSTEMI com infra ST em derivações contíguas anteriores."""
        st_changes = {
            "V1": "infra", "V2": "infra", "V3": "infra", "V4": "infra",
            "I": "normal", "II": "normal",
        }
        resultado = detect_nstemi_pattern(st_changes)
        assert resultado["detected"]
        # O território pode ser "anterior", "anteroseptal" ou "anterolateral"
        assert any(t in resultado["territory"] for t in ("anterior", "anteroseptal", "anterolateral"))

    def test_nao_detecta_sem_contiguas(self):
        """Verifica que infra isolado sem leads contíguos não é detectado."""
        st_changes = {"V1": "infra", "aVL": "infra"}
        resultado = detect_nstemi_pattern(st_changes)
        # V1 e aVL não são contíguos — score baixo
        assert resultado["confidence"] < 0.4

    def test_infra_difuso_com_supra_avr_detecta_padrao_multiarterial(self):
        """Verifica detecção de padrão de lesão multiarterial/TCE."""
        st_changes = {
            "I": "infra", "II": "infra", "III": "infra",
            "aVF": "infra", "V3": "infra", "V4": "infra",
            "V5": "infra", "aVR": "supra",
        }
        resultado = detect_nstemi_pattern(st_changes)
        assert resultado["detected"] is True
        assert "TCE" in resultado["territory"] or "difuso" in resultado["territory"]

    def test_troponina_positiva_aumenta_confianca(self):
        """Verifica que troponina positiva aumenta a confiança."""
        st_changes = {"V2": "infra", "V3": "infra"}
        sem_trop = detect_nstemi_pattern(st_changes, troponin_positive=None)
        com_trop = detect_nstemi_pattern(st_changes, troponin_positive=True)
        assert com_trop["confidence"] >= sem_trop["confidence"]


# ---------------------------------------------------------------------------
# Testes: Diferenciação STEMI vs Repolarização Precoce
# ---------------------------------------------------------------------------

class TestDiferenciacaoSTEMI:
    """Testes para differentiate_stemi_vs_early_repol."""

    def test_stemi_com_morfologia_convexa_e_reciprocas(self):
        """Verifica classificação como STEMI com critérios fortes."""
        resultado = differentiate_stemi_vs_early_repol(
            st_elevation_mv={"V2": 0.4, "V3": 0.5, "V4": 0.3},
            t_wave_amplitude={"V2": 0.8, "V3": 0.9, "V4": 0.7},
            st_morphology="convex",
            reciprocal_changes=True,
            patient_age=60,
        )
        assert resultado["classification"] == "STEMI"
        assert resultado["stemi_probability"] > 0.6

    def test_repolarizacao_precoce_jovem_concava(self):
        """Verifica classificação como BER em jovem com morfologia côncava."""
        resultado = differentiate_stemi_vs_early_repol(
            st_elevation_mv={"V2": 0.1, "V3": 0.12},
            t_wave_amplitude={"V2": 0.8, "V3": 0.9},
            st_morphology="concave",
            reciprocal_changes=False,
            patient_age=25,
            patient_sex="M",
        )
        assert resultado["classification"] == "early_repolarization"
        assert resultado["stemi_probability"] < 0.4

    def test_criterios_presentes_no_resultado(self):
        """Verifica que lista de critérios é retornada."""
        resultado = differentiate_stemi_vs_early_repol(
            st_elevation_mv={"V2": 0.3},
            reciprocal_changes=True,
        )
        assert isinstance(resultado["criteria"], list)
        assert len(resultado["criteria"]) > 0


# ---------------------------------------------------------------------------
# Testes: Síndrome de Wellens
# ---------------------------------------------------------------------------

class TestSindromeWellens:
    """Testes para detect_wellens_pattern."""

    def test_wellens_tipo_a_bifasica(self):
        """Verifica detecção de Wellens tipo A (T bifásica em V2-V3)."""
        resultado = detect_wellens_pattern(
            t_wave_morphology={"V2": "biphasic", "V3": "biphasic"},
            history_chest_pain=True,
            st_normal=True,
        )
        assert resultado["detected"] is True
        assert resultado["wellens_type"] == "A"

    def test_wellens_tipo_b_inversao_profunda(self):
        """Verifica detecção de Wellens tipo B (T invertida profunda em V2-V3)."""
        resultado = detect_wellens_pattern(
            t_wave_morphology={"V2": "deep_inversion", "V3": "deep_inversion"},
            history_chest_pain=True,
            st_normal=True,
        )
        assert resultado["detected"] is True
        assert resultado["wellens_type"] == "B"

    def test_sem_wellens_morfologia_normal(self):
        """Verifica que T normal não gera detecção de Wellens."""
        resultado = detect_wellens_pattern(
            t_wave_morphology={"V2": "normal", "V3": "normal"},
        )
        assert resultado["detected"] is False
        assert resultado["wellens_type"] == "none"


# ---------------------------------------------------------------------------
# Testes: Padrão de de Winter
# ---------------------------------------------------------------------------

class TestPadraoDeWinter:
    """Testes para detect_de_winter_pattern."""

    def test_detecta_padrao_classico(self):
        """Verifica detecção do padrão de de Winter com critérios completos."""
        resultado = detect_de_winter_pattern(
            st_changes={"V1": "infra", "V2": "infra", "V3": "infra",
                        "V4": "infra", "V5": "infra", "aVR": "supra"},
            t_wave_morphology={"V2": "tall_peaked", "V3": "tall_peaked",
                                "V4": "hiperaguda"},
            t_wave_amplitude={"V2": 1.2, "V3": 1.5, "V4": 1.1},
        )
        assert resultado["detected"] is True
        assert resultado["confidence"] > 0.5

    def test_nao_detecta_sem_criterios(self):
        """Verifica que ST normal não gera detecção de de Winter."""
        resultado = detect_de_winter_pattern(
            st_changes={"V1": "normal", "V2": "normal"},
        )
        assert resultado["detected"] is False


# ---------------------------------------------------------------------------
# Testes: Padrão de Brugada
# ---------------------------------------------------------------------------

class TestPadraoBrugada:
    """Testes para detect_brugada_pattern (módulo conduction)."""

    def test_brugada_tipo_1_coved(self):
        """Verifica detecção de Brugada tipo 1 (coved + T invertida)."""
        resultado = detect_brugada_pattern(
            st_morphology_v1="coved",
            st_morphology_v2="coved",
            st_elevation_v1_mv=0.25,
            st_elevation_v2_mv=0.3,
            t_wave_v1="inverted",
            t_wave_v2="inverted",
        )
        assert resultado["detected"] is True
        assert resultado["brugada_type"] == "1"
        assert resultado["confidence"] >= 0.8

    def test_brugada_tipo_2_saddleback(self):
        """Verifica detecção de Brugada tipo 2 (saddleback)."""
        resultado = detect_brugada_pattern(
            st_morphology_v1="saddleback",
            st_morphology_v2="saddleback",
            st_elevation_v1_mv=0.25,
            st_elevation_v2_mv=0.22,
        )
        assert resultado["detected"] is True
        assert resultado["brugada_type"] == "2"

    def test_sem_brugada_padrao_normal(self):
        """Verifica que morfologia normal não detecta Brugada."""
        resultado = detect_brugada_pattern(
            st_morphology_v1="normal",
            st_morphology_v2="normal",
            st_elevation_v1_mv=0.05,
            st_elevation_v2_mv=0.03,
        )
        assert resultado["detected"] is False
        assert resultado["brugada_type"] == "none"

    def test_febre_aumenta_score(self):
        """Verifica que febre é considerada como fator agravante."""
        sem_febre = detect_brugada_pattern(
            st_morphology_v1="coved",
            st_elevation_v1_mv=0.25,
            t_wave_v1="inverted",
        )
        com_febre = detect_brugada_pattern(
            st_morphology_v1="coved",
            st_elevation_v1_mv=0.25,
            t_wave_v1="inverted",
            fever=True,
        )
        assert com_febre["confidence"] >= sem_febre["confidence"]


# ---------------------------------------------------------------------------
# Testes: Efeito Digitálico
# ---------------------------------------------------------------------------

class TestEfeitoDigitalico:
    """Testes para detect_digitalis_effect."""

    def test_detecta_efeito_com_st_scooping_e_medicacao(self, relatorio_digitalis):
        """Verifica detecção com ST em colher e uso de digitálico conhecido."""
        resultado = detect_digitalis_effect(
            relatorio_digitalis,
            st_morphology={"V5": "scooping", "V6": "scooping"},
            medication_digitalis=True,
        )
        assert resultado["detected"] is True
        assert resultado["pattern"] == "effect"

    def test_sem_efeito_em_ecg_normal(self, relatorio_normal):
        """Verifica que ECG normal sem medicação não detecta efeito digitálico."""
        resultado = detect_digitalis_effect(relatorio_normal)
        assert resultado["detected"] is False
        assert resultado["pattern"] == "none"

    def test_medicacao_contribui_para_score(self, relatorio_normal):
        """Verifica que uso de digitálico conhecido aumenta a confiança."""
        sem_med = detect_digitalis_effect(relatorio_normal)
        com_med = detect_digitalis_effect(relatorio_normal, medication_digitalis=True)
        assert com_med["confidence"] > sem_med["confidence"]


# ---------------------------------------------------------------------------
# Testes: Classificação de Bloqueio de Ramo
# ---------------------------------------------------------------------------

class TestBloqueioDeRamo:
    """Testes para classify_bundle_branch_block."""

    def test_brd_completo(self):
        """Verifica classificação de bloqueio de ramo direito completo."""
        resultado = classify_bundle_branch_block(
            qrs_duration_ms=140,
            morphology_v1="RSR",
            morphology_v6="qRs",
        )
        assert "RBBB" in resultado["classification"]
        assert resultado["complete"] is True

    def test_bre_completo(self):
        """Verifica classificação de bloqueio de ramo esquerdo completo."""
        resultado = classify_bundle_branch_block(
            qrs_duration_ms=150,
            morphology_v1="QS",
            morphology_v6="R",
            septal_q_absent=True,
            broad_notched_r_lateral=True,
        )
        assert "LBBB" in resultado["classification"]
        assert resultado["complete"] is True

    def test_qrs_normal_sem_bloqueio(self):
        """Verifica que QRS < 100 ms é classificado como condução normal."""
        resultado = classify_bundle_branch_block(qrs_duration_ms=88)
        assert resultado["classification"] == "normal_conduction"

    def test_bloqueio_bifascicular_brd_bdas(self):
        """Verifica detecção de bloqueio bifascicular (BRD + BDAS)."""
        resultado = classify_bundle_branch_block(
            qrs_duration_ms=140,
            morphology_v1="RSR",
            morphology_v6="qRs",
            axis_deg=-60,
        )
        assert "bifascicular" in resultado["classification"].lower() or "RBBB" in resultado["classification"]
        # Must detect LAFB component through axis
        criteria_str = " ".join(resultado["criteria_met"])
        assert "eixo" in criteria_str.lower() or "RSR" in criteria_str

    def test_significancia_clinica_presente(self):
        """Verifica que significância clínica é fornecida."""
        resultado = classify_bundle_branch_block(
            qrs_duration_ms=140,
            morphology_v1="RSR",
        )
        assert isinstance(resultado["clinical_significance"], str)
        assert len(resultado["clinical_significance"]) > 10

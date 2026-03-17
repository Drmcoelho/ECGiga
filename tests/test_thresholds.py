"""Testes abrangentes para o módulo de limiares ajustados por sexo e idade.

Verifica limiares de STEMI, QTc, frequência cardíaca, intervalo PR, duração
do QRS e avaliação de medidas para diferentes grupos demográficos
(pediátricos, adultos, idosos, atletas, masculino, feminino).
"""

from __future__ import annotations

import pytest

from pathology.thresholds import (
    evaluate_measurement,
    get_adjusted_thresholds,
    get_qtc_thresholds,
    get_stemi_criteria,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def limiares_homem_adulto():
    """Limiares ajustados para homem adulto de 50 anos."""
    return get_adjusted_thresholds(age=50, sex="M")


@pytest.fixture
def limiares_mulher_adulta():
    """Limiares ajustados para mulher adulta de 50 anos."""
    return get_adjusted_thresholds(age=50, sex="F")


@pytest.fixture
def limiares_homem_jovem():
    """Limiares ajustados para homem jovem de 25 anos."""
    return get_adjusted_thresholds(age=25, sex="M")


@pytest.fixture
def limiares_crianca():
    """Limiares ajustados para criança de 8 anos."""
    return get_adjusted_thresholds(age=8, sex="M")


@pytest.fixture
def limiares_idoso():
    """Limiares ajustados para paciente idoso de 75 anos."""
    return get_adjusted_thresholds(age=75, sex="M")


@pytest.fixture
def limiares_neonato():
    """Limiares ajustados para neonato."""
    return get_adjusted_thresholds(age=0, sex="M")


@pytest.fixture
def limiares_atleta():
    """Limiares ajustados para atleta adulto."""
    return get_adjusted_thresholds(age=30, sex="M", is_athlete=True)


# ---------------------------------------------------------------------------
# Testes: get_adjusted_thresholds por grupo etário
# ---------------------------------------------------------------------------

class TestLimiaresAjustadosPorIdade:
    """Testes para get_adjusted_thresholds com diferentes faixas etárias."""

    def test_grupo_etario_adulto(self, limiares_homem_adulto):
        """Verifica que idade 50 é classificada como adulto."""
        assert limiares_homem_adulto["age_group"] == "adult"

    def test_grupo_etario_crianca(self, limiares_crianca):
        """Verifica que idade 8 é classificada como child."""
        assert limiares_crianca["age_group"] == "child"

    def test_grupo_etario_idoso(self, limiares_idoso):
        """Verifica que idade 75 é classificada como elderly."""
        assert limiares_idoso["age_group"] == "elderly"

    def test_grupo_etario_neonato(self, limiares_neonato):
        """Verifica que idade 0 é classificada como neonate."""
        assert limiares_neonato["age_group"] == "neonate"

    def test_hr_pediatrico_vs_adulto(self, limiares_crianca, limiares_homem_adulto):
        """Verifica que FC normal em crianças é mais alta que em adultos."""
        hr_crianca_low, hr_crianca_high = limiares_crianca["hr_range"]
        hr_adulto_low, hr_adulto_high = limiares_homem_adulto["hr_range"]
        assert hr_crianca_high > hr_adulto_high
        assert hr_crianca_low > hr_adulto_low

    def test_qrs_upper_pediatrico_menor_que_adulto(self, limiares_crianca, limiares_homem_adulto):
        """Verifica que limite de QRS é menor em crianças que em adultos."""
        assert limiares_crianca["qrs_upper_ms"] < limiares_homem_adulto["qrs_upper_ms"]

    def test_pr_range_pediatrico_mais_curto(self, limiares_neonato, limiares_homem_adulto):
        """Verifica que intervalo PR normal em neonatos é mais curto."""
        pr_neo_low, pr_neo_high = limiares_neonato["pr_range_ms"]
        pr_adulto_low, pr_adulto_high = limiares_homem_adulto["pr_range_ms"]
        assert pr_neo_high < pr_adulto_high

    def test_atleta_hr_range_mais_baixo(self, limiares_atleta, limiares_homem_adulto):
        """Verifica que atletas têm limite inferior de FC mais baixo."""
        hr_atleta_low, _ = limiares_atleta["hr_range"]
        hr_adulto_low, _ = limiares_homem_adulto["hr_range"]
        assert hr_atleta_low < hr_adulto_low

    def test_idade_none_usa_adulto(self):
        """Verifica que idade None retorna limiares de adulto."""
        resultado = get_adjusted_thresholds(age=None)
        assert resultado["age_group"] == "adult"


# ---------------------------------------------------------------------------
# Testes: get_stemi_criteria por sexo e idade
# ---------------------------------------------------------------------------

class TestCriteriosSTEMI:
    """Testes para get_stemi_criteria em diferentes derivações e demografias."""

    def test_v2v3_homem_ge40_limiar_0_2(self):
        """Verifica que homem >= 40 anos usa limiar de 0.2 mV em V2-V3."""
        assert get_stemi_criteria("V2", sex="M", age=50) == 0.2

    def test_v2v3_homem_lt40_limiar_0_25(self):
        """Verifica que homem < 40 anos usa limiar mais alto (0.25 mV) em V2-V3."""
        assert get_stemi_criteria("V2", sex="M", age=25) == 0.25

    def test_v2v3_mulher_limiar_0_15(self):
        """Verifica que mulheres usam limiar mais baixo (0.15 mV) em V2-V3."""
        assert get_stemi_criteria("V3", sex="F") == 0.15

    def test_v2v3_diferencas_por_sexo_e_idade(self):
        """Verifica que limiares diferem entre homem jovem, homem velho e mulher."""
        homem_jovem = get_stemi_criteria("V2", sex="M", age=25)
        homem_velho = get_stemi_criteria("V2", sex="M", age=50)
        mulher = get_stemi_criteria("V2", sex="F", age=50)
        assert homem_jovem > homem_velho > mulher

    def test_outras_derivacoes_limiar_0_1(self):
        """Verifica que derivações fora de V2-V3 usam limiar padrão de 0.1 mV."""
        for lead in ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V4", "V5", "V6"]:
            assert get_stemi_criteria(lead, sex="M", age=50) == 0.1

    def test_derivacoes_posteriores_limiar_0_05(self):
        """Verifica limiar reduzido (0.05 mV) para derivações posteriores."""
        for lead in ["V7", "V8", "V9"]:
            assert get_stemi_criteria(lead) == 0.05

    def test_derivacoes_direitas_limiar_0_05(self):
        """Verifica limiar de 0.05 mV para derivações direitas (V3R-V6R)."""
        for lead in ["V3R", "V4R", "V5R", "V6R"]:
            assert get_stemi_criteria(lead) == 0.05

    def test_sexo_none_usa_limiar_conservador(self):
        """Verifica que sexo desconhecido usa o limiar mais conservador."""
        valor_desconhecido = get_stemi_criteria("V2", sex=None)
        valor_homem_ge40 = get_stemi_criteria("V2", sex="M", age=50)
        assert valor_desconhecido == valor_homem_ge40


# ---------------------------------------------------------------------------
# Testes: get_qtc_thresholds por sexo
# ---------------------------------------------------------------------------

class TestLimiaresQTc:
    """Testes para get_qtc_thresholds."""

    def test_homem_normal_upper_450(self):
        """Verifica que limite superior normal para homens é 450 ms."""
        thresholds = get_qtc_thresholds(sex="M")
        assert thresholds["normal_upper"] == 450

    def test_mulher_normal_upper_460(self):
        """Verifica que limite superior normal para mulheres é 460 ms."""
        thresholds = get_qtc_thresholds(sex="F")
        assert thresholds["normal_upper"] == 460

    def test_diferenca_sexo_qtc(self):
        """Verifica que mulheres têm limiar QTc normal mais alto que homens."""
        masc = get_qtc_thresholds(sex="M")
        fem = get_qtc_thresholds(sex="F")
        assert fem["normal_upper"] > masc["normal_upper"]

    def test_prolonged_threshold_igual(self):
        """Verifica que limiar de alto risco (prolonged) é 500 ms para ambos."""
        masc = get_qtc_thresholds(sex="M")
        fem = get_qtc_thresholds(sex="F")
        assert masc["prolonged"] == 500
        assert fem["prolonged"] == 500

    def test_short_qt_threshold(self):
        """Verifica que limiar de QTc curto é 340 ms."""
        thresholds = get_qtc_thresholds(sex="M")
        assert thresholds["short_lower"] == 340
        assert thresholds["short_concerning"] == 320

    def test_sexo_desconhecido_retorna_valores(self):
        """Verifica que sexo None retorna limiares válidos."""
        thresholds = get_qtc_thresholds(sex=None)
        assert "normal_upper" in thresholds
        assert "prolonged" in thresholds

    def test_retorna_campos_completos(self):
        """Verifica que todos os campos esperados estão presentes."""
        thresholds = get_qtc_thresholds(sex="M")
        campos = {"normal_upper", "borderline", "prolonged", "short_lower", "short_concerning"}
        assert campos == set(thresholds.keys())


# ---------------------------------------------------------------------------
# Testes: evaluate_measurement
# ---------------------------------------------------------------------------

class TestAvaliacaoMedida:
    """Testes para evaluate_measurement com diferentes parâmetros."""

    def test_fc_normal_adulto(self):
        """Verifica que FC 75 bpm é normal para adulto."""
        resultado = evaluate_measurement("heart_rate", 75, age=40, sex="M")
        assert resultado["status"] == "normal"

    def test_fc_bradicardia_adulto(self):
        """Verifica que FC 45 bpm é baixa para adulto."""
        resultado = evaluate_measurement("heart_rate", 45, age=40, sex="M")
        assert resultado["status"] == "low"

    def test_fc_taquicardia_adulto(self):
        """Verifica que FC 120 bpm é alta para adulto."""
        resultado = evaluate_measurement("heart_rate", 120, age=40, sex="M")
        assert resultado["status"] == "high"

    def test_fc_critica_muito_alta(self):
        """Verifica que FC > 150 bpm é crítica para adulto."""
        resultado = evaluate_measurement("heart_rate", 160, age=40, sex="M")
        assert resultado["status"] == "critical"

    def test_pr_normal(self):
        """Verifica que PR 160 ms é normal para adulto."""
        resultado = evaluate_measurement("pr_interval", 160, age=40)
        assert resultado["status"] == "normal"

    def test_pr_prolongado(self):
        """Verifica que PR 220 ms é alto para adulto (BAV 1o grau)."""
        resultado = evaluate_measurement("pr_interval", 220, age=40)
        assert resultado["status"] == "high"

    def test_pr_curto(self):
        """Verifica que PR 100 ms é baixo para adulto (pré-excitação)."""
        resultado = evaluate_measurement("pr_interval", 100, age=40)
        assert resultado["status"] == "low"

    def test_qrs_normal(self):
        """Verifica que QRS 90 ms é normal para adulto."""
        resultado = evaluate_measurement("qrs_duration", 90, age=40)
        assert resultado["status"] == "normal"

    def test_qrs_alargado(self):
        """Verifica que QRS 130 ms é alto para adulto (bloqueio de ramo)."""
        resultado = evaluate_measurement("qrs_duration", 130, age=40)
        assert resultado["status"] == "high"

    def test_qrs_muito_alargado_critico(self):
        """Verifica que QRS > 160 ms é crítico para adulto."""
        resultado = evaluate_measurement("qrs_duration", 170, age=40)
        assert resultado["status"] == "critical"

    def test_qtc_normal_homem(self):
        """Verifica que QTc 430 ms é normal para homem."""
        resultado = evaluate_measurement("qtc", 430, age=40, sex="M")
        assert resultado["status"] == "normal"

    def test_qtc_prolongado_homem(self):
        """Verifica que QTc 470 ms é alto para homem."""
        resultado = evaluate_measurement("qtc", 470, age=40, sex="M")
        assert resultado["status"] == "high"

    def test_qtc_critico(self):
        """Verifica que QTc > 500 ms é crítico (risco de Torsades)."""
        resultado = evaluate_measurement("qtc", 520, age=40, sex="M")
        assert resultado["status"] == "critical"

    def test_qtc_curto(self):
        """Verifica que QTc < 340 ms é baixo (QT curto)."""
        resultado = evaluate_measurement("qtc", 320, age=40, sex="M")
        assert resultado["status"] == "low"

    def test_medida_desconhecida(self):
        """Verifica que medida desconhecida retorna status unknown."""
        resultado = evaluate_measurement("axis_deviation", 60, age=40)
        assert resultado["status"] == "unknown"

    def test_reference_range_presente(self):
        """Verifica que reference_range é string descritiva."""
        resultado = evaluate_measurement("heart_rate", 75, age=40, sex="M")
        assert isinstance(resultado["reference_range"], str)
        assert "bpm" in resultado["reference_range"]

    def test_details_contem_informacao_demografica(self):
        """Verifica que details menciona grupo etário e sexo."""
        resultado = evaluate_measurement("heart_rate", 75, age=40, sex="M")
        assert "adult" in resultado["details"]
        assert "male" in resultado["details"]


# ---------------------------------------------------------------------------
# Testes: Comparações entre grupos demográficos
# ---------------------------------------------------------------------------

class TestComparacoesDemograficas:
    """Testes comparativos entre diferentes grupos demográficos."""

    def test_limiares_pediatrico_vs_adulto_vs_idoso(self):
        """Verifica que limiares diferem adequadamente entre faixas etárias."""
        pediatrico = get_adjusted_thresholds(age=8, sex="M")
        adulto = get_adjusted_thresholds(age=40, sex="M")
        idoso = get_adjusted_thresholds(age=75, sex="M")

        # FC: pediatric high > adult high
        assert pediatrico["hr_range"][1] > adulto["hr_range"][1]
        # QRS: pediatric upper < adult upper
        assert pediatrico["qrs_upper_ms"] <= adulto["qrs_upper_ms"]
        # PR: idoso pode ter PR mais longo
        assert idoso["pr_range_ms"][1] >= adulto["pr_range_ms"][1]

    def test_stemi_v2v3_mais_conservador_mulher(self):
        """Verifica que mulheres têm limiar STEMI mais baixo em V2-V3."""
        homem = get_adjusted_thresholds(age=50, sex="M")
        mulher = get_adjusted_thresholds(age=50, sex="F")
        assert mulher["stemi_v2v3_mv"] < homem["stemi_v2v3_mv"]

    def test_stemi_other_leads_igual_para_todos(self):
        """Verifica que limiar STEMI em outras derivações é igual para todos."""
        homem = get_adjusted_thresholds(age=50, sex="M")
        mulher = get_adjusted_thresholds(age=50, sex="F")
        crianca = get_adjusted_thresholds(age=8, sex="M")
        assert homem["stemi_other_mv"] == mulher["stemi_other_mv"] == crianca["stemi_other_mv"]

    def test_adolescente_entre_crianca_e_adulto(self):
        """Verifica que limiares de adolescente são intermediários."""
        crianca = get_adjusted_thresholds(age=8, sex="M")
        adolescente = get_adjusted_thresholds(age=15, sex="M")
        adulto = get_adjusted_thresholds(age=30, sex="M")

        assert adolescente["age_group"] == "adolescent"
        # QRS upper: child <= adolescent <= adult
        assert crianca["qrs_upper_ms"] <= adolescente["qrs_upper_ms"] <= adulto["qrs_upper_ms"]

"""Testes abrangentes para o módulo de processamento de sinais ECG.

Verifica filtros digitais (passa-banda, passa-alta, passa-baixa, notch),
remoção de oscilação de linha de base, detecção de ruído, estimativa de SNR,
índice de qualidade do sinal e pipeline completo de pré-processamento.
"""

from __future__ import annotations

import numpy as np
import pytest

from signal_processing.filters import (
    bandpass_filter,
    highpass_filter,
    lowpass_filter,
    notch_filter,
    remove_baseline_wander,
)
from signal_processing.noise import (
    detect_noise_segments,
    estimate_snr,
    signal_quality_index,
)
from signal_processing.preprocessing import preprocess_ecg


# ---------------------------------------------------------------------------
# Fixtures - Sinais sintéticos
# ---------------------------------------------------------------------------

@pytest.fixture
def fs():
    """Frequência de amostragem padrão (500 Hz)."""
    return 500.0


@pytest.fixture
def sinal_senoidal_1hz(fs):
    """Sinal senoidal limpo a 1 Hz simulando ritmo cardíaco basal (5 segundos)."""
    duracao = 5.0
    t = np.arange(0, duracao, 1.0 / fs)
    sinal = np.sin(2 * np.pi * 1.0 * t)
    return sinal


@pytest.fixture
def sinal_ecg_sintetico(fs):
    """Sinal ECG sintético com componente QRS a ~1 Hz e onda T a ~3 Hz.

    Duração de 5 segundos, simulando morfologia básica de ECG.
    """
    duracao = 5.0
    t = np.arange(0, duracao, 1.0 / fs)
    # QRS-like: pico a 1 Hz
    qrs = 1.0 * np.sin(2 * np.pi * 1.0 * t)
    # Componente T-wave: pequena contribuição a 3 Hz
    onda_t = 0.3 * np.sin(2 * np.pi * 3.0 * t)
    # Componente de alta frequência QRS (10 Hz)
    hf_qrs = 0.2 * np.sin(2 * np.pi * 10.0 * t)
    return qrs + onda_t + hf_qrs


@pytest.fixture
def sinal_com_dc_offset(sinal_ecg_sintetico):
    """Sinal ECG com componente DC (offset de linha de base) de 2.0 mV."""
    return sinal_ecg_sintetico + 2.0


@pytest.fixture
def sinal_com_ruido_60hz(sinal_ecg_sintetico, fs):
    """Sinal ECG contaminado com interferência da rede elétrica (60 Hz)."""
    t = np.arange(len(sinal_ecg_sintetico)) / fs
    interferencia = 0.5 * np.sin(2 * np.pi * 60.0 * t)
    return sinal_ecg_sintetico + interferencia


@pytest.fixture
def sinal_com_baseline_wander(sinal_ecg_sintetico, fs):
    """Sinal ECG com oscilação de linha de base a 0.3 Hz."""
    t = np.arange(len(sinal_ecg_sintetico)) / fs
    wander = 1.5 * np.sin(2 * np.pi * 0.3 * t)
    return sinal_ecg_sintetico + wander


@pytest.fixture
def sinal_com_ruido_alta_frequencia(sinal_ecg_sintetico, fs):
    """Sinal ECG com ruído de alta frequência (EMG-like a 200 Hz)."""
    t = np.arange(len(sinal_ecg_sintetico)) / fs
    ruido_hf = 0.3 * np.sin(2 * np.pi * 200.0 * t)
    return sinal_ecg_sintetico + ruido_hf


@pytest.fixture
def sinal_multicanal(sinal_ecg_sintetico, fs):
    """Sinal ECG com 3 derivações (multi-lead) como array 2D [amostras, derivações]."""
    t = np.arange(len(sinal_ecg_sintetico)) / fs
    lead2 = sinal_ecg_sintetico * 0.8 + 0.1 * np.sin(2 * np.pi * 2.0 * t)
    lead3 = sinal_ecg_sintetico * 0.6 + 0.15 * np.sin(2 * np.pi * 4.0 * t)
    return np.column_stack([sinal_ecg_sintetico, lead2, lead3])


@pytest.fixture
def sinal_limpo_longo(fs):
    """Sinal ECG limpo de 10 segundos para avaliação de qualidade."""
    duracao = 10.0
    t = np.arange(0, duracao, 1.0 / fs)
    # Simula batimentos cardíacos a ~75 bpm (1.25 Hz)
    sinal = np.zeros_like(t)
    rr = 0.8  # 75 bpm
    beat_time = 0.2
    while beat_time < duracao - 0.5:
        idx = int(beat_time * fs)
        # QRS spike
        qrs_half = int(0.02 * fs)
        for j in range(-qrs_half, qrs_half):
            i = idx + j
            if 0 <= i < len(sinal):
                sinal[i] += 1.0 * np.exp(-0.5 * (j / (qrs_half * 0.3)) ** 2)
        # T wave
        t_center = idx + int(0.25 * fs)
        t_half = int(0.06 * fs)
        for j in range(-t_half, t_half):
            i = t_center + j
            if 0 <= i < len(sinal):
                sinal[i] += 0.3 * np.exp(-0.5 * (j / (t_half * 0.4)) ** 2)
        beat_time += rr
    return sinal


# ---------------------------------------------------------------------------
# Testes: Filtro Passa-Banda (bandpass_filter)
# ---------------------------------------------------------------------------

class TestFiltroBandpass:
    """Testes para o filtro passa-banda Butterworth."""

    def test_preserva_componente_dentro_da_banda(self, fs):
        """Verifica que frequências dentro da banda passante são preservadas."""
        duracao = 5.0
        t = np.arange(0, duracao, 1.0 / fs)
        # Sinal a 10 Hz — dentro da banda [0.5, 40]
        sinal = np.sin(2 * np.pi * 10.0 * t)
        filtrado = bandpass_filter(sinal, fs, lowcut=0.5, highcut=40.0)
        # A amplitude do sinal filtrado deve ser próxima da original
        assert np.max(np.abs(filtrado)) > 0.8

    def test_atenua_frequencia_fora_da_banda(self, fs):
        """Verifica que frequências fora da banda são atenuadas."""
        duracao = 5.0
        t = np.arange(0, duracao, 1.0 / fs)
        # Sinal a 200 Hz — acima da banda [0.5, 40]
        sinal = np.sin(2 * np.pi * 200.0 * t)
        filtrado = bandpass_filter(sinal, fs, lowcut=0.5, highcut=40.0)
        # A potência da saída deve ser muito menor que a entrada
        potencia_entrada = np.mean(sinal ** 2)
        potencia_saida = np.mean(filtrado ** 2)
        assert potencia_saida < 0.05 * potencia_entrada

    def test_aceita_sinal_2d_multicanal(self, sinal_multicanal, fs):
        """Verifica que o filtro processa corretamente sinais multi-derivação."""
        filtrado = bandpass_filter(sinal_multicanal, fs, lowcut=0.5, highcut=40.0)
        assert filtrado.shape == sinal_multicanal.shape

    def test_formato_saida_igual_entrada(self, sinal_ecg_sintetico, fs):
        """Verifica que a forma do array de saída é igual à entrada."""
        filtrado = bandpass_filter(sinal_ecg_sintetico, fs)
        assert filtrado.shape == sinal_ecg_sintetico.shape
        assert filtrado.dtype == sinal_ecg_sintetico.dtype


# ---------------------------------------------------------------------------
# Testes: Filtro Passa-Alta (highpass_filter)
# ---------------------------------------------------------------------------

class TestFiltroPassaAlta:
    """Testes para o filtro passa-alta (remoção de DC e baixas frequências)."""

    def test_remove_componente_dc(self, sinal_com_dc_offset, fs):
        """Verifica que o filtro passa-alta remove offset DC."""
        filtrado = highpass_filter(sinal_com_dc_offset, fs, cutoff=0.5)
        # A média do sinal filtrado deve ser próxima de zero
        assert abs(np.mean(filtrado)) < 0.2

    def test_preserva_componente_ecg(self, fs):
        """Verifica que componentes de ECG (1-40 Hz) são preservadas."""
        duracao = 5.0
        t = np.arange(0, duracao, 1.0 / fs)
        sinal = np.sin(2 * np.pi * 10.0 * t) + 3.0  # 10 Hz + DC
        filtrado = highpass_filter(sinal, fs, cutoff=0.5)
        # Componente de 10 Hz deve permanecer
        assert np.std(filtrado) > 0.5


# ---------------------------------------------------------------------------
# Testes: Filtro Passa-Baixa (lowpass_filter)
# ---------------------------------------------------------------------------

class TestFiltroPassaBaixa:
    """Testes para o filtro passa-baixa (remoção de ruído de alta frequência)."""

    def test_remove_ruido_alta_frequencia(self, sinal_com_ruido_alta_frequencia, fs):
        """Verifica que ruído de alta frequência (200 Hz) é removido."""
        filtrado = lowpass_filter(sinal_com_ruido_alta_frequencia, fs, cutoff=40.0)
        # Calcula potência na faixa de ruído usando FFT
        n = len(filtrado)
        freqs = np.fft.rfftfreq(n, d=1.0 / fs)
        fft_filtrado = np.abs(np.fft.rfft(filtrado))
        # Potência acima de 150 Hz deve ser desprezível
        hf_mask = freqs > 150
        potencia_hf = np.mean(fft_filtrado[hf_mask] ** 2)
        potencia_total = np.mean(fft_filtrado ** 2)
        assert potencia_hf < 0.01 * potencia_total

    def test_preserva_componente_baixa_frequencia(self, fs):
        """Verifica que componentes de baixa frequência passam pelo filtro."""
        duracao = 5.0
        t = np.arange(0, duracao, 1.0 / fs)
        sinal = np.sin(2 * np.pi * 5.0 * t)
        filtrado = lowpass_filter(sinal, fs, cutoff=40.0)
        assert np.max(np.abs(filtrado)) > 0.8


# ---------------------------------------------------------------------------
# Testes: Filtro Notch (notch_filter)
# ---------------------------------------------------------------------------

class TestFiltroNotch:
    """Testes para o filtro notch de remoção de interferência da rede elétrica."""

    def test_remove_interferencia_60hz(self, sinal_com_ruido_60hz, sinal_ecg_sintetico, fs):
        """Verifica que o filtro notch remove a componente de 60 Hz."""
        filtrado = notch_filter(sinal_com_ruido_60hz, fs, freq=60.0)
        # O sinal filtrado deve se aproximar do sinal limpo original
        correlacao = np.corrcoef(filtrado, sinal_ecg_sintetico)[0, 1]
        assert correlacao > 0.9

    def test_remove_interferencia_50hz(self, sinal_ecg_sintetico, fs):
        """Verifica remoção de interferência a 50 Hz (padrão europeu/Brasil)."""
        t = np.arange(len(sinal_ecg_sintetico)) / fs
        contaminado = sinal_ecg_sintetico + 0.5 * np.sin(2 * np.pi * 50.0 * t)
        filtrado = notch_filter(contaminado, fs, freq=50.0)
        correlacao = np.corrcoef(filtrado, sinal_ecg_sintetico)[0, 1]
        assert correlacao > 0.9

    def test_preserva_sinal_sem_interferencia(self, sinal_ecg_sintetico, fs):
        """Verifica que o notch não distorce sinal sem interferência de rede."""
        filtrado = notch_filter(sinal_ecg_sintetico, fs, freq=60.0)
        correlacao = np.corrcoef(filtrado, sinal_ecg_sintetico)[0, 1]
        assert correlacao > 0.95


# ---------------------------------------------------------------------------
# Testes: Remoção de Oscilação de Linha de Base
# ---------------------------------------------------------------------------

class TestRemocaoBaselineWander:
    """Testes para remove_baseline_wander com métodos highpass e median."""

    def test_metodo_highpass_remove_wander(self, sinal_com_baseline_wander, sinal_ecg_sintetico, fs):
        """Verifica que o método highpass remove oscilação de linha de base."""
        filtrado = remove_baseline_wander(
            sinal_com_baseline_wander, fs, method="highpass", cutoff=0.5
        )
        # O wander (0.3 Hz) deve ser substancialmente reduzido
        # Correlação com sinal limpo deve ser alta
        correlacao = np.corrcoef(filtrado, sinal_ecg_sintetico)[0, 1]
        assert correlacao > 0.85

    def test_metodo_median_remove_wander(self, sinal_com_baseline_wander, sinal_ecg_sintetico, fs):
        """Verifica que o método median remove oscilação de linha de base."""
        filtrado = remove_baseline_wander(
            sinal_com_baseline_wander, fs, method="median", window_s=0.6
        )
        # A média do sinal filtrado deve ser mais próxima de zero
        assert abs(np.mean(filtrado)) < abs(np.mean(sinal_com_baseline_wander))

    def test_metodo_invalido_levanta_erro(self, sinal_ecg_sintetico, fs):
        """Verifica que método desconhecido levanta ValueError."""
        with pytest.raises(ValueError, match="Unknown method"):
            remove_baseline_wander(sinal_ecg_sintetico, fs, method="wavelet")


# ---------------------------------------------------------------------------
# Testes: Detecção de Segmentos Ruidosos
# ---------------------------------------------------------------------------

class TestDeteccaoRuido:
    """Testes para detect_noise_segments."""

    def test_sinal_limpo_sem_segmentos_alta_variancia(self, sinal_limpo_longo, fs):
        """Verifica que sinal limpo não gera detecções de alta variância."""
        # Adiciona pequeno ruído de fundo para evitar detecções falsas de flatline/saturation
        rng = np.random.default_rng(42)
        sinal = sinal_limpo_longo + rng.normal(0, 0.01, size=len(sinal_limpo_longo))
        segmentos = detect_noise_segments(sinal, fs)
        # Não deve ter segmentos de alta variância
        hv_segs = [s for s in segmentos if s["noise_type"] == "high_variance"]
        assert len(hv_segs) == 0

    def test_sinal_ruidoso_detecta_alta_variancia(self, sinal_limpo_longo, fs):
        """Verifica detecção de segmentos com alta variância (artefato muscular)."""
        sinal = sinal_limpo_longo.copy()
        # Injeta ruído intenso no meio do sinal
        inicio = int(3.0 * fs)
        fim = int(4.0 * fs)
        sinal[inicio:fim] += np.random.randn(fim - inicio) * 10.0
        segmentos = detect_noise_segments(sinal, fs)
        # Deve detectar pelo menos um segmento ruidoso
        assert len(segmentos) > 0
        tipos = [s["noise_type"] for s in segmentos]
        assert "high_variance" in tipos or "spike" in tipos

    def test_retorna_estrutura_correta(self, sinal_limpo_longo, fs):
        """Verifica que cada segmento tem os campos esperados."""
        segmentos = detect_noise_segments(sinal_limpo_longo, fs)
        campos_obrigatorios = {"start_sample", "end_sample", "start_s", "end_s", "noise_type", "severity"}
        for seg in segmentos:
            assert campos_obrigatorios.issubset(seg.keys())

    def test_sinal_1d_obrigatorio(self, sinal_multicanal, fs):
        """Verifica que sinal 2D levanta ValueError."""
        with pytest.raises(ValueError, match="1D"):
            detect_noise_segments(sinal_multicanal, fs)


# ---------------------------------------------------------------------------
# Testes: Estimativa de SNR
# ---------------------------------------------------------------------------

class TestEstimativaSNR:
    """Testes para estimate_snr."""

    def test_snr_sinal_limpo_alto(self, sinal_limpo_longo, fs):
        """Verifica que sinal limpo tem SNR relativamente alto."""
        snr = estimate_snr(sinal_limpo_longo, fs)
        # Sinal limpo sem ruído de alta frequência deve ter SNR positivo
        assert isinstance(snr, float)
        assert snr > 0  # Deve ser positivo em dB

    def test_snr_sinal_ruidoso_menor(self, sinal_limpo_longo, fs):
        """Verifica que sinal ruidoso tem SNR menor que sinal limpo."""
        snr_limpo = estimate_snr(sinal_limpo_longo, fs)
        # Adiciona ruído de alta frequência (simulando EMG)
        ruidoso = sinal_limpo_longo + np.random.randn(len(sinal_limpo_longo)) * 2.0
        snr_ruidoso = estimate_snr(ruidoso, fs)
        assert snr_ruidoso < snr_limpo

    def test_snr_retorna_float_em_db(self, sinal_limpo_longo, fs):
        """Verifica que o retorno é um float representando dB."""
        snr = estimate_snr(sinal_limpo_longo, fs)
        assert isinstance(snr, float)
        # Valores típicos de SNR estão entre -20 e +40 dB
        assert -30 < snr < 60

    def test_sinal_curto_levanta_erro(self, fs):
        """Verifica que sinal muito curto levanta ValueError."""
        sinal_curto = np.sin(np.arange(50) / fs)
        with pytest.raises(ValueError, match="at least 2 seconds"):
            estimate_snr(sinal_curto, fs)

    def test_sinal_2d_levanta_erro(self, sinal_multicanal, fs):
        """Verifica que sinal 2D não é aceito para estimativa de SNR."""
        with pytest.raises(ValueError, match="1D"):
            estimate_snr(sinal_multicanal, fs)


# ---------------------------------------------------------------------------
# Testes: Índice de Qualidade do Sinal (SQI)
# ---------------------------------------------------------------------------

class TestIndiceQualidadeSinal:
    """Testes para signal_quality_index."""

    def test_retorna_estrutura_completa(self, sinal_limpo_longo, fs):
        """Verifica que o dicionário retornado contém todos os campos obrigatórios."""
        resultado = signal_quality_index(sinal_limpo_longo, fs)
        campos = {"sqi_score", "snr_db", "noise_segments", "noise_fraction",
                  "has_baseline_wander", "has_powerline_interference",
                  "quality_label", "details"}
        assert campos.issubset(resultado.keys())

    def test_score_entre_0_e_100(self, sinal_limpo_longo, fs):
        """Verifica que o score SQI está no intervalo [0, 100]."""
        resultado = signal_quality_index(sinal_limpo_longo, fs)
        assert 0 <= resultado["sqi_score"] <= 100

    def test_quality_label_valido(self, sinal_limpo_longo, fs):
        """Verifica que o rótulo de qualidade é um dos valores esperados."""
        resultado = signal_quality_index(sinal_limpo_longo, fs)
        labels_validos = {"excellent", "good", "acceptable", "poor", "unusable"}
        assert resultado["quality_label"] in labels_validos

    def test_sinal_curto_retorna_unusable(self, fs):
        """Verifica que sinal muito curto é classificado como unusable."""
        sinal_curto = np.zeros(int(fs * 0.5))  # 0.5 segundo
        resultado = signal_quality_index(sinal_curto, fs)
        assert resultado["quality_label"] == "unusable"
        assert resultado["sqi_score"] == 0.0

    def test_noise_fraction_entre_0_e_1(self, sinal_limpo_longo, fs):
        """Verifica que noise_fraction está no intervalo [0, 1]."""
        resultado = signal_quality_index(sinal_limpo_longo, fs)
        assert 0 <= resultado["noise_fraction"] <= 1


# ---------------------------------------------------------------------------
# Testes: Pipeline de Pré-processamento
# ---------------------------------------------------------------------------

class TestPipelinePreprocessamento:
    """Testes para preprocess_ecg."""

    def test_modo_diagnostico_aplica_filtros_corretos(self, sinal_ecg_sintetico, fs):
        """Verifica que o modo diagnóstico aplica a sequência correta de filtros."""
        resultado = preprocess_ecg(sinal_ecg_sintetico, fs, mode="diagnostic")
        assert resultado["mode"] == "diagnostic"
        assert "signal" in resultado
        assert len(resultado["steps_applied"]) >= 1

    def test_modo_monitoramento_aplica_filtros_corretos(self, sinal_ecg_sintetico, fs):
        """Verifica que o modo monitoramento usa banda passante mais estreita."""
        resultado = preprocess_ecg(sinal_ecg_sintetico, fs, mode="monitoring")
        assert resultado["mode"] == "monitoring"
        # Deve conter referência a 0.5-40 Hz na descrição dos passos
        steps_str = " ".join(resultado["steps_applied"])
        assert "40" in steps_str

    def test_pipeline_retorna_quality_quando_solicitado(self, sinal_limpo_longo, fs):
        """Verifica que a qualidade é calculada quando compute_quality=True."""
        resultado = preprocess_ecg(sinal_limpo_longo, fs, compute_quality=True)
        assert "quality" in resultado
        assert "sqi_score" in resultado["quality"]

    def test_pipeline_sem_quality(self, sinal_ecg_sintetico, fs):
        """Verifica que a qualidade não é calculada quando compute_quality=False."""
        resultado = preprocess_ecg(sinal_ecg_sintetico, fs, compute_quality=False)
        assert "quality" not in resultado

    def test_pipeline_aceita_sinal_2d(self, sinal_multicanal, fs):
        """Verifica que o pipeline processa sinais multi-derivação."""
        resultado = preprocess_ecg(sinal_multicanal, fs, mode="diagnostic")
        assert resultado["signal"].shape == sinal_multicanal.shape

    def test_modo_invalido_levanta_erro(self, sinal_ecg_sintetico, fs):
        """Verifica que modo desconhecido levanta ValueError."""
        with pytest.raises(ValueError, match="Unknown mode"):
            preprocess_ecg(sinal_ecg_sintetico, fs, mode="ambulatorial")

    def test_sinal_como_lista_e_convertido(self, fs):
        """Verifica que lista Python é convertida para ndarray automaticamente."""
        sinal_lista = [float(np.sin(2 * np.pi * 1.0 * i / fs)) for i in range(int(5 * fs))]
        resultado = preprocess_ecg(sinal_lista, fs, mode="diagnostic")
        assert isinstance(resultado["signal"], np.ndarray)

    def test_pipeline_com_todas_etapas_desabilitadas(self, sinal_ecg_sintetico, fs):
        """Verifica que pipeline sem filtros retorna sinal original."""
        resultado = preprocess_ecg(
            sinal_ecg_sintetico, fs,
            remove_baseline=False,
            remove_powerline=False,
            apply_bandpass=False,
            compute_quality=False,
        )
        assert len(resultado["steps_applied"]) == 0
        np.testing.assert_array_almost_equal(resultado["signal"], sinal_ecg_sintetico)


# ---------------------------------------------------------------------------
# Testes: Validação de Entrada
# ---------------------------------------------------------------------------

class TestValidacaoEntrada:
    """Testes de validação de parâmetros de entrada para os filtros."""

    def test_sinal_nao_numpy_levanta_typeerror(self, fs):
        """Verifica que lista pura (não ndarray) levanta TypeError nos filtros."""
        with pytest.raises(TypeError, match="numpy array"):
            bandpass_filter([1.0, 2.0, 3.0], fs)

    def test_sinal_3d_levanta_valueerror(self, fs):
        """Verifica que array 3D levanta ValueError."""
        sinal_3d = np.zeros((100, 3, 2))
        with pytest.raises(ValueError, match="1D or 2D"):
            bandpass_filter(sinal_3d, fs)

    def test_sinal_muito_curto_levanta_valueerror(self, fs):
        """Verifica que sinal com menos de 10 amostras levanta ValueError."""
        sinal_curto = np.zeros(5)
        with pytest.raises(ValueError, match="too short"):
            bandpass_filter(sinal_curto, fs)

    def test_frequencia_amostragem_negativa_levanta_valueerror(self):
        """Verifica que frequência de amostragem negativa levanta ValueError."""
        sinal = np.zeros(100)
        with pytest.raises(ValueError, match="positive"):
            bandpass_filter(sinal, -100.0)

    def test_lowcut_maior_que_highcut_levanta_erro(self, fs):
        """Verifica que lowcut >= highcut levanta ValueError no bandpass."""
        sinal = np.zeros(500)
        with pytest.raises(ValueError, match="lowcut"):
            bandpass_filter(sinal, fs, lowcut=50.0, highcut=10.0)

    def test_highcut_acima_nyquist_e_clampado(self, fs):
        """Verifica que highcut acima de Nyquist é ajustado automaticamente."""
        sinal = np.sin(np.arange(2500) / fs * 2 * np.pi * 5.0)
        # Não deve levantar erro — highcut é clampado internamente
        filtrado = bandpass_filter(sinal, fs, lowcut=0.5, highcut=300.0)
        assert filtrado.shape == sinal.shape

    def test_cutoff_negativo_levanta_erro_highpass(self, fs):
        """Verifica que cutoff negativo levanta ValueError no highpass."""
        sinal = np.zeros(500)
        with pytest.raises(ValueError, match="positive"):
            highpass_filter(sinal, fs, cutoff=-1.0)

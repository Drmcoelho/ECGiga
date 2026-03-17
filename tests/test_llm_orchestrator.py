"""
Testes para o módulo Multi-LLM orchestrator (mega.llm).

Todos os testes funcionam offline — sem APIs externas.
Refs: GitHub issue #20
"""

from __future__ import annotations

import json

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def offline_backend():
    """Backend offline para testes."""
    from mega.llm.backends import OfflineBackend
    return OfflineBackend()


@pytest.fixture
def verifier():
    """Verificador de casos."""
    from mega.llm.verify import CaseVerifier
    return CaseVerifier(strict=False)


@pytest.fixture
def strict_verifier():
    """Verificador de casos em modo estrito."""
    from mega.llm.verify import CaseVerifier
    return CaseVerifier(strict=True)


@pytest.fixture
def orchestrator():
    """Orquestrador usando apenas backend offline."""
    from mega.llm.orchestrator import CaseOrchestrator
    from mega.llm.backends import OfflineBackend
    offline = OfflineBackend()
    return CaseOrchestrator(
        draft_backend=offline,
        refine_backend=None,
        enable_cache=True,
    )


@pytest.fixture
def sample_valid_case():
    """Caso clínico válido para testes."""
    return {
        "id": "test_case",
        "titulo": "Caso Teste de STEMI Anterior",
        "topico": "STEMI",
        "dificuldade": "hard",
        "historia": (
            "Paciente masculino, 55 anos, tabagista, apresenta dor "
            "torácica retroesternal há 2 horas. PA 100/60 mmHg, FC 100 bpm."
        ),
        "achados_ecg": {
            "ritmo": "Taquicardia sinusal",
            "fc_bpm": 100,
            "eixo": "Normal (60°)",
            "pr_ms": 160,
            "qrs_ms": 90,
            "qtc_ms": 440,
            "st_segment": "Supradesnivelamento de ST em V1-V4",
            "ondas_t": "Ondas T hiperagudas",
            "reciprocidade": "Infra de ST em DII, DIII, aVF",
            "outras": "Sem ondas Q",
        },
        "diagnostico": "IAMCSST anterior — oclusão da DA",
        "perguntas": [
            "Quais derivações mostram supra de ST?",
            "Qual a conduta imediata?",
            "O que indicam as alterações recíprocas?",
        ],
        "explicacao": (
            "O supradesnivelamento de ST em V1-V4 indica lesão transmural "
            "aguda da parede anterior, irrigada pela DA. Conduta: ICP primária."
        ),
    }


@pytest.fixture
def sample_invalid_case():
    """Caso clínico com erros intencionais."""
    return {
        "titulo": "Caso Inválido",
        "historia": "Curta",
        "achados_ecg": {
            "ritmo": "Ritmo sinusal",
            "fc_bpm": 500,  # Impossível
            "qrs_ms": 10,   # Impossível
        },
        "diagnostico": "Bradicardia",  # Incoerente com FC 500
        "perguntas": ["Uma pergunta"],
        "explicacao": "Curta",
    }


# ===========================================================================
# Tests — Templates (mega.llm.templates)
# ===========================================================================

class TestTemplates:
    """Testes para templates de casos clínicos."""

    def test_templates_has_at_least_10(self):
        from mega.llm.templates import TEMPLATES
        assert len(TEMPLATES) >= 10

    def test_each_template_has_required_fields(self):
        from mega.llm.templates import TEMPLATES
        required = ["id", "titulo", "topico", "dificuldade", "historia",
                     "achados_ecg", "diagnostico", "perguntas", "explicacao"]
        for t in TEMPLATES:
            for field in required:
                assert field in t, f"Template '{t.get('id', '?')}' falta campo '{field}'"

    def test_each_template_has_ecg_findings(self):
        from mega.llm.templates import TEMPLATES
        ecg_fields = ["ritmo", "fc_bpm", "qrs_ms"]
        for t in TEMPLATES:
            achados = t["achados_ecg"]
            assert isinstance(achados, dict), f"Template '{t['id']}' achados_ecg não é dict"
            for field in ecg_fields:
                assert field in achados, f"Template '{t['id']}' falta achados_ecg.{field}"

    def test_each_template_has_at_least_2_questions(self):
        from mega.llm.templates import TEMPLATES
        for t in TEMPLATES:
            assert len(t["perguntas"]) >= 2, f"Template '{t['id']}' tem poucas perguntas"

    def test_get_template_no_filter(self):
        from mega.llm.templates import get_template
        t = get_template()
        assert isinstance(t, dict)
        assert "titulo" in t

    def test_get_template_by_topic(self):
        from mega.llm.templates import get_template
        t = get_template(topic="STEMI")
        assert "stemi" in t["topico"].lower() or "stemi" in t["titulo"].lower() or "stemi" in t["id"].lower()

    def test_get_template_by_difficulty(self):
        from mega.llm.templates import get_template
        t = get_template(difficulty="easy")
        assert t["dificuldade"] == "easy"

    def test_get_template_by_topic_and_difficulty(self):
        from mega.llm.templates import get_template
        t = get_template(topic="STEMI", difficulty="hard")
        assert t["dificuldade"] == "hard"

    def test_list_topics(self):
        from mega.llm.templates import list_topics
        topics = list_topics()
        assert isinstance(topics, list)
        assert len(topics) >= 5
        assert "STEMI" in topics

    def test_list_difficulties(self):
        from mega.llm.templates import list_difficulties
        diffs = list_difficulties()
        assert "easy" in diffs
        assert "medium" in diffs
        assert "hard" in diffs

    def test_all_text_is_portuguese(self):
        from mega.llm.templates import TEMPLATES
        # Verificar que títulos e histórias contêm caracteres típicos do Português
        for t in TEMPLATES:
            historia = t["historia"].lower()
            assert any(
                w in historia
                for w in ["paciente", "anos", "apresenta", "com"]
            ), f"Template '{t['id']}' história não parece estar em Português"


# ===========================================================================
# Tests — Offline Backend (mega.llm.backends)
# ===========================================================================

class TestOfflineBackend:
    """Testes para o backend offline."""

    def test_is_always_available(self, offline_backend):
        assert offline_backend.is_available() is True

    def test_name_is_offline(self, offline_backend):
        assert offline_backend.name == "offline"

    def test_generate_returns_json(self, offline_backend):
        result = offline_backend.generate("Tópico: STEMI\nDificuldade: hard")
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_generate_case_returns_dict(self, offline_backend):
        case = offline_backend.generate_case("STEMI", "hard")
        assert isinstance(case, dict)
        assert "titulo" in case
        assert "historia" in case
        assert "achados_ecg" in case
        assert "diagnostico" in case

    def test_generate_case_has_backend_field(self, offline_backend):
        case = offline_backend.generate_case("Fibrilação Atrial")
        assert case.get("backend") == "offline"

    def test_generate_case_various_topics(self, offline_backend):
        topics = ["STEMI", "Bradicardia", "Flutter", "Bloqueio"]
        for topic in topics:
            case = offline_backend.generate_case(topic)
            assert isinstance(case, dict)
            assert "titulo" in case

    def test_generate_case_default_difficulty(self, offline_backend):
        case = offline_backend.generate_case("STEMI")
        assert isinstance(case, dict)

    def test_refine_case_adds_guidelines(self, offline_backend):
        case = {
            "titulo": "Teste",
            "historia": "Paciente masculino, 50 anos.",
            "achados_ecg": {"ritmo": "sinusal", "fc_bpm": 70, "qrs_ms": 90},
            "diagnostico": "Normal",
            "perguntas": ["P1?", "P2?"],
            "explicacao": "Explicação do caso sem menção de protocolos.",
        }
        refined = offline_backend.refine_case(case)
        assert "diretriz" in refined["explicacao"].lower() or "SBC" in refined["explicacao"]

    def test_apply_variations_changes_age(self, offline_backend):
        """Variações devem mudar idade ligeiramente."""
        original = {
            "historia": "Paciente masculino, 50 anos, com dor torácica.",
            "achados_ecg": {"fc_bpm": 80},
        }
        # Aplicar variações múltiplas vezes e verificar que nem sempre é igual
        ages_seen = set()
        for _ in range(20):
            varied = offline_backend._apply_variations(dict(original))
            import re
            match = re.search(r"(\d+)\s*anos", varied["historia"])
            if match:
                ages_seen.add(int(match.group(1)))
        # Com 20 tentativas e variação de +-5, devemos ver mais de 1 idade
        assert len(ages_seen) > 1, f"Variações não alteraram idade: {ages_seen}"


# ===========================================================================
# Tests — Backend Base (parse JSON)
# ===========================================================================

class TestBackendJSONParsing:
    """Testes para parsing de JSON de respostas LLM."""

    def test_parse_clean_json(self, offline_backend):
        text = '{"titulo": "Caso Teste", "historia": "Paciente..."}'
        result = offline_backend._parse_json_response(text)
        assert result["titulo"] == "Caso Teste"

    def test_parse_json_in_markdown(self, offline_backend):
        text = '```json\n{"titulo": "Caso Teste"}\n```'
        result = offline_backend._parse_json_response(text)
        assert result["titulo"] == "Caso Teste"

    def test_parse_json_with_surrounding_text(self, offline_backend):
        text = 'Aqui está o caso:\n{"titulo": "Caso Teste"}\nFim.'
        result = offline_backend._parse_json_response(text)
        assert result["titulo"] == "Caso Teste"

    def test_parse_invalid_json_raises(self, offline_backend):
        with pytest.raises(ValueError, match="Não foi possível extrair JSON"):
            offline_backend._parse_json_response("Texto sem JSON nenhum")


# ===========================================================================
# Tests — Backend availability
# ===========================================================================

class TestBackendAvailability:
    """Testes de disponibilidade dos backends (offline — sem APIs)."""

    def test_ollama_not_available_without_server(self):
        from mega.llm.backends import OllamaBackend
        backend = OllamaBackend(base_url="http://localhost:99999")
        assert backend.is_available() is False

    def test_gemini_not_available_without_key(self):
        import os
        old = os.environ.pop("GEMINI_API_KEY", None)
        try:
            from mega.llm.backends import GeminiBackend
            backend = GeminiBackend(api_key="")
            assert backend.is_available() is False
        finally:
            if old:
                os.environ["GEMINI_API_KEY"] = old

    def test_openai_not_available_without_key(self):
        import os
        old = os.environ.pop("OPENAI_API_KEY", None)
        try:
            from mega.llm.backends import OpenAIBackend
            backend = OpenAIBackend(api_key="")
            assert backend.is_available() is False
        finally:
            if old:
                os.environ["OPENAI_API_KEY"] = old

    def test_offline_always_available(self):
        from mega.llm.backends import OfflineBackend
        assert OfflineBackend().is_available() is True


# ===========================================================================
# Tests — Verification (mega.llm.verify)
# ===========================================================================

class TestCaseVerifier:
    """Testes para o verificador de casos clínicos."""

    def test_valid_case_passes(self, verifier, sample_valid_case):
        result = verifier.verify(sample_valid_case)
        assert result["valid"] is True
        assert result["score"] > 50
        assert len(result["errors"]) == 0

    def test_valid_case_has_disclaimer(self, verifier, sample_valid_case):
        result = verifier.verify(sample_valid_case)
        assert "disclaimer" in result
        assert "educacionais" in result["disclaimer"]
        assert "disclaimer" in result["case"]

    def test_invalid_case_detects_errors(self, verifier, sample_invalid_case):
        result = verifier.verify(sample_invalid_case)
        assert len(result["errors"]) > 0
        assert result["score"] < 80

    def test_invalid_fc_detected(self, verifier, sample_invalid_case):
        result = verifier.verify(sample_invalid_case)
        fc_errors = [e for e in result["errors"] if "fc_bpm" in e.lower() or "frequência" in e.lower()]
        assert len(fc_errors) > 0

    def test_invalid_qrs_detected(self, verifier, sample_invalid_case):
        result = verifier.verify(sample_invalid_case)
        qrs_errors = [e for e in result["errors"] if "qrs" in e.lower()]
        assert len(qrs_errors) > 0

    def test_missing_fields_detected(self, verifier):
        case = {"titulo": "Incompleto"}
        result = verifier.verify(case)
        assert result["valid"] is False
        assert any("obrigatório" in e for e in result["errors"])

    def test_strict_mode_flags_coherence_as_error(self, strict_verifier):
        case = {
            "titulo": "Teste Estrito",
            "historia": "Paciente masculino, 50 anos, assintomático.",
            "achados_ecg": {
                "ritmo": "Ritmo sinusal",
                "fc_bpm": 120,  # Taquicardia
                "qrs_ms": 90,
            },
            "diagnostico": "Bradicardia sinusal",  # Incoerente!
            "perguntas": ["P1?", "P2?"],
            "explicacao": "Explicação detalhada do caso clínico com raciocínio.",
        }
        result = strict_verifier.verify(case)
        # Deve detectar incoerência bradicardia vs FC 120
        coherence_errors = [
            e for e in result["errors"] if "incoerência" in e.lower() or "coerência" in e.lower()
        ]
        assert len(coherence_errors) > 0

    def test_quick_check_valid(self, verifier, sample_valid_case):
        assert verifier.quick_check(sample_valid_case) is True

    def test_quick_check_invalid(self, verifier):
        assert verifier.quick_check({"titulo": "Só título"}) is False

    def test_add_disclaimer(self, verifier):
        case = {"titulo": "Teste"}
        result = verifier.add_disclaimer(case)
        assert "disclaimer" in result
        assert result["titulo"] == "Teste"

    def test_verify_all_templates(self, verifier):
        """Todos os templates pré-definidos devem passar na verificação."""
        from mega.llm.templates import TEMPLATES
        for t in TEMPLATES:
            result = verifier.verify(t)
            assert result["valid"] is True, (
                f"Template '{t['id']}' falhou na verificação: {result['errors']}"
            )
            assert result["score"] >= 50, (
                f"Template '{t['id']}' score baixo: {result['score']}"
            )


# ===========================================================================
# Tests — verify module-level functions
# ===========================================================================

class TestVerifyFunctions:
    """Testes para funções utilitárias de verificação."""

    def test_verify_case_function(self, sample_valid_case):
        from mega.llm.verify import verify_case
        result = verify_case(sample_valid_case)
        assert result["valid"] is True

    def test_validate_ecg_parameters_valid(self):
        from mega.llm.verify import validate_ecg_parameters
        achados = {"fc_bpm": 75, "pr_ms": 160, "qrs_ms": 90, "qtc_ms": 420}
        errors = validate_ecg_parameters(achados)
        assert len(errors) == 0

    def test_validate_ecg_parameters_invalid(self):
        from mega.llm.verify import validate_ecg_parameters
        achados = {"fc_bpm": 500, "qrs_ms": 5}
        errors = validate_ecg_parameters(achados)
        assert len(errors) == 2

    def test_disclaimer_constant(self):
        from mega.llm.verify import DISCLAIMER_PT
        assert "educacionais" in DISCLAIMER_PT
        assert len(DISCLAIMER_PT) > 50


# ===========================================================================
# Tests — Orchestrator (mega.llm.orchestrator)
# ===========================================================================

class TestCaseOrchestrator:
    """Testes para o orquestrador multi-LLM."""

    def test_draft_case_returns_dict(self, orchestrator):
        result = orchestrator.draft_case("STEMI", "hard")
        assert isinstance(result, dict)

    def test_draft_case_has_required_fields(self, orchestrator):
        result = orchestrator.draft_case("STEMI")
        assert "titulo" in result
        assert "historia" in result
        assert "achados_ecg" in result
        assert "diagnostico" in result
        assert "perguntas" in result
        assert "explicacao" in result

    def test_draft_case_has_pipeline_info(self, orchestrator):
        result = orchestrator.draft_case("Fibrilação Atrial")
        assert "pipeline" in result
        pipeline = result["pipeline"]
        assert "draft_backend" in pipeline

    def test_draft_case_has_verification(self, orchestrator):
        result = orchestrator.draft_case("STEMI")
        assert "verification" in result
        v = result["verification"]
        assert "valid" in v
        assert "score" in v
        assert "errors" in v

    def test_draft_case_has_disclaimer(self, orchestrator):
        result = orchestrator.draft_case("STEMI")
        assert "disclaimer" in result
        assert "educacionais" in result["disclaimer"]

    def test_draft_case_various_topics(self, orchestrator):
        topics = ["STEMI", "Bradicardia", "Fibrilação Atrial", "Flutter Atrial"]
        for topic in topics:
            result = orchestrator.draft_case(topic)
            assert isinstance(result, dict)
            assert "titulo" in result

    def test_draft_case_various_difficulties(self, orchestrator):
        for diff in ("easy", "medium", "hard"):
            result = orchestrator.draft_case("STEMI", difficulty=diff)
            assert isinstance(result, dict)

    def test_draft_case_default_language(self, orchestrator):
        result = orchestrator.draft_case("STEMI")
        # Verificar que o conteúdo está em Português
        historia = result.get("historia", "")
        assert any(
            w in historia.lower()
            for w in ["paciente", "anos", "apresenta"]
        )

    def test_cache_works(self, orchestrator):
        orchestrator.draft_case("STEMI", "hard")
        result2 = orchestrator.draft_case("STEMI", "hard")
        assert result2.get("pipeline", {}).get("from_cache") is True
        assert orchestrator.cache_size >= 1

    def test_clear_cache(self, orchestrator):
        orchestrator.draft_case("STEMI")
        assert orchestrator.cache_size >= 1
        orchestrator.clear_cache()
        assert orchestrator.cache_size == 0

    def test_draft_case_offline_method(self, orchestrator):
        result = orchestrator.draft_case_offline("STEMI")
        assert isinstance(result, dict)
        assert result["pipeline"]["draft_backend"] == "offline"
        assert "disclaimer" in result

    def test_get_available_backends(self, orchestrator):
        backends = orchestrator.get_available_backends()
        assert isinstance(backends, dict)
        assert backends["offline"] is True
        assert "ollama" in backends
        assert "gemini" in backends
        assert "openai" in backends

    def test_list_topics(self, orchestrator):
        topics = orchestrator.list_topics()
        assert isinstance(topics, list)
        assert len(topics) >= 5

    def test_orchestrator_without_cache(self):
        from mega.llm.orchestrator import CaseOrchestrator
        from mega.llm.backends import OfflineBackend
        orch = CaseOrchestrator(
            draft_backend=OfflineBackend(),
            refine_backend=None,
            enable_cache=False,
        )
        result = orch.draft_case("STEMI")
        assert isinstance(result, dict)
        assert orch.cache_size == 0


# ===========================================================================
# Tests — Integration (pipeline completo offline)
# ===========================================================================

class TestIntegration:
    """Testes de integração do pipeline completo em modo offline."""

    def test_full_pipeline_stemi(self, orchestrator):
        result = orchestrator.draft_case("STEMI", "hard")
        assert result["verification"]["valid"] is True
        assert result["verification"]["score"] >= 50

    def test_full_pipeline_fa(self, orchestrator):
        result = orchestrator.draft_case("Fibrilação Atrial", "medium")
        assert result["verification"]["valid"] is True

    def test_full_pipeline_bradicardia(self, orchestrator):
        result = orchestrator.draft_case("Bradicardia", "hard")
        assert result["verification"]["valid"] is True

    def test_full_pipeline_all_templates(self, orchestrator):
        """Gerar caso para cada tópico disponível e verificar."""
        topics = orchestrator.list_topics()
        for topic in topics:
            result = orchestrator.draft_case(topic)
            assert isinstance(result, dict), f"Falha para tópico: {topic}"
            assert "titulo" in result, f"Sem título para tópico: {topic}"
            assert result["verification"]["valid"] is True, (
                f"Verificação falhou para tópico '{topic}': "
                f"{result['verification']['errors']}"
            )

    def test_imports_from_package(self):
        """Verifica que o __init__.py exporta os módulos corretamente."""
        from mega.llm import (
            CaseOrchestrator,
            OllamaBackend,
            GeminiBackend,
            OpenAIBackend,
            OfflineBackend,
            CaseVerifier,
            TEMPLATES,
            get_template,
        )
        assert CaseOrchestrator is not None
        assert OfflineBackend is not None
        assert len(TEMPLATES) >= 10

"""
Tests for Phase 22 (p22) — AI/LLM integration modules.

All tests work fully offline (no API keys required).
"""

from __future__ import annotations

import os
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_report():
    """A sample ECG report dict for testing."""
    return {
        "meta": {"src": "test.png", "w": 1200, "h": 900, "lead_used": "II"},
        "version": "0.5.0",
        "rpeaks": {"peaks_idx": [100, 350, 600], "rr_sec": [1.0, 1.0]},
        "intervals": {
            "median": {
                "PR_ms": 160.0,
                "QRS_ms": 90.0,
                "QT_ms": 380.0,
                "QTc_B": 380.0,
                "QTc_F": 370.0,
                "RR_s": 1.0,
            },
        },
        "intervals_refined": {
            "median": {
                "PR_ms": 160.0,
                "QRS_ms": 90.0,
                "QT_ms": 380.0,
                "QTc_B": 380.0,
                "QTc_F": 370.0,
                "RR_s": 1.0,
            },
        },
        "axis": {"angle_deg": 45.0, "label": "Normal"},
        "flags": ["Sem flags relevantes"],
    }


@pytest.fixture
def abnormal_report():
    """An abnormal ECG report for testing rule triggers."""
    return {
        "meta": {"src": "abnormal.png", "lead_used": "II"},
        "version": "0.5.0",
        "intervals_refined": {
            "median": {
                "PR_ms": 240.0,
                "QRS_ms": 140.0,
                "QT_ms": 500.0,
                "QTc_B": 500.0,
                "QTc_F": 490.0,
                "RR_s": 0.5,
            },
        },
        "axis": {"angle_deg": -60.0, "label": "Desvio para esquerda"},
        "flags": ["Possível bloqueio de ramo"],
    }


@pytest.fixture
def question_dict():
    """A sample quiz question dict."""
    return {
        "pergunta": "Qual é o intervalo PR normal?",
        "opcoes": [
            "80-120 ms",
            "120-200 ms",
            "200-400 ms",
            "400-600 ms",
        ],
        "resposta_correta": 1,
        "explicacao": "O intervalo PR normal varia de 120 a 200 ms.",
    }


# ===========================================================================
# Tests for ai.prompts
# ===========================================================================

class TestPrompts:
    """Tests for prompt templates and builder functions."""

    def test_system_prompt_interpreter_non_empty(self):
        from ai.prompts import SYSTEM_PROMPT_INTERPRETER
        assert len(SYSTEM_PROMPT_INTERPRETER) > 100
        assert "ECG" in SYSTEM_PROMPT_INTERPRETER
        assert "especialista" in SYSTEM_PROMPT_INTERPRETER

    def test_system_prompt_tutor_non_empty(self):
        from ai.prompts import SYSTEM_PROMPT_TUTOR
        assert len(SYSTEM_PROMPT_TUTOR) > 100
        assert "tutor" in SYSTEM_PROMPT_TUTOR.lower()
        assert "câmera" in SYSTEM_PROMPT_TUTOR

    def test_camera_analogy_context_contains_camera(self):
        from ai.prompts import CAMERA_ANALOGY_CONTEXT
        assert "câmera" in CAMERA_ANALOGY_CONTEXT
        assert "derivações" in CAMERA_ANALOGY_CONTEXT.lower() or "derivação" in CAMERA_ANALOGY_CONTEXT.lower()
        assert len(CAMERA_ANALOGY_CONTEXT) > 200

    def test_build_interpretation_prompt(self, sample_report):
        from ai.prompts import build_interpretation_prompt
        prompt = build_interpretation_prompt(sample_report)
        assert isinstance(prompt, str)
        assert len(prompt) > 50
        assert "Relatório ECG" in prompt
        assert "PR_ms" in prompt
        assert "QRS_ms" in prompt
        assert "160" in prompt  # PR value

    def test_build_interpretation_prompt_minimal_report(self):
        from ai.prompts import build_interpretation_prompt
        minimal = {"meta": {}, "version": "0.1.0"}
        prompt = build_interpretation_prompt(minimal)
        assert isinstance(prompt, str)
        assert "Relatório ECG" in prompt

    def test_build_differential_prompt(self):
        from ai.prompts import build_differential_prompt
        findings = ["PR prolongado (240 ms)", "QRS alargado (140 ms)"]
        prompt = build_differential_prompt(findings)
        assert isinstance(prompt, str)
        assert "Diagnóstico Diferencial" in prompt
        assert "PR prolongado" in prompt
        assert "QRS alargado" in prompt
        assert "câmera" in prompt.lower()

    def test_build_tutor_prompt_beginner(self):
        from ai.prompts import build_tutor_prompt
        prompt = build_tutor_prompt("Fibrilação Atrial", "beginner")
        assert "Fibrilação Atrial" in prompt
        assert "Iniciante" in prompt
        assert "câmera" in prompt.lower()

    def test_build_tutor_prompt_advanced(self):
        from ai.prompts import build_tutor_prompt
        prompt = build_tutor_prompt("Bloqueio AV", "advanced")
        assert "Bloqueio AV" in prompt
        assert "Avançado" in prompt

    def test_build_quiz_feedback_prompt_correct(self, question_dict):
        from ai.prompts import build_quiz_feedback_prompt
        prompt = build_quiz_feedback_prompt(question_dict, user_answer=1)
        assert "CORRETO" in prompt
        assert "120-200 ms" in prompt
        assert "câmera" in prompt.lower()

    def test_build_quiz_feedback_prompt_incorrect(self, question_dict):
        from ai.prompts import build_quiz_feedback_prompt
        prompt = build_quiz_feedback_prompt(question_dict, user_answer=0)
        assert "INCORRETO" in prompt
        assert "80-120 ms" in prompt


# ===========================================================================
# Tests for ai.offline_rules
# ===========================================================================

class TestOfflineRules:
    """Tests for rule-based interpretation."""

    def test_interpret_normal_report(self, sample_report):
        from ai.offline_rules import interpret_report
        result = interpret_report(sample_report)
        assert isinstance(result, dict)
        assert "interpretation" in result
        assert "differentials" in result
        assert "recommendations" in result
        assert "confidence" in result
        assert isinstance(result["interpretation"], str)
        assert isinstance(result["differentials"], list)
        assert isinstance(result["recommendations"], list)
        assert result["confidence"] in ("alta", "moderada", "baixa")

    def test_interpret_normal_report_high_confidence(self, sample_report):
        from ai.offline_rules import interpret_report
        result = interpret_report(sample_report)
        assert result["confidence"] == "alta"
        assert "normal" in result["interpretation"].lower()

    def test_interpret_abnormal_report(self, abnormal_report):
        from ai.offline_rules import interpret_report
        result = interpret_report(abnormal_report)
        assert result["confidence"] in ("moderada", "baixa")
        interp_lower = result["interpretation"].lower()
        assert "prolongado" in interp_lower or "alargado" in interp_lower

    def test_interpret_abnormal_detects_pr(self, abnormal_report):
        from ai.offline_rules import interpret_report
        result = interpret_report(abnormal_report)
        assert "PR" in result["interpretation"] or "pr" in result["interpretation"].lower()

    def test_interpret_abnormal_detects_qrs(self, abnormal_report):
        from ai.offline_rules import interpret_report
        result = interpret_report(abnormal_report)
        assert "QRS" in result["interpretation"]

    def test_interpret_abnormal_detects_axis(self, abnormal_report):
        from ai.offline_rules import interpret_report
        result = interpret_report(abnormal_report)
        assert "eixo" in result["interpretation"].lower() or "esquerda" in result["interpretation"].lower()

    def test_interpret_tachycardia(self):
        from ai.offline_rules import interpret_report
        report = {
            "meta": {},
            "version": "0.5.0",
            "intervals_refined": {
                "median": {"PR_ms": 150.0, "QRS_ms": 80.0, "QT_ms": 300.0,
                           "QTc_B": 400.0, "QTc_F": 390.0, "RR_s": 0.4}
            },
            "axis": {"angle_deg": 60.0, "label": "Normal"},
            "flags": [],
        }
        result = interpret_report(report)
        assert "taquicardia" in result["interpretation"].lower()

    def test_interpret_bradycardia(self):
        from ai.offline_rules import interpret_report
        report = {
            "meta": {},
            "version": "0.5.0",
            "intervals_refined": {
                "median": {"PR_ms": 150.0, "QRS_ms": 80.0, "QT_ms": 420.0,
                           "QTc_B": 380.0, "QTc_F": 370.0, "RR_s": 1.5}
            },
            "axis": {"angle_deg": 60.0, "label": "Normal"},
            "flags": [],
        }
        result = interpret_report(report)
        assert "bradicardia" in result["interpretation"].lower()

    def test_interpret_empty_report(self):
        from ai.offline_rules import interpret_report
        result = interpret_report({"meta": {}, "version": "0.1.0"})
        assert isinstance(result, dict)
        assert "interpretation" in result
        assert "normal" in result["interpretation"].lower()

    def test_generate_differential_pr_prolonged(self):
        from ai.offline_rules import generate_differential
        findings = ["PR prolongado (240 ms)"]
        diffs = generate_differential(findings)
        assert isinstance(diffs, list)
        assert len(diffs) > 0
        diagnoses = [d["diagnosis"] for d in diffs]
        assert any("Bloqueio AV" in dx or "bloqueio" in dx.lower() for dx in diagnoses)

    def test_generate_differential_qrs_wide(self):
        from ai.offline_rules import generate_differential
        findings = ["QRS alargado (140 ms)"]
        diffs = generate_differential(findings)
        assert len(diffs) > 0
        diagnoses = [d["diagnosis"] for d in diffs]
        assert any("ramo" in dx.lower() for dx in diagnoses)

    def test_generate_differential_tachycardia(self):
        from ai.offline_rules import generate_differential
        findings = ["Taquicardia (120 bpm)"]
        diffs = generate_differential(findings)
        assert len(diffs) > 0
        assert any("camera" in d.get("camera_analogy", "").lower() or
                    "câmera" in d.get("camera_analogy", "").lower()
                    for d in diffs)

    def test_generate_differential_bradycardia(self):
        from ai.offline_rules import generate_differential
        findings = ["Bradicardia sinusal (FC 50 bpm)"]
        diffs = generate_differential(findings)
        assert len(diffs) > 0
        assert any("bradicardia" in d["diagnosis"].lower() for d in diffs)

    def test_generate_differential_no_match(self):
        from ai.offline_rules import generate_differential
        findings = ["achado desconhecido xyz"]
        diffs = generate_differential(findings)
        assert isinstance(diffs, list)
        assert len(diffs) > 0  # Should return fallback

    def test_generate_differential_empty(self):
        from ai.offline_rules import generate_differential
        result = generate_differential([])
        assert len(result) > 0  # should return fallback

    def test_generate_differential_multiple_findings(self):
        from ai.offline_rules import generate_differential
        findings = [
            "PR prolongado",
            "Taquicardia",
            "Desvio do eixo para esquerda",
        ]
        diffs = generate_differential(findings)
        assert len(diffs) >= 3  # At least one per finding

    def test_generate_differential_has_camera_analogy(self):
        from ai.offline_rules import generate_differential
        findings = ["QRS alargado (140 ms)"]
        diffs = generate_differential(findings)
        for d in diffs:
            assert "camera_analogy" in d

    def test_interpretation_rules_list(self):
        from ai.offline_rules import INTERPRETATION_RULES
        assert isinstance(INTERPRETATION_RULES, list)
        assert len(INTERPRETATION_RULES) > 5
        for rule in INTERPRETATION_RULES:
            assert "id" in rule
            assert "category" in rule
            assert "conclusion" in rule


# ===========================================================================
# Tests for ai.tutor (OfflineTutor)
# ===========================================================================

class TestOfflineTutor:
    """Tests for the OfflineTutor class."""

    def test_explain_finding_known(self):
        from ai.tutor import OfflineTutor
        tutor = OfflineTutor()
        explanation = tutor.explain_finding("Onda P")
        assert isinstance(explanation, str)
        assert len(explanation) > 50
        assert "flash" in explanation.lower() or "câmera" in explanation.lower()

    def test_explain_finding_fibrilacao(self):
        from ai.tutor import OfflineTutor
        tutor = OfflineTutor()
        explanation = tutor.explain_finding("Fibrilação Atrial")
        assert "irregular" in explanation.lower() or "caótic" in explanation.lower()

    def test_explain_finding_case_insensitive(self):
        from ai.tutor import OfflineTutor
        tutor = OfflineTutor()
        explanation = tutor.explain_finding("onda p")
        assert len(explanation) > 50
        assert "flash" in explanation.lower()

    def test_explain_finding_unknown(self):
        from ai.tutor import OfflineTutor
        tutor = OfflineTutor()
        explanation = tutor.explain_finding("achado_inexistente_xyz")
        assert isinstance(explanation, str)
        assert "câmera" in explanation.lower() or "camera" in explanation.lower()

    def test_explanations_has_at_least_20(self):
        from ai.tutor import OfflineTutor
        tutor = OfflineTutor()
        assert len(tutor.EXPLANATIONS) >= 20

    def test_suggest_next_topic_empty_performance(self):
        from ai.tutor import OfflineTutor
        tutor = OfflineTutor()
        suggestion = tutor.suggest_next_topic({})
        assert isinstance(suggestion, str)
        assert "Ritmo Sinusal" in suggestion

    def test_suggest_next_topic_with_weak_area(self):
        from ai.tutor import OfflineTutor
        tutor = OfflineTutor()
        perf = {"Onda P": 90, "Complexo QRS": 30, "Onda T": 80}
        suggestion = tutor.suggest_next_topic(perf)
        assert "Complexo QRS" in suggestion or "QRS" in suggestion

    def test_suggest_next_topic_all_studied(self):
        from ai.tutor import OfflineTutor
        tutor = OfflineTutor()
        perf = {k: 80 for k in tutor.EXPLANATIONS}
        suggestion = tutor.suggest_next_topic(perf)
        assert isinstance(suggestion, str)
        assert len(suggestion) > 20


# ===========================================================================
# Tests for ai.tutor (ECGTutor offline mode)
# ===========================================================================

class TestECGTutor:
    """Tests for ECGTutor in offline mode (no interpreter)."""

    def test_start_session_offline(self):
        from ai.tutor import ECGTutor
        tutor = ECGTutor(interpreter=None)
        intro = tutor.start_session("Fibrilação Atrial", "beginner")
        assert isinstance(intro, str)
        assert "Fibrilação Atrial" in intro
        assert "Iniciante" in intro

    def test_ask_question_offline(self):
        from ai.tutor import ECGTutor
        tutor = ECGTutor(interpreter=None)
        tutor.start_session("Onda P", "beginner")
        answer = tutor.ask_question("O que é a onda P?")
        assert isinstance(answer, str)
        assert len(answer) > 20

    def test_explain_report_offline(self, sample_report):
        from ai.tutor import ECGTutor
        tutor = ECGTutor(interpreter=None)
        explanation = tutor.explain_report(sample_report)
        assert isinstance(explanation, str)
        assert "Passo" in explanation
        assert "câmera" in explanation.lower() or "obturador" in explanation.lower()

    def test_generate_practice_case(self):
        from ai.tutor import ECGTutor
        tutor = ECGTutor(interpreter=None)
        for difficulty in ("easy", "medium", "hard"):
            case = tutor.generate_practice_case(difficulty)
            assert isinstance(case, dict)
            assert "scenario" in case
            assert "report" in case
            assert "questions" in case
            assert "expected_findings" in case

    def test_evaluate_student_offline(self, sample_report):
        from ai.tutor import ECGTutor
        tutor = ECGTutor(interpreter=None)
        result = tutor.evaluate_student_interpretation(
            sample_report,
            "ECG normal, ritmo sinusal, frequência cardíaca de 60 bpm."
        )
        assert isinstance(result, dict)
        assert "score" in result
        assert "feedback" in result
        assert "missed_findings" in result
        assert "correct_findings" in result
        assert isinstance(result["score"], int)


# ===========================================================================
# Tests for ai.interpreter (offline mode)
# ===========================================================================

class TestInterpreterOffline:
    """Tests for ECGInterpreter in offline mode."""

    def test_offline_interpret(self, sample_report):
        from ai.interpreter import ECGInterpreter
        interp = ECGInterpreter(backend="offline")
        result = interp.interpret(sample_report)
        assert isinstance(result, dict)
        assert "interpretation" in result
        assert "differentials" in result
        assert "recommendations" in result
        assert "confidence" in result

    def test_offline_differential(self):
        from ai.interpreter import ECGInterpreter
        interp = ECGInterpreter(backend="offline")
        result = interp.differential_diagnosis(["PR prolongado", "QRS alargado"])
        assert isinstance(result, dict)
        assert "differentials" in result
        assert len(result["differentials"]) > 0

    def test_offline_explain_with_cameras(self, sample_report):
        from ai.interpreter import ECGInterpreter
        interp = ECGInterpreter(backend="offline")
        explanation = interp.explain_with_cameras(sample_report)
        assert isinstance(explanation, str)
        assert "câmera" in explanation.lower() or "camera" in explanation.lower()

    def test_anthropic_without_key_fallback(self, sample_report):
        from ai.interpreter import ECGInterpreter
        # Ensure no key in env
        old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            interp = ECGInterpreter(backend="anthropic", api_key=None)
            # interpret should fallback to offline on error, not crash
            result = interp.interpret(sample_report)
            assert "interpretation" in result
        finally:
            if old_key:
                os.environ["ANTHROPIC_API_KEY"] = old_key

    def test_unknown_backend_raises(self):
        from ai.interpreter import ECGInterpreter
        interp = ECGInterpreter(backend="unknown_backend")
        with pytest.raises(ValueError, match="Backend desconhecido"):
            interp._dispatch([{"role": "user", "content": "test"}])

    def test_offline_interpret_with_intervals_only(self):
        from ai.interpreter import ECGInterpreter
        interp = ECGInterpreter(backend="offline")
        report = {
            "intervals": {"median": {"PR_ms": 160, "QRS_ms": 90, "RR_s": 0.85}},
        }
        result = interp.interpret(report)
        assert "interpretation" in result

    def test_offline_camera_explanation(self):
        from ai.interpreter import ECGInterpreter
        interp = ECGInterpreter(backend="offline")
        report = {"intervals": {"median": {"RR_s": 0.85}}}
        text = interp.explain_with_cameras(report)
        assert len(text) > 0

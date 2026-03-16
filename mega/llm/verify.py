"""
Verificação factual de casos clínicos de ECG gerados por LLM.

Valida estrutura, coerência médica, adiciona disclaimers e
garante que o caso gerado não contenha informações perigosamente incorretas.

Refs: GitHub issue #20
"""

from __future__ import annotations

import re
from typing import Any


# ---------------------------------------------------------------------------
# Constantes de validação médica
# ---------------------------------------------------------------------------

# Faixas fisiológicas aceitáveis para parâmetros de ECG
_PARAMETER_RANGES: dict[str, tuple[float, float, str]] = {
    "fc_bpm": (20, 300, "Frequência cardíaca fora da faixa fisiológica"),
    "pr_ms": (60, 400, "Intervalo PR fora da faixa possível"),
    "qrs_ms": (60, 250, "Duração do QRS fora da faixa possível"),
    "qtc_ms": (200, 700, "QTc fora da faixa possível"),
}

# Regras de coerência entre achados e diagnóstico
_COHERENCE_RULES: list[dict[str, Any]] = [
    {
        "id": "stemi_needs_supra",
        "descricao": "STEMI deve ter supradesnivelamento de ST",
        "condicao_diagnostico": ["stemi", "iamcsst", "infarto com supra"],
        "achado_obrigatorio": ["supra"],
        "campo_verificar": "st_segment",
    },
    {
        "id": "fa_needs_irregular",
        "descricao": "Fibrilação atrial deve ter ritmo irregularmente irregular",
        "condicao_diagnostico": ["fibrilação atrial", "fa "],
        "achado_obrigatorio": ["irregular", "fibrilat"],
        "campo_verificar": "ritmo",
    },
    {
        "id": "bav3_needs_dissociation",
        "descricao": "BAVT deve ter dissociação AV",
        "condicao_diagnostico": ["bloqueio av de 3", "bavt", "bloqueio total", "bav 3"],
        "achado_obrigatorio": ["dissociação", "independente"],
        "campo_verificar": "ritmo",
    },
    {
        "id": "bre_needs_wide_qrs",
        "descricao": "BRE deve ter QRS alargado (>= 120 ms)",
        "condicao_diagnostico": ["bloqueio de ramo esquerdo", "bre"],
        "achado_obrigatorio_numerico": {"qrs_ms": (120, 300)},
    },
    {
        "id": "brd_needs_rsr",
        "descricao": "BRD deve ter padrão RSR' em V1",
        "condicao_diagnostico": ["bloqueio de ramo direito", "brd"],
        "achado_obrigatorio": ["rsr", "m em v1", "v1"],
        "campo_verificar": "outras",
    },
    {
        "id": "wpw_needs_short_pr",
        "descricao": "WPW deve ter PR curto",
        "condicao_diagnostico": ["wolff-parkinson-white", "wpw", "pré-excitação"],
        "achado_obrigatorio_numerico": {"pr_ms": (50, 120)},
    },
    {
        "id": "qt_longo_needs_qtc",
        "descricao": "Síndrome do QT longo deve ter QTc prolongado",
        "condicao_diagnostico": ["qt longo", "lqts"],
        "achado_obrigatorio_numerico": {"qtc_ms": (460, 700)},
    },
    {
        "id": "bradicardia_needs_low_hr",
        "descricao": "Bradicardia deve ter FC < 60 bpm",
        "condicao_diagnostico": ["bradicardia"],
        "achado_obrigatorio_numerico": {"fc_bpm": (20, 60)},
    },
    {
        "id": "taquicardia_needs_high_hr",
        "descricao": "Taquicardia deve ter FC > 100 bpm",
        "condicao_diagnostico": ["taquicardia"],
        "achado_obrigatorio_numerico": {"fc_bpm": (100, 300)},
    },
]

# Campos obrigatórios em um caso clínico
_REQUIRED_FIELDS = [
    "titulo",
    "historia",
    "achados_ecg",
    "diagnostico",
    "perguntas",
    "explicacao",
]

_REQUIRED_ECG_FIELDS = [
    "ritmo",
    "fc_bpm",
    "qrs_ms",
]

# Disclaimer padrão
DISCLAIMER_PT = (
    "AVISO: Este caso clínico foi gerado para fins exclusivamente educacionais. "
    "Não substitui avaliação médica profissional. Sempre consulte as diretrizes "
    "clínicas vigentes e o julgamento de profissionais de saúde qualificados para "
    "decisões diagnósticas e terapêuticas."
)


# ---------------------------------------------------------------------------
# CaseVerifier
# ---------------------------------------------------------------------------

class CaseVerifier:
    """Verificador factual de casos clínicos de ECG.

    Executa validação estrutural, verificação de coerência médica,
    checagem de parâmetros dentro de faixas fisiológicas, e adiciona
    disclaimers obrigatórios.
    """

    def __init__(self, strict: bool = False) -> None:
        """
        Parameters
        ----------
        strict : bool
            Se True, erros de coerência resultam em ``valid=False``.
            Se False (padrão), gera apenas warnings.
        """
        self.strict = strict

    def verify(self, case: dict[str, Any]) -> dict[str, Any]:
        """Verifica um caso clínico completo.

        Parameters
        ----------
        case : dict
            Caso clínico no formato de template (ver ``templates.py``).

        Returns
        -------
        dict
            Resultado com chaves:
            - ``valid`` (bool): caso passou na verificação
            - ``errors`` (list[str]): erros críticos
            - ``warnings`` (list[str]): avisos não-críticos
            - ``score`` (int): pontuação de qualidade (0-100)
            - ``disclaimer`` (str): disclaimer obrigatório
            - ``case`` (dict): caso original com disclaimer adicionado
        """
        errors: list[str] = []
        warnings: list[str] = []

        # 1) Validação estrutural
        struct_errors, struct_warnings = self._validate_structure(case)
        errors.extend(struct_errors)
        warnings.extend(struct_warnings)

        # 2) Verificação de parâmetros numéricos
        param_errors, param_warnings = self._validate_parameters(case)
        errors.extend(param_errors)
        warnings.extend(param_warnings)

        # 3) Verificação de coerência médica
        coh_errors, coh_warnings = self._validate_coherence(case)
        if self.strict:
            errors.extend(coh_errors)
        else:
            warnings.extend(coh_errors)
        warnings.extend(coh_warnings)

        # 4) Verificação de conteúdo mínimo
        content_warnings = self._validate_content_quality(case)
        warnings.extend(content_warnings)

        # Calcular score
        score = self._calculate_score(errors, warnings)

        # Adicionar disclaimer ao caso
        case_with_disclaimer = dict(case)
        case_with_disclaimer["disclaimer"] = DISCLAIMER_PT

        valid = len(errors) == 0

        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "score": score,
            "disclaimer": DISCLAIMER_PT,
            "case": case_with_disclaimer,
        }

    def _validate_structure(
        self, case: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Valida a estrutura obrigatória do caso."""
        errors: list[str] = []
        warnings: list[str] = []

        for field in _REQUIRED_FIELDS:
            if field not in case or not case[field]:
                errors.append(f"Campo obrigatório ausente ou vazio: '{field}'")

        achados = case.get("achados_ecg", {})
        if isinstance(achados, dict):
            for field in _REQUIRED_ECG_FIELDS:
                if field not in achados:
                    warnings.append(f"Campo de ECG recomendado ausente: '{field}'")
        elif isinstance(achados, str):
            # Formato texto — aceitável mas menos estruturado
            warnings.append("achados_ecg em formato texto — preferir formato estruturado (dict)")
        else:
            errors.append("achados_ecg deve ser dict ou str")

        perguntas = case.get("perguntas", [])
        if isinstance(perguntas, list) and len(perguntas) < 2:
            warnings.append("Recomendado pelo menos 2 perguntas por caso")

        return errors, warnings

    def _validate_parameters(
        self, case: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Valida que os parâmetros numéricos estão em faixas fisiológicas."""
        errors: list[str] = []
        warnings: list[str] = []

        achados = case.get("achados_ecg", {})
        if not isinstance(achados, dict):
            return errors, warnings

        for param, (lo, hi, msg) in _PARAMETER_RANGES.items():
            val = achados.get(param)
            if val is None:
                continue
            if not isinstance(val, (int, float)):
                continue
            if val < lo or val > hi:
                errors.append(f"{msg}: {param}={val} (faixa: {lo}-{hi})")

        return errors, warnings

    def _validate_coherence(
        self, case: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Verifica coerência entre diagnóstico e achados do ECG."""
        errors: list[str] = []
        warnings: list[str] = []

        diagnostico = (case.get("diagnostico") or "").lower()
        achados = case.get("achados_ecg", {})
        if not isinstance(achados, dict):
            return errors, warnings

        for rule in _COHERENCE_RULES:
            # Verificar se o diagnóstico corresponde à regra
            matches_diag = any(
                kw in diagnostico for kw in rule["condicao_diagnostico"]
            )
            if not matches_diag:
                continue

            # Verificar achado obrigatório em campo de texto
            if "achado_obrigatorio" in rule and "campo_verificar" in rule:
                campo = rule["campo_verificar"]
                valor_campo = str(achados.get(campo, "") or "").lower()
                has_match = any(
                    kw in valor_campo for kw in rule["achado_obrigatorio"]
                )
                if not has_match:
                    errors.append(
                        f"Incoerência [{rule['id']}]: {rule['descricao']}. "
                        f"Campo '{campo}' não contém achado esperado."
                    )

            # Verificar achado numérico obrigatório
            if "achado_obrigatorio_numerico" in rule:
                for param, (lo, hi) in rule["achado_obrigatorio_numerico"].items():
                    val = achados.get(param)
                    if val is None:
                        warnings.append(
                            f"[{rule['id']}]: Campo numérico '{param}' ausente "
                            f"para validar '{rule['descricao']}'"
                        )
                        continue
                    if not isinstance(val, (int, float)):
                        continue
                    if val < lo or val > hi:
                        errors.append(
                            f"Incoerência [{rule['id']}]: {rule['descricao']}. "
                            f"{param}={val} fora da faixa esperada ({lo}-{hi})."
                        )

        return errors, warnings

    def _validate_content_quality(self, case: dict[str, Any]) -> list[str]:
        """Verifica qualidade mínima do conteúdo textual."""
        warnings: list[str] = []

        historia = case.get("historia", "")
        if isinstance(historia, str):
            if len(historia) < 50:
                warnings.append("História clínica muito curta (< 50 caracteres)")
            # Verificar se menciona idade e sexo
            if not re.search(r"\d+\s*anos", historia):
                warnings.append("História não menciona idade do paciente")
            if not re.search(
                r"(masculino|feminino|homem|mulher|paciente\s+de)",
                historia,
                re.IGNORECASE,
            ):
                warnings.append("História não menciona sexo do paciente")

        explicacao = case.get("explicacao", "")
        if isinstance(explicacao, str) and len(explicacao) < 50:
            warnings.append("Explicação muito curta (< 50 caracteres)")

        return warnings

    def _calculate_score(
        self, errors: list[str], warnings: list[str]
    ) -> int:
        """Calcula pontuação de qualidade (0-100)."""
        score = 100
        score -= len(errors) * 20
        score -= len(warnings) * 5
        return max(0, min(100, score))

    def add_disclaimer(self, case: dict[str, Any]) -> dict[str, Any]:
        """Adiciona disclaimer ao caso clínico.

        Parameters
        ----------
        case : dict
            Caso clínico.

        Returns
        -------
        dict
            Caso com campo ``disclaimer`` adicionado.
        """
        result = dict(case)
        result["disclaimer"] = DISCLAIMER_PT
        return result

    def quick_check(self, case: dict[str, Any]) -> bool:
        """Verificação rápida — retorna True se o caso é estruturalmente válido.

        Parameters
        ----------
        case : dict
            Caso clínico.

        Returns
        -------
        bool
            True se a estrutura mínima está presente.
        """
        for field in _REQUIRED_FIELDS:
            if field not in case or not case[field]:
                return False
        return True


# ---------------------------------------------------------------------------
# Funções utilitárias
# ---------------------------------------------------------------------------

def verify_case(case: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    """Atalho funcional para verificação de caso.

    Parameters
    ----------
    case : dict
        Caso clínico.
    strict : bool
        Modo estrito (erros de coerência são fatais).

    Returns
    -------
    dict
        Resultado da verificação.
    """
    verifier = CaseVerifier(strict=strict)
    return verifier.verify(case)


def validate_ecg_parameters(achados: dict[str, Any]) -> list[str]:
    """Valida parâmetros individuais de ECG.

    Parameters
    ----------
    achados : dict
        Dicionário de achados ECG.

    Returns
    -------
    list[str]
        Lista de mensagens de erro (vazia se tudo ok).
    """
    errors: list[str] = []
    for param, (lo, hi, msg) in _PARAMETER_RANGES.items():
        val = achados.get(param)
        if val is None:
            continue
        if not isinstance(val, (int, float)):
            continue
        if val < lo or val > hi:
            errors.append(f"{msg}: {param}={val}")
    return errors

"""Gerador de dados para dashboard de progresso do aluno.

Computa estatísticas e estruturas de dados prontas para
visualização com Plotly ou qualquer frontend.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from .engine import LearningEngine, ECG_SKILL_TREE


class DashboardData:
    """Gera dados de dashboard para visualização do progresso do aluno.

    Consome dados do LearningEngine e produz estruturas de dados
    otimizadas para gráficos Plotly.

    Parameters
    ----------
    engine : LearningEngine
        Motor de aprendizagem com dados do aluno carregados.
    """

    def __init__(self, engine: LearningEngine) -> None:
        self.engine = engine

    # ------------------------------------------------------------------
    # Mapa de competências
    # ------------------------------------------------------------------

    def get_competency_map(self) -> dict:
        """Gera mapa de competências hierárquico para visualização.

        Retorna estrutura para gráfico sunburst/treemap do Plotly com
        categorias, habilidades e sub-habilidades.

        Returns
        -------
        dict
            Estrutura com chaves ``labels``, ``parents``, ``values``,
            ``colors`` e ``ids`` para Plotly sunburst.
        """
        labels: list[str] = []
        parents: list[str] = []
        values: list[float] = []
        colors: list[str] = []
        ids: list[str] = []

        # Raiz
        overall = self.engine.profile.overall_mastery
        labels.append("ECG")
        parents.append("")
        values.append(overall)
        colors.append(self._mastery_color(overall))
        ids.append("ECG")

        for categoria, habilidades in ECG_SKILL_TREE.items():
            # Nível de categoria
            cat_masteries: list[float] = []

            for hab_pai, sub_habs in habilidades.items():
                pai_key = f"{categoria}::{hab_pai}"
                sub_masteries: list[float] = []

                for sub in sub_habs:
                    sub_key = f"{categoria}::{hab_pai}::{sub}"
                    mastery = self.engine.get_mastery(sub_key)
                    sub_masteries.append(mastery)

                    labels.append(sub)
                    parents.append(pai_key)
                    values.append(mastery)
                    colors.append(self._mastery_color(mastery))
                    ids.append(sub_key)

                # Maestria do pai = média dos filhos
                pai_mastery = (
                    sum(sub_masteries) / len(sub_masteries)
                    if sub_masteries
                    else 0.0
                )
                cat_masteries.append(pai_mastery)

                labels.append(hab_pai)
                parents.append(categoria)
                values.append(round(pai_mastery, 1))
                colors.append(self._mastery_color(pai_mastery))
                ids.append(pai_key)

            # Maestria da categoria
            cat_mastery = (
                sum(cat_masteries) / len(cat_masteries)
                if cat_masteries
                else 0.0
            )
            labels.append(categoria.capitalize())
            parents.append("ECG")
            values.append(round(cat_mastery, 1))
            colors.append(self._mastery_color(cat_mastery))
            ids.append(categoria)

        return {
            "labels": labels,
            "parents": parents,
            "values": values,
            "colors": colors,
            "ids": ids,
            "chart_type": "sunburst",
        }

    # ------------------------------------------------------------------
    # Linha do tempo de progresso
    # ------------------------------------------------------------------

    def get_progress_timeline(self, days: int = 30) -> dict:
        """Gera linha do tempo de progresso para gráfico de linhas.

        Parameters
        ----------
        days : int
            Número de dias para incluir na linha do tempo.

        Returns
        -------
        dict
            Estrutura com chaves ``dates``, ``overall_mastery``,
            ``skills`` (dict por habilidade com lista de valores),
            ``sessions`` e ``chart_type``.
        """
        profile = self.engine.profile
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Coleta todos os eventos do histórico de cada habilidade
        events: list[dict] = []
        for sid, skill in profile.skills.items():
            for entry in skill.history:
                try:
                    ts = datetime.fromisoformat(entry["ts"])
                    if ts >= start_date:
                        events.append({
                            "ts": ts,
                            "skill_id": sid,
                            "skill_name": skill.skill_name,
                            "mastery": entry.get("mastery_after", 0.0),
                            "correct": entry.get("correct", False),
                        })
                except (ValueError, KeyError):
                    continue

        events.sort(key=lambda e: e["ts"])

        # Agrupa por dia
        daily: dict[str, list[dict]] = defaultdict(list)
        for ev in events:
            day_key = ev["ts"].strftime("%Y-%m-%d")
            daily[day_key].append(ev)

        # Gera séries temporais
        dates: list[str] = []
        overall_values: list[float] = []
        skill_series: dict[str, list[float]] = defaultdict(list)
        session_counts: list[int] = []

        current = start_date
        last_masteries: dict[str, float] = {}

        while current <= end_date:
            day_key = current.strftime("%Y-%m-%d")
            dates.append(day_key)

            day_events = daily.get(day_key, [])
            session_counts.append(len(day_events))

            # Atualiza maestrias do dia
            for ev in day_events:
                last_masteries[ev["skill_id"]] = ev["mastery"]

            # Calcula maestria geral do dia
            if last_masteries:
                overall = sum(last_masteries.values()) / len(last_masteries)
            else:
                overall = 0.0
            overall_values.append(round(overall, 1))

            # Registra cada habilidade rastreada
            for sid in last_masteries:
                skill_series[sid].append(round(last_masteries[sid], 1))

            current += timedelta(days=1)

        return {
            "dates": dates,
            "overall_mastery": overall_values,
            "skills": dict(skill_series),
            "sessions": session_counts,
            "chart_type": "line",
        }

    # ------------------------------------------------------------------
    # Áreas fracas
    # ------------------------------------------------------------------

    def get_weak_areas(self, top_n: int = 10) -> dict:
        """Identifica e formata áreas fracas para visualização.

        Returns
        -------
        dict
            Estrutura para gráfico de barras horizontais com
            ``skills``, ``masteries``, ``attempts``, ``accuracies``,
            ``colors`` e ``chart_type``.
        """
        weak = self.engine.get_weak_areas()[:top_n]

        skills: list[str] = []
        masteries: list[float] = []
        attempts: list[int] = []
        accuracies: list[float] = []
        colors: list[str] = []

        for area in weak:
            skills.append(area["skill_name"])
            masteries.append(area["mastery"])
            attempts.append(area["attempts"])
            accuracies.append(area["accuracy"])
            colors.append(self._mastery_color(area["mastery"]))

        return {
            "skills": skills,
            "masteries": masteries,
            "attempts": attempts,
            "accuracies": accuracies,
            "colors": colors,
            "chart_type": "bar_horizontal",
        }

    # ------------------------------------------------------------------
    # Recomendações
    # ------------------------------------------------------------------

    def get_recommendations(self, n: int = 5) -> dict:
        """Gera recomendações formatadas para exibição.

        Returns
        -------
        dict
            Estrutura com ``items`` (lista de recomendações) e
            ``summary`` (resumo textual).
        """
        recs = self.engine.get_recommendations(n=n)

        items: list[dict] = []
        for rec in recs:
            icon = {
                "revisão": "🔄",
                "reforço": "💪",
                "novo_tópico": "📚",
            }.get(rec["tipo"], "📋")

            items.append({
                "tipo": rec["tipo"],
                "icone": icon,
                "skill_name": rec["skill_name"],
                "mastery": rec["mastery"],
                "razão": rec["razão"],
                "prioridade": round(rec["prioridade"], 2),
            })

        # Resumo textual
        profile = self.engine.profile
        n_skills = len(profile.skills)
        overall = profile.overall_mastery

        if n_skills == 0:
            summary = (
                "Bem-vindo ao ECGiga! Você ainda não começou a estudar. "
                "Recomendamos iniciar pelos fundamentos — é como aprender "
                "a segurar a câmera antes de fotografar."
            )
        elif overall >= 80:
            summary = (
                f"Excelente progresso! Maestria geral: {overall:.0f}/100. "
                f"Você domina {n_skills} tópicos. Continue revisando para "
                "manter a retenção a longo prazo."
            )
        elif overall >= 50:
            summary = (
                f"Bom progresso! Maestria geral: {overall:.0f}/100. "
                "Foque nas áreas mais fracas para equilibrar o conhecimento."
            )
        else:
            summary = (
                f"Continue praticando! Maestria geral: {overall:.0f}/100. "
                "Revise os conceitos fundamentais e pratique regularmente."
            )

        return {
            "items": items,
            "summary": summary,
            "overall_mastery": overall,
            "total_skills_studied": n_skills,
        }

    # ------------------------------------------------------------------
    # Resumo geral
    # ------------------------------------------------------------------

    def get_summary(self) -> dict:
        """Resumo geral para o topo do dashboard.

        Returns
        -------
        dict
            Métricas resumidas: maestria geral, total de habilidades,
            revisões pendentes, sessões, tempo de estudo.
        """
        profile = self.engine.profile
        due = self.engine.get_due_reviews()

        # Conta habilidades dominadas
        mastered = sum(
            1
            for sid in profile.skills
            if self.engine.get_mastery(sid) >= self.engine.MASTERY_THRESHOLD
        )

        return {
            "maestria_geral": profile.overall_mastery,
            "total_habilidades": len(profile.skills),
            "habilidades_dominadas": mastered,
            "revisoes_pendentes": len(due),
            "sessoes_totais": profile.sessions_count,
            "tempo_estudo_min": round(profile.total_study_time_min, 1),
        }

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    @staticmethod
    def _mastery_color(mastery: float) -> str:
        """Retorna cor hexadecimal baseada na maestria.

        Vermelho (0) → Amarelo (50) → Verde (100).
        """
        if mastery >= 80:
            return "#2ecc71"  # verde
        elif mastery >= 60:
            return "#27ae60"  # verde escuro
        elif mastery >= 40:
            return "#f39c12"  # amarelo/laranja
        elif mastery >= 20:
            return "#e67e22"  # laranja
        else:
            return "#e74c3c"  # vermelho

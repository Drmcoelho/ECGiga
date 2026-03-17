"""Pacote de aprendizagem adaptativa do ECGiga.

Contém o motor de aprendizagem adaptativa e o gerador de dados
para dashboard de progresso do aluno.
"""

from .engine import LearningEngine
from .dashboard import DashboardData

__all__ = ["LearningEngine", "DashboardData"]

"""Pacote de agentes inteligentes do ECGiga.

Contém o orquestrador multi-agente e os agentes especializados:
TutorAgent, CriticAgent e ExplainerAgent.
"""

from .orchestrator import AgentOrchestrator
from .tutor import TutorAgent
from .critic import CriticAgent
from .explainer import ExplainerAgent

__all__ = [
    "AgentOrchestrator",
    "TutorAgent",
    "CriticAgent",
    "ExplainerAgent",
]

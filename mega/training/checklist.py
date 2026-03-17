"""
mega.training.checklist — Checklists de acurácia médica para ECG.

Define critérios de avaliação para interpretação de eletrocardiogramas,
organizados por categorias: ritmo, frequência, eixo, intervalos,
morfologia, segmento ST, ondas e achados clínicos.
"""

from __future__ import annotations

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Checklist principal de interpretação de ECG
# ---------------------------------------------------------------------------

ECG_CHECKLIST: List[Dict[str, Any]] = [
    # --- Ritmo (1-4) ---
    {
        "id": "ritmo_01",
        "categoria": "Ritmo",
        "descricao": "Identificação do ritmo sinusal (presença de onda P antes de cada QRS)",
        "palavras_chave": ["ritmo sinusal", "onda p", "sinusal"],
        "obrigatorio": True,
    },
    {
        "id": "ritmo_02",
        "categoria": "Ritmo",
        "descricao": "Reconhecimento de fibrilação atrial (ausência de ondas P, RR irregular)",
        "palavras_chave": [
            "fibrilação atrial",
            "fa",
            "rr irregular",
            "irregularmente irregular",
        ],
        "obrigatorio": True,
    },
    {
        "id": "ritmo_03",
        "categoria": "Ritmo",
        "descricao": "Identificação de flutter atrial (ondas F em dente de serra)",
        "palavras_chave": [
            "flutter atrial",
            "dente de serra",
            "ondas f",
            "serrilhadas",
        ],
        "obrigatorio": False,
    },
    {
        "id": "ritmo_04",
        "categoria": "Ritmo",
        "descricao": "Reconhecimento de taquicardia ventricular (QRS largo, FC elevada)",
        "palavras_chave": [
            "taquicardia ventricular",
            "tv",
            "qrs largo",
        ],
        "obrigatorio": False,
    },
    # --- Frequência cardíaca (5-6) ---
    {
        "id": "fc_05",
        "categoria": "Frequência",
        "descricao": "Cálculo ou menção da frequência cardíaca",
        "palavras_chave": [
            "frequência cardíaca",
            "fc",
            "bpm",
            "batimentos por minuto",
        ],
        "obrigatorio": True,
    },
    {
        "id": "fc_06",
        "categoria": "Frequência",
        "descricao": "Classificação de bradicardia (<60 bpm) ou taquicardia (>100 bpm)",
        "palavras_chave": [
            "bradicardia",
            "taquicardia",
            "normocardia",
        ],
        "obrigatorio": False,
    },
    # --- Eixo elétrico (7-9) ---
    {
        "id": "eixo_07",
        "categoria": "Eixo",
        "descricao": "Determinação do eixo elétrico cardíaco",
        "palavras_chave": [
            "eixo",
            "desvio",
            "eixo elétrico",
            "eixo cardíaco",
        ],
        "obrigatorio": True,
    },
    {
        "id": "eixo_08",
        "categoria": "Eixo",
        "descricao": "Desvio do eixo para a esquerda (associação com BRE, BDAS)",
        "palavras_chave": [
            "desvio para a esquerda",
            "eixo desviado",
            "bdas",
        ],
        "obrigatorio": False,
    },
    {
        "id": "eixo_09",
        "categoria": "Eixo",
        "descricao": "Desvio do eixo para a direita (associação com BRD, BDPI)",
        "palavras_chave": [
            "desvio para a direita",
            "bdpi",
            "sobrecarga vd",
        ],
        "obrigatorio": False,
    },
    # --- Intervalos (10-14) ---
    {
        "id": "intervalo_10",
        "categoria": "Intervalos",
        "descricao": "Avaliação do intervalo PR (normal: 120-200 ms)",
        "palavras_chave": [
            "intervalo pr",
            "pr",
            "condução atrioventricular",
        ],
        "obrigatorio": True,
    },
    {
        "id": "intervalo_11",
        "categoria": "Intervalos",
        "descricao": "Avaliação da duração do QRS (normal: <120 ms)",
        "palavras_chave": [
            "duração do qrs",
            "qrs",
            "complexo qrs",
        ],
        "obrigatorio": True,
    },
    {
        "id": "intervalo_12",
        "categoria": "Intervalos",
        "descricao": "Avaliação do intervalo QT/QTc (QTc normal: <450 ms homens, <460 ms mulheres)",
        "palavras_chave": [
            "intervalo qt",
            "qtc",
            "qt corrigido",
        ],
        "obrigatorio": True,
    },
    {
        "id": "intervalo_13",
        "categoria": "Intervalos",
        "descricao": "Reconhecimento de bloqueio AV (1o, 2o ou 3o grau)",
        "palavras_chave": [
            "bloqueio av",
            "bloqueio atrioventricular",
            "bav",
            "wenckebach",
            "mobitz",
        ],
        "obrigatorio": False,
    },
    {
        "id": "intervalo_14",
        "categoria": "Intervalos",
        "descricao": "Identificação de QT longo ou curto",
        "palavras_chave": [
            "qt longo",
            "qt prolongado",
            "qt curto",
        ],
        "obrigatorio": False,
    },
    # --- Morfologia (15-18) ---
    {
        "id": "morfologia_15",
        "categoria": "Morfologia",
        "descricao": "Identificação de bloqueio de ramo direito (rSR' em V1, S empastada em V6)",
        "palavras_chave": [
            "bloqueio de ramo direito",
            "brd",
            "rsr'",
        ],
        "obrigatorio": False,
    },
    {
        "id": "morfologia_16",
        "categoria": "Morfologia",
        "descricao": "Identificação de bloqueio de ramo esquerdo (QRS largo, R empastada em V5-V6)",
        "palavras_chave": [
            "bloqueio de ramo esquerdo",
            "bre",
        ],
        "obrigatorio": False,
    },
    {
        "id": "morfologia_17",
        "categoria": "Morfologia",
        "descricao": "Reconhecimento de hipertrofia ventricular esquerda (critérios de Sokolow-Lyon)",
        "palavras_chave": [
            "hipertrofia ventricular",
            "hve",
            "sokolow",
            "sobrecarga ventricular",
        ],
        "obrigatorio": False,
    },
    {
        "id": "morfologia_18",
        "categoria": "Morfologia",
        "descricao": "Avaliação da onda P (sobrecarga atrial direita ou esquerda)",
        "palavras_chave": [
            "onda p",
            "sobrecarga atrial",
            "p mitrale",
            "p pulmonale",
        ],
        "obrigatorio": False,
    },
    # --- Segmento ST e isquemia (19-21) ---
    {
        "id": "st_19",
        "categoria": "Segmento ST",
        "descricao": "Avaliação do segmento ST (supra ou infradesnivelamento)",
        "palavras_chave": [
            "segmento st",
            "supradesnivelamento",
            "infradesnivelamento",
            "supra de st",
            "infra de st",
        ],
        "obrigatorio": True,
    },
    {
        "id": "st_20",
        "categoria": "Segmento ST",
        "descricao": "Correlação de alterações de ST com território coronariano",
        "palavras_chave": [
            "parede anterior",
            "parede inferior",
            "parede lateral",
            "território",
            "coronariano",
            "descendente anterior",
            "circunflexa",
            "coronária direita",
        ],
        "obrigatorio": False,
    },
    {
        "id": "st_21",
        "categoria": "Segmento ST",
        "descricao": "Reconhecimento de imagem em espelho (alterações recíprocas)",
        "palavras_chave": [
            "imagem em espelho",
            "alterações recíprocas",
            "espelho",
        ],
        "obrigatorio": False,
    },
    # --- Onda T (22-23) ---
    {
        "id": "onda_t_22",
        "categoria": "Onda T",
        "descricao": "Avaliação da onda T (inversão, apiculamento, achatamento)",
        "palavras_chave": [
            "onda t",
            "inversão de t",
            "t invertida",
            "t apiculada",
        ],
        "obrigatorio": False,
    },
    {
        "id": "onda_t_23",
        "categoria": "Onda T",
        "descricao": "Reconhecimento de hipercalemia (T apiculada, QRS alargado)",
        "palavras_chave": [
            "hipercalemia",
            "hiperpotassemia",
            "t apiculada",
            "potássio",
        ],
        "obrigatorio": False,
    },
    # --- Pré-excitação e canalopatias (24-25) ---
    {
        "id": "pre_exc_24",
        "categoria": "Pré-excitação",
        "descricao": "Identificação de síndrome de Wolff-Parkinson-White (onda delta, PR curto)",
        "palavras_chave": [
            "wolff-parkinson-white",
            "wpw",
            "onda delta",
            "pré-excitação",
        ],
        "obrigatorio": False,
    },
    {
        "id": "canal_25",
        "categoria": "Canalopatias",
        "descricao": "Reconhecimento do padrão de Brugada (ST coved em V1-V2)",
        "palavras_chave": [
            "brugada",
            "coved",
            "padrão de brugada",
        ],
        "obrigatorio": False,
    },
]


def get_checklist_by_category(
    category: str, checklist: List[Dict[str, Any]] | None = None
) -> List[Dict[str, Any]]:
    """Filtra itens do checklist por categoria.

    Parameters
    ----------
    category : str
        Nome da categoria (ex.: "Ritmo", "Intervalos").
    checklist : list, optional
        Checklist a filtrar. Se None, usa ECG_CHECKLIST.

    Returns
    -------
    list[dict]
        Itens da categoria especificada.
    """
    source = checklist if checklist is not None else ECG_CHECKLIST
    return [
        item for item in source if item.get("categoria", "").lower() == category.lower()
    ]


def get_mandatory_items(
    checklist: List[Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    """Retorna apenas os itens obrigatórios do checklist.

    Parameters
    ----------
    checklist : list, optional
        Checklist a filtrar. Se None, usa ECG_CHECKLIST.

    Returns
    -------
    list[dict]
        Itens obrigatórios.
    """
    source = checklist if checklist is not None else ECG_CHECKLIST
    return [item for item in source if item.get("obrigatorio", False)]


def get_all_categories(
    checklist: List[Dict[str, Any]] | None = None,
) -> List[str]:
    """Retorna lista de categorias únicas no checklist.

    Parameters
    ----------
    checklist : list, optional
        Checklist a consultar. Se None, usa ECG_CHECKLIST.

    Returns
    -------
    list[str]
        Categorias únicas ordenadas.
    """
    source = checklist if checklist is not None else ECG_CHECKLIST
    categories = sorted(set(item.get("categoria", "") for item in source))
    return [c for c in categories if c]

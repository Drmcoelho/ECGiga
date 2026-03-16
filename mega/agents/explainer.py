"""ExplainerAgent — agente explicador de conceitos de ECG.

Fornece explicações em múltiplos níveis (iniciante, intermediário,
avançado), utiliza analogias com câmera fotográfica e gera
descrições visuais para conceitos de ECG.
Possui fallback offline baseado em regras.
"""

from __future__ import annotations

from typing import Any


# ======================================================================
# Base de explicações multinível
# ======================================================================

_EXPLANATIONS: dict[str, dict[str, str]] = {
    "onda_p": {
        "iniciante": (
            "A onda P é como o flash da câmera fotográfica se acendendo. "
            "Antes de tirar qualquer foto (batimento), o flash precisa disparar. "
            "Na câmera-coração, o flash são os átrios (câmaras superiores) se "
            "contraindo para empurrar sangue para os ventrículos. "
            "A onda P é pequena e arredondada — como um piscar suave de luz."
        ),
        "intermediário": (
            "A onda P representa a despolarização atrial, originada no nó "
            "sinusal (SA). Normalmente é positiva em DII (o flash está apontando "
            "para baixo e para a esquerda) e negativa em aVR. "
            "Duração normal: <120 ms. Amplitude: <2.5 mm em DII.\n\n"
            "Alterações da onda P:\n"
            "- P mitrale (entalhada, >120 ms): sobrecarga atrial esquerda\n"
            "- P pulmonale (pontiaguda, >2.5 mm): sobrecarga atrial direita\n"
            "- P ausente: ritmo não sinusal (juncional, FA, flutter)"
        ),
        "avançado": (
            "A onda P resulta da propagação do impulso do nó SA através do "
            "miocárdio atrial. O vetor de despolarização atrial normalmente "
            "aponta para baixo, esquerda e ligeiramente anterior.\n\n"
            "Análise vetorial:\n"
            "- Componente inicial (átrio direito): anterior e inferior\n"
            "- Componente terminal (átrio esquerdo): posterior e esquerdo\n"
            "- Em V1, a P normal é bifásica (positiva/negativa)\n"
            "- Índice de Morris (fase negativa em V1 >1mm·s): SAE\n\n"
            "Condução interatrial pelo feixe de Bachmann — sua lesão causa "
            "onda P ≥120ms com entalhe (bloqueio interatrial avançado)."
        ),
    },
    "complexo_qrs": {
        "iniciante": (
            "O complexo QRS é o momento em que o obturador da câmera dispara — "
            "CLIQUE! É a parte principal da foto cardíaca. Os ventrículos "
            "(câmaras inferiores e maiores) se contraem com força para "
            "bombear sangue para todo o corpo e pulmões. "
            "É a deflexão mais alta e rápida do ECG — um clique rápido e preciso."
        ),
        "intermediário": (
            "O complexo QRS representa a despolarização ventricular. "
            "Componentes:\n"
            "- Q: primeira deflexão negativa (septo despolarizando da E→D)\n"
            "- R: primeira deflexão positiva (paredes ventriculares)\n"
            "- S: deflexão negativa após R (bases ventriculares)\n\n"
            "Duração normal: 80-120 ms (o obturador abre e fecha rápido).\n"
            "QRS >120 ms sugere bloqueio de ramo ou ritmo ventricular."
        ),
        "avançado": (
            "A despolarização ventricular ocorre em 3 vetores principais:\n\n"
            "1. Septal (0-20 ms): septo de E→D — gera q em DI/V5-V6 e r em V1\n"
            "2. Paredes livres (20-60 ms): vetor dominante para E e inferior\n"
            "3. Basal (60-100 ms): bases póstero-superiores\n\n"
            "Progressão de R em precordiais: rS em V1 → Rs em V6. "
            "Zona de transição normal: V3-V4.\n\n"
            "Padrões patológicos:\n"
            "- RSR' em V1: BRD (obturador com duplo clique à direita)\n"
            "- QS em V1 + R mono em V6: BRE (obturador lento à esquerda)\n"
            "- Onda delta: pré-excitação (WPW — atalho no mecanismo)\n"
            "- Q patológica (>40ms, >25% do R): necrose miocárdica"
        ),
    },
    "segmento_st": {
        "iniciante": (
            "O segmento ST é como a pausa entre o clique do obturador e o "
            "reset da câmera. Normalmente é plano e nivelado — a câmera está "
            "em repouso momentâneo. Se ele sobe (supra) ou desce (infra), "
            "algo está errado — como se a câmera tremesse entre uma foto e outra."
        ),
        "intermediário": (
            "O segmento ST vai do ponto J (fim do QRS) ao início da onda T. "
            "Representa a fase de platô do potencial de ação ventricular "
            "(fase 2), quando todos os miócitos estão no mesmo potencial.\n\n"
            "Alterações:\n"
            "- Supra de ST: lesão transmural (IAM), pericardite, repolarização precoce\n"
            "- Infra de ST: isquemia subendocárdica, efeito digitálico, HVE\n"
            "- Ponto J: deve estar na linha de base (segmento TP como referência)"
        ),
        "avançado": (
            "O segmento ST é isoelétrico porque durante a fase 2 do potencial "
            "de ação não há gradiente de voltagem no miocárdio.\n\n"
            "Mecanismos de alteração:\n"
            "- Teoria da corrente de lesão: células isquêmicas têm potencial "
            "de repouso menos negativo → corrente diastólica entre tecido "
            "sadio e lesado → desvio da linha de base\n"
            "- Supra = epicárdio isquêmico (transmural)\n"
            "- Infra = subendocárdio isquêmico\n\n"
            "Critérios para IAM com supra:\n"
            "- ≥1 mm em 2 derivações contíguas dos membros\n"
            "- ≥2 mm em 2 derivações precordiais contíguas\n"
            "- V2-V3: ≥2.5 mm (H <40a), ≥2 mm (H ≥40a), ≥1.5 mm (M)"
        ),
    },
    "eixo_eletrico": {
        "iniciante": (
            "O eixo elétrico é como a direção para onde a câmera está apontando. "
            "Normalmente aponta para baixo e para a esquerda (como a maioria "
            "das câmeras num estúdio fotográfico). Se aponta muito para a "
            "direita ou esquerda, algo pode estar diferente com o coração."
        ),
        "intermediário": (
            "O eixo elétrico representa a direção média do vetor de "
            "despolarização ventricular no plano frontal.\n\n"
            "Faixas:\n"
            "- Normal: -30° a +90°\n"
            "- Desvio para esquerda: -30° a -90° (HBAE, HVE)\n"
            "- Desvio para direita: +90° a +180° (HVD, HBPE, TEP)\n"
            "- Eixo indeterminado: -90° a -180°\n\n"
            "Método rápido: DI e aVF — positivo em ambos = normal."
        ),
        "avançado": (
            "O eixo é calculado pela soma vetorial das forças elétricas "
            "no plano frontal (sistema hexaxial de Bailey).\n\n"
            "Cálculo preciso: use a derivação com QRS mais isoelétrico — "
            "o eixo é perpendicular a ela.\n\n"
            "Causas de desvio:\n"
            "- HBAE: desvio E além de -45°, qR em aVL, rS em DII/DIII\n"
            "- HBPE: desvio D além de +120°, rS em DI, qR em DIII\n"
            "- Desvio extremo: pode indicar TV, hipercalemia, canal AV\n\n"
            "Na presença de BRD/BRE, o eixo dos primeiros 40ms "
            "(parte não bloqueada) é mais útil clinicamente."
        ),
    },
    "fibrilacao_atrial": {
        "iniciante": (
            "Na fibrilação atrial, o flash da câmera disparou fora de controle — "
            "centenas de flashes por minuto, todos caóticos! Em vez de um flash "
            "organizado antes de cada foto, temos uma luz piscando loucamente. "
            "O resultado? O obturador dispara em momentos aleatórios, sem ritmo "
            "definido. É o ritmo 'irregularmente irregular'."
        ),
        "intermediário": (
            "Na FA, múltiplos focos reentrantes nos átrios geram atividade "
            "elétrica caótica a 350-600/min. O nó AV filtra, permitindo "
            "passagem apenas de alguns impulsos (resposta ventricular).\n\n"
            "Critérios ECG:\n"
            "- Ausência de ondas P (substituídas por ondas f)\n"
            "- Linha de base irregular (ondulação fibrilatória)\n"
            "- Intervalos RR irregularmente irregulares\n"
            "- QRS normalmente estreito (a menos que haja bloqueio)\n\n"
            "Classificação: paroxística (<7d), persistente (>7d), permanente."
        ),
        "avançado": (
            "Mecanismos da FA:\n"
            "- Múltiplas wavelets reentrantes (Moe, 1962)\n"
            "- Focos ectópicos nas veias pulmonares (Haïssaguerre, 1998)\n"
            "- Rotores de alta frequência (teoria focal)\n\n"
            "Remodelamento atrial: 'FA gera FA' — o remodelamento elétrico "
            "(encurtamento do período refratário) e estrutural (fibrose) "
            "perpetuam a arritmia.\n\n"
            "Avaliação de risco: CHA₂DS₂-VASc para tromboembolismo. "
            "HAS-BLED para risco de sangramento com anticoagulação.\n\n"
            "FA com QRS largo: diferenciar de TV. Na FA + WPW, o impulso "
            "pode conduzir pelo feixe acessório → QRS largo irregular "
            "(contraindicação absoluta para bloqueadores do nó AV)."
        ),
    },
    "bloqueio_ramo": {
        "iniciante": (
            "Imagine que o obturador da câmera tem dois lados — direito e "
            "esquerdo. Normalmente, ambos abrem ao mesmo tempo. No bloqueio "
            "de ramo, um lado está mais lento. O resultado é um clique mais "
            "demorado (QRS largo >120 ms) e a foto sai ligeiramente 'borrada'."
        ),
        "intermediário": (
            "Bloqueio de Ramo Direito (BRD):\n"
            "- QRS ≥120 ms\n"
            "- RSR' em V1-V2 (duplo clique do lado direito)\n"
            "- S empastado em DI/V5-V6\n"
            "- Pode ser benigno (variante normal)\n\n"
            "Bloqueio de Ramo Esquerdo (BRE):\n"
            "- QRS ≥120 ms\n"
            "- QS ou rS em V1 (o lado esquerdo domina tardiamente)\n"
            "- R monofásico e entalhado em V5-V6/DI/aVL\n"
            "- Ausência de q septal em DI/V5-V6\n"
            "- Sempre patológico (investigar cardiopatia)"
        ),
        "avançado": (
            "BRD: o septo despolariza normalmente (E→D), depois o VD é ativado "
            "tardiamente pelo miocárdio (vetor terminal para D e anterior).\n"
            "Repolarização: T invertida em V1-V3 é esperada (discordância).\n\n"
            "BRE: o septo despolariza de D→E (inversão!), depois o VE ativa "
            "tardiamente. Altera toda a sequência de ativação → invalida "
            "critérios de HVE e dificulta diagnóstico de IAM.\n\n"
            "Critérios de Sgarbossa (IAM + BRE):\n"
            "- Supra ≥1mm concordante com QRS (5 pts)\n"
            "- Infra ≥1mm em V1-V3 (3 pts)\n"
            "- Supra ≥5mm discordante (2 pts)\n"
            "≥3 pts sugere IAM. Smith modificou: razão ST/S ≤-0.25 "
            "em derivações com QRS negativo."
        ),
    },
}

# Mapeamento de palavras-chave para tópicos de explicação
_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "onda_p": ["onda p", "p wave", "atrial", "despolarização atrial"],
    "complexo_qrs": ["qrs", "complexo", "ventricular", "despolarização ventricular"],
    "segmento_st": ["st", "segmento st", "supra", "infra", "isquemia"],
    "eixo_eletrico": ["eixo", "axis", "desvio"],
    "fibrilacao_atrial": ["fibrilação", "fa", "atrial", "irregularmente"],
    "bloqueio_ramo": ["bloqueio", "ramo", "brd", "bre", "branch block"],
}

_VISUAL_DESCRIPTIONS: dict[str, str] = {
    "onda_p": (
        "Visualmente, a onda P é uma deflexão pequena, arredondada e suave "
        "que precede o QRS. Em DII, parece uma colina suave de ~2 mm de altura "
        "e ~80 ms de largura. Imagine um sino delicado — simétrico e discreto."
    ),
    "complexo_qrs": (
        "O QRS é a deflexão mais proeminente: um pico agudo e estreito. "
        "Em DII, começa com uma pequena deflexão negativa (q), sobe "
        "rapidamente até o pico (R), e desce abaixo da linha (S). "
        "Parece uma torre estreita — rápida e decisiva."
    ),
    "segmento_st": (
        "O segmento ST é uma linha plana e horizontal logo após o QRS. "
        "Deve estar nivelado com a linha de base (segmento TP). "
        "Visualmente, é como um platô calmo entre o pico do QRS e "
        "a subida da onda T."
    ),
    "eixo_eletrico": (
        "O eixo não é visível diretamente, mas inferido: olhe para DI e aVF. "
        "Se ambos têm QRS positivo (para cima), o eixo está no quadrante "
        "normal (inferior-esquerdo). Imagine uma bússola no centro do ECG "
        "apontando na direção do maior vetor elétrico."
    ),
    "fibrilacao_atrial": (
        "Na FA, a linha de base ondula irregularmente (ondas f) — como "
        "a superfície de um lago com vento. Não há ondas P definidas. "
        "Os complexos QRS aparecem em intervalos irregulares, como "
        "gotas de chuva caindo sem ritmo."
    ),
    "bloqueio_ramo": (
        "No bloqueio de ramo, o QRS fica mais largo (>3 quadradinhos). "
        "No BRD, V1 mostra um padrão 'M' ou 'orelhas de coelho' (RSR'). "
        "No BRE, V1 mostra um QRS predominantemente negativo (QS ou rS) "
        "e V6 mostra R alto e entalhado."
    ),
}


class ExplainerAgent:
    """Agente explicador que fornece explicações multinível de ECG.

    Gera explicações em três níveis (iniciante, intermediário, avançado),
    utiliza analogias com câmera fotográfica e produz descrições visuais.

    Parameters
    ----------
    llm_backend : Any, optional
        Backend de LLM para explicações avançadas. Se None, usa fallback offline.
    """

    def __init__(self, llm_backend: Any = None) -> None:
        self.llm_backend = llm_backend

    def explain(
        self,
        topic: str,
        level: str = "iniciante",
        include_visual: bool = True,
    ) -> dict:
        """Gera explicação sobre um tópico de ECG.

        Parameters
        ----------
        topic : str
            Tópico a explicar (ex: "onda P", "QRS", "fibrilação atrial").
        level : str
            Nível: ``"iniciante"``, ``"intermediário"`` ou ``"avançado"``.
        include_visual : bool
            Se deve incluir descrição visual.

        Returns
        -------
        dict
            Explicação com chaves: ``explanation``, ``level``, ``topic``,
            ``visual_description``, ``camera_analogy``.
        """
        # Tenta LLM primeiro
        if self.llm_backend is not None:
            try:
                return self._explain_with_llm(topic, level, include_visual)
            except Exception:
                pass

        # Fallback offline
        return self._explain_offline(topic, level, include_visual)

    def explain_all_levels(self, topic: str) -> dict:
        """Gera explicações em todos os níveis para um tópico.

        Parameters
        ----------
        topic : str
            Tópico a explicar.

        Returns
        -------
        dict
            Dicionário com chaves ``iniciante``, ``intermediário``,
            ``avançado``, cada uma contendo a explicação do nível.
        """
        result: dict[str, dict] = {}
        for level in ["iniciante", "intermediário", "avançado"]:
            result[level] = self.explain(topic, level=level, include_visual=False)

        return result

    def generate_visual_description(self, topic: str) -> str:
        """Gera descrição visual de um achado ECG.

        Descreve como o achado aparece visualmente no traçado,
        útil para alunos que estão aprendendo a reconhecer padrões.

        Parameters
        ----------
        topic : str
            Tópico ou achado ECG.

        Returns
        -------
        str
            Descrição visual detalhada.
        """
        topic_key = self._resolve_topic(topic)

        if topic_key and topic_key in _VISUAL_DESCRIPTIONS:
            return _VISUAL_DESCRIPTIONS[topic_key]

        # Descrição genérica para tópicos não mapeados
        return (
            f"Para identificar '{topic}' no ECG, observe o traçado "
            "sistematicamente: comece pelo ritmo (regularidade dos RR), "
            "depois analise as ondas (P, QRS, T) em cada derivação. "
            "Compare com um ECG normal — as diferenças apontarão o achado. "
            "Cada derivação é uma câmera em ângulo diferente: o que parece "
            "pequeno em uma pode ser evidente em outra."
        )

    def explain_finding(self, finding: str, report: dict | None = None) -> str:
        """Explica um achado específico de um relatório ECG.

        Parameters
        ----------
        finding : str
            O achado a explicar (ex: "QRS alargado", "supra de ST").
        report : dict, optional
            Relatório ECG para contexto adicional.

        Returns
        -------
        str
            Explicação do achado em português.
        """
        finding_lower = finding.lower()

        # Mapeamento de achados para explicações contextuais
        explanations: dict[str, str] = {
            "qrs alargado": (
                "O QRS está alargado (>120 ms), indicando que o obturador da câmera "
                "demora mais para abrir e fechar. Causas possíveis:\n"
                "- Bloqueio de ramo (direito ou esquerdo)\n"
                "- Ritmo ventricular (sem condução pelo sistema normal)\n"
                "- Pré-excitação (WPW)\n"
                "- Hipercalemia grave"
            ),
            "pr prolongado": (
                "O intervalo PR está prolongado (>200 ms), significando que o "
                "tempo entre o flash (onda P) e o disparo do obturador (QRS) "
                "é maior que o normal. Isso é BAV de 1° grau — a câmera "
                "funciona, mas com atraso."
            ),
            "pr curto": (
                "O intervalo PR está curto (<120 ms), sugerindo um atalho "
                "no mecanismo da câmera. Pode indicar pré-excitação (WPW) "
                "ou ritmo juncional."
            ),
            "qtc prolongado": (
                "O QTc está prolongado (>460 ms), indicando que a câmera demora "
                "mais para resetar. Riscos:\n"
                "- Torsades de pointes\n"
                "- Causas: medicamentos, distúrbios eletrolíticos, congênito"
            ),
            "supra de st": (
                "Há elevação do segmento ST — como se a câmera tremesse entre "
                "fotos. Em contexto clínico apropriado (dor torácica), "
                "suspeitar de IAM com supra. Outras causas: pericardite "
                "(supra difuso), repolarização precoce."
            ),
            "taquicardia": (
                "A frequência cardíaca está elevada (>100 bpm) — a câmera está "
                "em modo burst. Pode ser sinusal (fisiológica) ou patológica "
                "(supraventricular ou ventricular)."
            ),
            "bradicardia": (
                "A frequência cardíaca está baixa (<60 bpm) — a câmera está "
                "em modo lento. Pode ser fisiológica (atletas) ou patológica "
                "(disfunção sinusal, BAV)."
            ),
            "desvio eixo": (
                "O eixo elétrico está desviado — a câmera aponta para um "
                "ângulo incomum. Desvio para esquerda pode indicar HBAE ou HVE. "
                "Desvio para direita pode indicar HVD, HBPE ou TEP."
            ),
        }

        for key, explanation in explanations.items():
            if key in finding_lower:
                # Adiciona contexto do relatório se disponível
                if report:
                    context = self._extract_report_context(report, key)
                    if context:
                        explanation += f"\n\nNo seu ECG: {context}"
                return explanation

        return (
            f"Achado: '{finding}'. Analise este achado no contexto clínico "
            "do paciente. Lembre-se: cada derivação é uma câmera em ângulo "
            "diferente — compare o achado em múltiplas derivações para "
            "determinar sua significância."
        )

    # ------------------------------------------------------------------
    # Resolução de tópicos
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_topic(topic: str) -> str | None:
        """Resolve um tópico livre para uma chave do dicionário."""
        topic_lower = topic.lower().strip()

        # Match direto
        if topic_lower.replace(" ", "_") in _EXPLANATIONS:
            return topic_lower.replace(" ", "_")

        # Busca por palavras-chave
        for key, keywords in _TOPIC_KEYWORDS.items():
            for kw in keywords:
                if kw in topic_lower or topic_lower in kw:
                    return key

        return None

    @staticmethod
    def _extract_report_context(report: dict, finding_key: str) -> str:
        """Extrai contexto relevante do relatório ECG."""
        iv = report.get("intervals_refined") or report.get("intervals") or {}
        med = iv.get("median", {})
        axis = report.get("axis", {})

        contexts: dict[str, str] = {}

        qrs = med.get("QRS_ms")
        if qrs:
            contexts["qrs alargado"] = f"QRS medido: {qrs:.0f} ms"
        pr = med.get("PR_ms")
        if pr:
            contexts["pr prolongado"] = f"PR medido: {pr:.0f} ms"
            contexts["pr curto"] = f"PR medido: {pr:.0f} ms"
        qtc = med.get("QTc_B")
        if qtc:
            contexts["qtc prolongado"] = f"QTc (Bazett): {qtc:.0f} ms"
        rr = med.get("RR_s")
        if rr and rr > 0:
            hr = 60.0 / rr
            contexts["taquicardia"] = f"FC calculada: {hr:.0f} bpm"
            contexts["bradicardia"] = f"FC calculada: {hr:.0f} bpm"
        angle = axis.get("angle_deg")
        if angle is not None:
            contexts["desvio eixo"] = f"Eixo: {angle:.0f}°"

        return contexts.get(finding_key, "")

    # ------------------------------------------------------------------
    # Offline e LLM
    # ------------------------------------------------------------------

    def _explain_offline(
        self, topic: str, level: str, include_visual: bool
    ) -> dict:
        """Explicação offline usando base de conhecimento."""
        topic_key = self._resolve_topic(topic)

        # Normaliza nível
        level_map = {
            "beginner": "iniciante",
            "intermediate": "intermediário",
            "advanced": "avançado",
        }
        level_normalized = level_map.get(level.lower(), level.lower())
        if level_normalized not in ("iniciante", "intermediário", "avançado"):
            level_normalized = "iniciante"

        if topic_key and topic_key in _EXPLANATIONS:
            levels = _EXPLANATIONS[topic_key]
            explanation = levels.get(level_normalized, levels.get("iniciante", ""))
        else:
            explanation = (
                f"Sobre '{topic}': este é um conceito importante em ECG. "
                "Pense em cada aspecto do ECG como uma parte da câmera "
                "fotográfica — cada componente tem uma função específica "
                "na captura da atividade elétrica do coração.\n\n"
                "Para uma explicação mais detalhada, consulte material "
                "de referência ou ative o modo online."
            )

        # Extrai analogia com câmera (primeira frase com "câmera")
        camera_analogy = ""
        for sentence in explanation.split(". "):
            if "câmera" in sentence.lower() or "obturador" in sentence.lower():
                camera_analogy = sentence.strip()
                if not camera_analogy.endswith("."):
                    camera_analogy += "."
                break

        visual = ""
        if include_visual:
            visual = self.generate_visual_description(topic)

        return {
            "explanation": explanation,
            "level": level_normalized,
            "topic": topic,
            "topic_key": topic_key or topic,
            "visual_description": visual,
            "camera_analogy": camera_analogy,
        }

    def _explain_with_llm(
        self, topic: str, level: str, include_visual: bool
    ) -> dict:
        """Explicação usando LLM."""
        system_prompt = (
            "Você é um professor de ECG que usa analogias com câmera fotográfica. "
            "Adapte sua explicação ao nível do aluno. Responda em português."
        )

        user_msg = (
            f"Explique '{topic}' no nível '{level}'.\n"
            "Use analogias com câmera fotográfica.\n"
        )
        if include_visual:
            user_msg += "Inclua uma descrição visual de como isso aparece no ECG."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]

        response = self.llm_backend(messages)
        text = response if isinstance(response, str) else str(response)

        return {
            "explanation": text,
            "level": level,
            "topic": topic,
            "topic_key": self._resolve_topic(topic) or topic,
            "visual_description": "",
            "camera_analogy": "",
        }

    # ------------------------------------------------------------------
    # Listagem de tópicos disponíveis
    # ------------------------------------------------------------------

    @staticmethod
    def available_topics() -> list[str]:
        """Lista tópicos disponíveis para explicação offline."""
        return list(_EXPLANATIONS.keys())

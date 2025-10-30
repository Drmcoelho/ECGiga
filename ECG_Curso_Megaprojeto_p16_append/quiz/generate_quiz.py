import json
import random
from typing import Dict


def _fmt(val, nd=0):
    return (
        "N/D" if val is None else (f"{val:.{nd}f}" if isinstance(val, (int, float)) else str(val))
    )


def quiz_from_report(report: Dict, seed: int = 42) -> Dict:
    """
    Gera um pequeno conjunto de MCQs com base no laudo analisado (HR/QRS/PR/QT/QTc e bandeiras).
    Saída: {"questions":[{id, prompt, choices:[{id,text,is_correct,explanation}] }]}
    """
    random.seed(seed)
    q = []
    # HR (se disponível via rpeaks)
    hr = None
    if report.get("rpeaks", {}).get("rr_sec"):
        rr = report["rpeaks"]["rr_sec"]
        if rr:
            hr = 60.0 / (sum(rr) / len(rr))
    # Intervais medianos
    iv = report.get("intervals", {}).get("median", {})
    pr, qrs, qt, qtc = iv.get("PR_ms"), iv.get("QRS_ms"), iv.get("QT_ms"), iv.get("QTc_B")
    # Q1: Ritmo
    if hr:
        prompt = f"Com RR médio ≈ {_fmt(1.0/(hr/60.0), 2)} s, qual a FC aproximada?"
        correct = f"{_fmt(hr,0)} bpm"
        choices = [
            correct,
            f"{_fmt(hr*0.5,0)} bpm",
            f"{_fmt(hr*1.5,0)} bpm",
            f"{_fmt(hr+30,0)} bpm",
        ]
        random.shuffle(choices)
        expl = f"A FC ≈ 60/RR(s) ≈ {hr:.0f} bpm."
        q.append(
            {
                "id": "q_hr",
                "prompt": prompt,
                "choices": [
                    {"id": i, "text": c, "is_correct": (c == correct), "explanation": expl}
                    for i, c in enumerate(choices)
                ],
            }
        )
    # Q2: QRS largo?
    if qrs is not None:
        prompt = f"O QRS mediano é {_fmt(qrs,0)} ms. Ele é considerado largo?"
        correct = "Sim" if qrs >= 120 else "Não"
        expl = "QRS ≥ 120 ms é considerado largo (bloqueio de ramo ou condução intraventricular)."
        choices = ["Sim", "Não"]
        random.shuffle(choices)
        q.append(
            {
                "id": "q_qrs",
                "prompt": prompt,
                "choices": [
                    {"id": i, "text": c, "is_correct": (c == correct), "explanation": expl}
                    for i, c in enumerate(choices)
                ],
            }
        )
    # Q3: PR prolongado?
    if pr is not None:
        prompt = f"O PR mediano é {_fmt(pr,0)} ms. Há 1º grau AV?"
        correct = "Sim" if pr > 200 else "Não"
        expl = "PR > 200 ms define bloqueio AV de 1º grau."
        choices = ["Sim", "Não"]
        random.shuffle(choices)
        q.append(
            {
                "id": "q_pr",
                "prompt": prompt,
                "choices": [
                    {"id": i, "text": c, "is_correct": (c == correct), "explanation": expl}
                    for i, c in enumerate(choices)
                ],
            }
        )
    # Q4: QT/QTc
    if qt is not None and qtc is not None:
        prompt = f"O QT mediano é {_fmt(qt,0)} ms e QTc(B) {_fmt(qtc,0)} ms. Qual a interpretação?"

        def interp(qtcv):
            if qtcv > 480:
                return "Prolongado (alto risco)"
            if qtcv > 440:
                return "Prolongado (leve/moderado)"
            if qtcv < 350:
                return "Curto"
            return "Normal"

        correct = interp(qtc)
        choices = ["Prolongado (alto risco)", "Prolongado (leve/moderado)", "Normal", "Curto"]
        random.shuffle(choices)
        expl = "Limiares típicos: >440–450 ms (prolongado), >480 ms alto risco; <350 ms, curto."
        q.append(
            {
                "id": "q_qtc",
                "prompt": prompt,
                "choices": [
                    {"id": i, "text": c, "is_correct": (c == correct), "explanation": expl}
                    for i, c in enumerate(choices)
                ],
            }
        )
    return {"questions": q}


if __name__ == "__main__":
    import json
    import sys

    rep = json.load(open(sys.argv[1], "r", encoding="utf-8"))
    print(json.dumps(quiz_from_report(rep), ensure_ascii=False, indent=2))

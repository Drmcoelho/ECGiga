
import json, random
from typing import Dict, List

ITEMS = [
    {"id":"axis_left_1","tag":"axis_left","prompt":"O eixo elétrico frontal está desviado para a esquerda quando:",
     "choices":[
        {"text":"Ângulo entre -30° e -90°","ok":True,"exp":"Definição clássica: -30° a -90°."},
        {"text":"Ângulo > +90°","ok":False,"exp":"Isso é desvio para a direita."},
        {"text":"Ângulo entre -15° e +75°","ok":False,"exp":"Faixa aproximada de normalidade."},
        {"text":"Ângulo < -150°","ok":False,"exp":"< -90° = desvio extremo (noroeste)."}]},
    {"id":"axis_right_1","tag":"axis_right","prompt":"Selecione o intervalo que define desvio do eixo para a direita:",
     "choices":[
        {"text":"> +90° a ≤ +180°","ok":True,"exp":"Definição pragmática usual."},
        {"text":"-30° a +90°","ok":False,"exp":"Região normal."},
        {"text":"-90° a -30°","ok":False,"exp":"Esquerda."},
        {"text":"≤ -90°","ok":False,"exp":"Extremo."}]},
    {"id":"qrs_wide_1","tag":"qrs_wide","prompt":"QRS é considerado largo quando:",
     "choices":[
        {"text":"≥ 120 ms","ok":True,"exp":"Corte para bloqueios de ramo."},
        {"text":"≥ 100 ms","ok":False,"exp":"Intermediário/limítrofe."},
        {"text":"≤ 80 ms","ok":False,"exp":"Em geral, estreito."},
        {"text":"≥ 200 ms","ok":False,"exp":"Muito incomum."}]},
    {"id":"pr_long_1","tag":"pr_long","prompt":"Bloqueio AV de 1º grau é definido por:",
     "choices":[
        {"text":"PR > 200 ms","ok":True,"exp":"Definição formal."},
        {"text":"PR > 160 ms","ok":False,"exp":"Abaixo do limiar."},
        {"text":"QRS > 120 ms","ok":False,"exp":"Critério de QRS largo."},
        {"text":"RR < 600 ms","ok":False,"exp":"Ritmo rápido, não 1º grau."}]},
    {"id":"qtc_long_1","tag":"qtc_long","prompt":"QTc prolongado de alto risco (genérico) é:",
     "choices":[
        {"text":"> 480 ms","ok":True,"exp":"Risco aumentado de TdP em contexto adequado."},
        {"text":"> 440 ms","ok":False,"exp":"Leve/moderado (sexo-dependente)."},
        {"text":"< 350 ms","ok":False,"exp":"QTc curto."},
        {"text":"350–440 ms","ok":False,"exp":"Faixa normal aproximada."}]}
]

def infer_gaps_from_report(report: Dict) -> List[str]:
    tags = []
    iv = report.get("intervals_refined", report.get("intervals", {})).get("median", {})
    qrs = iv.get("QRS_ms"); pr = iv.get("PR_ms"); qtc = iv.get("QTc_B")
    axis = (report.get("axis") or {}).get("label","").lower()
    if qrs is not None and qrs >= 120: tags.append("qrs_wide")
    if pr is not None and pr > 200: tags.append("pr_long")
    if qtc is not None and qtc > 480: tags.append("qtc_long")
    if "esquerda" in axis: tags.append("axis_left")
    if "direita" in axis: tags.append("axis_right")
    return tags or ["qrs_wide","pr_long","qtc_long","axis_left"]

def build_adaptive_quiz(report: Dict, n_questions: int = 6, seed: int = 123) -> Dict:
    random.seed(seed)
    tags = infer_gaps_from_report(report)
    pool = [it for it in ITEMS if it["tag"] in tags]
    random.shuffle(pool)
    sel = pool[:n_questions] if len(pool)>=n_questions else (pool + random.sample(ITEMS, k=max(0, n_questions-len(pool))))
    questions = []
    for it in sel:
        ch = it["choices"][:]
        random.shuffle(ch)
        questions.append({
            "id": it["id"], "tag": it["tag"], "prompt": it["prompt"],
            "choices": [{"id":i, "text":c["text"], "is_correct":c["ok"], "explanation":c["exp"]} for i,c in enumerate(ch)]
        })
    return {"questions": questions, "tags": tags}

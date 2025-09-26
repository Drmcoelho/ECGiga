
from __future__ import annotations
import json, subprocess, shlex
from pathlib import Path
from typing import Dict, List, Optional

def _add_q(questions: List[Dict], prompt: str, correct: str, wrong: List[str], exp: str, image: Optional[str] = None):
    choices = [{"text": correct, "is_correct": True, "explanation": exp}] + \
              [{"text": w, "is_correct": False, "explanation": "Incorreto no contexto do laudo."} for w in wrong]
    questions.append({"prompt": prompt, "choices": choices, **({"image": image} if image else {})})

def quiz_from_report_illustrated(report_json: str, out_json: str,
                                 image_path: Optional[str] = None,
                                 overlay_json: Optional[str] = None,
                                 overlay_out: Optional[str] = None) -> str:
    """
    Gera um quiz MCQ a partir do laudo v0.5 e, opcionalmente, cria overlay a partir de um annotations.json.
    - report_json: caminho para laudo JSON
    - image_path: imagem PNG/JPG de ECG (opcional; se fornecido e overlay_json também, gera overlay_out e usa como imagem)
    - overlay_json: gabarito annotations.json (opcional)
    - overlay_out: saída do overlay gerado (PNG)
    """
    rep = json.loads(Path(report_json).read_text(encoding="utf-8"))
    qs: List[Dict] = []
    # 1) Intervalos (QRS/QTc)
    med = (rep.get("intervals_refined") or {}).get("median") or {}
    qrs = med.get("QRS_ms"); qtc = med.get("QTc_B") or med.get("QTc_ms")
    if qrs is not None:
        _add_q(qs, "Quanto à largura do QRS, a melhor interpretação é:",
               f"QRS ≈ {qrs:.0f} ms (≥120 ms sugere bloqueio completo).",
               ["QRS inerente ao eixo (não depende de condução).","QRS não é interpretável em derivação de membros."],
               "Bloqueios completos costumam ter QRS ≥ 120 ms.")
    if qtc is not None:
        _add_q(qs, "Sobre o QT corrigido (QTc), assinale a correta:",
               f"QTc ≈ {qtc:.0f} ms; valores > 480–500 ms aumentam o risco (depende do contexto).",
               ["QTc normal implica risco zero de arritmia.","QTc só se mede em V5/V6."],
               "QTc é global e depende de FC; cortes variam conforme a referência.")
    # 2) Eixo
    ax = rep.get("axis_hex") or rep.get("axis") or {}
    ang = ax.get("angle_deg"); lab = ax.get("label")
    if ang is not None:
        _add_q(qs, "Qual a melhor descrição do eixo frontal?",
               f"Eixo ≈ {ang:.0f}° — {lab or ''}".strip(),
               ["Eixo depende exclusivamente de V1 e V6.","Eixo indeterminável sem VCG."],
               "Sistema hexaxial usa I, II, III, aVR, aVL, aVF.")
    # 3) Condução (BRD/BRE)
    cd = rep.get("conduction") or {}
    if cd:
        _add_q(qs, "Quanto à condução intraventricular, o laudo sugere:",
               cd.get("label","Sem bloqueio maior evidente"),
               ["Bloqueio AV tipo Mobitz II.","Pré-excitação (WPW)."],
               "Heurística morfológica com V1/V2 e I/V6 + QRS.")
    # 4) HVE
    hv = rep.get("hypertrophy_extended") or rep.get("hypertrophy") or {}
    if hv:
        sok = hv.get("sokolow_lyon_mm"); cp = hv.get("cornell_product_mm_ms") or hv.get("cornell_mV")
        _add_q(qs, "Sobre critérios de HVE, assinale a correta:",
               f"Sokolow-Lyon ≈ {sok:.1f} mm; Cornell product ≈ {cp}.",
               ["Sokolow usa apenas V5.","Cornell product ignora QRSd."],
               "Sokolow: S(V1)+max(R(V5,V6)); Cornell product: (RaVL+SV3)×QRSd.")
    # Overlay ilustrativo se solicitado
    used_image = None
    if image_path and overlay_json and overlay_out:
        try:
            # usa CLI existente para overlay
            from annotations.cli import overlay as _ov  # type: ignore
        except Exception:
            _ov = None
        if _ov is None:
            # fallback via subprocess à CLI (se for rodado por python -m)
            cmd = f"python -m ecgcourse annotations overlay {shlex.quote(image_path)} {shlex.quote(overlay_json)} --out {shlex.quote(overlay_out)}"
            try:
                subprocess.check_call(cmd, shell=True)
                used_image = overlay_out
            except Exception:
                used_image = None
        else:
            _ov.callback(image_path=image_path, annotations_json=overlay_json, out_image=overlay_out)  # type: ignore
            used_image = overlay_out
    # Atribui a imagem (se houver) à primeira pergunta para ilustração
    if used_image and qs:
        qs[0]["image"] = used_image
    out = {"questions": qs}
    Path(out_json).parent.mkdir(parents=True, exist_ok=True)
    Path(out_json).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_json

"""
education/interactive.py — Funções interativas para o Dash web app

Gera figuras Plotly para visualização didática das câmeras cardíacas.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objects as go

from education.cameras import LEAD_CAMERAS, _normalize_angle, _angle_difference

# ---------------------------------------------------------------------------
# Constantes de layout
# ---------------------------------------------------------------------------

_HEART_COLOR = "#e74c3c"
_CAMERA_COLOR = "#3498db"
_ACTIVE_CAMERA_COLOR = "#e67e22"
_VECTOR_COLOR = "#2ecc71"
_BG_COLOR = "#f8f9fa"
_GRID_COLOR = "#dee2e6"

_FRONTAL_LEADS = ["I", "II", "III", "aVR", "aVL", "aVF"]
_HORIZONTAL_LEADS = ["V1", "V2", "V3", "V4", "V5", "V6"]

# Mapeamento de ângulos para posição (x, y) em um círculo unitário
# Para plano frontal: 0° = esquerda (3 o'clock na convenção ECG),
# ângulos crescem no sentido horário
def _lead_xy(angle_deg: float, radius: float = 1.3) -> Tuple[float, float]:
    """Converte ângulo ECG em coordenadas (x, y) para plotagem.

    Convenção ECG: 0° = esquerda, 90° = baixo, -90° = cima.
    Convertemos para ângulo matemático para plotar.
    """
    # ECG: 0°=right? Actually in ECG convention:
    # 0° points left (lead I positive), 90° points down (aVF)
    # We map: math_angle = -ecg_angle (flip vertical) then rotate
    # For display: 0° ECG → right on display, 90° ECG → down
    rad = math.radians(angle_deg)
    x = radius * math.cos(rad)
    y = -radius * math.sin(rad)  # flip because y-axis inverted in ECG convention
    # Actually, let's use standard ECG hexaxial display:
    # 0° = 3 o'clock, 90° = 6 o'clock (down), -90° = 12 o'clock (up)
    # In math coords: angle_math = -angle_ecg
    # x = cos(-angle_ecg) = cos(angle_ecg), y = sin(-angle_ecg) = -sin(angle_ecg)
    # But we want 90° to point down on screen, so y should be positive for 90°
    # y_screen = sin(angle_ecg) → 90° → 1.0 (down)
    x = radius * math.cos(rad)
    y = radius * math.sin(rad)  # 90° → y positive = down in our figure
    return (x, y)


# ---------------------------------------------------------------------------
# create_camera_visualization_figure
# ---------------------------------------------------------------------------

def create_camera_visualization_figure(
    active_lead: str = "II",
    vector_angle: float = 60,
) -> go.Figure:
    """
    Cria figura Plotly mostrando o coração com 12 câmeras ao redor,
    destacando a derivação ativa e o vetor elétrico.

    Parameters
    ----------
    active_lead : str
        Derivação a destacar (default "II").
    vector_angle : float
        Ângulo do vetor elétrico em graus (default 60°).

    Returns
    -------
    plotly.graph_objects.Figure
    """
    fig = go.Figure()

    # Determine which plane to show based on active lead
    if active_lead in _FRONTAL_LEADS:
        leads_to_show = _FRONTAL_LEADS
        plane_title = "Plano Frontal"
    else:
        leads_to_show = _HORIZONTAL_LEADS
        plane_title = "Plano Horizontal"

    # --- Draw heart shape (simplified ellipse) ---
    heart_theta = [i * 2 * math.pi / 100 for i in range(101)]
    heart_x = [0.3 * math.cos(t) for t in heart_theta]
    heart_y = [0.35 * math.sin(t) for t in heart_theta]
    fig.add_trace(go.Scatter(
        x=heart_x, y=heart_y,
        fill="toself",
        fillcolor="rgba(231, 76, 60, 0.3)",
        line=dict(color=_HEART_COLOR, width=2),
        name="Coração",
        hoverinfo="skip",
    ))

    # Label the heart
    fig.add_annotation(
        x=0, y=0, text="<b>Coração</b>",
        showarrow=False, font=dict(size=12, color=_HEART_COLOR),
    )

    # --- Draw cameras (lead positions) ---
    for lead in leads_to_show:
        info = LEAD_CAMERAS[lead]
        angle = info["angle_deg"]
        cx, cy = _lead_xy(angle, radius=1.3)

        is_active = (lead == active_lead)
        color = _ACTIVE_CAMERA_COLOR if is_active else _CAMERA_COLOR
        size = 18 if is_active else 12
        symbol = "square" if is_active else "diamond"

        # Camera marker
        fig.add_trace(go.Scatter(
            x=[cx], y=[cy],
            mode="markers+text",
            marker=dict(size=size, color=color, symbol=symbol,
                        line=dict(width=2, color="white")),
            text=[f"<b>{lead}</b>"],
            textposition="top center" if cy < 0 else "bottom center",
            textfont=dict(size=14 if is_active else 11, color=color),
            name=lead,
            hovertext=info["description_pt"],
            hoverinfo="text",
        ))

        # Line from heart to camera (dashed for inactive)
        fig.add_trace(go.Scatter(
            x=[0, cx], y=[0, cy],
            mode="lines",
            line=dict(
                color=color,
                width=3 if is_active else 1,
                dash="solid" if is_active else "dot",
            ),
            hoverinfo="skip",
            showlegend=False,
        ))

    # --- Draw electrical vector ---
    vx, vy = _lead_xy(vector_angle, radius=0.9)
    fig.add_trace(go.Scatter(
        x=[0, vx], y=[0, vy],
        mode="lines",
        line=dict(color=_VECTOR_COLOR, width=4),
        name=f"Vetor ({vector_angle}°)",
        hoverinfo="name",
    ))
    # Arrowhead
    fig.add_annotation(
        x=vx, y=vy, ax=0, ay=0,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=3, arrowsize=2, arrowwidth=3,
        arrowcolor=_VECTOR_COLOR,
    )
    fig.add_annotation(
        x=vx * 1.15, y=vy * 1.15,
        text=f"<b>Vetor {vector_angle}°</b>",
        showarrow=False,
        font=dict(size=12, color=_VECTOR_COLOR),
    )

    # --- Deflection indicator for active lead ---
    if active_lead in LEAD_CAMERAS:
        lead_angle = LEAD_CAMERAS[active_lead]["angle_deg"]
        diff = _angle_difference(lead_angle, vector_angle)
        if diff <= 80:
            deflection_text = "Deflexão POSITIVA (vetor se aproxima)"
            deflection_color = "#27ae60"
        elif diff >= 100:
            deflection_text = "Deflexão NEGATIVA (vetor se afasta)"
            deflection_color = "#c0392b"
        else:
            deflection_text = "BIFÁSICO (vetor perpendicular)"
            deflection_color = "#8e44ad"

        fig.add_annotation(
            x=0, y=-1.9,
            text=f"<b>Câmera {active_lead}: {deflection_text}</b>",
            showarrow=False,
            font=dict(size=14, color=deflection_color),
        )

    # --- Layout ---
    fig.update_layout(
        title=dict(
            text=f"Câmeras Cardíacas — {plane_title}",
            font=dict(size=18),
        ),
        xaxis=dict(
            range=[-2, 2], showgrid=False, zeroline=False,
            showticklabels=False, scaleanchor="y",
        ),
        yaxis=dict(
            range=[-2.2, 2], showgrid=False, zeroline=False,
            showticklabels=False,
        ),
        plot_bgcolor=_BG_COLOR,
        showlegend=False,
        width=700,
        height=700,
        margin=dict(l=20, r=20, t=60, b=40),
    )

    return fig


# ---------------------------------------------------------------------------
# create_deflection_animation_data
# ---------------------------------------------------------------------------

def create_deflection_animation_data(
    lead: str,
    vector_start: float,
    vector_end: float,
    n_frames: int = 60,
) -> Dict[str, Any]:
    """
    Retorna dados para animar como a deflexão muda conforme o vetor
    elétrico se move de vector_start a vector_end.

    Parameters
    ----------
    lead : str
        Nome da derivação.
    vector_start : float
        Ângulo inicial do vetor (graus).
    vector_end : float
        Ângulo final do vetor (graus).
    n_frames : int
        Número de frames da animação.

    Returns
    -------
    dict com:
        frames: list[dict] — cada frame tem vector_deg, deflection_amplitude,
                              deflection_type, explanation_pt
        lead: str
        lead_angle_deg: float
    """
    if lead not in LEAD_CAMERAS:
        raise ValueError(f"Derivação '{lead}' não encontrada.")

    lead_angle = LEAD_CAMERAS[lead]["angle_deg"]
    frames: List[Dict[str, Any]] = []

    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)
        angle = vector_start + t * (vector_end - vector_start)
        diff = _angle_difference(lead_angle, angle)

        # Amplitude: cos(diff) — positivo quando se aproxima, negativo quando foge
        amplitude = math.cos(math.radians(diff))

        if diff <= 80:
            dtype = "positiva"
        elif diff >= 100:
            dtype = "negativa"
        else:
            dtype = "bifásica"

        frames.append({
            "vector_deg": round(angle, 1),
            "deflection_amplitude": round(amplitude, 3),
            "deflection_type": dtype,
            "angle_diff": round(diff, 1),
            "explanation_pt": (
                f"Vetor a {angle:.0f}° | Câmera {lead} a {lead_angle}° | "
                f"Diferença: {diff:.0f}° → {dtype} (amplitude: {amplitude:.2f})"
            ),
        })

    return {
        "lead": lead,
        "lead_angle_deg": lead_angle,
        "frames": frames,
    }


# ---------------------------------------------------------------------------
# create_axis_wheel_figure
# ---------------------------------------------------------------------------

def create_axis_wheel_figure(angle_deg: float) -> go.Figure:
    """
    Cria a roda hexaxial de referência com ícones de câmera,
    destacando o eixo cardíaco informado.

    Parameters
    ----------
    angle_deg : float
        Eixo cardíaco em graus.

    Returns
    -------
    plotly.graph_objects.Figure
    """
    fig = go.Figure()

    # --- Draw reference circle ---
    circle_t = [i * 2 * math.pi / 200 for i in range(201)]
    circle_x = [math.cos(t) for t in circle_t]
    circle_y = [math.sin(t) for t in circle_t]
    fig.add_trace(go.Scatter(
        x=circle_x, y=circle_y,
        mode="lines",
        line=dict(color=_GRID_COLOR, width=1),
        hoverinfo="skip",
        showlegend=False,
    ))

    # --- Draw lead axes ---
    lead_colors = {
        "I": "#e74c3c", "II": "#2ecc71", "III": "#3498db",
        "aVR": "#9b59b6", "aVL": "#e67e22", "aVF": "#1abc9c",
    }

    for lead in _FRONTAL_LEADS:
        info = LEAD_CAMERAS[lead]
        la = info["angle_deg"]
        x1, y1 = _lead_xy(la, radius=1.0)
        x2, y2 = _lead_xy(la + 180, radius=1.0)
        color = lead_colors.get(lead, _CAMERA_COLOR)

        # Lead axis line
        fig.add_trace(go.Scatter(
            x=[x2, x1], y=[y2, y1],
            mode="lines",
            line=dict(color=color, width=1.5, dash="dash"),
            hoverinfo="skip",
            showlegend=False,
        ))

        # Positive pole label
        lx, ly = _lead_xy(la, radius=1.15)
        fig.add_annotation(
            x=lx, y=ly,
            text=f"<b>{lead}</b><br>{la}°",
            showarrow=False,
            font=dict(size=10, color=color),
        )

    # --- Draw the axis vector ---
    ax, ay = _lead_xy(angle_deg, radius=0.85)
    fig.add_trace(go.Scatter(
        x=[0, ax], y=[0, ay],
        mode="lines",
        line=dict(color=_VECTOR_COLOR, width=5),
        name=f"Eixo: {angle_deg}°",
    ))
    fig.add_annotation(
        x=ax, y=ay, ax=0, ay=0,
        xref="x", yref="y", axref="x", ayref="y",
        showarrow=True,
        arrowhead=3, arrowsize=2.5, arrowwidth=4,
        arrowcolor=_VECTOR_COLOR,
    )

    # --- Classification ---
    norm_angle = _normalize_angle(angle_deg)
    if -30 <= norm_angle <= 90:
        class_text = "EIXO NORMAL"
        class_color = "#27ae60"
    elif -90 <= norm_angle < -30:
        class_text = "DESVIO ESQUERDO"
        class_color = "#e67e22"
    elif 90 < norm_angle <= 180:
        class_text = "DESVIO DIREITO"
        class_color = "#e74c3c"
    else:
        class_text = "DESVIO EXTREMO"
        class_color = "#8e44ad"

    fig.add_annotation(
        x=0, y=-1.5,
        text=f"<b>Eixo: {angle_deg}° — {class_text}</b>",
        showarrow=False,
        font=dict(size=16, color=class_color),
    )

    # --- Normal zone shading ---
    # Shade the normal axis zone (-30° to 90°)
    zone_angles = list(range(-30, 91, 2))
    zone_x = [0] + [0.95 * math.cos(math.radians(a)) for a in zone_angles] + [0]
    zone_y = [0] + [0.95 * math.sin(math.radians(a)) for a in zone_angles] + [0]
    fig.add_trace(go.Scatter(
        x=zone_x, y=zone_y,
        fill="toself",
        fillcolor="rgba(39, 174, 96, 0.1)",
        line=dict(color="rgba(39, 174, 96, 0.3)", width=1),
        hoverinfo="skip",
        showlegend=False,
    ))

    # --- Layout ---
    fig.update_layout(
        title=dict(
            text="Roda Hexaxial — Câmeras Cardíacas",
            font=dict(size=18),
        ),
        xaxis=dict(
            range=[-1.6, 1.6], showgrid=False, zeroline=False,
            showticklabels=False, scaleanchor="y",
        ),
        yaxis=dict(
            range=[-1.7, 1.5], showgrid=False, zeroline=False,
            showticklabels=False,
        ),
        plot_bgcolor=_BG_COLOR,
        showlegend=False,
        width=650,
        height=700,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig

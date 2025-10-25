import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

dash.register_page(__name__, name="Laboratório de Fisiologia")

# --- Funções de Geração da Onda de ECG ---


def gaussian(x, mu, sig, amp):
    """Gera uma curva gaussiana."""
    return amp * np.exp(-np.power(x - mu, 2.0) / (2 * np.power(sig, 2.0)))


def generate_ecg_waveform(hr=60, pr_ms=160, qrs_ms=90, qt_ms=400, k_level=4.5, ca_level=9.5):
    """Gera uma forma de onda de ECG paramétrica."""
    rr_interval_s = 60.0 / hr
    t = np.linspace(0, rr_interval_s, int(rr_interval_s * 500))  # 500 Hz sampling rate

    # --- P wave ---
    p_wave = gaussian(t, 0.1, 0.025, 0.1)

    # --- QRS complex ---
    pr_s = pr_ms / 1000.0
    qrs_s = qrs_ms / 1000.0
    q_wave = gaussian(t, pr_s - qrs_s / 3, 0.008, -0.2)
    r_wave = gaussian(t, pr_s, 0.01, 1.5)
    s_wave = gaussian(t, pr_s + qrs_s / 3, 0.015, -0.4)
    qrs_complex = q_wave + r_wave + s_wave

    # --- T wave (influenciada por K+ e Ca2+) ---
    qt_s = qt_ms / 1000.0
    t_wave_center = pr_s + qt_s - qrs_s / 2 - 0.1  # Heurística para o centro da onda T

    # Influência do Potássio (K+) na amplitude da onda T
    t_amp = 0.35 + (k_level - 4.5) * 0.2
    # Influência do Potássio (K+) na largura da onda T
    t_width = 0.04 + (k_level - 4.5) * 0.01

    t_wave = gaussian(t, t_wave_center, t_width, t_amp)

    # --- U wave (influenciada por K+) ---
    u_wave = np.zeros_like(t)
    if k_level < 3.5:
        u_amp = 0.15 * (3.5 - k_level)
        u_wave = gaussian(t, t_wave_center + 0.15, 0.04, u_amp)

    # Combina todas as ondas
    waveform = p_wave + qrs_complex + t_wave + u_wave
    return t, waveform


# --- Layout da Página ---

controls = dbc.Card(
    [
        dbc.CardHeader("Controles Fisiológicos"),
        dbc.CardBody(
            [
                dbc.Label("Frequência Cardíaca (bpm)"),
                dcc.Slider(
                    id="hr-slider",
                    min=30,
                    max=150,
                    step=5,
                    value=60,
                    marks={30: "30", 60: "60", 90: "90", 120: "120", 150: "150"},
                ),
                html.Hr(),
                dbc.Label("Potássio [K+] (mEq/L)"),
                dcc.Slider(
                    id="k-slider",
                    min=2.5,
                    max=8.0,
                    step=0.5,
                    value=4.5,
                    marks={2.5: "2.5", 4.5: "4.5", 6.0: "6.0", 8.0: "8.0"},
                ),
                html.Hr(),
                dbc.Label("Cálcio [Ca2+] (mg/dL) - Afeta QT"),
                dcc.Slider(
                    id="ca-slider",
                    min=7.0,
                    max=13.0,
                    step=0.5,
                    value=9.5,
                    marks={7: "7", 9.5: "9.5", 11: "11", 13: "13"},
                ),
                html.Hr(),
                dbc.Label("Intervalo PR (ms)"),
                dcc.Slider(
                    id="pr-slider",
                    min=100,
                    max=300,
                    step=10,
                    value=160,
                    marks={100: "100", 200: "200", 300: "300"},
                ),
                html.Hr(),
                dbc.Label("Duração QRS (ms)"),
                dcc.Slider(
                    id="qrs-slider",
                    min=70,
                    max=180,
                    step=10,
                    value=90,
                    marks={70: "70", 120: "120", 180: "180"},
                ),
            ]
        ),
    ],
    className="mb-3",
)

layout = dbc.Container(
    [
        html.H1("Laboratório Interativo de Fisiologia do ECG"),
        html.P(
            "Use os sliders para alterar os parâmetros e observar o impacto na forma de onda do ECG em tempo real."
        ),
        dbc.Row(
            [
                dbc.Col(controls, md=4),
                dbc.Col(
                    [dcc.Graph(id="ecg-graph"), dbc.Alert(id="feedback-panel", color="info")], md=8
                ),
            ]
        ),
    ],
    fluid=True,
)

# --- Callback para atualizar o gráfico e o feedback ---


@callback(
    Output("ecg-graph", "figure"),
    Output("feedback-panel", "children"),
    Input("hr-slider", "value"),
    Input("k-slider", "value"),
    Input("ca-slider", "value"),
    Input("pr-slider", "value"),
    Input("qrs-slider", "value"),
)
def update_ecg_lab(hr, k_level, ca_level, pr_ms, qrs_ms):
    # Ajusta o intervalo QT com base no Cálcio e na FC (fórmula de Bazett simplificada)
    qt_base_ms = 400 - (ca_level - 9.5) * 20
    rr_s = 60.0 / hr
    qtc_ms = qt_base_ms / (rr_s**0.5)
    qt_ms = qtc_ms * (rr_s**0.5)

    t, waveform = generate_ecg_waveform(hr, pr_ms, qrs_ms, qt_ms, k_level, ca_level)

    # Cria a figura
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=waveform, mode="lines", name="ECG"))
    fig.update_layout(
        title="Forma de Onda de ECG Simulada",
        xaxis_title="Tempo (s)",
        yaxis_title="Amplitude (mV)",
        yaxis_range=[-1, 2],
        template="plotly_white",
    )

    # Gera o feedback textual
    feedback = []
    if k_level > 5.5:
        feedback.append(html.Strong("Hipercalemia:"))
        feedback.append(" Ondas T altas e apiculadas. QRS pode alargar.")
    if k_level < 3.5:
        feedback.append(html.Strong("Hipocalemia:"))
        feedback.append(" Ondas T achatadas, surgimento de ondas U.")
    if ca_level > 10.5:
        feedback.append(html.Strong("Hipercalcemia:"))
        feedback.append(" Encurtamento do intervalo QT.")
    if ca_level < 8.5:
        feedback.append(html.Strong("Hipocalcemia:"))
        feedback.append(" Prolongamento do intervalo QT.")
    if pr_ms > 200:
        feedback.append(html.Strong("Bloqueio AV de 1º Grau:"))
        feedback.append(" Intervalo PR > 200ms.")
    if qrs_ms > 120:
        feedback.append(html.Strong("QRS Alargado:"))
        feedback.append(" Pode indicar um bloqueio de ramo.")

    if not feedback:
        feedback.append("Parâmetros dentro da faixa de normalidade.")

    return fig, html.Div(feedback)

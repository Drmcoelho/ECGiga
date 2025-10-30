import base64
import time
from io import BytesIO

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, dcc, html, long_callback, no_update
from PIL import Image

dash.register_page(__name__, name="Análise Comparativa")


# --- Funções de Utilidade (similares às de analysis.py) ---
def decode_image(content):
    header, b64 = content.split(",")
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")


def run_ecg_pipeline(set_progress, content, filename, start_step, total_steps):
    """Executa o pipeline de análise para um único ECG."""
    if not content:
        return None, None, go.Figure().update_layout(title="Aguardando imagem...")

    summary = [f"**Arquivo: {filename}**"]

    # 1. Decodificar
    set_progress((start_step, total_steps))
    img = decode_image(content)
    summary.append("1. Imagem decodificada.")
    time.sleep(0.2)

    # 2. Pré-processamento (simulado)
    set_progress((start_step + 1, total_steps))
    summary.append("2. Pré-processamento (deskew/normalize) concluído.")
    time.sleep(0.3)

    # 3. Detecção de Layout (simulado)
    set_progress((start_step + 2, total_steps))
    summary.append("3. Layout e grid detectados.")
    time.sleep(0.3)

    # 4. Análise Principal (simulada)
    set_progress((start_step + 3, total_steps))
    # Simula um resultado de análise
    report = {
        "hr": np.random.randint(50, 90),
        "pr": np.random.randint(150, 210),
        "qrs": np.random.randint(80, 110),
        "qtc": np.random.randint(400, 450),
        "axis": np.random.randint(-10, 80),
    }
    summary.append(f"- FC: {report['hr']} bpm")
    summary.append(f"- PR: {report['pr']} ms")
    summary.append(f"- QRS: {report['qrs']} ms")
    summary.append(f"- QTc: {report['qtc']} ms")
    summary.append(f"- Eixo: {report['axis']}°")
    time.sleep(0.5)

    # 5. Gerar Figura
    set_progress((start_step + 4, total_steps))
    w, h = img.size
    fig = go.Figure()
    fig.add_layout_image(
        dict(
            source=img,
            xref="x",
            yref="y",
            x=0,
            y=h,
            sizex=w,
            sizey=h,
            sizing="stretch",
            layer="below",
        )
    )
    fig.update_layout(title=f"Preview de {filename}", margin=dict(l=0, r=0, t=40, b=0))

    return report, "\n".join(summary), fig


def create_comparison_card(id_prefix):
    """Cria um card de upload e resultado para um ECG."""
    return dbc.Card(
        [
            dbc.CardHeader(f"ECG {id_prefix.upper()}"),
            dbc.CardBody(
                [
                    dcc.Upload(
                        id=f"upload-ecg-{id_prefix}",
                        children=["Arraste ou ", html.A("selecione")],
                        style={
                            "width": "100%",
                            "height": "60px",
                            "lineHeight": "60px",
                            "borderWidth": "1px",
                            "borderStyle": "dashed",
                            "borderRadius": "5px",
                            "textAlign": "center",
                            "marginBottom": "10px",
                        },
                    ),
                    dcc.Graph(id=f"graph-{id_prefix}"),
                    dbc.Alert("Aguardando análise...", id=f"summary-{id_prefix}"),
                ]
            ),
        ]
    )


# --- Layout da Página ---

layout = dbc.Container(
    [
        html.H1("Análise Comparativa de ECGs"),
        html.P("Faça o upload de dois ECGs para analisá-los e comparar os resultados lado a lado."),
        dbc.Row(
            [
                dbc.Col(create_comparison_card("a"), md=4),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Comparação"),
                            dbc.CardBody(
                                [
                                    dbc.Button(
                                        "Comparar ECGs",
                                        id="btn-compare",
                                        color="primary",
                                        className="w-100 mb-3",
                                    ),
                                    dbc.Progress(
                                        id="progress-bar-compare",
                                        style={"height": "20px"},
                                        className="mb-3",
                                    ),
                                    dbc.Spinner(html.Div(id="spinner-compare-dummy")),
                                    dbc.Alert(id="comparison-results", color="info"),
                                ]
                            ),
                        ]
                    ),
                    md=4,
                ),
                dbc.Col(create_comparison_card("b"), md=4),
            ]
        ),
    ],
    fluid=True,
)

# --- Callback ---


@long_callback(
    Output("graph-a", "figure"),
    Output("summary-a", "children"),
    Output("graph-b", "figure"),
    Output("summary-b", "children"),
    Output("comparison-results", "children"),
    Input("btn-compare", "n_clicks"),
    State("upload-ecg-a", "contents"),
    State("upload-ecg-a", "filename"),
    State("upload-ecg-b", "contents"),
    State("upload-ecg-b", "filename"),
    running=[
        (Output("btn-compare", "disabled"), True, False),
        (Output("spinner-compare-dummy", "children"), dbc.Spinner(size="lg"), ""),
    ],
    progress=Output("progress-bar-compare", "value"),
    prevent_initial_call=True,
)
def compare_ecgs_callback(set_progress, n_clicks, content_a, filename_a, content_b, filename_b):
    if not content_a or not content_b:
        return no_update, no_update, no_update, no_update, "Por favor, envie dois arquivos de ECG."

    total_steps = 10
    report_a, summary_a, fig_a = run_ecg_pipeline(
        set_progress, content_a, filename_a, 0, total_steps
    )
    report_b, summary_b, fig_b = run_ecg_pipeline(
        set_progress, content_b, filename_b, 5, total_steps
    )

    # Gerar a tabela de comparação
    header = [
        html.Thead(
            html.Tr([html.Th("Parâmetro"), html.Th("ECG A"), html.Th("ECG B"), html.Th("Delta")])
        )
    ]

    def get_delta_row(param, unit):
        val_a = report_a[param]
        val_b = report_b[param]
        delta = val_b - val_a
        color = "danger" if abs(delta) > 0.15 * val_a else "secondary"
        return html.Tr(
            [
                html.Td(param.upper()),
                html.Td(f"{val_a} {unit}"),
                html.Td(f"{val_b} {unit}"),
                html.Td(dbc.Badge(f"{delta:+.0f} {unit}", color=color)),
            ]
        )

    body = [
        html.Tbody(
            [
                get_delta_row("hr", "bpm"),
                get_delta_row("pr", "ms"),
                get_delta_row("qrs", "ms"),
                get_delta_row("qtc", "ms"),
                get_delta_row("axis", "°"),
            ]
        )
    ]

    comparison_table = dbc.Table(header + body, bordered=True, striped=True, hover=True)

    return fig_a, summary_a, fig_b, summary_b, comparison_table

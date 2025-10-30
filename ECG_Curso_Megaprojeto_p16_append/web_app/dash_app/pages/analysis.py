import base64
import time
from io import BytesIO

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, dcc, html, long_callback, no_update
from PIL import Image

dash.register_page(__name__, path="/", name="Análise ao Vivo")


# --- Funções de Utilidade ---
def decode_image(content):
    header, b64 = content.split(",")
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")


def make_overlay_figure(img, seg=None, title="Preview do ECG"):
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
    shapes, annotations = [], []
    if seg and seg.get("leads"):
        for ld in seg["leads"]:
            x0, y0, x1, y1 = ld["bbox"]
            shapes.append(
                dict(
                    type="rect",
                    x0=x0,
                    y0=h - y1,
                    x1=x1,
                    y1=h - y0,
                    line=dict(width=2, color="cyan"),
                )
            )
            annotations.append(
                dict(
                    x=(x0 + x1) / 2,
                    y=h - y1 + 15,
                    text=ld.get("lead", "?"),
                    showarrow=False,
                    bgcolor="rgba(255,255,255,0.5)",
                )
            )
    fig.update_layout(
        title=title,
        xaxis=dict(visible=False, range=[0, w]),
        yaxis=dict(visible=False, range=[0, h], scaleanchor="x", scaleratio=1),
        shapes=shapes,
        annotations=annotations,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


# --- Layout da Página ---

analysis_controls = dbc.Card(
    [
        dbc.CardHeader(html.H3("Upload e Análise de ECG")),
        dbc.CardBody(
            [
                dcc.Upload(
                    id="upload-ecg",
                    children=html.Div(["Arraste e solte ou ", html.A("selecione um arquivo")]),
                    multiple=False,
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
                dcc.Textarea(
                    id="upload-meta",
                    placeholder="Cole o sidecar META (JSON) opcional...",
                    style={"width": "100%", "height": "80px"},
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Checklist(
                                id="ops",
                                options=[
                                    {"label": "Deskew", "value": "deskew"},
                                    {"label": "Normalize", "value": "normalize"},
                                ],
                                value=[],
                                inline=True,
                            ),
                            width="auto",
                        ),
                        dbc.Col(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText("Layout"),
                                    dcc.Dropdown(
                                        id="layout-select",
                                        options=[
                                            {"label": "3x4", "value": "3x4"},
                                            {"label": "6x2", "value": "6x2"},
                                        ],
                                        value="3x4",
                                        clearable=False,
                                    ),
                                ],
                                size="sm",
                            ),
                            width="auto",
                        ),
                    ],
                    align="center",
                    className="mb-2",
                ),
                html.Div(
                    [
                        dbc.Button(
                            "Processar Imagem", id="btn-process", n_clicks=0, color="primary"
                        ),
                        dbc.Spinner(html.Div(id="spinner-dummy"), color="primary"),
                    ],
                    style={"display": "flex", "gap": "15px", "alignItems": "center"},
                    className="mb-2",
                ),
                dbc.Progress(id="progress-bar", style={"height": "20px"}, className="mb-2"),
                html.Div(
                    id="upload-summary",
                    style={
                        "whiteSpace": "pre-wrap",
                        "maxHeight": "250px",
                        "overflowY": "auto",
                        "border": "1px solid #ccc",
                        "padding": "10px",
                    },
                ),
            ]
        ),
    ]
)

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(analysis_controls, md=4),
                dbc.Col(
                    dcc.Graph(
                        id="overlay-graph",
                        figure=go.Figure().update_layout(title="Aguardando imagem..."),
                    ),
                    md=8,
                ),
            ]
        )
    ],
    fluid=True,
)

# --- Callback em Background ---


@long_callback(
    Output("overlay-graph", "figure"),
    Output("upload-summary", "children"),
    Input("btn-process", "n_clicks"),
    State("upload-ecg", "contents"),
    State("upload-ecg", "filename"),
    State("upload-meta", "value"),
    State("ops", "value"),
    State("layout-select", "value"),
    running=[
        (Output("btn-process", "disabled"), True, False),
        (Output("spinner-dummy", "children"), dbc.Spinner(size="sm"), ""),
    ],
    progress=Output("progress-bar", "value"),
    prevent_initial_call=True,
)
def process_image_callback(set_progress, n_clicks, content, filename, meta_text, ops, layout):
    if not content:
        return no_update, no_update

    total_steps = 5
    summary = [f"Arquivo: {filename}"]

    # 1. Decodificar Imagem
    set_progress((1, total_steps))
    img = decode_image(content)
    summary.append("1. Imagem decodificada.")
    time.sleep(0.5)

    # 2. Pré-processamento
    set_progress((2, total_steps))
    if "deskew" in ops:
        from cv.deskew import estimate_rotation_angle, rotate_image

        info = estimate_rotation_angle(img)
        img = rotate_image(img, info["angle_deg"])
        summary.append(f"2a. Deskew aplicado (ângulo: {info['angle_deg']:.2f}°).")
    if "normalize" in ops:
        from cv.normalize import normalize_scale

        img, _, _ = normalize_scale(img, 10.0)
        summary.append("2b. Escala normalizada.")
    time.sleep(0.5)

    # 3. Detecção de Grid e Layout
    set_progress((3, total_steps))
    from cv.grid_detect import estimate_grid_period_px
    from cv.lead_ocr import detect_labels_per_box
    from cv.segmentation_ext import segment_layout

    arr = np.asarray(img.convert("L"))
    grid = estimate_grid_period_px(arr)
    leads_boxes = segment_layout(arr, layout=layout)
    labels = detect_labels_per_box(arr, [d["bbox"] for d in leads_boxes])
    for i, l_info in enumerate(labels):
        if l_info.get("label"):
            leads_boxes[i]["lead"] = l_info["label"]
    seg = {"leads": leads_boxes}
    summary.append("3. Layout e grid detectados.")
    time.sleep(0.5)

    # 4. Análise Principal (simulada com placeholders)
    set_progress((4, total_steps))
    summary.append("4. Executando análise de R-peaks, intervalos e eixo...")
    # A chamada real aos módulos `cv/rpeaks_robust.py`, `cv/intervals_refined.py`, etc., entraria aqui.
    time.sleep(1.5)  # Simula trabalho pesado

    # 5. Geração do Relatório
    set_progress((5, total_steps))
    summary.append("5. Análise concluída. Gerando visualização.")
    fig = make_overlay_figure(img, seg, title=f"Análise de {filename}")
    time.sleep(0.5)

    return fig, "\n".join(summary)

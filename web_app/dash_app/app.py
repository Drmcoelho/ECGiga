import base64
import json
from io import BytesIO

import dash
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, dcc, html
from PIL import Image

app = dash.Dash(__name__)
app.title = "ECG Dash — p4 (upload + overlay + QTc + 12 leads)"


def synth_wave(phase=0.0, n=2000):
    t = np.linspace(0, 1, n)
    base = 0.02 * np.sin(2 * np.pi * 2 * t + phase)
    qrs = np.exp(-((t - 0.3) ** 2) / (2 * 0.0003)) - 0.25 * np.exp(
        -((t - 0.31) ** 2) / (2 * 0.00015)
    )
    p = 0.05 * np.exp(-((t - 0.2) ** 2) / (2 * 0.0012))
    tw = 0.1 * np.exp(-((t - 0.52) ** 2) / (2 * 0.008))
    return base + p + qrs + tw


leads = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
series = [synth_wave(phase=i * 0.1) for i in range(len(leads))]
traces = [
    go.Scatter(y=series[i], mode="lines", name=leads[i], visible=True) for i in range(len(leads))
]
layout = go.Layout(
    title="12 derivações sintéticas — zoom habilitado",
    legend=dict(orientation="h"),
    xaxis=dict(title="Tempo (s)"),
    yaxis=dict(title="mV"),
)
fig_synth = go.Figure(data=traces, layout=layout)


def decode_image(content):
    header, b64 = content.split(",")
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")


def make_overlay_figure(img, seg):
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
    shapes = []
    annotations = []
    if seg and seg.get("leads"):
        for ld in seg["leads"]:
            x0, y0, x1, y1 = ld["bbox"]
            shapes.append(dict(type="rect", x0=x0, y0=h - y1, x1=x1, y1=h - y0, line=dict(width=2)))
            annotations.append(
                dict(
                    x=(x0 + x1) / 2,
                    y=h - y1 + 15,
                    text=ld["lead"],
                    showarrow=False,
                    bgcolor="rgba(255,255,255,0.4)",
                )
            )
    fig.update_layout(
        title="Overlay — Segmentação 12 derivações (básica)",
        xaxis=dict(visible=False, range=[0, w]),
        yaxis=dict(visible=False, range=[0, h], scaleanchor="x", scaleratio=1),
        shapes=shapes,
        annotations=annotations,
        margin=dict(l=0, r=0, t=30, b=0),
        height=min(800, int(800 * w / h)),
    )
    return fig


def qtc_b(qt_ms, rr_ms):
    return qt_ms / ((rr_ms / 1000.0) ** 0.5)


def qtc_f(qt_ms, rr_ms):
    return qt_ms / ((rr_ms / 1000.0) ** (1 / 3))


def axis_label_from(I, aVF):
    if I is None or aVF is None:
        return None
    if I >= 0 and aVF >= 0:
        return "Normal"
    if I >= 0 and aVF < 0:
        return "Desvio para a esquerda"
    if I < 0 and aVF >= 0:
        return "Desvio para a direita"
    return "Desvio extremo (noroeste)"


app.layout = html.Div(
    [
        html.H2(
            "ECG Dashboard (p4) — Upload + Overlay 12D + Calculadora QTc + 12 leads sintéticos"
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Upload de ECG (PNG/JPG)"),
                        dcc.Upload(
                            id="upload-ecg",
                            children=html.Div(
                                ["Arraste e solte ou ", html.A("selecione um arquivo")]
                            ),
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
                            style={"width": "100%", "height": "120px"},
                        ),
                        html.Div(
                            [
                                dcc.Checklist(
                                    id="ops",
                                    options=[
                                        {"label": "Deskew", "value": "deskew"},
                                        {"label": "Normalize (px/mm≈10)", "value": "normalize"},
                                    ],
                                    value=[],
                                ),
                                html.Label("Layout"),
                                dcc.Dropdown(
                                    id="layout-select",
                                    options=[
                                        {"label": "3x4", "value": "3x4"},
                                        {"label": "6x2", "value": "6x2"},
                                        {"label": "3x4 + ritmo (II)", "value": "3x4+rhythm"},
                                    ],
                                    value="3x4",
                                    clearable=False,
                                    style={"width": "260px"},
                                ),
                            ],
                            style={
                                "display": "flex",
                                "gap": "16px",
                                "alignItems": "center",
                                "marginBottom": "8px",
                            },
                        ),
                        html.Button("Processar", id="btn-process", n_clicks=0),
                        html.Div(
                            id="upload-summary",
                            style={"marginTop": "10px", "whiteSpace": "pre-wrap"},
                        ),
                        html.Div(
                            [
                                html.Label("Lead para FC (R-peaks)"),
                                dcc.Dropdown(
                                    id="lead-select",
                                    options=[{"label": l, "value": l} for l in ["II", "V2", "V5"]],
                                    value="II",
                                    clearable=False,
                                    style={"width": "200px"},
                                ),
                                html.Button("R-peaks robustos", id="btn-rrob", n_clicks=0),
                                html.Button(
                                    "Intervalos (PR/QRS/QT/QTc)", id="btn-intervals", n_clicks=0
                                ),
                                html.Button("Eixo (I/aVF)", id="btn-axis", n_clicks=0),
                            ],
                            style={
                                "display": "flex",
                                "gap": "12px",
                                "alignItems": "center",
                                "marginTop": "8px",
                            },
                        ),
                        dcc.Graph(id="overlay", figure=go.Figure()),
                    ],
                    className="card",
                    style={"maxWidth": "900px"},
                )
            ],
            style={"marginBottom": "16px"},
        ),
        html.Div(
            [
                html.H3("Calculadora QTc (rápida)"),
                html.Label("QT (ms)"),
                dcc.Input(id="qt-ms", type="number", value=400, step=1),
                html.Label("RR (ms)"),
                dcc.Input(id="rr-ms", type="number", value=800, step=1),
                html.Div(id="qtc-out", style={"marginTop": "8px", "fontWeight": "bold"}),
            ],
            className="card",
            style={"maxWidth": "520px", "marginBottom": "16px"},
        ),
        dcc.Graph(id="ecg12", figure=fig_synth),
    ]
)


@app.callback(
    Output("overlay", "figure"),
    Output("upload-summary", "children"),
    Input("btn-process", "n_clicks"),
    Input("btn-hr", "n_clicks"),
    Input("btn-rrob", "n_clicks"),
    Input("btn-intervals", "n_clicks"),
    Input("btn-axis", "n_clicks"),
    State("upload-ecg", "contents"),
    State("upload-ecg", "filename"),
    State("upload-meta", "value"),
    State("ops", "value"),
    State("layout-select", "value"),
    prevent_initial_call=True,
)
def process(n, nhr, nrrob, nintv, naxis, content, filename, meta_text, ops, layout):
    if not content:
        return go.Figure(), "Nenhuma imagem enviada."
    img = decode_image(content)
    # pré-processo: deskew/normalize
    if ops and "deskew" in ops:
        from cv.deskew import estimate_rotation_angle, rotate_image

        info = estimate_rotation_angle(img, search_deg=6.0, step=0.5)
        img = rotate_image(img, info["angle_deg"])
    if ops and "normalize" in ops:
        from cv.normalize import normalize_scale

        img, scale, pxmm = normalize_scale(img, 10.0)
    # META opcional
    meta = None
    if meta_text:
        try:
            meta = json.loads(meta_text)
        except Exception as e:
            meta = {"_error": f"Falha lendo META: {e}"}

    # Grid + segmentação básica (servidor)
    from cv.grid_detect import estimate_grid_period_px
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout

    arr = np.asarray(img.convert("L"))
    grid = estimate_grid_period_px(np.asarray(img))
    bbox = find_content_bbox(arr)
    leads = segment_layout(arr, layout=layout, bbox=bbox)
    from cv.lead_ocr import detect_labels_per_box

    seg = {"content_bbox": bbox, "leads": leads}
    labels = detect_labels_per_box(arr, [d["bbox"] for d in leads])
    summary = [
        f"Arquivo: {filename}",
        f"Layout: {layout}",
        f"Rótulos detectados: {sum(1 for d in labels if d.get('label'))}/{len(labels)}",
        f"Grid small≈{grid.get('px_small_x') or grid.get('px_small_y'):.1f}px, big≈{grid.get('px_big_x') or grid.get('px_big_y'):.1f}px (conf {grid.get('confidence',0):.2f})",
        f"Content bbox: {bbox} | Leads: {len(leads)}",
    ]
    if meta and isinstance(meta, dict):
        m = meta.get("measures", {})
        qt = m.get("qt_ms")
        rr = m.get("rr_ms") or (60000.0 / (m.get("fc_bpm") or 0) if m.get("fc_bpm") else None)
        if qt and rr:
            summary.append(f"QT: {qt} ms | QTc (B/F): {qtc_b(qt, rr):.1f}/{qtc_f(qt, rr):.1f} ms")
    # Se solicitado Estimar FC, calcula em lead selecionável (II por padrão)
    from cv.intervals import intervals_from_trace
    from cv.rpeaks_from_image import estimate_px_per_sec, extract_trace_centerline, smooth_signal
    from cv.rpeaks_robust import pan_tompkins_like

    # estimadores (opcionais, via botões)
    if nrrob or nintv:
        lab = "II"
        lab2box = {d["lead"]: d["bbox"] for d in leads}
        if lab in lab2box:
            x0, y0, x1, y1 = lab2box[lab]
            crop = arr[y0:y1, x0:x1]
            trace = smooth_signal(extract_trace_centerline(crop), win=11)
            from cv.grid_detect import estimate_grid_period_px

            pxmm = estimate_grid_period_px(np.asarray(img)).get(
                "px_small_x"
            ) or estimate_grid_period_px(np.asarray(img)).get("px_small_y")
            pxsec = estimate_px_per_sec(pxmm, 25.0) or 250.0
            if nrrob:
                rdet = pan_tompkins_like(trace, pxsec)
                summary.append(
                    f"R-peaks robustos: {len(rdet['peaks_idx'])} picos (fs≈{pxsec:.1f} px/s)"
                )
            if nintv:
                rdet = pan_tompkins_like(trace, pxsec)
                iv = intervals_from_trace(trace, rdet["peaks_idx"], pxsec)
                m = iv["median"]
                summary.append(
                    f"PR {m.get('PR_ms')} ms | QRS {m.get('QRS_ms')} ms | QT {m.get('QT_ms')} ms | QTcB {m.get('QTc_B')} ms | QTcF {m.get('QTc_F')} ms"
                )
    if naxis:
        from cv.axis import frontal_axis_from_image

        lab2box = {d["lead"]: d["bbox"] for d in leads}
        from cv.grid_detect import estimate_grid_period_px
        from cv.rpeaks_from_image import (
            estimate_px_per_sec,
            extract_trace_centerline,
            smooth_signal,
        )
        from cv.rpeaks_robust import pan_tompkins_like

        lab = "II"
        if "I" in lab2box and "aVF" in lab2box:
            arrL = np.asarray(img.convert("L"))
            x0, y0, x1, y1 = lab2box[lab] if lab in lab2box else list(lab2box.values())[0]["bbox"]
            crop = arrL[y0:y1, x0:x1]
            trace = smooth_signal(extract_trace_centerline(crop), win=11)
            pxmm = estimate_grid_period_px(np.asarray(img)).get(
                "px_small_x"
            ) or estimate_grid_period_px(np.asarray(img)).get("px_small_y")
            pxsec = estimate_px_per_sec(pxmm, 25.0) or 250.0
            rdet = pan_tompkins_like(trace, pxsec)
            axis = frontal_axis_from_image(
                arrL,
                {"I": lab2box["I"], "aVF": lab2box["aVF"]},
                {"I": rdet["peaks_idx"], "aVF": rdet["peaks_idx"]},
                {"I": pxsec, "aVF": pxsec},
            )
            summary.append(f"Eixo: {axis.get('angle_deg',0):.1f}° — {axis.get('label','?')}")
    fig = make_overlay_figure(img, seg)
    return fig, "\n".join(summary)


@app.callback(Output("qtc-out", "children"), [Input("qt-ms", "value"), Input("rr-ms", "value")])
def calc_qtc(qt, rr):
    if not qt or not rr or rr <= 0:
        return "Informe QT e RR em ms."
    return f"QTc Bazett: {qtc_b(qt, rr):.1f} ms | QTc Fridericia: {qtc_f(qt, rr):.1f} ms"


if __name__ == "__main__":
    app.run(debug=True)

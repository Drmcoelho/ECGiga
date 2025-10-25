
import dash
from dash import html, dcc, Input, Output, State
import plotly.graph_objs as go
import numpy as np, base64, json

app = dash.Dash(__name__)
app.title = "ECG Dash — p3 (upload + QTc + 12 leads)"

def synth_wave(phase=0.0, n=2000):
    t = np.linspace(0, 1, n)
    base = 0.02*np.sin(2*np.pi*2*t + phase)
    qrs = (np.exp(-((t-0.3)**2)/(2*0.0003)) - 0.25*np.exp(-((t-0.31)**2)/(2*0.00015)))
    p = 0.05*np.exp(-((t-0.2)**2)/(2*0.0012))
    tw = 0.1*np.exp(-((t-0.52)**2)/(2*0.008))
    return base + p + qrs + tw

leads = ["I","II","III","aVR","aVL","aVF","V1","V2","V3","V4","V5","V6"]
series = [synth_wave(phase=i*0.1) for i in range(len(leads))]
traces = [go.Scatter(y=series[i], mode="lines", name=leads[i], visible=True) for i in range(len(leads))]
layout = go.Layout(title="12 derivações sintéticas — zoom habilitado",
                   legend=dict(orientation="h"), xaxis=dict(title="Tempo (s)"),
                   yaxis=dict(title="mV"))
fig = go.Figure(data=traces, layout=layout)

def qtc_b(qt_ms, rr_ms):
    return qt_ms/((rr_ms/1000.0)**0.5)

def qtc_f(qt_ms, rr_ms):
    return qt_ms/((rr_ms/1000.0)**(1/3))

def axis_label_from(I, aVF):
    if I is None or aVF is None: return None
    if I>=0 and aVF>=0: return "Normal"
    if I>=0 and aVF<0: return "Desvio para a esquerda"
    if I<0 and aVF>=0: return "Desvio para a direita"
    return "Desvio extremo (noroeste)"

app.layout = html.Div([
    html.H2("ECG Dashboard (p3) — Upload + Calculadora QTc + 12 leads"),
    html.Div([
        html.Div([
            html.H3("Upload de ECG (PNG/JPG)"),
            dcc.Upload(
                id='upload-ecg', children=html.Div(['Arraste e solte ou ', html.A('selecione um arquivo')]),
                multiple=False, style={'width':'100%','height':'60px','lineHeight':'60px','borderWidth':'1px','borderStyle':'dashed','borderRadius':'5px','textAlign':'center','marginBottom':'10px'}
            ),
            dcc.Textarea(id="upload-meta", placeholder="Cole aqui o conteúdo do sidecar META (JSON) se desejar...", style={"width":"100%","height":"120px"}),
            html.Button("Processar", id="btn-process", n_clicks=0),
            html.Div(id="upload-summary", style={"marginTop":"10px","whiteSpace":"pre-wrap"}),
            html.Img(id="upload-preview", style={"maxWidth":"100%","marginTop":"10px"}),
        ], className="card", style={"maxWidth":"680px"})
    ], style={"marginBottom":"16px"}),
    html.Div([
        html.H3("Calculadora QTc (rápida)"),
        html.Label("QT (ms)"), dcc.Input(id="qt-ms", type="number", value=400, step=1),
        html.Label("RR (ms)"), dcc.Input(id="rr-ms", type="number", value=800, step=1),
        html.Div(id="qtc-out", style={"marginTop":"8px","fontWeight":"bold"}),
    ], className="card", style={"maxWidth":"520px","marginBottom":"16px"}),
    dcc.Graph(id="ecg12", figure=fig)
])

@app.callback(
    Output("upload-preview","src"),
    Output("upload-summary","children"),
    Input("btn-process","n_clicks"),
    State("upload-ecg","contents"),
    State("upload-ecg","filename"),
    State("upload-meta","value"),
    prevent_initial_call=True
)
def process(n, content, filename, meta_text):
    if not content:
        return None, "Nenhuma imagem enviada."
    header, b64 = content.split(","); 
    # META opcional
    meta = None
    if meta_text:
        try: meta = json.loads(meta_text)
        except Exception as e: meta = {"_error": f"Falha lendo META: {e}"}
    summary = [f"Arquivo: {filename}"]
    if meta: summary.append("META: detectado")
    if meta and isinstance(meta, dict):
        m = meta.get("measures", {})
        qt = m.get("qt_ms"); rr = m.get("rr_ms") or (60000.0/(m.get("fc_bpm") or 0) if m.get("fc_bpm") else None)
        if qt and rr:
            summary.append(f"QT: {qt} ms | QTc (B/F): {qtc_b(qt, rr):.1f}/{qtc_f(qt, rr):.1f} ms")
        I = m.get("lead_i_mv"); aVF = m.get("avf_mv")
        if I is not None and aVF is not None:
            summary.append(f"Eixo (I/aVF): {axis_label_from(I,aVF)}")
    return content, "\n".join(summary)

@app.callback(Output("qtc-out","children"), [Input("qt-ms","value"), Input("rr-ms","value")])
def calc_qtc(qt, rr):
    if not qt or not rr or rr<=0: return "Informe QT e RR em ms."
    return f"QTc Bazett: {qtc_b(qt, rr):.1f} ms | QTc Fridericia: {qtc_f(qt, rr):.1f} ms"

if __name__ == "__main__":
    app.run(debug=True)

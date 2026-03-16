
import dash
from dash import html, dcc, Input, Output, State, ctx
import plotly.graph_objs as go
import numpy as np, base64, json
from PIL import Image
from io import BytesIO

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "ECGiga — Plataforma Educacional de ECG"

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
fig_layout = go.Layout(title="12 derivações sintéticas — zoom habilitado",
                   legend=dict(orientation="h"), xaxis=dict(title="Tempo (s)"),
                   yaxis=dict(title="mV"))
fig_synth = go.Figure(data=traces, layout=fig_layout)

def decode_image(content):
    header, b64 = content.split(",")
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")

def make_overlay_figure(img, seg):
    w, h = img.size
    fig = go.Figure()
    fig.add_layout_image(
        dict(source=img, xref="x", yref="y", x=0, y=h, sizex=w, sizey=h, sizing="stretch", layer="below")
    )
    shapes = []
    annotations = []
    if seg and seg.get("leads"):
        for ld in seg["leads"]:
            x0,y0,x1,y1 = ld["bbox"]
            shapes.append(dict(type="rect", x0=x0, y0=h-y1, x1=x1, y1=h-y0, line=dict(width=2)))
            annotations.append(dict(x=(x0+x1)/2, y=h-y1+15, text=ld["lead"], showarrow=False, bgcolor="rgba(255,255,255,0.4)"))
    fig.update_layout(
        title="Overlay — Segmentação 12 derivações (básica)",
        xaxis=dict(visible=False, range=[0, w]),
        yaxis=dict(visible=False, range=[0, h], scaleanchor="x", scaleratio=1),
        shapes=shapes, annotations=annotations, margin=dict(l=0,r=0,t=30,b=0), height=min(800, int(800*w/h))
    )
    return fig

def qtc_b(qt_ms, rr_ms): return qt_ms/((rr_ms/1000.0)**0.5)
def qtc_f(qt_ms, rr_ms): return qt_ms/((rr_ms/1000.0)**(1/3))
def axis_label_from(I, aVF):
    if I is None or aVF is None: return None
    if I>=0 and aVF>=0: return "Normal"
    if I>=0 and aVF<0: return "Desvio para a esquerda"
    if I<0 and aVF>=0: return "Desvio para a direita"
    return "Desvio extremo (noroeste)"

app.layout = html.Div([
    html.H2("ECGiga — Plataforma Educacional de ECG", style={"textAlign": "center", "color": "#1a5276"}),
    dcc.Tabs(id="tabs-main", value="tab-analise", children=[
        dcc.Tab(label="Análise de ECG", value="tab-analise"),
        dcc.Tab(label="Educação", value="tab-educacao"),
        dcc.Tab(label="Quiz", value="tab-quiz"),
        dcc.Tab(label="Simulador", value="tab-simulador"),
        dcc.Tab(label="Interpretação IA", value="tab-ia"),
    ]),
    html.Div(id="tab-content"),
])


# ---------------------------------------------------------------------------
# Conteúdo das abas
# ---------------------------------------------------------------------------

def _layout_analise():
    """Layout da aba de análise de ECG — pipeline completo de CV."""
    return html.Div([
    html.Div([
        html.Div([
            html.H3("Upload de ECG (PNG/JPG)"),
            html.P(
                "Envie uma imagem de ECG para análise automática. O pipeline detecta a grade, "
                "segmenta as 12 derivações, localiza R-peaks, mede intervalos e calcula o eixo.",
                style={"fontSize": "0.9em", "color": "#555", "marginBottom": "10px"},
            ),
            dcc.Upload(
                id='upload-ecg', children=html.Div(['Arraste e solte ou ', html.A('selecione um arquivo')]),
                multiple=False, style={'width':'100%','height':'60px','lineHeight':'60px','borderWidth':'1px','borderStyle':'dashed','borderRadius':'5px','textAlign':'center','marginBottom':'10px'}
            ),
            dcc.Textarea(id="upload-meta", placeholder="Cole o sidecar META (JSON) opcional...", style={"width":"100%","height":"120px"}),
            html.Div([
                dcc.Checklist(id='ops', options=[
                    {'label':'Deskew','value':'deskew'},
                    {'label':'Normalize (px/mm≈10)','value':'normalize'}
                ], value=[]),
                html.Label('Layout'), dcc.Dropdown(id='layout-select', options=[
                    {'label':'3x4','value':'3x4'},
                    {'label':'6x2','value':'6x2'},
                    {'label':'3x4 + ritmo (II)','value':'3x4+rhythm'}
                ], value='3x4', clearable=False, style={'width':'260px'})
            ], style={'display':'flex','gap':'16px','alignItems':'center','marginBottom':'8px'}),
            html.Button("Processar", id="btn-process", n_clicks=0),
            html.Div(id="upload-summary", style={"marginTop":"10px","whiteSpace":"pre-wrap"}),
            html.Div([
                html.Label('Lead para FC (R-peaks)'),
                dcc.Dropdown(id='lead-select', options=[{'label':l,'value':l} for l in ['II','V2','V5']], value='II', clearable=False, style={'width':'200px'}),
                html.Button('R-peaks robustos', id='btn-rrob', n_clicks=0),
                html.Button('Intervalos (PR/QRS/QT/QTc)', id='btn-intervals', n_clicks=0),
                html.Button('Eixo (I/aVF)', id='btn-axis', n_clicks=0),
                html.Button('Ritmo', id='btn-rhythm', n_clicks=0),
            ], style={'display':'flex','gap':'12px','alignItems':'center','marginTop':'8px'}),
            dcc.Graph(id="overlay", figure=go.Figure()),
        ], className="card", style={"maxWidth":"900px"})
    ], style={"marginBottom":"16px"}),
    html.Div([
        html.H3("Calculadora QTc (rápida)"),
        html.Label("QT (ms)"), dcc.Input(id="qt-ms", type="number", value=400, step=1),
        html.Label("RR (ms)"), dcc.Input(id="rr-ms", type="number", value=800, step=1),
        html.Div(id="qtc-out", style={"marginTop":"8px","fontWeight":"bold"}),
    ], className="card", style={"maxWidth":"520px","marginBottom":"16px"}),
    dcc.Graph(id="ecg12", figure=fig_synth)
    ])


def _layout_educacao():
    """Layout da aba de educação — conteúdo didático sobre ECG."""
    return html.Div([
        html.H3("Módulo Educacional — Analogia das Câmeras"),
        html.Div([
            html.P(
                "Imagine o coração como um objeto sendo fotografado por 12 câmeras (derivações). "
                "Cada derivação vê o mesmo evento elétrico de um ângulo diferente. "
                "A atividade elétrica que se aproxima do eletrodo positivo gera uma deflexão "
                "positiva (para cima); a que se afasta gera deflexão negativa (para baixo)."
            ),
            html.P(
                "As derivações dos membros (I, II, III, aVR, aVL, aVF) avaliam o plano frontal, "
                "enquanto as precordiais (V1–V6) avaliam o plano horizontal. Juntas, fornecem "
                "uma visão tridimensional da atividade elétrica cardíaca.",
                style={"marginTop": "8px"},
            ),
        ], className="card", style={"maxWidth": "700px"}),
        html.Div([
            html.H4("Mnemônico CAFÉ — Como interpretar deflexões"),
            html.Ul([
                html.Li([html.B("C"), " — Câmera = polo positivo (onde está o eletrodo explorador)"]),
                html.Li([html.B("A"), " — Aproximando = deflexão positiva (vetor vem em direção à câmera)"]),
                html.Li([html.B("F"), " — Fugindo = deflexão negativa (vetor se afasta da câmera)"]),
                html.Li([html.B("É"), " — Esquece (perpendicular) = bifásico (vetor cruza perpendicular à câmera)"]),
            ]),
            html.P(
                "Exemplo prático: em DII, o vetor do QRS normal (≈+60°) se aproxima do polo positivo "
                "(perna esquerda), gerando um QRS predominantemente positivo. Em aVR, o mesmo vetor "
                "foge do polo positivo (braço direito), gerando QRS negativo.",
                style={"marginTop": "8px", "fontStyle": "italic"},
            ),
        ], className="card", style={"maxWidth": "700px", "marginTop": "16px"}),
        html.Div([
            html.H4("Explorar Derivações"),
            html.P("Selecione uma derivação para ver sua posição anatômica, ângulo e dica clínica:"),
            dcc.Dropdown(
                id="edu-lead-select",
                options=[{"label": l, "value": l} for l in leads],
                value="II",
                clearable=False,
                style={"width": "200px"},
            ),
            html.Div(id="edu-lead-info", style={"marginTop": "10px", "whiteSpace": "pre-wrap"}),
        ], className="card", style={"maxWidth": "700px", "marginTop": "16px"}),
        html.Div([
            html.H4("Visualização do Eixo Elétrico Frontal"),
            html.P(
                "O eixo elétrico indica a direção predominante da despolarização ventricular. "
                "Normal: entre −30° e +90°. Desvio para a esquerda pode sugerir BDASE; "
                "desvio para a direita pode sugerir BDPSE ou sobrecarga de VD."
            ),
            dcc.Graph(id="edu-axis-wheel"),
        ], className="card", style={"maxWidth": "700px", "marginTop": "16px"}),
    ])


def _layout_quiz():
    """Layout da aba de quiz — questões de múltipla escolha adaptativas."""
    return html.Div([
        html.H3("Quiz Adaptativo de ECG"),
        html.P(
            "Teste seus conhecimentos com questões de múltipla escolha (MCQ) geradas "
            "automaticamente. As questões são adaptadas aos achados do ECG analisado, "
            "focando nas áreas onde há maior potencial de aprendizado — como intervalos "
            "anormais, desvios de eixo ou padrões patológicos detectados."
        ),
        html.Div([
            html.Label("Número de questões:"),
            dcc.Input(id="quiz-n", type="number", value=6, min=1, max=20, step=1),
            html.Button("Gerar Quiz", id="btn-quiz-generate", n_clicks=0, style={"marginLeft": "10px"}),
        ], style={"display": "flex", "gap": "10px", "alignItems": "center"}),
        html.Div(id="quiz-content", style={"marginTop": "20px"}),
    ])


def _layout_simulador():
    """Layout da aba de simulador de ECG — geração de sinais sintéticos."""
    return html.Div([
        html.H3("Simulador de ECG"),
        html.P(
            "Gere sinais de ECG sintéticos com diferentes patologias para estudo. "
            "O simulador modela ondas P-QRS-T com parâmetros ajustáveis, permitindo "
            "visualizar como alterações de frequência e patologias afetam o traçado."
        ),
        html.Div([
            html.Label("FC (bpm):"),
            dcc.Input(id="sim-hr", type="number", value=75, min=30, max=250, step=1),
            html.Label("Duração (s):"),
            dcc.Input(id="sim-duration", type="number", value=5, min=1, max=30, step=1),
            html.Label("Patologia:"),
            dcc.Dropdown(
                id="sim-pathology",
                options=[
                    {"label": "Normal (sinusal)", "value": "normal"},
                    {"label": "Taquicardia sinusal", "value": "tachycardia"},
                    {"label": "Bradicardia sinusal", "value": "bradycardia"},
                    {"label": "PR prolongado (BAV 1°)", "value": "first_degree_block"},
                    {"label": "QRS alargado (BRE)", "value": "lbbb"},
                    {"label": "Fibrilação atrial", "value": "afib"},
                    {"label": "Supra de ST (STEMI)", "value": "stemi"},
                ],
                value="normal",
                clearable=False,
                style={"width": "300px"},
            ),
            html.Button("Simular", id="btn-simulate", n_clicks=0),
        ], style={"display": "flex", "gap": "10px", "alignItems": "center", "flexWrap": "wrap"}),
        dcc.Graph(id="sim-ecg-graph"),
    ])


def _layout_ia():
    """Layout da aba de interpretação com IA offline — regras clínicas."""
    return html.Div([
        html.H3("Interpretação de ECG com IA Offline"),
        html.P(
            "Interprete um ECG fornecendo os intervalos medidos. "
            "O sistema aplica regras clínicas validadas (offline, sem enviar dados externos) "
            "para gerar interpretação, diagnósticos diferenciais e recomendações. "
            "Inclui detecção de patologias (arritmias, bloqueios, isquemia) e "
            "limiares ajustados por idade e sexo."
        ),
        html.Div([
            html.Div([
                html.Label("PR (ms):"), dcc.Input(id="ia-pr", type="number", value=160, step=1),
                html.Label("QRS (ms):"), dcc.Input(id="ia-qrs", type="number", value=90, step=1),
                html.Label("QT (ms):"), dcc.Input(id="ia-qt", type="number", value=380, step=1),
                html.Label("QTc (ms):"), dcc.Input(id="ia-qtc", type="number", value=425, step=1),
                html.Label("RR (s):"), dcc.Input(id="ia-rr", type="number", value=0.8, step=0.01),
                html.Label("Eixo (°):"), dcc.Input(id="ia-axis", type="number", value=60, step=1),
                html.Label("Idade:"), dcc.Input(id="ia-age", type="number", value=50, step=1),
                html.Label("Sexo:"), dcc.Dropdown(
                    id="ia-sex",
                    options=[{"label": "Masculino", "value": "M"}, {"label": "Feminino", "value": "F"}],
                    value="M", clearable=False, style={"width": "150px"},
                ),
            ], style={"display": "flex", "gap": "10px", "alignItems": "center", "flexWrap": "wrap"}),
            html.Button("Interpretar", id="btn-interpret", n_clicks=0, style={"marginTop": "10px"}),
        ], className="card", style={"maxWidth": "900px"}),
        html.Div(id="ia-result", style={"marginTop": "20px", "whiteSpace": "pre-wrap"}),
    ])


# ---------------------------------------------------------------------------
# Callback de renderização de abas
# ---------------------------------------------------------------------------

@app.callback(Output("tab-content", "children"), Input("tabs-main", "value"))
def render_tab(tab):
    if tab == "tab-analise":
        return _layout_analise()
    elif tab == "tab-educacao":
        return _layout_educacao()
    elif tab == "tab-quiz":
        return _layout_quiz()
    elif tab == "tab-simulador":
        return _layout_simulador()
    elif tab == "tab-ia":
        return _layout_ia()
    return html.Div("Aba não encontrada")


# ---------------------------------------------------------------------------
# Callbacks da aba de educação
# ---------------------------------------------------------------------------

@app.callback(Output("edu-lead-info", "children"), Input("edu-lead-select", "value"))
def update_lead_info(lead):
    try:
        from education.cameras import explain_lead
        info = explain_lead(lead)
        lines = [
            f"Derivação: {lead}",
            f"Plano: {info.get('plano', info.get('plane', '?'))}",
            f"Ângulo: {info.get('angulo', info.get('angle', '?'))}°",
            f"Polo positivo: {info.get('polo_positivo', info.get('positive_pole', '?'))}",
            f"Dica: {info.get('dica_clinica', info.get('clinical_tip', ''))}",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Módulo de educação não disponível: {e}"


@app.callback(Output("edu-axis-wheel", "figure"), Input("edu-lead-select", "value"))
def update_axis_wheel(lead):
    try:
        from education.interactive import create_axis_wheel_figure
        return create_axis_wheel_figure()
    except Exception:
        # Fallback: roda do eixo frontal simplificada
        import plotly.graph_objs as go
        labels_ax = ["aVL(-30°)", "I(0°)", "II(60°)", "aVF(90°)", "III(120°)"]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[1]*5, theta=[-30, 0, 60, 90, 120], mode="markers+text",
            text=labels_ax, textposition="top center",
        ))
        fig.update_layout(
            title="Roda do Eixo Elétrico Frontal",
            polar=dict(radialaxis=dict(visible=False), angularaxis=dict(direction="clockwise")),
            showlegend=False, height=400,
        )
        return fig


# ---------------------------------------------------------------------------
# Callbacks da aba de quiz
# ---------------------------------------------------------------------------

@app.callback(Output("quiz-content", "children"), Input("btn-quiz-generate", "n_clicks"), State("quiz-n", "value"), prevent_initial_call=True)
def generate_quiz(n_clicks, n_questions):
    try:
        from quiz.engine import build_adaptive_quiz
        result = build_adaptive_quiz({}, n_questions=n_questions or 6, seed=n_clicks)
        questions = result.get("questions", [])
        elements = []
        for i, q in enumerate(questions):
            choices = []
            for c in q.get("choices", []):
                marker = "✓" if c.get("is_correct") else "✗"
                choices.append(html.Li(f"{c.get('text', '')} [{marker}] — {c.get('explanation', '')}"))
            elements.append(html.Div([
                html.H4(f"Questão {i+1}: {q.get('prompt', '')}"),
                html.Ul(choices),
            ], className="card", style={"marginBottom": "10px"}))
        return elements
    except Exception as e:
        return html.P(f"Erro ao gerar quiz: {e}")


# ---------------------------------------------------------------------------
# Callbacks da aba de simulador
# ---------------------------------------------------------------------------

@app.callback(Output("sim-ecg-graph", "figure"), Input("btn-simulate", "n_clicks"),
              State("sim-hr", "value"), State("sim-duration", "value"), State("sim-pathology", "value"),
              prevent_initial_call=True)
def simulate_ecg(n_clicks, hr, duration, pathology):
    pathology_params = {
        "normal": {},
        "tachycardia": {"hr_bpm": max(hr or 75, 120)},
        "bradycardia": {"hr_bpm": min(hr or 75, 50)},
        "first_degree_block": {"pr_ms": 240},
        "lbbb": {"qrs_ms": 160},
        "afib": {"noise": 0.15},
        "stemi": {},
    }
    pathology_labels = {
        "normal": "Normal (sinusal)",
        "tachycardia": "Taquicardia sinusal",
        "bradycardia": "Bradicardia sinusal",
        "first_degree_block": "BAV 1° grau (PR prolongado)",
        "lbbb": "BRE (QRS alargado)",
        "afib": "Fibrilação atrial",
        "stemi": "Supra de ST (STEMI)",
    }
    try:
        from simulation.ecg_generator import generate_ecg
        params = pathology_params.get(pathology, {})
        base_hr = params.pop("hr_bpm", hr or 75)
        result = generate_ecg(hr_bpm=base_hr, duration_s=duration or 5, **params)
        leads_data = result.get("leads", {})
        fig = go.Figure()
        if leads_data:
            for lead_name in ["II", "V1", "V5"]:
                if lead_name in leads_data:
                    sig = leads_data[lead_name]
                    fig.add_trace(go.Scatter(
                        y=sig.tolist() if hasattr(sig, 'tolist') else sig,
                        mode="lines", name=lead_name,
                    ))
        else:
            signal = result.get("signal", result) if isinstance(result, dict) else result
            if hasattr(signal, 'tolist'):
                signal = signal.tolist() if len(signal) < 10000 else signal[:10000].tolist()
            fig.add_trace(go.Scatter(y=signal, mode="lines", name="ECG"))
        label = pathology_labels.get(pathology, pathology)
        fig.update_layout(
            title=f"ECG Simulado — {label} ({base_hr} bpm, {duration}s)",
            xaxis_title="Amostras", yaxis_title="mV",
            legend=dict(orientation="h"),
        )
        return fig
    except Exception as exc:
        fig = go.Figure()
        t = np.linspace(0, duration or 5, (duration or 5) * 500)
        signal = synth_wave(n=len(t))
        fig.add_trace(go.Scatter(y=signal, mode="lines", name="ECG Sintético"))
        fig.update_layout(title=f"ECG Sintético (fallback) — {hr} bpm ({exc})", xaxis_title="Amostras", yaxis_title="mV")
        return fig


# ---------------------------------------------------------------------------
# Callbacks da aba de interpretação IA
# ---------------------------------------------------------------------------

@app.callback(Output("ia-result", "children"), Input("btn-interpret", "n_clicks"),
              State("ia-pr", "value"), State("ia-qrs", "value"), State("ia-qt", "value"),
              State("ia-qtc", "value"), State("ia-rr", "value"), State("ia-axis", "value"),
              State("ia-age", "value"), State("ia-sex", "value"),
              prevent_initial_call=True)
def interpret_ecg(n_clicks, pr, qrs, qt, qtc, rr, axis_deg, age, sex):
    try:
        from ai.offline_rules import interpret_report
        report = {
            "intervals_refined": {"median": {
                "PR_ms": pr, "QRS_ms": qrs, "QT_ms": qt, "QTc_B": qtc, "RR_s": rr,
            }},
            "axis": {"angle_deg": axis_deg, "label": ""},
            "flags": [],
        }
        result = interpret_report(report)

        elements = [
            html.H4("Resultado da Interpretação"),
            dcc.Markdown(result.get("interpretation", "")),
        ]

        # Limiares ajustados por demografia
        try:
            from pathology.thresholds import get_adjusted_thresholds
            thresholds = get_adjusted_thresholds(age, sex)
            elements.append(html.Div([
                html.H5("Limiares Ajustados"),
                html.P(f"Grupo etário: {thresholds['age_group']} | Sexo: {thresholds['sex']}"),
                html.P(f"FC normal: {thresholds['hr_range'][0]}-{thresholds['hr_range'][1]} bpm"),
                html.P(f"QTc normal até: {thresholds['qtc_upper_ms']} ms | Prolongado: >{thresholds['qtc_prolonged_ms']} ms"),
                html.P(f"STEMI V2-V3: ≥{thresholds['stemi_v2v3_mv']} mV"),
            ], className="card", style={"marginTop": "10px"}))
        except ImportError:
            pass

        # Diagnósticos diferenciais
        diffs = result.get("differentials", [])
        if diffs:
            elements.append(html.H5("Diagnósticos Diferenciais"))
            elements.append(html.Ul([html.Li(d) for d in diffs]))

        # Recomendações
        recs = result.get("recommendations", [])
        if recs:
            elements.append(html.H5("Recomendações"))
            elements.append(html.Ul([html.Li(r) for r in recs]))

        # Severidade
        severity = result.get("severity", "unknown")
        badge_color = {"critical": "red", "high": "orange", "moderate": "goldenrod", "low": "green", "normal": "green"}.get(severity, "gray")
        elements.append(html.Div(
            f"Severidade: {severity.upper()} | Confiança: {result.get('confidence', '?')}",
            style={"fontWeight": "bold", "color": badge_color, "marginTop": "10px"},
        ))

        return elements
    except Exception as e:
        return html.P(f"Erro na interpretação: {e}")


# ---------------------------------------------------------------------------
# Callbacks da aba de análise (original)
# ---------------------------------------------------------------------------

@app.callback(
    Output("overlay","figure"),
    Output("upload-summary","children"),
    Input("btn-process","n_clicks"),
    Input('btn-rrob','n_clicks'),
    Input('btn-intervals','n_clicks'),
    Input('btn-axis','n_clicks'),
    Input('btn-rhythm','n_clicks'),
    State("upload-ecg","contents"),
    State("upload-ecg","filename"),
    State("upload-meta","value"),
    State('ops','value'),
    State('layout-select','value'),
    State('lead-select','value'),
    prevent_initial_call=True
)
def process(n, nrrob, nintv, naxis, nrhythm, content, filename, meta_text, ops, layout_sel, lead_sel):
    if not content:
        return go.Figure(), "Nenhuma imagem enviada."
    img = decode_image(content)
    # pré-processo: deskew/normalize
    if ops and 'deskew' in ops:
        from cv.deskew import estimate_rotation_angle, rotate_image
        info = estimate_rotation_angle(img, search_deg=6.0, step=0.5)
        img = rotate_image(img, info['angle_deg'])
    if ops and 'normalize' in ops:
        from cv.normalize import normalize_scale
        img, _scale, _pxmm = normalize_scale(img, 10.0)
    # META opcional
    meta = None
    if meta_text:
        try: meta = json.loads(meta_text)
        except Exception as e: meta = {"_error": f"Falha lendo META: {e}"}

    # Grid + segmentação
    from cv.grid_detect import estimate_grid_period_px
    from cv.segmentation import find_content_bbox
    from cv.segmentation_ext import segment_layout
    arr = np.asarray(img.convert("L"))
    grid = estimate_grid_period_px(np.asarray(img))
    bbox = find_content_bbox(arr)
    seg_leads = segment_layout(arr, layout=layout_sel, bbox=bbox)
    from cv.lead_ocr import detect_labels_per_box
    seg = {"content_bbox": bbox, "leads": seg_leads}
    labels = detect_labels_per_box(arr, [d['bbox'] for d in seg_leads])
    px_small = grid.get('px_small_x') or grid.get('px_small_y') or 0
    px_big = grid.get('px_big_x') or grid.get('px_big_y') or 0
    summary = [
        f"Arquivo: {filename}",
        f"Layout: {layout_sel}",
        f"Rótulos detectados: {sum(1 for d in labels if d.get('label'))}/{len(labels)}",
        f"Grid small≈{px_small:.1f}px, big≈{px_big:.1f}px (conf {grid.get('confidence',0):.2f})",
        f"Content bbox: {bbox} | Leads: {len(seg_leads)}",
    ]
    if meta and isinstance(meta, dict):
        m = meta.get("measures", {})
        qt = m.get("qt_ms"); rr = m.get("rr_ms") or (60000.0/(m.get("fc_bpm") or 0) if m.get("fc_bpm") else None)
        if qt and rr:
            summary.append(f"QT: {qt} ms | QTc (B/F): {qtc_b(qt, rr):.1f}/{qtc_f(qt, rr):.1f} ms")

    # Imports de CV para análise de R-peaks/intervalos/eixo
    from cv.rpeaks_from_image import extract_trace_centerline, smooth_signal, estimate_px_per_sec
    from cv.rpeaks_robust import pan_tompkins_like
    from cv.intervals import intervals_from_trace

    lab2box = {d['lead']: d['bbox'] for d in seg_leads}

    # Auxiliar: calcula px/s a partir da grade
    def _get_pxsec():
        pxmm = grid.get('px_small_x') or grid.get('px_small_y') or 10.0
        return estimate_px_per_sec(pxmm, 25.0) or 250.0

    triggered = ctx.triggered_id

    # R-peaks robustos
    if triggered == 'btn-rrob' or triggered == 'btn-intervals':
        lab = lead_sel or 'II'
        if lab in lab2box:
            x0,y0,x1,y1 = lab2box[lab]
            crop = arr[y0:y1, x0:x1]
            trace = smooth_signal(extract_trace_centerline(crop), win=11)
            pxsec = _get_pxsec()
            rdet = pan_tompkins_like(trace, pxsec)
            if triggered == 'btn-rrob':
                summary.append(f"R-peaks robustos ({lab}): {len(rdet['peaks_idx'])} picos (fs≈{pxsec:.1f} px/s)")
            if triggered == 'btn-intervals':
                iv = intervals_from_trace(trace, rdet['peaks_idx'], pxsec)
                m = iv['median']
                summary.append(f"PR {m.get('PR_ms')} ms | QRS {m.get('QRS_ms')} ms | QT {m.get('QT_ms')} ms | QTcB {m.get('QTc_B')} ms | QTcF {m.get('QTc_F')} ms")

    # Eixo
    if triggered == 'btn-axis':
        from cv.axis import frontal_axis_from_image
        if 'I' in lab2box and 'aVF' in lab2box:
            arrL = np.asarray(img.convert('L'))
            ref_lead = lead_sel if lead_sel in lab2box else 'II'
            x0,y0,x1,y1 = lab2box.get(ref_lead, list(lab2box.values())[0])
            crop = arrL[y0:y1, x0:x1]
            trace = smooth_signal(extract_trace_centerline(crop), win=11)
            pxsec = _get_pxsec()
            rdet = pan_tompkins_like(trace, pxsec)
            axis = frontal_axis_from_image(arrL, {'I': lab2box['I'], 'aVF': lab2box['aVF']}, {'I': rdet['peaks_idx'], 'aVF': rdet['peaks_idx']}, {'I': pxsec, 'aVF': pxsec})
            summary.append(f"Eixo: {axis.get('angle_deg',0):.1f}° — {axis.get('label','?')}")

    # Ritmo
    if triggered == 'btn-rhythm':
        lab = lead_sel or 'II'
        if lab in lab2box:
            x0,y0,x1,y1 = lab2box[lab]
            crop = arr[y0:y1, x0:x1]
            trace = smooth_signal(extract_trace_centerline(crop), win=11)
            pxsec = _get_pxsec()
            rdet = pan_tompkins_like(trace, pxsec)
            peaks = rdet.get('peaks_idx', [])
            if len(peaks) >= 2:
                rr_arr = np.diff(peaks) / pxsec
                hr = 60.0 / np.median(rr_arr)
                sdnn = 1000.0 * float(np.std(rr_arr, ddof=1)) if len(rr_arr) > 1 else 0.0
                cv_rr = float(np.std(rr_arr) / (np.mean(rr_arr) + 1e-9))
                label = "Indeterminado"
                if cv_rr < 0.06 and sdnn < 60:
                    label = "Provável sinusal (RR regular)"
                elif cv_rr > 0.12 and sdnn > 100:
                    label = "Irregular (suspeitar FA se P ausente)"
                else:
                    label = "Possível irregularidade leve/variação sinusal"
                summary.append(f"Ritmo ({lab}): {label} | HR≈{hr:.0f} bpm | SDNN≈{sdnn:.1f} ms | CV-RR={cv_rr:.3f}")
            else:
                summary.append(f"Ritmo ({lab}): Picos insuficientes ({len(peaks)})")

    fig = make_overlay_figure(img, seg)
    return fig, "\n".join(summary)

@app.callback(Output("qtc-out","children"), [Input("qt-ms","value"), Input("rr-ms","value")])
def calc_qtc(qt, rr):
    if not qt or not rr or rr<=0: return "Informe QT e RR em ms."
    return f"QTc Bazett: {qtc_b(qt, rr):.1f} ms | QTc Fridericia: {qtc_f(qt, rr):.1f} ms"

if __name__ == "__main__":
    app.run(debug=True)

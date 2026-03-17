
import dash
from dash import html, dcc, Input, Output, State, ctx
import plotly.graph_objs as go
import numpy as np, base64, json
from PIL import Image
from io import BytesIO

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "ECGiga — Plataforma Educacional de ECG"
server = app.server  # expose Flask server for gunicorn

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
        dcc.Tab(label="Eletrólitos & ECG", value="tab-electrolytes"),
        dcc.Tab(label="Eletrofisiologia", value="tab-ephys"),
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
        html.Div([
            html.H4("Segmento ST — Foco, Desfoco e a Linha de Base"),
            html.P(
                "O segmento ST é o trecho entre o fim do QRS (ponto J) e o início da onda T. "
                "Entender por que ele é normalmente isoelétrico — e quando sai da linha de base — "
                "é fundamental para diagnosticar isquemia e infarto.",
                style={"marginBottom": "12px"},
            ),
            html.Div([
                html.H5("Por que o ST normal fica na linha de base?"),
                html.P(
                    "Durante a despolarização (QRS), parte do miocárdio está despolarizada e parte "
                    "ainda em repouso — isso cria um gradiente, um vetor, que a câmera registra como "
                    "deflexão (positiva se vem, negativa se foge). A câmera FOCA no movimento."
                ),
                html.P(
                    "Mas quando TODA a parede ventricular atinge o plateau (fase 2 do potencial de ação), "
                    "todas as células estão no mesmo estado elétrico. Sem diferença de potencial, sem vetor, "
                    "sem sinal. Nenhuma câmera vê contraste. O registro volta ao zero — a linha de base. "
                    "É como uma sala toda iluminada por igual: nenhuma câmera detecta movimento.",
                    style={"marginTop": "6px"},
                ),
                html.P(
                    "Depois, a repolarização (onda T) recria um gradiente — do epicárdio para o endocárdio — "
                    "e a câmera volta a focar. Como a repolarização vai de fora para dentro (oposta à "
                    "despolarização), o vetor T aponta na mesma direção geral do QRS. Por isso, "
                    "normalmente T e QRS têm a mesma polaridade.",
                    style={"marginTop": "6px"},
                ),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("Supra de ST — Lesão transmural (STEMI)"),
                html.P(
                    "Quando uma artéria é totalmente ocluída, a região lesada não mantém o plateau normal. "
                    "As células lesadas repolarizam prematuramente, criando um gradiente durante o que "
                    "deveria ser um plateau uniforme. Surge uma corrente de lesão."
                ),
                html.Ul([
                    html.Li([
                        html.B("Câmera voltada para a lesão: "),
                        "vê a corrente de lesão vindo → ST sobe acima da base → SUPRA. "
                        "É como filmar um incêndio diretamente.",
                    ]),
                    html.Li([
                        html.B("Câmera oposta (recíproca): "),
                        "vê a corrente de lesão fugindo → ST desce → INFRA recíproco. "
                        "É como ver a sombra do incêndio na parede oposta.",
                    ]),
                ]),
                html.P(
                    "Territórios: IAM anterior → supra em V1-V4 + infra em II/III/aVF | "
                    "IAM inferior → supra em II/III/aVF + infra em I/aVL | "
                    "IAM lateral → supra em I/aVL/V5/V6.",
                    style={"fontStyle": "italic", "marginTop": "6px"},
                ),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("Infra de ST — Isquemia subendocárdica"),
                html.P(
                    "Sem oclusão total, a lesão atinge o subendocárdio (camada interna, mais vulnerável). "
                    "O vetor de corrente de lesão aponta para dentro do ventrículo — fugindo de TODAS "
                    "as câmeras de superfície. Resultado: infra de ST difuso, sem supra recíproco."
                ),
                html.P(
                    "É como um defeito escondido por dentro da parede: todas as câmeras veem uma sombra "
                    "sutil por igual, mas nenhuma filma a lesão diretamente.",
                    style={"fontStyle": "italic", "marginTop": "6px"},
                ),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("Outras causas de alteração do ST"),
                html.Ul([
                    html.Li([html.B("Pericardite: "), "inflamação difusa → supra côncavo generalizado (todas as câmeras veem irritação)"]),
                    html.Li([html.B("BRE: "), "condução anormal distorce o ST (discordante ao QRS) — artefato, não lesão"]),
                    html.Li([html.B("Repolarização precoce: "), "variante normal em jovens → supra côncavo com entalhe no ponto J"]),
                    html.Li([html.B("Hipercalemia: "), "potássio alto altera o plateau → ST funde-se com T apiculada"]),
                    html.Li([html.B("Hipotermia: "), "frio prolonga o plateau → onda J (Osborn) no ponto J"]),
                ]),
            ]),
        ], className="card", style={"maxWidth": "700px", "marginTop": "16px"}),
        html.Div([
            html.H4("Inversão da Onda T — Quando a Câmera Vê a Repolarização Fugindo"),
            html.P(
                "A onda T normal é positiva nas mesmas derivações em que o QRS é positivo. "
                "Entender o porquê — e quando isso se inverte — é essencial para reconhecer "
                "isquemia, sobrecarga e outras condições.",
                style={"marginBottom": "12px"},
            ),
            html.Div([
                html.H5("Por que a T normal é positiva?"),
                html.P(
                    "A despolarização vai do endocárdio para o epicárdio (de dentro para fora) — "
                    "o vetor vem na direção da câmera de superfície → QRS positivo."
                ),
                html.P(
                    "A repolarização vai na direção oposta: do epicárdio para o endocárdio (de fora "
                    "para dentro), porque o epicárdio tem potencial de ação mais curto e repolariza "
                    "primeiro. Mas a repolarização é o processo elétrico oposto da despolarização.",
                    style={"marginTop": "6px"},
                ),
                html.P([
                    "Dois 'negativos' fazem um positivo: ",
                    html.B("(processo invertido) × (direção invertida) = mesmo sinal. "),
                    "A câmera registra T positiva onde o QRS é positivo. É como um ator que caminha "
                    "de costas se afastando — a câmera vê a cena como se ele estivesse de frente "
                    "se aproximando.",
                ], style={"marginTop": "6px"}),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("Inversão por isquemia — a repolarização muda de direção"),
                html.P(
                    "Na isquemia, o epicárdio lesado demora mais para repolarizar. A repolarização "
                    "agora vai do endocárdio para o epicárdio (de dentro para fora) — na DIREÇÃO "
                    "da câmera. Mas como é um processo negativo vindo na direção da câmera, o "
                    "resultado é deflexão negativa → T invertida."
                ),
                html.Ul([
                    html.Li([
                        html.B("Padrão de Wellens: "),
                        "T profunda, simétrica e invertida em V2-V3 → altamente específico para "
                        "estenose crítica da artéria descendente anterior. As câmeras anteriores "
                        "filmam a repolarização invertida da parede anterior isquêmica.",
                    ]),
                ]),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("Inversão por sobrecarga (strain pattern)"),
                html.P(
                    "Na hipertrofia ventricular, a parede espessa sofre isquemia relativa crônica. "
                    "O padrão de strain é característico: infra de ST descendente (convexo) + T "
                    "invertida assimétrica (descida lenta, subida rápida)."
                ),
                html.Ul([
                    html.Li([html.B("HVE: "), "strain em V5-V6, DI, aVL — câmeras laterais veem o VE estressado"]),
                    html.Li([html.B("HVD: "), "strain em V1-V3, DIII, aVF — câmeras direitas veem o VD estressado"]),
                ]),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("Outras causas de inversão da T"),
                html.Ul([
                    html.Li([html.B("TEP (embolia pulmonar): "), "sobrecarga aguda do VD → T invertida em V1-V4 + S1Q3T3"]),
                    html.Li([html.B("Memória cardíaca: "), "após taquicardia/pacing, T fica invertida por horas-dias (o coração 'lembra' o padrão anormal)"]),
                    html.Li([html.B("HSA (hemorragia subaracnóidea): "), "descarga simpática → T gigantes invertidas ('T cerebrais') difusas"]),
                    html.Li([html.B("Padrão juvenil: "), "T invertida em V1-V3 em jovens — benigno, desaparece com a idade"]),
                    html.Li([html.B("QT longo: "), "repolarização prolongada e heterogênea → T invertida ou bífida"]),
                ]),
            ]),
        ], className="card", style={"maxWidth": "700px", "marginTop": "16px"}),
        html.Div([
            html.H4("Onda Q Patológica — A Câmera Filma Através da Necrose"),
            html.P(
                "A onda Q patológica é a assinatura eletrocardiográfica do infarto consumado. "
                "Entender a 'teoria da janela elétrica' é a chave para interpretar infartos antigos "
                "e localizar a necrose.",
                style={"marginBottom": "12px"},
            ),
            html.Div([
                html.H5("A onda q fisiológica (minúscula) — normal"),
                html.P(
                    "A despolarização ventricular começa pelo septo, da esquerda para a direita. "
                    "As câmeras laterais (V5-V6, DI) veem esse primeiro vetor se afastando brevemente "
                    "→ registram uma q pequena (< 40 ms, < 25% do R). É como o ator principal dando "
                    "um passo para trás antes de avançar na direção da câmera."
                ),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("A onda Q patológica — a 'janela elétrica'"),
                html.P(
                    "Quando uma região do miocárdio sofre necrose (infarto), o tecido morre e vira "
                    "cicatriz fibrosa — eletricamente muda. Não gera vetor."
                ),
                html.P([
                    "A câmera voltada para essa região morta olha e não vê nada ali. Mas ",
                    html.B("através da 'janela' da necrose"),
                    ", ela enxerga a parede oposta — que está viva, mas gerando vetor na direção "
                    "contrária (se afastando). Resultado: Q profunda e larga.",
                ], style={"marginTop": "6px"}),
                html.P(
                    "Analogia: o ator principal (parede viva) não compareceu. A câmera, preparada "
                    "para filmá-lo, olha para o palco vazio e, através do cenário, vê figurantes "
                    "caminhando de costas no fundo. Tudo é negativo — essa é a Q patológica.",
                    style={"fontStyle": "italic", "marginTop": "6px"},
                ),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("q fisiológica vs. Q patológica"),
                html.Ul([
                    html.Li([
                        html.B("q fisiológica: "),
                        "< 40 ms, < 25% do R, derivações isoladas. O ator deu um passo para trás "
                        "antes de avançar.",
                    ]),
                    html.Li([
                        html.B("Q patológica: "),
                        "≥ 40 ms (1 quadradinho) ou ≥ 25% do R, em derivações contíguas. "
                        "O ator morreu — a câmera filma através da janela.",
                    ]),
                    html.Li([
                        html.B("QS (sem R): "),
                        "necrose transmural completa. A câmera não vê NENHUM vetor vindo. "
                        "Tudo negativo. O ator não existe mais nessa cena.",
                    ]),
                ]),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("Territórios — qual câmera vê qual necrose?"),
                html.Ul([
                    html.Li([html.B("Anterior (DA): "), "Q/QS em V1-V4 — câmeras anteriores filmam através da janela anterior"]),
                    html.Li([html.B("Inferior (CD): "), "Q em DII, DIII, aVF — câmeras inferiores filmam através da janela inferior"]),
                    html.Li([html.B("Lateral (Cx): "), "Q em DI, aVL, V5-V6 — câmeras laterais filmam através da janela lateral"]),
                    html.Li([html.B("Posterior (CD/Cx): "), "sem Q direta — pista indireta: R alto em V1-V2 (imagem espelho da Q posterior)"]),
                ]),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("Evolução do infarto — os 4 capítulos na câmera"),
                html.P(
                    "O ECG do infarto conta uma história em fases, como capítulos de um filme:",
                    style={"marginBottom": "6px"},
                ),
                html.Ul([
                    html.Li([html.B("1. Hiperagudo (minutos): "), "T apiculadas — primeiros sinais de fumaça"]),
                    html.Li([html.B("2. Agudo (horas): "), "supra de ST + Q começa a surgir — o incêndio em tempo real"]),
                    html.Li([html.B("3. Subagudo (dias-semanas): "), "ST normaliza, T inverte profundamente, Q se aprofunda — a fuligem"]),
                    html.Li([html.B("4. Crônico (permanente): "), "ST e T podem normalizar, mas Q persiste para sempre — a cicatriz"]),
                ]),
            ], style={"marginBottom": "16px"}),
            html.Div([
                html.H5("Armadilhas — quando Q NÃO é infarto"),
                html.Ul([
                    html.Li([html.B("Miocardiopatia hipertrófica: "), "septo espesso → Q profunda e estreita em laterais/inferiores (excesso de vetor, não janela)"]),
                    html.Li([html.B("WPW: "), "pré-excitação gera onda delta que simula Q ('pseudo-Q')"]),
                    html.Li([html.B("BRE: "), "condução invertida → QS em V1-V3 sem necrose"]),
                    html.Li([html.B("Eletrodos mal posicionados: "), "câmera no ângulo errado simula Q — sempre verificar posicionamento"]),
                ]),
            ]),
        ], className="card", style={"maxWidth": "700px", "marginTop": "16px"}),
    ])


def _layout_quiz():
    """Layout da aba de quiz — questões de múltipla escolha adaptativas."""
    return html.Div([
        html.H3("Quiz Adaptativo de ECG"),
        html.Div([
            html.Label("Número de questões: "),
            dcc.Input(id="quiz-n", type="number", value=6, min=1, max=20, step=1),
            html.Button("Gerar Quiz", id="btn-quiz-generate", n_clicks=0, style={"marginLeft": "10px"}),
            html.Button("Ver Progresso", id="btn-quiz-progress", n_clicks=0, style={"marginLeft": "10px"}),
        ]),
        html.Div(id="quiz-content", style={"marginTop": "20px"}),
        html.Div(id="quiz-progress-content", style={"marginTop": "20px"}),
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
                    {"label": "STEMI anterior (V1-V4)", "value": "stemi_anterior"},
                    {"label": "STEMI inferior (II,III,aVF)", "value": "stemi_inferior"},
                    {"label": "BRE (QRS alargado)", "value": "lbbb"},
                    {"label": "BRD (RSR' em V1)", "value": "rbbb"},
                    {"label": "Fibrilação atrial", "value": "af"},
                    {"label": "WPW (PR curto, onda delta)", "value": "wpw"},
                    {"label": "Hipercalemia leve (T apiculadas)", "value": "hyperkalemia"},
                    {"label": "Hipercalemia grave (sine wave)", "value": "hyperkalemia_severe"},
                    {"label": "Hipocalemia (T achata, onda U)", "value": "hypokalemia"},
                    {"label": "Hipercalcemia (QT curto)", "value": "hypercalcemia"},
                    {"label": "Hipocalcemia (QT longo, ST longo)", "value": "hypocalcemia"},
                    {"label": "QT longo", "value": "long_qt"},
                ],
                value="normal",
                clearable=False,
                style={"width": "300px"},
            ),
            html.Button("Simular", id="btn-simulate", n_clicks=0),
        ], style={"display": "flex", "gap": "10px", "alignItems": "center", "flexWrap": "wrap"}),
        dcc.Graph(id="sim-ecg-graph"),
    ])


def _layout_electrolytes():
    """Layout da aba de eletrólitos e ECG — mega-analogia clínico-eletrolítica."""
    return html.Div([
        html.H3("Eletrólitos & ECG — Mega-Analogia Clínico-Eletrolítica"),
        html.P(
            "Explore como distúrbios eletrolíticos alteram o ECG. Cada íon é um "
            "'diretor' que controla uma fase diferente do potencial de ação. "
            "Visualize os ECGs sintéticos e teste seus conhecimentos com quiz.",
            style={"marginBottom": "16px"},
        ),

        # --- SEÇÃO 1: Conceitos fundamentais ---
        html.Div([
            html.H4("Conceitos Fundamentais: Íons como Diretores do Filme Cardíaco"),
            html.P(
                "O potencial de ação cardíaco é o 'roteiro' que cada célula segue. "
                "Os eletrólitos são os 'diretores' que controlam cada fase:"
            ),
            html.Ul([
                html.Li([html.B("K+ (Potássio)"), " — Diretor da REPOLARIZAÇÃO (fases 3-4). "
                         "Controla forma das ondas T, QRS, P. O que MAIS muda o ECG."]),
                html.Li([html.B("Ca²+ (Cálcio)"), " — Diretor do PLATEAU (fase 2). "
                         "Controla duração do QT. Não mexe na forma das ondas."]),
                html.Li([html.B("Mg²+ (Magnésio)"), " — Codiretor silencioso. "
                         "Estabiliza canais K+/Ca²+. Baixo → instabilidade → Torsades."]),
            ]),
            html.Div([
                html.P([
                    html.B("Regra de ouro: "),
                    '"K+ mexe nas ONDAS. Ca²+ mexe no INTERVALO. Mg²+ mexe na ESTABILIDADE."',
                ], style={"fontWeight": "bold", "color": "#c0392b", "marginTop": "10px"}),
            ]),
        ], className="card", style={"maxWidth": "800px"}),

        # --- SEÇÃO 2: Hipercalemia ---
        html.Div([
            html.H4("Hipercalemia — Os 4 Estágios do K+ Alto"),
            html.P("O ECG é o 'exame de potássio mais rápido'. A progressão é previsível:"),
            html.Div([
                html.Div([
                    html.H5("Estágio 1 — Leve (K+ 5.5-6.5)"),
                    html.P("T APICULADAS: altas, simétricas, base estreita (tent-shaped)."),
                    html.P(
                        "A repolarização acelerada faz o 'ator T' correr na direção da câmera "
                        "em vez de caminhar → imagem mais alta e estreita.",
                        style={"fontStyle": "italic"},
                    ),
                ], style={"borderLeft": "4px solid #f39c12", "paddingLeft": "12px", "marginBottom": "12px"}),
                html.Div([
                    html.H5("Estágio 2 — Moderado (K+ 6.5-7.5)"),
                    html.P("PR prolonga → P achata e SOME → QRS ALARGA."),
                    html.P(
                        "O 'porteiro' AV demora mais (PR↑). Os atores atriais param (P some). "
                        "Os ventriculares ficam em câmera lenta (QRS largo).",
                        style={"fontStyle": "italic"},
                    ),
                ], style={"borderLeft": "4px solid #e67e22", "paddingLeft": "12px", "marginBottom": "12px"}),
                html.Div([
                    html.H5("Estágio 3 — Grave (K+ 7.5-8.5)"),
                    html.P("SINE WAVE: QRS funde com T. Sem P. Padrão sinusoidal."),
                    html.P(
                        "A câmera não distingue mais quem é quem — QRS, ST e T viraram uma "
                        "massa única ondulante. EMERGÊNCIA!",
                        style={"fontStyle": "italic", "color": "#c0392b"},
                    ),
                ], style={"borderLeft": "4px solid #e74c3c", "paddingLeft": "12px", "marginBottom": "12px"}),
                html.Div([
                    html.H5("Estágio 4 — Crítico (K+ > 8.5)"),
                    html.P("Bradicardia extrema → FV ou ASSISTOLIA → PARADA."),
                    html.P(
                        "O diretor destruiu o set. Os atores param. Silêncio. Linha reta.",
                        style={"fontStyle": "italic", "color": "#c0392b", "fontWeight": "bold"},
                    ),
                ], style={"borderLeft": "4px solid #900", "paddingLeft": "12px", "marginBottom": "12px"}),
            ]),
        ], className="card", style={"maxWidth": "800px", "marginTop": "16px"}),

        # --- SEÇÃO 3: Hipocalemia ---
        html.Div([
            html.H4("Hipocalemia — O K+ Cai e a Onda U Entra em Cena"),
            html.P("O oposto da hipercalemia: repolarização arrasta em vez de correr."),
            html.Ul([
                html.Li([html.B("1. T achata"), " — repolarização lenta, amplitude diminui"]),
                html.Li([html.B("2. Infra de ST"), " — segmento ST desce suavemente"]),
                html.Li([html.B("3. Onda U aparece"), " — 'ator extra' sobe ao palco (V2-V3). "
                         "Repolarização tardia de fibras de Purkinje"]),
                html.Li([html.B("4. Fusão T-U"), " — U cresce e funde com T → QT aparente longo. "
                         "RISCO de Torsades!"]),
                html.Li([html.B("5. Tardio"), " — QRS pode alargar, arritmias, risco de parada"]),
            ]),
            html.P([
                html.B("Dica: "),
                "Hipocalemia refratária? DOSA O MAGNÉSIO! Sem corrigir Mg²+, o K+ não normaliza.",
            ], style={"color": "#c0392b", "marginTop": "8px"}),
        ], className="card", style={"maxWidth": "800px", "marginTop": "16px"}),

        # --- SEÇÃO 4: Cálcio ---
        html.Div([
            html.H4("Cálcio — O Diretor do Plateau (QT)"),
            html.Div([
                html.Div([
                    html.H5("Hipercalcemia — QT Curto"),
                    html.P("Ca²+ alto → plateau curto → ST quase ausente → T 'gruda' no QRS"),
                    html.P(
                        "A pausa dramática entre os atos foi eliminada. Os atores passam de "
                        "um ato ao próximo sem intervalo.",
                        style={"fontStyle": "italic"},
                    ),
                ], style={"flex": "1", "marginRight": "8px"}),
                html.Div([
                    html.H5("Hipocalcemia — QT Longo"),
                    html.P("Ca²+ baixo → plateau longo → ST prolongado → T normal"),
                    html.P(
                        "Pausa dramática enorme entre QRS e T. Mas quando T aparece, "
                        "está perfeita. PISTA: ST longo + T normal = Ca²+ baixo.",
                        style={"fontStyle": "italic"},
                    ),
                ], style={"flex": "1"}),
            ], style={"display": "flex", "gap": "8px"}),
        ], className="card", style={"maxWidth": "800px", "marginTop": "16px"}),

        # --- SEÇÃO 5: Tabela comparativa ---
        html.Div([
            html.H4("Tabela Comparativa Rápida"),
            html.Table([
                html.Thead(html.Tr([
                    html.Th("Distúrbio"), html.Th("Fase afetada"), html.Th("O que a câmera vê"),
                ])),
                html.Tbody([
                    html.Tr([html.Td("K+ alto"), html.Td("Fases 3-4"), html.Td("T apiculada → P some → QRS alarga → sine wave")]),
                    html.Tr([html.Td("K+ baixo"), html.Td("Fase 3"), html.Td("T achata → infra ST → onda U → fusão T-U")]),
                    html.Tr([html.Td("Ca²+ alto"), html.Td("Fase 2"), html.Td("ST encurta → QT curto (T gruda no QRS)")]),
                    html.Tr([html.Td("Ca²+ baixo"), html.Td("Fase 2"), html.Td("ST prolonga → QT longo (T normal)")]),
                    html.Tr([html.Td("Mg²+ baixo"), html.Td("Canais K+/Ca²+"), html.Td("≈ K+ baixo + QT longo + Torsades")]),
                ]),
            ], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.9em"}),
        ], className="card", style={"maxWidth": "800px", "marginTop": "16px"}),

        # --- SEÇÃO 6: Visualizador de ECG eletrolítico ---
        html.Div([
            html.H4("Visualizador de ECG — Distúrbios Eletrolíticos"),
            html.P("Selecione um distúrbio para gerar o ECG sintético correspondente:"),
            html.Div([
                dcc.Dropdown(
                    id="elec-pathology-select",
                    options=[
                        {"label": "Normal (referência)", "value": "normal"},
                        {"label": "Hipercalemia leve (T apiculadas)", "value": "hyperkalemia"},
                        {"label": "Hipercalemia grave (sine wave)", "value": "hyperkalemia_severe"},
                        {"label": "Hipocalemia (T achata, onda U)", "value": "hypokalemia"},
                        {"label": "Hipercalcemia (QT curto)", "value": "hypercalcemia"},
                        {"label": "Hipocalcemia (QT longo, ST longo)", "value": "hypocalcemia"},
                    ],
                    value="normal",
                    clearable=False,
                    style={"width": "400px"},
                ),
                html.Button("Gerar ECG", id="btn-elec-ecg", n_clicks=0, style={"marginLeft": "10px"}),
            ], style={"display": "flex", "alignItems": "center", "marginBottom": "10px"}),
            dcc.Graph(id="elec-ecg-graph"),
            html.Div(id="elec-ecg-description", style={"marginTop": "8px", "fontStyle": "italic"}),
        ], className="card", style={"maxWidth": "800px", "marginTop": "16px"}),

        # --- SEÇÃO 7: Quiz de eletrólitos ---
        html.Div([
            html.H4("Quiz — Eletrólitos & ECG"),
            html.P("Teste seus conhecimentos. Questões com e sem ECG sintético."),
            html.Div([
                html.Label("Tipo:"),
                dcc.Dropdown(
                    id="elec-quiz-type",
                    options=[
                        {"label": "Todas as questões", "value": "all"},
                        {"label": "Apenas com ECG (imagem)", "value": "image"},
                        {"label": "Apenas texto (sem imagem)", "value": "text"},
                    ],
                    value="all",
                    clearable=False,
                    style={"width": "250px"},
                ),
                html.Label("Nº de questões:", style={"marginLeft": "10px"}),
                dcc.Input(id="elec-quiz-n", type="number", value=5, min=1, max=20, step=1),
                html.Button("Gerar Quiz", id="btn-elec-quiz", n_clicks=0, style={"marginLeft": "10px"}),
            ], style={"display": "flex", "gap": "8px", "alignItems": "center", "flexWrap": "wrap"}),
            html.Div(id="elec-quiz-content", style={"marginTop": "20px"}),
        ], className="card", style={"maxWidth": "800px", "marginTop": "16px"}),

        # --- SEÇÃO 8: Pérolas clínicas ---
        html.Div([
            html.H4("Pérolas Clínicas"),
            html.Ul([
                html.Li([html.B("1. "), "O ECG é o exame de potássio mais rápido. T apiculada + QRS largo → trate ANTES do resultado."]),
                html.Li([html.B("2. "), "Hipocalemia + hipomagnesemia = a dupla mais arritmogênica. Tratar AMBOS."]),
                html.Li([html.B("3. "), "QT longo com T normal = Ca²+. QT longo com T estranha = K+/Mg²+/drogas."]),
                html.Li([html.B("4. "), "Gluconato de Ca²+ IV é o 'escudo' da hipercalemia. Age em 1-3 min."]),
                html.Li([html.B("5. "), "Sulfato de Mg²+ IV é o tratamento de Torsades, MESMO com Mg²+ sérico normal."]),
                html.Li([html.B("6. "), "Acidose + hipercalemia = combinação letal. Corrigir acidose ajuda o K+."]),
            ]),
        ], className="card", style={"maxWidth": "800px", "marginTop": "16px"}),
    ])


def _layout_electrophysiology():
    """Layout da aba de eletrofisiologia cardíaca — potencial de ação, fases 0-4, refratariedade."""
    return html.Div([
        html.H3("Eletrofisiologia Cardíaca — O Potencial de Ação e o ECG"),
        html.P(
            "Entenda como cada fase do potencial de ação gera os componentes do ECG, "
            "a fisiologia do automatismo sinusal e os períodos refratários."
        ),

        # --- SEÇÃO 1: Visão geral ---
        html.Div([
            html.H4("O Potencial de Ação como 'Roteiro' do Filme Cardíaco"),
            html.P([
                "Cada célula cardíaca segue um ",
                html.B("potencial de ação (PA)"),
                " de ~250-350 ms (5 fases). O ECG é o que as câmeras (derivações) "
                "registram de milhões de PAs simultâneos.",
            ]),
            html.Table([
                html.Thead(html.Tr([
                    html.Th("Fase"), html.Th("Evento"), html.Th("Corrente"), html.Th("ECG"), html.Th("Voltagem"),
                ])),
                html.Tbody([
                    html.Tr([html.Td("0"), html.Td("Despolarização rápida"), html.Td("INa (Nav1.5)"), html.Td("QRS"), html.Td("-90 → +20 mV")]),
                    html.Tr([html.Td("1"), html.Td("Repol. precoce (notch)"), html.Td("Ito"), html.Td("Ponto J"), html.Td("+20 → +5 mV")]),
                    html.Tr([html.Td("2"), html.Td("Platô"), html.Td("ICa,L vs IKr/IKs"), html.Td("Segmento ST"), html.Td("~0 mV, 200 ms")]),
                    html.Tr([html.Td("3"), html.Td("Repolarização"), html.Td("IKr + IKs + IK1"), html.Td("Onda T"), html.Td("0 → -90 mV")]),
                    html.Tr([html.Td("4"), html.Td("Repouso"), html.Td("IK1 + Na/K-ATPase"), html.Td("Linha isoelétrica (T-P)"), html.Td("-90 mV")]),
                ]),
            ], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.9em", "marginTop": "10px"}),
        ], className="card", style={"maxWidth": "850px"}),

        # --- SEÇÃO 2: Figura interativa do PA contrátil ---
        html.Div([
            html.H4("Potencial de Ação — Cardiomiócito Contrátil vs ECG"),
            html.P("Selecione uma fase para destacar e ver detalhes:"),
            dcc.Dropdown(
                id="ephys-phase-select",
                options=[
                    {"label": "Todas as fases", "value": "all"},
                    {"label": "Fase 0 — Despolarização rápida (INa → QRS)", "value": "0"},
                    {"label": "Fase 1 — Repolarização precoce (Ito → Ponto J)", "value": "1"},
                    {"label": "Fase 2 — Platô (ICa,L ↔ IK → Segmento ST)", "value": "2"},
                    {"label": "Fase 3 — Repolarização (IKr+IKs → Onda T)", "value": "3"},
                    {"label": "Fase 4 — Repouso (IK1 → T-P isoelétrico)", "value": "4"},
                ],
                value="all",
                clearable=False,
                style={"width": "500px"},
            ),
            dcc.Graph(id="ephys-contractile-graph"),
            html.Div(id="ephys-phase-details", style={"marginTop": "8px"}),
        ], className="card", style={"maxWidth": "850px", "marginTop": "16px"}),

        # --- SEÇÃO 3: Detalhes de cada fase ---
        html.Div([
            html.H4("Detalhes de Cada Fase"),
            # Fase 0
            html.Div([
                html.H5("Fase 0 — Despolarização Rápida", style={"color": "#e74c3c"}),
                html.P([
                    html.B("Corrente: "), "INa (Nav1.5). ", html.B("Voltagem: "), "-90 → +20 mV em 1-2 ms.",
                ]),
                html.P(
                    "Milhares de canais de Na+ abrem simultaneamente → entrada massiva de Na+ → "
                    "upstroke ultra-rápido (200-400 V/s). No ECG: complexo QRS."
                ),
                html.P([
                    html.B("Velocidade de condução depende da INa: "),
                    "Purkinje (2-4 m/s) > miócitos (0.3-1 m/s) > nó AV (0.02-0.05 m/s, usa ICa,L).",
                ]),
                html.P([
                    html.B("Clínica: "),
                    "INa bloqueada (hipercalemia, classe I) → upstroke lento → QRS alargado.",
                ], style={"fontStyle": "italic"}),
            ], style={"borderLeft": "4px solid #e74c3c", "paddingLeft": "12px", "marginBottom": "16px"}),
            # Fase 1
            html.Div([
                html.H5("Fase 1 — Repolarização Precoce (Notch)", style={"color": "#f39c12"}),
                html.P([
                    html.B("Corrente: "), "Ito (Kv4.3). ", html.B("Voltagem: "), "+20 → +5 mV.",
                ]),
                html.P(
                    "Canais Ito abrem brevemente → K+ sai → entalhe (notch) entre fase 0 e platô. "
                    "Mais proeminente no EPICÁRDIO."
                ),
                html.P([
                    html.B("Clínica: "),
                    "Ito exagerada no epicárdio → colapso do platô → Síndrome de Brugada. "
                    "No ECG: ponto J (junção QRS-ST).",
                ], style={"fontStyle": "italic"}),
            ], style={"borderLeft": "4px solid #f39c12", "paddingLeft": "12px", "marginBottom": "16px"}),
            # Fase 2
            html.Div([
                html.H5("Fase 2 — Platô (O Grande Ato do Cálcio)", style={"color": "#2ecc71"}),
                html.P([
                    html.B("Correntes: "), "ICa,L (entrada Ca²+) vs IKr/IKs (saída K+). ",
                    html.B("Voltagem: "), "~0 mV por ~200 ms.",
                ]),
                html.P(
                    "O platô é EXCLUSIVO do coração. Equilíbrio entre Ca²+ entrando e K+ saindo. "
                    "Ca²+ desencadeia CICR → contração mecânica."
                ),
                html.P([
                    html.B("Por que é essencial: "),
                    "1) Contração mecânica (Ca²+ = gatilho). "
                    "2) Período refratário (impede tetania). "
                    "3) Coordenação (toda massa despolariza antes de repolarizar).",
                ]),
                html.P([
                    html.B("Clínica: "),
                    "Ca²+ alto → ICa,L inativa rápido → platô curto → QT curto. "
                    "Ca²+ baixo → platô longo → QT longo. No ECG: segmento ST.",
                ], style={"fontStyle": "italic"}),
            ], style={"borderLeft": "4px solid #2ecc71", "paddingLeft": "12px", "marginBottom": "16px"}),
            # Fase 3
            html.Div([
                html.H5("Fase 3 — Repolarização", style={"color": "#3498db"}),
                html.P([
                    html.B("Correntes: "), "IKr (hERG) + IKs + IK1. ",
                    html.B("Voltagem: "), "0 → -90 mV em ~100-150 ms.",
                ]),
                html.P(
                    "Quando ICa,L inativa, K+ predomina → repolarização. "
                    "IKr age primeiro, IKs é reserva, IK1 finaliza."
                ),
                html.P([
                    html.B("Por que T é positiva: "),
                    "Epicárdio repolariza ANTES do endocárdio (PA epicárdico mais curto). "
                    "Vetor de repolarização = mesma direção do de despolarização → T concordante com QRS.",
                ]),
                html.P([
                    html.B("Clínica: "),
                    "K+ alto → fase 3 acelerada → T apiculada. "
                    "K+ baixo → fase 3 lenta → T achatada. "
                    "Classe III (sotalol) bloqueia IKr → fase 3 lenta → QT longo.",
                ], style={"fontStyle": "italic"}),
            ], style={"borderLeft": "4px solid #3498db", "paddingLeft": "12px", "marginBottom": "16px"}),
            # Fase 4
            html.Div([
                html.H5("Fase 4 — Repouso / Diástole Elétrica", style={"color": "#9b59b6"}),
                html.P([
                    html.B("Corrente: "), "IK1 (Kir2.1) + bomba Na+/K+-ATPase. ",
                    html.B("Voltagem: "), "-90 mV (estável no contrátil).",
                ]),
                html.P(
                    "No cardiomiócito contrátil: fase 4 ESTÁVEL (não dispara sozinha). "
                    "No nó sinusal: fase 4 INSTÁVEL (automatismo — If + ICaT)."
                ),
                html.P([
                    html.B("Clínica: "),
                    "Digitálicos inibem Na/K-ATPase → acúmulo Na+ → troca Na/Ca reversa → "
                    "mais Ca²+ → inotropismo positivo (mas risco de intoxicação → arritmias). "
                    "No ECG: intervalo T-P (linha isoelétrica).",
                ], style={"fontStyle": "italic"}),
            ], style={"borderLeft": "4px solid #9b59b6", "paddingLeft": "12px", "marginBottom": "16px"}),
        ], className="card", style={"maxWidth": "850px", "marginTop": "16px"}),

        # --- SEÇÃO 4: Nó Sinusal ---
        html.Div([
            html.H4("Automatismo do Nó Sinusal — O Marcapasso Natural"),
            html.P([
                "O nó sinusal tem ", html.B("fase 4 INSTÁVEL"), " — se despolariza sozinho. "
                "Três correntes formam o 'relógio de membrana':",
            ]),
            html.Ul([
                html.Li([html.B("1. If (funny current / HCN4): "), "inicia a despolarização diastólica. "
                         "Ativada por HIPERPOLARIZAÇÃO (peculiar!). Alvo da IVABRADINA."]),
                html.Li([html.B("2. ICa,T (Ca²+ tipo T): "), "'empurrão' intermediário (~-50 mV)."]),
                html.Li([html.B("3. ICa,L (Ca²+ tipo L): "), "produz a fase 0 LENTA (upstroke dependente de Ca²+, "
                         "não Na+). Limiar: ~-40 mV."]),
            ]),
            dcc.Graph(id="ephys-pacemaker-graph"),
            html.Div([
                html.H5("Controle Autonômico da FC"),
                html.Div([
                    html.Div([
                        html.P([html.B("SIMPÁTICO (↑ FC):")]),
                        html.Ul([
                            html.Li("Noradrenalina → β1 → ↑ AMPc"),
                            html.Li("↑ AMPc → mais If + mais ICa,L"),
                            html.Li("Fase 4 mais rápida → FC aumenta"),
                        ]),
                    ], style={"flex": "1"}),
                    html.Div([
                        html.P([html.B("PARASSIMPÁTICO (↓ FC):")]),
                        html.Ul([
                            html.Li("Acetilcolina → M2 → ↓ AMPc + ativa IKACh"),
                            html.Li("Menos If + hiperpolarização"),
                            html.Li("Fase 4 mais lenta e partindo de mais negativo → FC cai"),
                        ]),
                    ], style={"flex": "1"}),
                ], style={"display": "flex", "gap": "16px"}),
            ]),
            html.Div([
                html.H5("Hierarquia dos Marcapassos"),
                html.Table([
                    html.Thead(html.Tr([html.Th("Localização"), html.Th("FC intrínseca"), html.Th("Ritmo de escape")])),
                    html.Tbody([
                        html.Tr([html.Td("Nó sinusal"), html.Td("60-100 bpm"), html.Td("Ritmo sinusal (comanda)")]),
                        html.Tr([html.Td("Nó AV"), html.Td("40-60 bpm"), html.Td("Juncional (QRS estreito, P retrógrada)")]),
                        html.Tr([html.Td("His-Purkinje"), html.Td("20-40 bpm"), html.Td("Escape ventricular (QRS largo)")]),
                    ]),
                ], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.9em"}),
            ], style={"marginTop": "12px"}),
        ], className="card", style={"maxWidth": "850px", "marginTop": "16px"}),

        # --- SEÇÃO 5: Comparação PA contrátil vs pacemaker ---
        html.Div([
            html.H4("Comparação: PA Contrátil vs Pacemaker"),
            dcc.Graph(id="ephys-comparison-graph"),
            html.Table([
                html.Thead(html.Tr([html.Th("Característica"), html.Th("Contrátil"), html.Th("Nó Sinusal")])),
                html.Tbody([
                    html.Tr([html.Td("Repouso"), html.Td("-90 mV (estável)"), html.Td("-60 mV (instável)")]),
                    html.Tr([html.Td("Fase 0"), html.Td("INa (rápido, 200-400 V/s)"), html.Td("ICa,L (lento, 1-10 V/s)")]),
                    html.Tr([html.Td("Fase 1"), html.Td("Ito (notch)"), html.Td("Ausente")]),
                    html.Tr([html.Td("Fase 2"), html.Td("Platô proeminente"), html.Td("Ausente/mínimo")]),
                    html.Tr([html.Td("Fase 3"), html.Td("IKr + IKs + IK1"), html.Td("IKr + IKs")]),
                    html.Tr([html.Td("Fase 4"), html.Td("Estável (IK1)"), html.Td("Automatismo (If)")]),
                    html.Tr([html.Td("Automatismo"), html.Td("NÃO"), html.Td("SIM")]),
                ]),
            ], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.9em", "marginTop": "10px"}),
        ], className="card", style={"maxWidth": "850px", "marginTop": "16px"}),

        # --- SEÇÃO 6: Períodos refratários ---
        html.Div([
            html.H4("Períodos Refratários — A Defesa Contra Arritmias"),
            html.Div([
                html.Div([
                    html.H5("Período Refratário Absoluto (PRA)", style={"color": "#e74c3c"}),
                    html.P([html.B("Fases 0, 1, 2 + início da 3"), " (~250 ms)"]),
                    html.P(
                        "NENHUM estímulo, por mais forte, gera novo PA. "
                        "Canais Na+ no estado INATIVADO (porta h fechada). "
                        "Precisam voltar a < -60 mV para recuperar."
                    ),
                    html.P([
                        html.B("ECG: "), "do início do QRS até ~pico da onda T.",
                    ]),
                ], style={"borderLeft": "4px solid #e74c3c", "paddingLeft": "12px", "marginBottom": "16px"}),
                html.Div([
                    html.H5("Período Refratário Relativo (PRR)", style={"color": "#3498db"}),
                    html.P([html.B("Final da fase 3"), " (~50 ms)"]),
                    html.P(
                        "Estímulo MAIS FORTE que o normal pode gerar PA anormal: "
                        "amplitude menor, upstroke lento, condução lenta."
                    ),
                    html.P([
                        html.B("ECG: "), "parte DESCENDENTE da onda T.",
                    ]),
                    html.P([
                        html.B("JANELA VULNERÁVEL! "),
                        "R sobre T aqui → PA anormal → bloqueio unidirecional → reentrada → TV/FV!",
                    ], style={"color": "#c0392b", "fontWeight": "bold"}),
                ], style={"borderLeft": "4px solid #3498db", "paddingLeft": "12px", "marginBottom": "16px"}),
                html.Div([
                    html.H5("Período Refratário Efetivo (PRE)"),
                    html.P("PRE = PRA + parte do PRR onde PA é fraco demais para se propagar."),
                    html.P([
                        html.B("Clinicamente: "),
                        "classe III (amiodarona, sotalol) aumenta PRE → antiarrítmico. "
                        "Hipercalemia diminui PRE → pró-arrítmico.",
                    ]),
                ], style={"borderLeft": "4px solid #95a5a6", "paddingLeft": "12px", "marginBottom": "16px"}),
            ]),
            html.Div([
                html.H5("Mapa dos Períodos Refratários no ECG"),
                html.Pre(
                    "  QRS ──── ST ──── T(↑) ──── T(↓) ──── T-P\n"
                    "  │←── PRA (ABSOLUTO) ──────→│← PRR →│← resp.→│\n"
                    "  │ Na+ INATIVADOS           │parcial│ pronto │\n"
                    "  │ Nenhum PA possível        │R/T!   │PA norm.│",
                    style={"background": "#f8f9fa", "padding": "12px", "fontSize": "0.85em",
                           "fontFamily": "monospace", "borderRadius": "6px"},
                ),
            ]),
        ], className="card", style={"maxWidth": "850px", "marginTop": "16px"}),

        # --- SEÇÃO 7: O que altera os períodos refratários ---
        html.Div([
            html.H4("O Que Altera os Períodos Refratários?"),
            html.Div([
                html.Div([
                    html.H5("AUMENTAM PRE (antiarrítmico)", style={"color": "#27ae60"}),
                    html.Ul([
                        html.Li("Classe III (amiodarona, sotalol): bloqueia IKr → fase 3 lenta → PA longo"),
                        html.Li("Hipocalemia: repolarização lenta → PRE↑ (mas dispersão pode ser pró-arrítmica!)"),
                        html.Li("FC baixa: PA mais longo → PRE mais longo"),
                    ]),
                ], style={"flex": "1"}),
                html.Div([
                    html.H5("DIMINUEM PRE (pró-arrítmico)", style={"color": "#c0392b"}),
                    html.Ul([
                        html.Li("Hipercalemia: fase 3 acelerada → PA curto → PRE curto"),
                        html.Li("Catecolaminas (adrenalina): encurtam o PA"),
                        html.Li("FC muito alta: PA encurta → PRE diminui"),
                        html.Li("Isquemia: encurta PA nas zonas afetadas → dispersão → reentrada"),
                    ]),
                ], style={"flex": "1"}),
            ], style={"display": "flex", "gap": "16px"}),
        ], className="card", style={"maxWidth": "850px", "marginTop": "16px"}),

        # --- SEÇÃO 8: Quiz ---
        html.Div([
            html.H4("Quiz — Eletrofisiologia Cardíaca"),
            html.P("Questões sobre potencial de ação, correntes iônicas, automatismo e refratariedade."),
            html.Div([
                html.Label("Tipo:"),
                dcc.Dropdown(
                    id="ephys-quiz-type",
                    options=[
                        {"label": "Todas as questões", "value": "all"},
                        {"label": "Com figura do PA", "value": "figure"},
                        {"label": "Apenas texto", "value": "text"},
                    ],
                    value="all", clearable=False, style={"width": "250px"},
                ),
                html.Label("Nº:", style={"marginLeft": "10px"}),
                dcc.Input(id="ephys-quiz-n", type="number", value=5, min=1, max=25, step=1),
                html.Button("Gerar Quiz", id="btn-ephys-quiz", n_clicks=0, style={"marginLeft": "10px"}),
            ], style={"display": "flex", "gap": "8px", "alignItems": "center", "flexWrap": "wrap"}),
            html.Div(id="ephys-quiz-content", style={"marginTop": "20px"}),
        ], className="card", style={"maxWidth": "850px", "marginTop": "16px"}),

        # --- SEÇÃO 9: Genes e Síndromes ---
        html.Div([
            html.H4("Canais Iônicos: Genes e Síndromes"),
            html.Table([
                html.Thead(html.Tr([html.Th("Canal"), html.Th("Gene"), html.Th("Corrente"), html.Th("Síndrome (mutação)")])),
                html.Tbody([
                    html.Tr([html.Td("Nav1.5"), html.Td("SCN5A"), html.Td("INa (fase 0)"), html.Td("Brugada, LQT3")]),
                    html.Tr([html.Td("Cav1.2"), html.Td("CACNA1C"), html.Td("ICa,L (fase 2)"), html.Td("Timothy, Brugada tipo 3")]),
                    html.Tr([html.Td("Kv11.1 (hERG)"), html.Td("KCNH2"), html.Td("IKr (fase 3)"), html.Td("LQT2")]),
                    html.Tr([html.Td("Kv7.1 (KvLQT1)"), html.Td("KCNQ1"), html.Td("IKs (fase 3)"), html.Td("LQT1")]),
                    html.Tr([html.Td("Kv4.3"), html.Td("KCND3"), html.Td("Ito (fase 1)"), html.Td("Brugada")]),
                    html.Tr([html.Td("Kir2.1"), html.Td("KCNJ2"), html.Td("IK1 (fase 4)"), html.Td("Andersen-Tawil")]),
                    html.Tr([html.Td("HCN4"), html.Td("HCN4"), html.Td("If (automatismo)"), html.Td("Doença do nó sinusal")]),
                ]),
            ], style={"width": "100%", "borderCollapse": "collapse", "fontSize": "0.9em"}),
        ], className="card", style={"maxWidth": "850px", "marginTop": "16px"}),
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
    elif tab == "tab-electrolytes":
        return _layout_electrolytes()
    elif tab == "tab-ephys":
        return _layout_electrophysiology()
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
        from quiz.adaptive import AdaptiveEngine
        engine = AdaptiveEngine(quiz_bank_path="quiz/bank")
        questions = []
        history = []
        for _ in range(n_questions or 6):
            q = engine.select_next_question(history)
            if not q:
                break
            questions.append(q)
            history.append({"question_id": q.get("id", ""), "correct": True, "tag": q.get("tag", q.get("topic", ""))})

        if not questions:
            # Fallback to simple engine
            from quiz.engine import build_adaptive_quiz
            result = build_adaptive_quiz({}, n_questions=n_questions or 6, seed=n_clicks)
            questions = result.get("questions", [])

        items = []
        for i, q in enumerate(questions):
            correct_idx = q.get("answer_index", 0)
            options_html = []
            for j, opt in enumerate(q.get("options", [])):
                marker = "\u2713" if j == correct_idx else "\u2717"
                color = "green" if j == correct_idx else "gray"
                options_html.append(html.Li(f"{marker} {opt}", style={"color": color}))
            items.append(html.Div([
                html.H4(f"{i+1}. [{q.get('difficulty','?')}] {q.get('topic','?')}"),
                html.P(q.get("stem", "")),
                html.Ul(options_html),
                html.Details([
                    html.Summary("Explicação"),
                    html.P(q.get("explanation", "Sem explicação."))
                ]),
                html.Hr(),
            ]))
        return html.Div(items) if items else html.P("Nenhuma questão disponível.")
    except Exception as e:
        return html.P(f"Erro ao gerar quiz: {e}")


@app.callback(Output("quiz-progress-content", "children"), Input("btn-quiz-progress", "n_clicks"), prevent_initial_call=True)
def show_quiz_progress(n_clicks):
    try:
        from quiz.progress import ProgressTracker
        from quiz.spaced_repetition import SpacedRepetitionScheduler
        tracker = ProgressTracker(data_dir="quiz_progress")
        sr = SpacedRepetitionScheduler(data_path="quiz_progress/sr_state.json")

        dashboard = tracker.get_dashboard_data()
        sr_stats = sr.get_stats()

        badges_html = []
        for b in dashboard.get("badges", []):
            icon = "\U0001f3c6" if b["earned"] else "\U0001f512"
            badges_html.append(html.Span(f"{icon} {b['name']}  ", style={"color": "gold" if b["earned"] else "gray"}))

        topic_rows = []
        for topic, stats in dashboard.get("topic_breakdown", {}).items():
            topic_rows.append(html.Tr([
                html.Td(topic),
                html.Td(f"{stats['correct']}/{stats['total']}"),
                html.Td(f"{stats['accuracy']*100:.0f}%"),
            ]))

        # Radar chart for competency profile
        radar_chart = html.P("")
        topic_data = dashboard.get("topic_breakdown", {})
        if topic_data and len(topic_data) >= 3:
            import plotly.graph_objects as go
            topics = list(topic_data.keys())
            accuracies = [topic_data[t]["accuracy"] * 100 for t in topics]
            # Close the polygon
            topics_closed = topics + [topics[0]]
            acc_closed = accuracies + [accuracies[0]]
            fig = go.Figure(data=go.Scatterpolar(
                r=acc_closed, theta=topics_closed, fill='toself',
                name='Acurácia (%)', line_color='#2196F3',
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False, title="Perfil de Competência",
                height=350, margin=dict(t=40, b=20, l=40, r=40),
            )
            radar_chart = dcc.Graph(figure=fig, config={"displayModeBar": False})

        return html.Div([
            html.H4("Seu Progresso"),
            html.Div([
                html.Span(f"Total: {dashboard['total_questions_answered']} | ", style={"fontWeight": "bold"}),
                html.Span(f"Acurácia: {dashboard['overall_accuracy']*100:.0f}% | "),
                html.Span(f"Streak: {dashboard['streak']} dias | "),
                html.Span(f"Dominadas: {sr_stats['mastered']} | "),
                html.Span(f"Aprendendo: {sr_stats['learning']} | "),
                html.Span(f"Para revisar hoje: {sr_stats['due_today']}"),
            ], style={"marginBottom": "15px"}),
            radar_chart,
            html.Div(badges_html, style={"marginBottom": "15px"}),
            html.Table([
                html.Thead(html.Tr([html.Th("Tópico"), html.Th("Acertos"), html.Th("Acurácia")])),
                html.Tbody(topic_rows),
            ], style={"width": "100%", "borderCollapse": "collapse"}) if topic_rows else html.P("Nenhuma sessão registrada ainda. Gere um quiz para começar!"),
        ])
    except Exception as e:
        return html.P(f"Erro ao carregar progresso: {e}")


# ---------------------------------------------------------------------------
# Callbacks da aba de eletrofisiologia
# ---------------------------------------------------------------------------

@app.callback(
    Output("ephys-contractile-graph", "figure"),
    Output("ephys-phase-details", "children"),
    Input("ephys-phase-select", "value"),
)
def update_contractile_ap(phase_val):
    phase_details = {
        "0": "Fase 0 — INa: a 'explosão' de Na+ que gera o QRS. Upstroke 200-400 V/s em 1-2 ms.",
        "1": "Fase 1 — Ito: o 'entalhe' epicárdico. Gera o ponto J. Ito exagerada → Brugada.",
        "2": "Fase 2 — ICa,L vs IKr/IKs: o platô (~200 ms). Ca²+ entra → contração. Gera o segmento ST.",
        "3": "Fase 3 — IKr+IKs+IK1: repolarização → onda T. Epicárdio primeiro → T positiva concordante com QRS.",
        "4": "Fase 4 — IK1: repouso a -90 mV. Estável no contrátil. Gera a linha isoelétrica T-P.",
        "all": "Todas as fases visíveis. Selecione uma fase para destacar e ver detalhes.",
    }
    try:
        from education.electrophysiology import create_action_potential_figure
        highlight = int(phase_val) if phase_val != "all" else None
        fig = create_action_potential_figure("contractile", highlight)
        return fig, phase_details.get(phase_val, "")
    except Exception as exc:
        fig = go.Figure()
        fig.update_layout(title=f"Erro: {exc}")
        return fig, f"Erro: {exc}"


@app.callback(
    Output("ephys-pacemaker-graph", "figure"),
    Input("tabs-main", "value"),
)
def update_pacemaker_ap(tab):
    if tab != "tab-ephys":
        import dash
        raise dash.exceptions.PreventUpdate
    try:
        from education.electrophysiology import create_action_potential_figure
        return create_action_potential_figure("pacemaker")
    except Exception as exc:
        fig = go.Figure()
        fig.update_layout(title=f"Erro: {exc}")
        return fig


@app.callback(
    Output("ephys-comparison-graph", "figure"),
    Input("tabs-main", "value"),
)
def update_comparison_ap(tab):
    if tab != "tab-ephys":
        import dash
        raise dash.exceptions.PreventUpdate
    try:
        from education.electrophysiology import create_phase_comparison_figure
        return create_phase_comparison_figure()
    except Exception as exc:
        fig = go.Figure()
        fig.update_layout(title=f"Erro: {exc}")
        return fig


@app.callback(
    Output("ephys-quiz-content", "children"),
    Input("btn-ephys-quiz", "n_clicks"),
    State("ephys-quiz-type", "value"),
    State("ephys-quiz-n", "value"),
    prevent_initial_call=True,
)
def generate_ephys_quiz(n_clicks, quiz_type, n_questions):
    import random as _rnd
    _rnd.seed(n_clicks)
    n_questions = n_questions or 5
    try:
        from quiz.electrophysiology_questions import (
            ALL_QUESTIONS, get_figure_questions, get_text_questions,
        )
        if quiz_type == "figure":
            pool = get_figure_questions()
        elif quiz_type == "text":
            pool = get_text_questions()
        else:
            pool = list(ALL_QUESTIONS)
        _rnd.shuffle(pool)
        selected = pool[:n_questions]
        elements = []
        for i, q in enumerate(selected):
            q_elements = [html.H5(f"Questão {i+1} [{q['difficulty']}] — {q['topic']}")]
            # Generate figure if question has one
            if q.get("image_figure"):
                try:
                    from education.electrophysiology import (
                        create_action_potential_figure, create_phase_comparison_figure,
                    )
                    fig_type = q["image_figure"]
                    if fig_type == "comparison":
                        fig = create_phase_comparison_figure()
                    else:
                        fig = create_action_potential_figure(fig_type)
                    fig.update_layout(height=400, width=700)
                    q_elements.append(dcc.Graph(figure=fig, style={"marginBottom": "8px"}))
                except Exception:
                    q_elements.append(html.P("[Figura não pôde ser gerada]", style={"color": "gray"}))
            q_elements.append(html.P(q["stem"], style={"fontWeight": "bold"}))
            choices = []
            for j, opt in enumerate(q["options"]):
                marker = "✓" if j == q["answer_index"] else "✗"
                choices.append(html.Li(f"[{marker}] {opt}"))
            q_elements.append(html.Ul(choices))
            q_elements.append(html.Details([
                html.Summary("Ver explicação"),
                html.P(q["explanation"], style={"marginTop": "6px", "color": "#2c3e50"}),
            ]))
            elements.append(html.Div(q_elements, className="card", style={"marginBottom": "12px"}))
        return elements
    except Exception as e:
        return html.P(f"Erro ao gerar quiz: {e}")


# ---------------------------------------------------------------------------
# Callbacks da aba de eletrólitos
# ---------------------------------------------------------------------------

@app.callback(
    Output("elec-ecg-graph", "figure"),
    Output("elec-ecg-description", "children"),
    Input("btn-elec-ecg", "n_clicks"),
    State("elec-pathology-select", "value"),
    prevent_initial_call=True,
)
def generate_electrolyte_ecg(n_clicks, pathology):
    pathology = pathology or "normal"
    descriptions = {
        "normal": "ECG normal — referência para comparação.",
        "hyperkalemia": (
            "Hipercalemia leve (K+ 5.5-6.5): observe as ondas T apiculadas, "
            "simétricas e de base estreita, especialmente em V2-V4. PR e QRS normais."
        ),
        "hyperkalemia_severe": (
            "Hipercalemia grave (K+ > 7.5): padrão sine wave — QRS muito alargado "
            "fundindo com T, sem onda P. EMERGÊNCIA: gluconato de cálcio IV imediato!"
        ),
        "hypokalemia": (
            "Hipocalemia: T achatada, infradesnivelamento de ST e onda U proeminente "
            "(deflexão positiva após T). Melhor visualizada em V2-V3."
        ),
        "hypercalcemia": (
            "Hipercalcemia: QT curto — o segmento ST praticamente desaparece. "
            "A onda T parece 'grudada' no QRS, sem a pausa habitual."
        ),
        "hypocalcemia": (
            "Hipocalcemia: QT longo por prolongamento do segmento ST. "
            "A onda T mantém morfologia normal — a pausa entre QRS e T é longa."
        ),
    }
    try:
        from simulation.ecg_generator import generate_ecg, generate_pathological_ecg
        if pathology == "normal":
            result = generate_ecg(hr_bpm=72, duration_s=10)
        else:
            result = generate_pathological_ecg(pathology)
        leads_data = result.get("leads", {})
        fig = go.Figure()
        for lead_name in ["II", "V2", "V4"]:
            if lead_name in leads_data:
                sig = leads_data[lead_name]
                t = result.get("time")
                x_vals = t.tolist() if t is not None else None
                y_vals = sig.tolist() if hasattr(sig, 'tolist') else sig
                # Show only 5 seconds
                if x_vals and len(x_vals) > 2500:
                    x_vals = x_vals[:2500]
                    y_vals = y_vals[:2500]
                fig.add_trace(go.Scatter(
                    x=x_vals, y=y_vals, mode="lines", name=lead_name,
                ))
        desc_label = result.get("pathology_description_pt", pathology)
        fig.update_layout(
            title=f"ECG Eletrolítico — {desc_label}",
            xaxis_title="Tempo (s)", yaxis_title="mV",
            legend=dict(orientation="h"),
            paper_bgcolor="#FFF5F5", plot_bgcolor="#FFF5F5",
            xaxis=dict(showgrid=True, gridcolor="rgba(255,150,150,0.3)", dtick=0.2),
            yaxis=dict(showgrid=True, gridcolor="rgba(255,150,150,0.3)", dtick=0.5),
        )
        return fig, descriptions.get(pathology, "")
    except Exception as exc:
        fig = go.Figure()
        fig.update_layout(title=f"Erro: {exc}")
        return fig, f"Erro ao gerar ECG: {exc}"


@app.callback(
    Output("elec-quiz-content", "children"),
    Input("btn-elec-quiz", "n_clicks"),
    State("elec-quiz-type", "value"),
    State("elec-quiz-n", "value"),
    prevent_initial_call=True,
)
def generate_electrolyte_quiz(n_clicks, quiz_type, n_questions):
    import random as _rnd
    _rnd.seed(n_clicks)
    n_questions = n_questions or 5
    try:
        from quiz.electrolyte_questions import ALL_QUESTIONS, get_image_questions, get_text_questions
        if quiz_type == "image":
            pool = get_image_questions()
        elif quiz_type == "text":
            pool = get_text_questions()
        else:
            pool = list(ALL_QUESTIONS)
        _rnd.shuffle(pool)
        selected = pool[:n_questions]
        elements = []
        for i, q in enumerate(selected):
            # Build question card
            q_elements = [html.H5(f"Questão {i+1} [{q['difficulty']}] — {q['topic']}")]
            # If question has image, generate ECG figure
            if q.get("image_pathology"):
                try:
                    from simulation.ecg_generator import generate_ecg, generate_pathological_ecg
                    pathology = q["image_pathology"]
                    if pathology == "normal":
                        result = generate_ecg(hr_bpm=72, duration_s=5)
                    else:
                        result = generate_pathological_ecg(pathology)
                    leads_data = result.get("leads", {})
                    fig = go.Figure()
                    for lead_name in ["II", "V2"]:
                        if lead_name in leads_data:
                            sig = leads_data[lead_name]
                            y_vals = sig[:2500].tolist() if hasattr(sig, 'tolist') else sig[:2500]
                            fig.add_trace(go.Scatter(y=y_vals, mode="lines", name=lead_name))
                    fig.update_layout(
                        height=250, margin=dict(l=40, r=20, t=30, b=20),
                        paper_bgcolor="#FFF5F5", plot_bgcolor="#FFF5F5",
                        xaxis=dict(showgrid=True, gridcolor="rgba(255,150,150,0.3)"),
                        yaxis=dict(showgrid=True, gridcolor="rgba(255,150,150,0.3)"),
                        legend=dict(orientation="h"),
                    )
                    q_elements.append(dcc.Graph(figure=fig, style={"marginBottom": "8px"}))
                except Exception:
                    q_elements.append(html.P("[ECG não pôde ser gerado]", style={"color": "gray"}))
            q_elements.append(html.P(q["stem"], style={"fontWeight": "bold"}))
            # Options with reveal
            choices = []
            for j, opt in enumerate(q["options"]):
                marker = "✓" if j == q["answer_index"] else "✗"
                choices.append(html.Li(f"[{marker}] {opt}"))
            q_elements.append(html.Ul(choices))
            q_elements.append(html.Details([
                html.Summary("Ver explicação"),
                html.P(q["explanation"], style={"marginTop": "6px", "color": "#2c3e50"}),
            ]))
            elements.append(html.Div(q_elements, className="card", style={"marginBottom": "12px"}))
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
    hr = hr or 75
    duration = duration or 5
    pathology = pathology or "normal"
    try:
        from simulation.ecg_generator import generate_ecg, generate_pathological_ecg

        if pathology == "normal":
            result = generate_ecg(hr_bpm=hr, duration_s=duration)
        else:
            result = generate_pathological_ecg(pathology)

        leads_data = result.get("leads", {})
        desc = result.get("pathology_description_pt", pathology)
        actual_hr = result.get("params", {}).get("hr_bpm", hr)

        fig = go.Figure()
        for lead_name in ["II", "V1", "V5"]:
            if lead_name in leads_data:
                sig = leads_data[lead_name]
                fig.add_trace(go.Scatter(
                    y=sig.tolist() if hasattr(sig, 'tolist') else sig,
                    mode="lines", name=lead_name,
                ))

        title = f"ECG Simulado — {desc} ({actual_hr} bpm)"
        fig.update_layout(
            title=title,
            xaxis_title="Amostras", yaxis_title="mV",
            legend=dict(orientation="h"),
        )
        return fig
    except Exception as exc:
        fig = go.Figure()
        t = np.linspace(0, duration, duration * 500)
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
            pxsec = _get_pxsec()
            axis_rpeaks = {}
            for axis_lead in ('I', 'aVF'):
                x0,y0,x1,y1 = lab2box[axis_lead]
                crop = arrL[y0:y1, x0:x1]
                trace = smooth_signal(extract_trace_centerline(crop), win=11)
                axis_rpeaks[axis_lead] = pan_tompkins_like(trace, pxsec).get('peaks_idx', [])
            axis = frontal_axis_from_image(
                arrL,
                {'I': lab2box['I'], 'aVF': lab2box['aVF']},
                axis_rpeaks,
                {'I': pxsec, 'aVF': pxsec},
            )
            angle = axis.get('angle_deg')
            if angle is None:
                summary.append(f"Eixo: {axis.get('label','Indeterminado')}")
            else:
                summary.append(f"Eixo: {angle:.1f}° — {axis.get('label','?')}")

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

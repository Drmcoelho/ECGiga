import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, DiskcacheManager
import diskcache

# Gerenciador de callbacks em background usando cache em disco
cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)

app = dash.Dash(
    __name__, 
    use_pages=True, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    background_callback_manager=background_callback_manager,
    suppress_callback_exceptions=True # Necessário pois os callbacks estão em arquivos separados
)
app.title = "ECG Giga - Curso Interativo de ECG"

# Define a barra de navegação superior
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink(page["name"], href=page["relative_path"])) for page in dash.page_registry.values()
    ] + [
        html.Span("", id="welcome-message", className="ms-auto text-white")
    ],
    brand="ECG Giga",
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-2",
)

# Layout principal da aplicação
app.layout = html.Div([
    dcc.Location(id="url"),
    # Armazenamento de dados do perfil do usuário no navegador
    dcc.Store(id='user-profile-store', storage_type='local'),
    navbar,
    dbc.Container(id="page-content", children=[dash.page_container], fluid=True)
])

# Callback para atualizar a mensagem de boas-vindas
@app.callback(
    Output("welcome-message", "children"),
    Input("user-profile-store", "data")
)
def update_welcome_message(data):
    if data and data.get("user_name"):
        return f"Bem-vindo(a), {data['user_name']}!"
    return "Bem-vindo(a)!"

if __name__ == "__main__":
    app.run(debug=True)
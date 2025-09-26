import dash
import dash_bootstrap_components as dbc
from dash import html, dcc
import diskcache
from dash.long_callback import DiskcacheManager

# Gerenciador de callbacks em background usando cache em disco
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheManager(cache)

# Conecta ao app Dash principal. O `use_pages=True` habilita o roteamento de páginas.
app = dash.Dash(
    __name__, 
    use_pages=True, 
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    long_callback_manager=long_callback_manager
)
app.title = "ECG Giga - Curso Interativo de ECG"

# Define a barra de navegação superior
navbar = dbc.NavbarSimple(
    children=[
        # Cria um link para cada página registrada no diretório `pages`
        dbc.NavItem(dbc.NavLink(page["name"], href=page["relative_path"])) for page in dash.page_registry.values()
    ],
    brand="ECG Giga",
    brand_href="/",
    color="primary",
    dark=True,
    className="mb-2",
)

# Layout principal da aplicação
app.layout = html.Div([
    # `dcc.Location` monitora a URL na barra de endereços
    dcc.Location(id="url"),

    # A barra de navegação que será exibida em todas as páginas
    navbar,

    # O conteúdo da página atual será renderizado aqui. 
    # `dash.page_container` é preenchido pelo Dash com base na URL.
    dbc.Container(id="page-content", children=[dash.page_container], fluid=True)
])

if __name__ == "__main__":
    app.run(debug=True)
import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(__name__, name="Biblioteca de Casos")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("Biblioteca de Casos Clínicos"),
                        html.P(
                            "Esta seção abrigará a funcionalidade do Case Player, permitindo a prática com uma vasta coleção de ECGs."
                        ),
                        html.P("Em breve..."),
                    ]
                )
            ]
        )
    ]
)

import json

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, html

dash.register_page(__name__, name="Perfil")

layout = dbc.Container(
    [
        html.H1("Gerenciamento de Perfil"),
        html.P("Os dados inseridos aqui são salvos localmente no seu navegador."),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Seus Dados"),
                                dbc.CardBody(
                                    [
                                        dbc.Label("Nome de Usuário:"),
                                        dbc.Input(
                                            id="input-user-name",
                                            type="text",
                                            placeholder="Digite seu nome...",
                                        ),
                                        dbc.Button(
                                            "Salvar Perfil",
                                            id="btn-save-profile",
                                            color="primary",
                                            className="mt-3",
                                        ),
                                        dbc.Alert(
                                            id="profile-save-status",
                                            color="success",
                                            is_open=False,
                                            duration=4000,
                                            className="mt-3",
                                        ),
                                    ]
                                ),
                            ]
                        )
                    ],
                    md=6,
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Dados Salvos (JSON)"),
                                dbc.CardBody(
                                    [
                                        html.Pre(
                                            id="stored-data-display",
                                            style={"whiteSpace": "pre-wrap"},
                                        )
                                    ]
                                ),
                            ]
                        )
                    ],
                    md=6,
                ),
            ]
        ),
    ],
    fluid=True,
)


# Callback para carregar os dados existentes na página
@callback(
    Output("input-user-name", "value"),
    Output("stored-data-display", "children"),
    Input("user-profile-store", "data"),
)
def load_profile_data(data):
    if data is None:
        # Inicializa o perfil se não existir
        initial_profile = {"user_name": "Visitante", "quiz_history": {}, "reviewed_cases": []}
        return "Visitante", json.dumps(initial_profile, indent=2)

    user_name = data.get("user_name", "")
    stored_json = json.dumps(data, indent=2)
    return user_name, stored_json


# Callback para salvar os dados
@callback(
    Output("user-profile-store", "data"),
    Output("profile-save-status", "is_open"),
    Output("profile-save-status", "children"),
    Input("btn-save-profile", "n_clicks"),
    State("input-user-name", "value"),
    State("user-profile-store", "data"),  # Pega os dados existentes para não sobrescrever tudo
    prevent_initial_call=True,
)
def save_profile_data(n_clicks, user_name, existing_data):
    if not user_name:
        return dash.no_update, True, "O nome não pode estar vazio."

    # Se não há dados, inicializa
    if existing_data is None:
        existing_data = {"user_name": "Visitante", "quiz_history": {}, "reviewed_cases": []}

    # Atualiza apenas o campo do nome
    updated_data = existing_data
    updated_data["user_name"] = user_name

    return updated_data, True, f"Perfil de '{user_name}' salvo com sucesso!"

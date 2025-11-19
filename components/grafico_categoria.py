from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc

def render(df):
    categorias = sorted(df["Categoría"].unique())
    municipios = sorted(df["Municipio"].unique())

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Categoría:", className="fw-bold"),
                dcc.Dropdown(
                    id="gc-categoria-dropdown",
                    options=[{"label": c, "value": c} for c in categorias],
                    value=categorias[0],
                    clearable=False,
                    className="mb-3"
                )
            ], width=4),
            dbc.Col([
                html.Label("Municipio:", className="fw-bold"),
                dcc.Dropdown(
                    id="gc-municipio-dropdown",
                    options=[{"label": m, "value": m} for m in municipios],
                    value=municipios[0],
                    clearable=False,
                    className="mb-3"
                )
            ], width=4),
            dbc.Col([
                html.Label("Tipo:", className="fw-bold"),
                dcc.Dropdown(
                    id="gc-tipo-dropdown",
                    options=[
                        {"label": "Barras", "value": "Barras"},
                        {"label": "Línea",  "value": "Línea"},
                        {"label": "Pastel", "value": "Pastel"}
                    ],
                    value="Barras",
                    clearable=False,
                    className="mb-3"
                )
            ], width=4)
        ]),
        dcc.Loading(dcc.Graph(id="gc-graph"), type="circle")
    ], className="mb-5")


def register_callbacks(app, df):
    @app.callback(
        Output("gc-graph", "figure"),
        Input("gc-categoria-dropdown", "value"),
        Input("gc-municipio-dropdown", "value"),
        Input("gc-tipo-dropdown", "value")
    )
    def actualizar_gc(categoria, municipio, tipo):
        dff = df[(df["Categoría"] == categoria) & (df["Municipio"] == municipio)]
        if tipo == "Pastel":
            return px.pie(dff, names="Indicador", values="Valor (%)",
                          title=f"{categoria} en {municipio}")
        if tipo == "Línea":
            return px.line(dff, x="Año", y="Valor (%)",
                           title=f"{categoria} en {municipio}")
        return px.bar(dff, x="Indicador", y="Valor (%)",
                      title=f"{categoria} en {municipio}")

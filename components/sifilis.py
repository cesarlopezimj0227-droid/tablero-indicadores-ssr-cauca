# sifilis.py

import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output

# Carga de datos
df_sifilis = pd.read_excel("assets/data/its_sifilis.xlsx")
df_sifilis["fecha_notif"] = pd.to_datetime(df_sifilis["fecha_notif"], errors="coerce")
df_sifilis["casos"] = pd.to_numeric(df_sifilis["casos"], errors="coerce")
df_sifilis["semana"] = pd.to_numeric(df_sifilis["semana"], errors="coerce")

# Layout del módulo
layout = html.Div([
    html.H3("Indicadores de Sífilis", className="module-title"),

    dbc.Tabs([
        dbc.Tab(label="Sífilis Gestacional", tab_id="gestacional"),
        dbc.Tab(label="Sífilis Congénita", tab_id="congenita"),
    ], id="sifilis-tabs", active_tab="gestacional"),

    html.Div(id="sifilis-content")
])

# Callback para renderizar contenido según pestaña
def register_callbacks(app):
    @app.callback(
        Output("sifilis-content", "children"),
        Input("sifilis-tabs", "active_tab")
    )
    def render_tab(tab):
        df = df_sifilis[df_sifilis["evento"] == ("Sífilis Gestacional" if tab == "gestacional" else "Sífilis Congénita")]

        municipios = sorted(df["municipio"].dropna().unique())
        eps_list = sorted(df["eps"].dropna().unique())

        return html.Div([
            dbc.Row([
                dbc.Col(dcc.Dropdown(
                    options=[{"label": m, "value": m} for m in municipios],
                    id="filtro-municipio",
                    placeholder="Filtrar por municipio"
                ), md=6),
                dbc.Col(dcc.Dropdown(
                    options=[{"label": e, "value": e} for e in eps_list],
                    id="filtro-eps",
                    placeholder="Filtrar por EPS"
                ), md=6),
            ]),
            dcc.Graph(id="grafico-sifilis")
        ])

    @app.callback(
        Output("grafico-sifilis", "figure"),
        Input("sifilis-tabs", "active_tab"),
        Input("filtro-municipio", "value"),
        Input("filtro-eps", "value")
    )
    def update_graph(tab, municipio, eps):
        df = df_sifilis[df_sifilis["evento"] == ("Sífilis Gestacional" if tab == "gestacional" else "Sífilis Congénita")]

        if municipio:
            df = df[df["municipio"] == municipio]
        if eps:
            df = df[df["eps"] == eps]

        df_grouped = df.groupby("semana")["casos"].sum().reset_index()

        fig = px.bar(
            df_grouped,
            x="semana", y="casos",
            title="Casos por semana epidemiológica",
            labels={"semana": "Semana", "casos": "Número de casos"},
            color_discrete_sequence=["#0072B5"]
        )
        fig.update_layout(margin=dict(t=40, l=20, r=20, b=20))
        return fig

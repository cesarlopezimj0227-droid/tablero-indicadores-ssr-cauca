# components/control_prenatal.py
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc

def render(df_cpn):
    """Renderiza los controles y contenedor para Control Prenatal (CPN)."""
    # municipios disponibles
    municipios = sorted(df_cpn["Municipio"].unique())

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Municipio:", className="fw-bold"),
                dcc.Dropdown(
                    id="cpn-municipio-dropdown",
                    options=[{"label": m, "value": m} for m in municipios],
                    value=municipios[0],
                    clearable=False,
                    className="mb-3"
                )
            ], width=6),
            dbc.Col([
                html.Label("Tipo de gráfico:", className="fw-bold"),
                dcc.Dropdown(
                    id="cpn-tipo-dropdown",
                    options=[
                        {"label": "📊 Barras", "value": "Barras"},
                        {"label": "📈 Líneas", "value": "Línea"},
                        {"label": "🥧 Pastel", "value": "Pastel"},
                        {"label": "📋 Tabla",  "value": "Tabla"}
                    ],
                    value="Barras",
                    clearable=False,
                    className="mb-3"
                )
            ], width=6),
        ], className="mb-4"),

        html.Div(id="cpn-contenido")
    ], className="mb-5")


def register_callbacks(app, df_cpn):
    @app.callback(
        Output("cpn-contenido", "children"),
        Input("cpn-municipio-dropdown", "value"),
        Input("cpn-tipo-dropdown", "value")
    )
    def actualizar_cpn(municipio, tipo):
        dff = df_cpn[df_cpn["Municipio"] == municipio]

        if tipo == "Tabla":
            return dbc.Table.from_dataframe(
                dff, striped=True, bordered=True, hover=True
            )

        if tipo == "Pastel":
            fig = px.pie(
                dff, names="Indicador", values="Valor (%)",
                title=f"CPN en {municipio}"
            )
        elif tipo == "Línea":
            fig = px.line(
                dff, x="Año", y="Valor (%)",
                title=f"Tendencia CPN en {municipio}"
            )
        else:  # Barras
            fig = px.bar(
                dff, x="Indicador", y="Valor (%)",
                title=f"Control Prenatal en {municipio}"
            )

        return dcc.Graph(figure=fig)

from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import dash_bootstrap_components as dbc

def render(df):
    if df.empty:
        return dbc.Alert("No hay datos disponibles", color="warning")

    df_vs = df[df["Categoría"] == "Violencia Sexual"]
    municipios = sorted(df_vs["Municipio"].unique())

    # layout
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Municipio:", className="fw-bold"),
                dcc.Dropdown(
                    id="vs-municipio-dropdown",
                    options=[{"label": m, "value": m} for m in municipios],
                    value=municipios[0],
                    clearable=False,
                    className="mb-3"
                )
            ], width=6),
            dbc.Col([
                html.Label("Tipo de gráfico:", className="fw-bold"),
                dcc.Dropdown(
                    id="vs-tipo-grafico-dropdown",
                    options=[
                        {"label": "Barras", "value": "Barras"},
                        {"label": "Línea",  "value": "Línea"},
                        {"label": "Pastel", "value": "Pastel"},
                        {"label": "Tabla",  "value": "Tabla"}
                    ],
                    value="Barras",
                    clearable=False,
                    className="mb-3"
                )
            ], width=6),
        ], className="mb-4"),

        html.Div(id="vs-contenido")
    ], className="mb-5")


def register_callbacks(app, df):
    @app.callback(
        Output("vs-contenido", "children"),
        Input("vs-municipio-dropdown", "value"),
        Input("vs-tipo-grafico-dropdown", "value")
    )
    def actualizar_vs(municipio, tipo):
        df_vs = df[df["Categoría"] == "Violencia Sexual"]
        df_sel = df_vs[df_vs["Municipio"] == municipio]

        if tipo == "Tabla":
            return dbc.Table.from_dataframe(
                df_sel.drop(columns=["Categoría"]), striped=True, bordered=True, hover=True
            )

        if tipo == "Pastel":
            fig = px.pie(df_sel, names="Indicador", values="Valor (%)",
                         title=f"Violencia Sexual en {municipio}")
        elif tipo == "Línea":
            fig = px.line(df_sel, x="Año", y="Valor (%)",
                          title=f"Tendencia de VS en {municipio}")
        else:
            fig = px.bar(df_sel, x="Indicador", y="Valor (%)",
                         title=f"Violencia Sexual en {municipio}")

        return dcc.Graph(figure=fig)

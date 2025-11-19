from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

def render(df):
    return html.Div(id="kpi-cards-container", className="mb-5")

def register_callbacks(app, df):
    @app.callback(
        Output("kpi-cards-container", "children"),
        Input("gc-graph", "figure")  # un “trigger” cualquiera para lanzar la actualización
    )
    def actualizar_kpis(_):
        cards = []
        for _, row in df.iterrows():
            color = ("success" if row["Valor (%)"] >= row["Meta (%)"]
                     else "warning" if row["Valor (%)"] >= 60
                     else "danger")
            cards.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H5(row["Indicador"], className="card-title"),
                        html.H2(f"{row['Valor (%)']:.1f}%", className=f"text-{color}"),
                        html.P(f"Meta: {row['Meta (%)']}%"),
                        html.P(f"Categoría: {row['Categoría']}")
                    ])
                ], className="m-2", style={"width": "200px"})
            )
        return dbc.Row(cards, justify="start")

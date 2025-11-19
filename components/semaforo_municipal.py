from dash import dcc, html
from dash.dependencies import Input, Output
import dash_table
import dash_bootstrap_components as dbc

def render(df):
    municipios = sorted(df["Municipio"].unique())
    return html.Div([
        html.H2("Semáforo por Municipio", className="mb-3"),
        dcc.Dropdown(
            id="sm-municipio-dropdown",
            options=[{"label": m, "value": m} for m in municipios],
            value=municipios[0],
            clearable=False,
            className="mb-3"
        ),
        html.Div(id="sm-table")
    ], className="mb-5")

def register_callbacks(app, df):
    @app.callback(
        Output("sm-table", "children"),
        Input("sm-municipio-dropdown", "value")
    )
    def actualizar_semaforo(mun):
        dff = df[df["Municipio"] == mun].copy()
        # ejemplo: añadir columna color según Valor vs Meta
        dff["Semáforo"] = dff.apply(
            lambda r: ("🟢" if r["Valor (%)"] >= r["Meta (%)"] 
                       else "🟠" if r["Valor (%)"] >= 60 
                       else "🔴"),
            axis=1
        )
        return dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in dff.columns],
            data=dff.to_dict("records"),
            style_cell={'textAlign': 'center'},
            style_header={'fontWeight': 'bold'}
        )


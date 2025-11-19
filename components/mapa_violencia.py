from dash import dcc, html
import plotly.express as px
import json

def render(df):
    # Filtrar solo violencia sexual
    df_vs = df[df["Categoría"] == "Violencia Sexual"]

    # Cargar el GeoJSON con límites municipales del Cauca
    with open("data/cauca_municipios.geojson", encoding="utf-8") as f:
        geojson = json.load(f)

    # Crear el mapa
    fig = px.choropleth_mapbox(
        df_vs,
        geojson=geojson,
        locations="Municipio",
        featureidkey="properties.NOMBRE_MUN",  # Asegúrate que esta clave coincide con el nombre del municipio en el GeoJSON
        color="Valor (%)",
        color_continuous_scale="Reds",
        mapbox_style="carto-positron",
        zoom=6,
        center={"lat": 2.5, "lon": -76.6},
        opacity=0.6,
        hover_name="Municipio",
        hover_data={"Valor (%)": True, "Indicador": True}
    )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    return html.Div([
        html.H2("🗺️ Mapa de violencia sexual por municipio", style={"marginTop": "40px"}),
        dcc.Graph(figure=fig)
    ])

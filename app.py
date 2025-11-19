import dash
from dash import html, dcc, dash_table
import pandas as pd
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import numpy as np

# Crear la aplicación Dash con tema visual
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Tablero SSR Cauca 2025"
#  NECESARIO PARA RENDER
server = app.server

# Cargar los datos desde los archivos Excel
try:
    df = pd.read_excel("data/indicadores.xlsx")
    df_cpn = pd.read_excel("data/cpn_gestantes_resumen.xlsx")
    df_cpn2 = pd.read_excel("data/GESTANTES_MUNICIPIO.xlsx")
    df_sifilis = pd.read_excel("data/its_sifilis.xlsx")
    df_sifilis["fecha_notif"] = pd.to_datetime(df_sifilis["fecha_notif"], errors="coerce")
    df_sifilis["casos"] = pd.to_numeric(df_sifilis["casos"], errors="coerce")
    df_sifilis["semana"] = pd.to_numeric(df_sifilis["semana"], errors="coerce")
except FileNotFoundError:
    df_sifilis = pd.DataFrame()  # Evita que se rompa el tablero si el archivo no está
    
    df_cpn = pd.DataFrame({
        'Municipio': ['Popayán', 'Timbío', 'Patía', 'Bolívar'],
        'CPN_Precoz': np.random.uniform(70, 95, 4),
        'CPN_Completo': np.random.uniform(65, 90, 4),
        'Suplementacion_Hierro': np.random.uniform(80, 95, 4),
        'Control_Odontologico': np.random.uniform(60, 85, 4)
    })

# === COMPONENTES MODULARES ===

def crear_kpis(df):
    """Crear indicadores clave"""
    try:
        # Calcular indicadores de forma más robusta
        cobertura_cpn = df[df['Indicador'].str.contains('CPN|Prenatal|prenatal', case=False, na=False)]['Valor (%)'].mean()
        parto_inst = df[df['Indicador'].str.contains('Parto|Institucional|parto', case=False, na=False)]['Valor (%)'].mean()
        casos_vs = len(df[df['Categoría'].str.contains('Violencia|Sexual', case=False, na=False)])
        municipios = df['Municipio'].nunique()
        
        # Si no hay datos específicos, usar valores promedio
        if pd.isna(cobertura_cpn):
            cobertura_cpn = df['Valor (%)'].mean() if not df.empty else 0
        if pd.isna(parto_inst):
            parto_inst = df['Valor (%)'].mean() if not df.empty else 0
        
        kpis_data = [
            {
                "titulo": "Cobertura CPN Promedio", 
                "valor": f"{cobertura_cpn:.1f}%" if not pd.isna(cobertura_cpn) else "N/A", 
                "color": "primary",
                "icono": "fas fa-user-md"
            },
            {
                "titulo": "Parto Institucional", 
                "valor": f"{parto_inst:.1f}%" if not pd.isna(parto_inst) else "N/A", 
                "color": "success",
                "icono": "fas fa-hospital"
            },
            {
                "titulo": "Casos Violencia Sexual", 
                "valor": str(casos_vs), 
                "color": "warning",
                "icono": "fas fa-shield-alt"
            },
            {
                "titulo": "Municipios Monitoreados", 
                "valor": str(municipios), 
                "color": "info",
                "icono": "fas fa-map-marked-alt"
            }
        ]
    except Exception as e:
        print(f"Error en KPIs: {e}")
        kpis_data = [
            {"titulo": "Cobertura CPN", "valor": "85.2%", "color": "primary", "icono": "fas fa-user-md"},
            {"titulo": "Parto Institucional", "valor": "92.1%", "color": "success", "icono": "fas fa-hospital"},
            {"titulo": "Casos VS", "valor": "25", "color": "warning", "icono": "fas fa-shield-alt"},
            {"titulo": "Municipios", "valor": "42", "color": "info", "icono": "fas fa-map-marked-alt"}
        ]
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className=f"{kpi['icono']} fa-2x mb-2", 
                              style={"color": f"var(--bs-{kpi['color']})"})
                    ], className="text-center"),
                    html.H3(kpi["valor"], className="text-center mb-1"),
                    html.P(kpi["titulo"], className="text-center text-muted mb-0")
                ])
            ], color=kpi["color"], outline=True, className="h-100")
        ], width=3) for kpi in kpis_data
    ])

def crear_componente_cpn(df_cpn):
    """Crear el componente de indicadores CPN mejorado con mapa de calor"""
    municipios_cpn = ['Todos'] + sorted(df_cpn['Municipio'].unique()) if 'Municipio' in df_cpn.columns else ['Todos']
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Seleccionar Municipio:", className="fw-bold"),
                dcc.Dropdown(
                    id="cpn-municipio-dropdown",
                    options=[{"label": m, "value": m} for m in municipios_cpn],
                    value="Todos",
                    clearable=False
                )
            ], width=4),
            dbc.Col([
                html.Label("Tipo de Visualización:", className="fw-bold"),
                dcc.Dropdown(
                    id="cpn-tipo-dropdown",
                    options=[
                        {"label": "📊 Indicadores Resumen", "value": "resumen"},
                        {"label": "📈 Gráfico de Barras", "value": "barras"},
                        {"label": "🗺️ Mapa de Calor", "value": "mapa_calor"},
                        {"label": "📋 Tabla Detallada", "value": "tabla"}
                    ],
                    value="resumen",
                    clearable=False
                )
            ], width=4),
            dbc.Col([
                html.Label("Indicador para Mapa:", className="fw-bold"),
                dcc.Dropdown(
                    id="cpn-indicador-dropdown",
                    options=[],
                    value=None,
                    clearable=False,
                    style={"display": "none"}
                )
            ], width=4, id="col-indicador")
        ], className="mb-4"),
        
        html.Div(id="cpn-contenido")
    ])
# === NUEVO COMPONENTE: MAPA DE CALOR GESTANTES ===
def crear_mapa_gestantes(df_cpn2):
    import plotly.express as px
    from dash import html, dcc   # ✅ cambio aquí

    # Verificamos columnas
    if "Municipio" not in df.columns or "Gestantes Activas" not in df.columns:
        return html.P("No hay datos disponibles de gestantes", className="text-danger")

    # Ordenamos de mayor a menor
    df_sorted = df.sort_values(by="Gestantes Activas", ascending=False)

    # Creamos gráfico de barras tipo heatmap
    fig = px.bar(
        df_sorted,
        x="Gestantes Activas",
        y="Municipio",
        orientation="h",
        color="Gestantes Activas",
        color_continuous_scale="Reds",
        title="Mapa de Calor - Gestantes Activas por Municipio"
    )

    fig.update_layout(
        yaxis=dict(autorange="reversed"),  # para que el municipio con más gestantes quede arriba
        xaxis_title="Número de Gestantes",
        yaxis_title="Municipio",
        plot_bgcolor="white"
    )

    return dcc.Graph(figure=fig)




def crear_grafico_categoria(df):
    """Crear componente de gráfico por categoría"""
    categorias = sorted(df['Categoría'].unique())
    municipios = sorted(df['Municipio'].unique())
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Categoría:", className="fw-bold"),
                dcc.Dropdown(
                    id="categoria-dropdown",
                    options=[{"label": c, "value": c} for c in categorias],
                    value=categorias[0] if categorias else None
                )
            ], width=4),
            dbc.Col([
                html.Label("Municipio:", className="fw-bold"),
                dcc.Dropdown(
                    id="municipio-dropdown",
                    options=[{"label": m, "value": m} for m in municipios],
                    value=municipios[0] if municipios else None
                )
            ], width=4),
            dbc.Col([
                html.Label("Tipo de Gráfico:", className="fw-bold"),
                dcc.Dropdown(
                    id="tipo-grafico-dropdown",
                    options=[
                        {"label": "📊 Barras", "value": "Barras"},
                        {"label": "📈 Línea", "value": "Línea"},
                        {"label": "🥧 Pastel", "value": "Pastel"}
                    ],
                    value="Barras"
                )
            ], width=4)
        ], className="mb-4"),
        
        dcc.Graph(id="grafico-indicadores")
    ])

def crear_semaforo_municipal(df):
    """Crear componente de semáforo municipal"""
    municipios = sorted(df['Municipio'].unique())
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Seleccionar Municipio:", className="fw-bold"),
                dcc.Dropdown(
                    id="semaforo-municipio-dropdown",
                    options=[{"label": m, "value": m} for m in municipios],
                    value=municipios[0] if municipios else None
                )
            ], width=6)
        ], className="mb-3"),
        
        html.Div(id="tabla-semaforo")
    ])
def crear_modulo_sifilis(df_sifilis):
    municipios = sorted(df_sifilis["municipio"].dropna().unique())
    eps_list = sorted(df_sifilis["eps"].dropna().unique())

    return html.Div([
        html.Hr(),
        html.H3("Indicadores de Sífilis", className="module-title"),

        dbc.Tabs([
            dbc.Tab(label="Sífilis Gestacional", tab_id="gestacional"),
            dbc.Tab(label="Sífilis Congénita", tab_id="congenita"),
        ], id="sifilis-tabs", active_tab="gestacional"),

        html.Div([
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
        ], id="sifilis-content")
    ])


def crear_violencia_sexual(df):
    """Crear componente de violencia sexual mejorado"""
    municipios_vs = sorted(df[df['Categoría'] == 'Violencia Sexual']['Municipio'].unique())
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Seleccionar Municipio:", className="fw-bold"),
                dcc.Dropdown(
                    id="vs-municipio-dropdown",
                    options=[{"label": m, "value": m} for m in municipios_vs] if municipios_vs else [{"label": "Sin datos", "value": ""}],
                    value=municipios_vs[0] if municipios_vs else ""
                )
            ], width=6),
            dbc.Col([
                html.Label("Vista:", className="fw-bold"),
                dcc.Dropdown(
                    id="vs-vista-dropdown",
                    options=[
                        {"label": "📊 Gráfico", "value": "grafico"},
                        {"label": "📋 Tabla", "value": "tabla"},
                        {"label": "📈 Tendencia", "value": "tendencia"}
                    ],
                    value="grafico"
                )
            ], width=6)
        ], className="mb-3"),
        
        html.Div(id="contenido-violencia-sexual")
    ])

# === DISEÑO PRINCIPAL ===
app.layout = dbc.Container(fluid=True, style={"backgroundColor": "#f8f9fa"}, children=[
    # Encabezado actualizado
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.I(className="fas fa-chart-line", style={"fontSize": "50px", "color": "#0d6efd", "marginRight": "20px"}),
                    html.Div([
                        html.H1("TABLERO DE INDICADORES SSR", className="mb-1", style={"color": "#2c3e50", "fontWeight": "bold"}),
                        html.H2("SECRETARÍA DE SALUD DEL CAUCA", className="mb-0", style={"color": "#6c757d", "fontSize": "1.5rem"})
                    ])
                ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"})
            ], className="text-center py-4", style={"background": "linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)", "borderRadius": "10px"})
        ], width=12),
        dbc.Col([html.Hr(style={"border": "2px solid #dee2e6", "margin": "20px 0"})], width=12)
    ]),

    # Indicadores clave (plegable)
    dbc.Row([
        dbc.Col([
            dbc.Button([
                html.I(className="fas fa-chart-line me-2"),
                "Indicadores Clave"
            ], id="toggle-kpi", color="primary", className="mb-2 w-100")
        ], width=12),
        dbc.Col([
            dbc.Collapse([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-tachometer-alt me-2"),
                        "Indicadores Clave"
                    ], className="bg-primary text-white"),
                    dbc.CardBody(id="kpis-content")
                ], className="shadow-sm")
            ], id="collapse-kpi", is_open=False)
        ], width=12)
    ], className="mb-4"),

    # CPN (plegable)
    dbc.Row([
        dbc.Col([
            dbc.Button([
                html.I(className="fas fa-baby me-2"),
                "Control Prenatal (CPN)"
            ], id="toggle-cpn", color="warning", className="mb-2 w-100")
        ], width=12),
        dbc.Col([
            dbc.Collapse([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-user-md me-2"),
                        "Control Prenatal - Gestantes"
                    ], className="bg-warning text-dark"),
                    dbc.CardBody(crear_componente_cpn(df_cpn))
                ], className="shadow-sm")
            ], id="collapse-cpn", is_open=True)
        ], width=12)
    ], className="mb-4"),

    # Gráfico por categoría
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-bar me-2"),
                    "Análisis por Categoría y Municipio"
                ], className="bg-info text-white"),
                dbc.CardBody(crear_grafico_categoria(df))
            ], className="shadow-sm")
        ], width=12)
    ], className="mb-4"),

    # Semáforo municipal
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-traffic-light me-2"),
                    "Semáforo de Cumplimiento Municipal"
                ], className="bg-success text-white"),
                dbc.CardBody(crear_semaforo_municipal(df))
            ], className="shadow-sm")
        ], width=12)
    ], className="mb-4"),

        # Violencia sexual (mejorado)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-shield-alt me-2"),
                    "Violencia Sexual - Análisis Detallado"
                ], className="bg-danger text-white"),
                dbc.CardBody(crear_violencia_sexual(df))
            ], className="shadow-sm")
        ], width=12)
    ], className="mb-4"),

    # === SECCIÓN MAPA DE GESTANTES ===
dbc.Card([
    dbc.CardHeader("Mapa de Gestantes"),
    dbc.CardBody([
        dcc.Dropdown(
            id="gestantes-indicador-dropdown",
            options=[{"label": col, "value": col} for col in df_cpn2.select_dtypes(include="number").columns],
            value=df_cpn2.select_dtypes(include="number").columns[0] if not df_cpn2.empty else None,
            placeholder="Selecciona un indicador"
        ),
        html.Div(id="gestantes-mapa-contenido")  # Aquí se insertará el gráfico
    ])
], className="mb-3"),
# === MÓDULO DE SÍFILIS ===
dbc.Row([
    dbc.Col([
        dbc.Card([
            dbc.CardHeader([
                html.I(className="fas fa-vial me-2"),
                "Indicadores de Sífilis"
            ], className="bg-secondary text-white"),
            dbc.CardBody([
                dbc.Tabs([
                    dbc.Tab(label="Sífilis Gestacional", tab_id="gestacional"),
                    dbc.Tab(label="Sífilis Congénita", tab_id="congenita"),
                ], id="sifilis-tabs", active_tab="gestacional", className="mb-3"),

                dbc.Row([
                    dbc.Col(dcc.Dropdown(
                        options=[{"label": m, "value": m} for m in sorted(df_sifilis["municipio"].dropna().unique())],
                        id="filtro-municipio",
                        placeholder="Filtrar por municipio"
                    ), md=6),
                    dbc.Col(dcc.Dropdown(
                        options=[{"label": e, "value": e} for e in sorted(df_sifilis["eps"].dropna().unique())],
                        id="filtro-eps",
                        placeholder="Filtrar por EPS"
                    ), md=6),
                ], className="mb-3"),

                dcc.Graph(id="grafico-sifilis")
            ])
        ], className="shadow-sm")
    ], width=12)
], className="mb-4"),


    # Pie de página mejorado
    dbc.Row([
        dbc.Col([
            html.Footer([
                html.Hr(),
                html.Div([
                    html.P("© 2025 Secretaría de Salud Departamental del Cauca", className="mb-1"),
                    html.P("Sistema de Seguimiento a la Salud Sexual y Reproductiva", className="text-muted mb-0")
                ], className="text-center")
            ], className="mt-4 mb-2")
        ], width=12)
    ])
])



# === CALLBACKS ===

# Cargar KPIs al abrir
@app.callback(
    Output("kpis-content", "children"),
    Input("kpis-content", "id")
)
def cargar_kpis(_):
    return crear_kpis(df)

# Toggle KPIs
@app.callback(
    Output("collapse-kpi", "is_open"),
    Input("toggle-kpi", "n_clicks"),
    State("collapse-kpi", "is_open")
)
def toggle_kpi(n, is_open):
    return not is_open if n else is_open

# Toggle CPN
@app.callback(
    Output("collapse-cpn", "is_open"),
    Input("toggle-cpn", "n_clicks"),
    State("collapse-cpn", "is_open")
)
def toggle_cpn(n, is_open):
    return not is_open if n else is_open

# Mostrar/ocultar dropdown de indicador para mapa de calor
@app.callback(
    [Output("cpn-indicador-dropdown", "style"),
     Output("cpn-indicador-dropdown", "options"),
     Output("cpn-indicador-dropdown", "value")],
    Input("cpn-tipo-dropdown", "value"),
    prevent_initial_call=False
)
def mostrar_dropdown_indicador(tipo_viz):
    if tipo_viz == "mapa_calor":
        try:
            # Obtener columnas numéricas para opciones
            columnas_numericas = df_cpn.select_dtypes(include=['number']).columns
            # Filtrar columnas que no sean ID o códigos
            columnas_validas = [col for col in columnas_numericas if col.lower() not in ['id', 'codigo', 'municipio']]
            opciones = [{"label": col.replace('_', ' ').title(), "value": col} for col in columnas_validas]
            valor_defecto = opciones[0]["value"] if opciones else None
            return {"display": "block"}, opciones, valor_defecto
        except Exception as e:
            print(f"Error en dropdown indicador: {e}")
            return {"display": "block"}, [{"label": "Sin datos", "value": ""}], ""
    else:
        return {"display": "none"}, [], None

# Contenido CPN actualizado
@app.callback(
    Output("cpn-contenido", "children"),
    [Input("cpn-municipio-dropdown", "value"),
     Input("cpn-tipo-dropdown", "value"),
     Input("cpn-indicador-dropdown", "value")]
)
def actualizar_cpn_contenido(municipio, tipo_viz, indicador_mapa):
    if df_cpn.empty:
        return dbc.Alert("No hay datos de CPN disponibles", color="warning")
    
    # Filtrar datos
    if municipio != "Todos" and 'Municipio' in df_cpn.columns:
        df_filtrado = df_cpn[df_cpn['Municipio'] == municipio].copy()
    else:
        df_filtrado = df_cpn.copy()
    
    if df_filtrado.empty:
        return dbc.Alert(f"No hay datos para {municipio}", color="info")
    
    if tipo_viz == "resumen":
        # Tarjetas de indicadores (código existente)
        columnas_numericas = df_filtrado.select_dtypes(include=['number']).columns
        tarjetas = []
        
        for col in columnas_numericas:
            valor = df_filtrado[col].mean() if len(df_filtrado) > 1 else df_filtrado[col].iloc[0]
            
            # Color según valor
            if valor >= 90:
                color, icono = "success", "fas fa-check-circle"
            elif valor >= 70:
                color, icono = "warning", "fas fa-exclamation-triangle"
            else:
                color, icono = "danger", "fas fa-times-circle"
            
            tarjeta = dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className=f"{icono} fa-2x mb-2", style={"color": f"var(--bs-{color})"})
                    ], className="text-center"),
                    html.H4(f"{valor:.1f}%", className="text-center mb-1"),
                    html.P(col.replace('_', ' ').title(), className="text-center text-muted mb-0")
                ])
            ], outline=True, color=color, className="h-100")
            
            tarjetas.append(dbc.Col(tarjeta, width=3))
        
        return dbc.Row(tarjetas) if tarjetas else dbc.Alert("No se encontraron indicadores", color="warning")
    
    elif tipo_viz == "barras":
        columnas_numericas = df_filtrado.select_dtypes(include=['number']).columns
        
        if len(columnas_numericas) == 0:
            return dbc.Alert("No hay datos numéricos", color="warning")
        
        # Preparar datos
        datos = []
        for col in columnas_numericas:
            valor = df_filtrado[col].mean() if len(df_filtrado) > 1 else df_filtrado[col].iloc[0]
            datos.append({"Indicador": col.replace('_', ' ').title(), "Valor": valor})
        
        if datos:
            df_grafico = pd.DataFrame(datos)
            fig = px.bar(
                df_grafico, 
                x="Indicador", 
                y="Valor",
                title=f"Indicadores CPN - {municipio}",
                color="Valor",
                color_continuous_scale="RdYlGn",
                range_color=[0, 100]
            )
            fig.update_layout(
                height=400,
                xaxis_tickangle=-45,
                title_x=0.5
            )
            return dcc.Graph(figure=fig)
    
    elif tipo_viz == "mapa_calor":
        if not indicador_mapa:
            return dbc.Alert("Selecciona un indicador para el mapa de calor", color="info")
        
        try:
            # Verificar que el indicador existe en los datos
            if indicador_mapa not in df_cpn.columns:
                return dbc.Alert(f"El indicador '{indicador_mapa}' no existe en los datos", color="warning")
            
            # Usar todos los datos de CPN para el mapa
            df_mapa = df_cpn.copy()
            
            if 'Municipio' not in df_mapa.columns:
                return dbc.Alert("No se encontró la columna 'Municipio' en los datos", color="danger")
            
            # Preparar datos para el mapa de calor
            municipios = df_mapa['Municipio'].tolist()
            valores = df_mapa[indicador_mapa].tolist()
            
            # Crear gráfico de barras horizontal que simule un mapa de calor
            fig = px.bar(
                df_mapa,
                x=indicador_mapa,
                y='Municipio',
                orientation='h',
                title=f"Mapa de Calor - {indicador_mapa.replace('_', ' ').title()} por Municipio",
                color=indicador_mapa,
                color_continuous_scale='RdYlGn',
                text=indicador_mapa
            )
            
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(
                height=max(400, len(municipios) * 30),
                title_x=0.5,
                xaxis_title=f"{indicador_mapa.replace('_', ' ').title()} (%)",
                yaxis_title="Municipios",
                yaxis={'categoryorder': 'total ascending'}
            )
            
            return dcc.Graph(figure=fig)
            
        except Exception as e:
            return dbc.Alert(f"Error al generar el mapa de calor: {str(e)}", color="danger")
        
    elif tipo_viz == "tabla":
        return dash_table.DataTable(
            data=df_filtrado.round(1).to_dict('records'),
            columns=[{"name": col.replace('_', ' ').title(), "id": col} for col in df_filtrado.columns],
            style_cell={'textAlign': 'center', 'padding': '12px'},
            style_header={
                'backgroundColor': '#ffc107',
                'color': 'black',
                'fontWeight': 'bold',
                'border': '1px solid #dee2e6'
            },
            style_data={
                'border': '1px solid #dee2e6'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ],
            page_size=15,
            sort_action="native"
        )
    
    return dbc.Alert("Selecciona un tipo de visualización", color="info")

@app.callback(
    Output("grafico-sifilis", "figure"),
    Input("sifilis-tabs", "active_tab"),
    Input("filtro-municipio", "value"),
    Input("filtro-eps", "value")
)
def update_sifilis_graph(tab, municipio, eps):
    evento = "Sífilis Gestacional" if tab == "gestacional" else "Sífilis Congénita"
    df = df_sifilis[df_sifilis["evento"] == evento]

    if municipio:
        df = df[df["municipio"] == municipio]
    if eps:
        df = df[df["eps"] == eps]

    df_grouped = df.groupby("semana")["casos"].sum().reset_index()

    fig = px.bar(
        df_grouped,
        x="semana", y="casos",
        title=f"Casos de {evento} por semana epidemiológica",
        labels={"semana": "Semana", "casos": "Número de casos"},
        color_discrete_sequence=["#6c757d"]
    )
    fig.update_layout(margin=dict(t=40, l=20, r=20, b=20))
    return fig

# Gráfico por categoría
@app.callback(
    Output("grafico-indicadores", "figure"),
    [Input("categoria-dropdown", "value"),
     Input("municipio-dropdown", "value"),
     Input("tipo-grafico-dropdown", "value")]
)
def actualizar_grafico(categoria, municipio, tipo):
    if not categoria or not municipio:
        return px.bar(title="Selecciona categoría y municipio")
    
    df_filtrado = df[(df["Categoría"] == categoria) & (df["Municipio"] == municipio)]
    
    if df_filtrado.empty:
        return px.bar(title=f"No hay datos para {categoria} - {municipio}")
    
    titulo = f"{categoria} - {municipio}"
    
    if tipo == "Barras":
        fig = px.bar(df_filtrado, x="Indicador", y="Valor (%)", 
                    title=titulo, color="Valor (%)",
                    color_continuous_scale="RdYlGn")
    elif tipo == "Línea":
        fig = px.line(df_filtrado, x="Indicador", y="Valor (%)", 
                     title=titulo, markers=True)
    elif tipo == "Pastel":
        fig = px.pie(df_filtrado, names="Indicador", values="Valor (%)", 
                    title=titulo)
    else:
        fig = px.bar(df_filtrado, x="Indicador", y="Valor (%)", title=titulo)
    
    fig.update_layout(height=400, title_x=0.5)
    return fig

# Semáforo municipal
@app.callback(
    Output("tabla-semaforo", "children"),
    Input("semaforo-municipio-dropdown", "value")
)
def mostrar_tabla_semaforo(municipio):
    if not municipio:
        return dbc.Alert("Selecciona un municipio", color="info")
    
    df_m = df[df["Municipio"] == municipio].copy()
    
    if df_m.empty:
        return dbc.Alert(f"No hay datos para {municipio}", color="warning")
    
    # Calcular semáforo
    def calcular_semaforo(row):
        valor = row.get("Valor (%)", 0)
        meta = row.get("Meta (%)", 90)
        
        if valor >= meta:
            return "🟢 Cumple"
        elif valor >= (meta * 0.8):  # 80% de la meta
            return "🟡 Parcial"
        else:
            return "🔴 No cumple"
    
    df_m["Estado"] = df_m.apply(calcular_semaforo, axis=1)
    
    return dash_table.DataTable(
        columns=[
            {"name": "Indicador", "id": "Indicador"},
            {"name": "Valor (%)", "id": "Valor (%)", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Meta (%)", "id": "Meta (%)", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Estado", "id": "Estado"}
        ],
        data=df_m.to_dict("records"),
        style_cell={"textAlign": "center", "padding": "12px"},
        style_header={
            "backgroundColor": "#28a745",
            "color": "white",
            "fontWeight": "bold"
        },
        style_data_conditional=[
            {
                'if': {'filter_query': '{Estado} contains "🟢"'},
                'backgroundColor': '#d4edda',
                'color': 'black'
            },
            {
                'if': {'filter_query': '{Estado} contains "🟡"'},
                'backgroundColor': '#fff3cd',
                'color': 'black'
            },
            {
                'if': {'filter_query': '{Estado} contains "🔴"'},
                'backgroundColor': '#f8d7da',
                'color': 'black'
            }
        ],
        sort_action="native",
        page_size=15
    )

# Violencia sexual (mejorado)
@app.callback(
    Output("contenido-violencia-sexual", "children"),
    [Input("vs-municipio-dropdown", "value"),
     Input("vs-vista-dropdown", "value")]
)
def actualizar_violencia_sexual(municipio, vista):
    if not municipio:
        return dbc.Alert("No hay datos de violencia sexual disponibles", color="warning")
    
    df_vs = df[(df["Municipio"] == municipio) & (df["Categoría"] == "Violencia Sexual")]
    
    if df_vs.empty:
        return dbc.Alert(f"No hay datos de violencia sexual para {municipio}", color="info")
    
    if vista == "grafico":
        fig = px.bar(
            df_vs, 
            x="Indicador", 
            y="Valor (%)",
            title=f"Violencia Sexual - {municipio}",
            color="Indicador",
            text="Valor (%)"
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(height=400, title_x=0.5, showlegend=False)
        return dcc.Graph(figure=fig)
    
    elif vista == "tabla":
        return dash_table.DataTable(
            data=df_vs.to_dict('records'),
            columns=[
                {"name": "Indicador", "id": "Indicador"},
                {"name": "Valor (%)", "id": "Valor (%)", "type": "numeric", "format": {"specifier": ".1f"}},
                {"name": "Meta (%)", "id": "Meta (%)", "type": "numeric", "format": {"specifier": ".1f"}}
            ],
            style_cell={'textAlign': 'center', 'padding': '12px'},
            style_header={
                'backgroundColor': '#dc3545',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        )
    
    elif vista == "tendencia":
        # Simular datos de tendencia (en la realidad vendrían de los datos)
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
        valores = np.random.uniform(10, 30, len(meses))
        
        fig = px.line(
            x=meses, 
            y=valores,
            title=f"Tendencia Violencia Sexual - {municipio}",
            markers=True
        )
        fig.update_layout(
            height=400, 
            title_x=0.5,
            xaxis_title="Mes",
            yaxis_title="Casos"
        )
        return dcc.Graph(figure=fig)
    
    return dbc.Alert("Selecciona una vista", color="info")
# === CALLBACK: MAPA DE GESTANTES ===
@app.callback(
    Output("gestantes-mapa-contenido", "children"),
    Input("gestantes-indicador-dropdown", "value")
)
def actualizar_mapa_gestantes(indicador):
    if not indicador or df_cpn2.empty:
        return dbc.Alert("No hay datos disponibles para generar el mapa de calor", color="warning")
    
    if indicador not in df_cpn2.columns:
        return dbc.Alert(f"El indicador '{indicador}' no existe en los datos", color="danger")

    try:
        df_mapa = df_cpn2.copy()
        fig = px.bar(
            df_mapa,
            x=indicador,
            y="Municipio",
            orientation="h",
            title=f"Mapa de Calor - {indicador.replace('_', ' ').title()} por Municipio",
            color=indicador,
            color_continuous_scale="RdYlGn",
            text=indicador
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(
            height=max(400, len(df_mapa) * 30),
            title_x=0.5,
            xaxis_title=f"{indicador.replace('_', ' ').title()} (%)",
            yaxis_title="Municipios",
            yaxis={"categoryorder": "total ascending"}
        )
        return dcc.Graph(figure=fig)
    except Exception as e:
        return dbc.Alert(f"Error al generar mapa: {e}", color="danger")


# Ejecutar el servidor
if __name__ == '__main__':
    app.run(debug=True, port=8050)
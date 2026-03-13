import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard RRHH - Vigencia Contratos", layout="wide")

# Título del Dashboard
st.title("📊 Dashboard de Vigencia de Contratos - Constructora Tafca SPA")
st.markdown("Plataforma de consulta online para Gerencia General.")

# Función para cargar datos de forma eficiente
@st.cache_data
def load_data():
    # Asegúrate de subir el archivo limpio al repositorio
    df = pd.read_csv("Base_Datos_Vigencia_Limpia.csv")
    return df

df = load_data()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros de Búsqueda")

# Filtro por Unidad (UN)
unidades = ["Todas"] + list(df['UN'].dropna().unique())
unidad_sel = st.sidebar.selectbox("Seleccione Centro de Costo (UN):", unidades)

# Filtro por Estado Actual
estados = ["Todos"] + list(df['ESTADO_ACTUAL'].dropna().unique())
estado_sel = st.sidebar.selectbox("Seleccione Estado del Contrato:", estados)

# Aplicar filtros
df_filtrado = df.copy()
if unidad_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['UN'] == unidad_sel]
if estado_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ESTADO_ACTUAL'] == estado_sel]

# --- KPIs (MÉTRICAS PRINCIPALES) ---
st.markdown("### Resumen General")
col1, col2, col3, col4 = st.columns(4)

total_trabajadores = len(df_filtrado)
vigentes = len(df_filtrado[df_filtrado['ESTADO_ACTUAL'] == 'VIGENTE'])
vencidos = len(df_filtrado[df_filtrado['ESTADO_ACTUAL'] == 'VENCIDO'])
renovacion = len(df_filtrado[df_filtrado['ESTADO_ACTUAL'] == 'EN PROCESO DE RENOVACIÓN'])

col1.metric("Total Trabajadores (Filtro)", total_trabajadores)
col2.metric("✅ Contratos Vigentes", vigentes)
col3.metric("⚠️ Contratos Vencidos", vencidos)
col4.metric("🔄 En Proceso de Renovación", renovacion)

st.markdown("---")

# --- GRÁFICOS ---
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown("#### Distribución por Estado de Contrato")
    fig_estado = px.pie(df_filtrado, names='ESTADO_ACTUAL', hole=0.4, 
                        color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_estado, use_container_width=True)

with col_graf2:
    st.markdown("#### Tipos de Contrato")
    tipo_ctto_counts = df_filtrado['TIPO_CONTRATO'].value_counts().reset_index()
    tipo_ctto_counts.columns = ['TIPO_CONTRATO', 'Cantidad']
    fig_tipo = px.bar(tipo_ctto_counts, x='TIPO_CONTRATO', y='Cantidad', text='Cantidad',
                      color='TIPO_CONTRATO', color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig_tipo, use_container_width=True)

# --- TABLA DE DATOS INTERACTIVA ---
st.markdown("### 📋 Detalle de Trabajadores")
st.markdown("Puedes buscar a un trabajador específico usando la barra de búsqueda en la tabla.")

# Seleccionamos las columnas más relevantes para mostrar a Gerencia
columnas_mostrar = ['RUT', 'NOMBRE', 'CARGO', 'UN', 'FECHA INGRESO', 'VIGENCIA CTTO', 'TIPO_CONTRATO', 'ESTADO_ACTUAL']
st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True)
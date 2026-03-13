import os
import re
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard RRHH - Vigencia Contratos", layout="wide")

# Función para cargar datos y limpiarlos automáticamente
@st.cache_data
def load_data():
    # Cargar el archivo con separador de punto y coma
    df = pd.read_csv("Base_Datos_Vigencia_RRHH.csv", sep=";")
    
    # --- Limpieza de datos en vivo ---
    # 1. Limpiar espacios vacíos y poner todo en mayúscula
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip().str.upper()
        df[col] = df[col].replace('NAN', np.nan)
        
    # 2. Crear columna TIPO_CONTRATO a partir de VIGENCIA CTTO
    def clasificar_contrato(val):
        if pd.isna(val): return "DESCONOCIDO"
        val = str(val)
        if 'INDEFINIDO' in val: return 'INDEFINIDO'
        elif 'ITEM' in val or 'HASTA' in val: return 'OBRA O FAENA'
        elif re.match(r'\d{4}-\d{2}-\d{2}', val): return 'PLAZO FIJO'
        else: return 'OTRO'
    df['TIPO_CONTRATO'] = df['VIGENCIA CTTO'].apply(clasificar_contrato)

    # 3. Simplificar SITUACIÓN en ESTADO_ACTUAL para los gráficos
    def simplificar_situacion(val):
        if pd.isna(val): return "SIN ESTADO"
        val = str(val)
        if 'VIGENTE' in val or 'INDEFINIDO' in val: return 'VIGENTE'
        elif 'FINIQUITADO' in val: return 'FINIQUITADO'
        elif 'VENCIDO' in val: return 'VENCIDO'
        elif 'RENOVACION' in val: return 'EN PROCESO DE RENOVACIÓN'
        else: return val
    df['ESTADO_ACTUAL'] = df['SITUACIÓN'].apply(simplificar_situacion)
    
    return df

# --- MANEJO INTELIGENTE DE ERRORES ---
# Si falla, mostrará en pantalla la lista real de archivos para que detectemos el problema
try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ Error Crítico: No se encontró el archivo 'Base_Datos_Vigencia_RRHH.csv'.")
    st.info(f"🔍 Archivos que el servidor está viendo actualmente en la carpeta principal: {os.listdir()}")
    st.stop()
except Exception as e:
    st.error(f"❌ Ocurrió un error al leer el archivo: {e}")
    st.stop()

# --- TÍTULO Y BARRA LATERAL (FILTROS) ---
st.title("📊 Dashboard de Vigencia de Contratos - Constructora Tafca SPA")
st.markdown("Plataforma de consulta online para Gerencia General.")

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

col1.metric("Total Trabajadores (Filtro)", len(df_filtrado))
col2.metric("✅ Contratos Vigentes", len(df_filtrado[df_filtrado['ESTADO_ACTUAL'] == 'VIGENTE']))
col3.metric("⚠️ Contratos Vencidos", len(df_filtrado[df_filtrado['ESTADO_ACTUAL'] == 'VENCIDO']))
col4.metric("🔄 En Proceso de Renovación", len(df_filtrado[df_filtrado['ESTADO_ACTUAL'] == 'EN PROCESO DE RENOVACIÓN']))

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
st.markdown("Puedes buscar a un trabajador específico usando la barra de búsqueda en la tabla (arriba a la derecha).")

# Seleccionamos las columnas más relevantes
columnas_mostrar = ['RUT', 'NOMBRE', 'CARGO', 'UN', 'FECHA INGRESO', 'VIGENCIA CTTO', 'TIPO_CONTRATO', 'ESTADO_ACTUAL']
st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True)

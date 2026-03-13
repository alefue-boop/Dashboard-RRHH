import os
import re
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard RRHH - Vigencia Contratos", layout="wide")

@st.cache_data
def load_data():
    # Leer el NUEVO archivo (asegúrate que en GitHub se llame exactamente así)
    df = pd.read_csv("Base_Datos_Vigencia_RRHH.csv.csv", sep=";")
    
    # 1. Limpiar espacios vacíos y poner todo en mayúscula
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype(str).str.strip().str.upper()
        df[col] = df[col].replace('NAN', np.nan)
        
    # 2. NUEVA LÓGICA: Crear TIPO_CONTRATO a partir de las nuevas columnas
    def clasificar_contrato(row):
        term = str(row.get('FECHA APROX TERMINO ITEM', '')).upper()
        renov = str(row.get('RENOVACIÓN 2', '')).upper()
        
        if term == 'INDEFINIDO' or renov == 'INDEFINIDO':
            return 'INDEFINIDO'
        elif 'HASTA TERMINO' in renov or 'ITEM' in renov:
            return 'OBRA O FAENA'
        elif re.match(r'\d{4}-\d{2}-\d{2}', term):
            return 'PLAZO FIJO'
        return 'OTRO'

    # 3. NUEVA LÓGICA: Crear ESTADO_ACTUAL
    def estado_actual(row):
        term = str(row.get('FECHA APROX TERMINO ITEM', '')).upper()
        if 'VENCIDO' in term:
            return 'VENCIDO'
        elif term != 'NAN' and term != '':
            return 'VIGENTE'
        return 'SIN ESTADO'

    # Aplicar las funciones a nivel de fila (axis=1)
    df['TIPO_CONTRATO'] = df.apply(clasificar_contrato, axis=1)
    df['ESTADO_ACTUAL'] = df.apply(estado_actual, axis=1)
    
    return df

# --- MANEJO INTELIGENTE DE ERRORES ---
try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ Error Crítico: No se encontró el archivo '.csv'.")
    st.info(f"🔍 Archivos que el servidor está viendo: {os.listdir()}")
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
col1, col2, col3, col4, col5 = st.columns(5)

total_trabajadores = len(df_filtrado)
vigentes = len(df_filtrado[df_filtrado['ESTADO_ACTUAL'] == 'VIGENTE'])
indefinidos = len(df_filtrado[df_filtrado['TIPO_CONTRATO'] == 'INDEFINIDO'])
vencidos = len(df_filtrado[df_filtrado['ESTADO_ACTUAL'] == 'VENCIDO'])
renovacion = len(df_filtrado[df_filtrado['ESTADO_ACTUAL'] == 'EN PROCESO DE RENOVACIÓN']) # Se mantiene en 0 si no hay en la bd

col1.metric("Total Trabajadores", total_trabajadores)
col2.metric("✅ Total Vigentes", vigentes)
col3.metric("♾️ Indefinidos", indefinidos)
col4.metric("⚠️ Vencidos", vencidos)
col5.metric("🔄 En Renovación", renovacion)

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
st.markdown("Busca a un trabajador específico usando la barra de búsqueda en la tabla (esquina superior derecha).")

# Actualizado a las columnas de este nuevo archivo
columnas_mostrar = ['RUT', 'NOMBRE', 'CARGO', 'UN', 'FECHA INGRESO', 'RENOVACIÓN 2', 'FECHA APROX TERMINO ITEM', 'TIPO_CONTRATO', 'ESTADO_ACTUAL']
st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True)

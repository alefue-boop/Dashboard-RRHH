import os
import re
import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. CONFIGURACIÓN GENERAL ---
st.set_page_config(page_title="Portal RRHH - Constructora Tafca SPA", layout="wide")

# --- 2. IDENTIDAD CORPORATIVA (CSS SEGURO) ---
st.markdown("""
    <style>
    h1, h2, h3, h4 {
        font-family: 'Times New Roman', Times, serif !important;
        color: #800020 !important; 
    }
    [data-testid="stMetricValue"] {
        font-family: 'Times New Roman', Times, serif !important;
        color: #228B22 !important;
    }
    [data-testid="stMetricLabel"] p {
        color: #7A7A7A !important;
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

colores_tafca = ['#800020', '#228B22', '#7A7A7A', '#4A0010', '#1E592F', '#A3A3A3']

# --- 3. SISTEMA DE SEGURIDAD (CONTRASEÑA) ---
def check_password():
    """Retorna True si el usuario ingresó la contraseña correcta."""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Por seguridad, borramos la contraseña de la memoria
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("### 🔒 Acceso Restringido")
        st.text_input("Ingrese la contraseña corporativa para acceder al Portal de RRHH:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("### 🔒 Acceso Restringido")
        st.text_input("Ingrese la contraseña corporativa para acceder al Portal de RRHH:", type="password", on_change=password_entered, key="password")
        st.error("❌ Contraseña incorrecta. Intente nuevamente.")
        return False
    else:
        return True

# Si la contraseña no es correcta, la app se detiene aquí y no muestra nada de lo que sigue
if not check_password():
    st.stop()


# --- 4. CONEXIÓN A GOOGLE SHEETS ---
# 👉 PEGA AQUÍ EL ENLACE DE TU GOOGLE SHEET (Mantenlo entre las comillas)
URL_GOOGLE_SHEET = "https://docs.google.com/spreadsheets/d/18cMneau8DxF6FCzMQmeY0EPoCrSXYt8-dSmbC1USa-s/edit?usp=sharing"

@st.cache_resource
def init_connection():
    creds_json = st.secrets["google_credentials"]
    creds_dict = json.loads(creds_json)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

try:
    client = init_connection()
except Exception as e:
    st.error("❌ Error de Conexión a Google Sheets. Revisa la configuración en 'Secrets'.")
    st.stop()


# --- 5. MENÚ DE NAVEGACIÓN ---
st.sidebar.title("🏢 Portal Tafca SPA")
st.sidebar.markdown("Seleccione el panel que desea visualizar:")
opcion = st.sidebar.radio("", ("Vigencia de Contratos", "Control de Multas"))
st.sidebar.markdown("---")

# ==========================================
# SECCIÓN 1: VIGENCIA DE CONTRATOS
# ==========================================
if opcion == "Vigencia de Contratos":
    st.title("📊 Dashboard de Vigencia de Contratos")
    st.markdown("Plataforma de consulta online para Gerencia General.")

    @st.cache_data(ttl=300)
    def load_data_contratos():
        sheet = client.open_by_url(URL_GOOGLE_SHEET).worksheet("Contratos")
        data = sheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.replace("", np.nan, inplace=True)
        
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace('NAN', np.nan)
            
        def clasificar_contrato(row):
            term = str(row.get('FECHA APROX TERMINO ITEM', '')).upper()
            renov = str(row.get('RENOVACIÓN 2', '')).upper()
            if term == 'INDEFINIDO' or renov == 'INDEFINIDO': return 'INDEFINIDO'
            elif 'HASTA TERMINO' in renov or 'ITEM' in renov: return 'OBRA O FAENA'
            elif re.match(r'\d{4}-\d{2}-\d{2}', term): return 'PLAZO FIJO'
            return 'OTRO'

        def estado_actual(row):
            term = str(row.get('FECHA APROX TERMINO ITEM', '')).upper()
            if 'VENCIDO' in term: return 'VENCIDO'
            elif term != 'NAN' and term != '': return 'VIGENTE'
            return 'SIN ESTADO'

        df['TIPO_CONTRATO'] = df.apply(clasificar_contrato, axis=1)
        df['ESTADO_ACTUAL'] = df.apply(estado_actual, axis=1)
        return df

    try:
        df_contratos = load_data_contratos()
    except Exception as e:
        st.error(f"❌ Error al leer la pestaña 'Contratos'. Detalles: {e}")
        st.stop()

    st.sidebar.header("Filtros de Contratos")
    unidades = ["Todas"] + list(df_contratos['UN'].dropna().unique())
    unidad_sel = st.sidebar.selectbox("Centro de Costo (UN):", unidades)

    estados = ["Todos"] + list(df_contratos['ESTADO_ACTUAL'].dropna().unique())
    estado_sel = st.sidebar.selectbox("Estado del Contrato:", estados)

    df_filtrado_ctto = df_contratos.copy()
    if unidad_sel != "Todas": df_filtrado_ctto = df_filtrado_ctto[df_filtrado_ctto['UN'] == unidad_sel]
    if estado_sel != "Todos": df_filtrado_ctto = df_filtrado_ctto[df_filtrado_ctto['ESTADO_ACTUAL'] == estado_sel]

    st.markdown("### Resumen General")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Total Trabajadores", len(df_filtrado_ctto))
    col2.metric("✅ Total Vigentes", len(df_filtrado_ctto[df_filtrado_ctto['ESTADO_ACTUAL'] == 'VIGENTE']))
    col3.metric("♾️ Indefinidos", len(df_filtrado_ctto[df_filtrado_ctto['TIPO_CONTRATO'] == 'INDEFINIDO']))
    col4.metric("⚠️ Vencidos", len(df_filtrado_ctto[df_filtrado_ctto['ESTADO_ACTUAL'] == 'VENCIDO']))
    col5.metric("🔄 En Renovación", len(df_filtrado_ctto[df_filtrado_ctto['ESTADO_ACTUAL'] == 'EN PROCESO DE RENOVACIÓN']))

    st.markdown("---")
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.markdown("#### Distribución por Estado")
        fig_estado = px.pie(df_filtrado_ctto, names='ESTADO_ACTUAL', hole=0.4, color_discrete_sequence=colores_tafca)
        fig_estado.update_layout(font_family="Times New Roman") 
        st.plotly_chart(fig_estado, use_container_width=True)

    with col_graf2:
        st.markdown("#### Tipos de Contrato")
        tipo_ctto_counts = df_filtrado_ctto['TIPO_CONTRATO'].value_counts().reset_index()
        tipo_ctto_counts.columns = ['TIPO_CONTRATO', 'Cantidad']
        fig_tipo = px.bar(tipo_ctto_counts, x='TIPO_CONTRATO', y='Cantidad', text='Cantidad', color='TIPO_CONTRATO', color_discrete_sequence=colores_tafca)
        fig_tipo.update_layout(font_family="Times New Roman", showlegend=False) 
        st.plotly_chart(fig_tipo, use_container_width=True)

    st.markdown("### 📋 Detalle de Trabajadores")
    columnas_mostrar = ['RUT', 'NOMBRE', 'CARGO', 'UN', 'FECHA INGRESO', 'RENOVACIÓN 2', 'FECHA APROX TERMINO ITEM', 'TIPO_CONTRATO', 'ESTADO_ACTUAL']
    st.dataframe(df_filtrado_ctto[columnas_mostrar], use_container_width=True, hide_index=True)


# ==========================================
# SECCIÓN 2: CONTROL DE MULTAS
# ==========================================
elif opcion == "Control de Multas":
    st.title("🚨 Dashboard de Control de Multas")
    st.markdown("Visualización e histórico de multas laborales y de prevención.")

    @st.cache_data(ttl=300)
    def load_data_multas():
        sheet = client.open_by_url(URL_GOOGLE_SHEET).worksheet("Multas")
        data = sheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        df.replace("", np.nan, inplace=True)
        
        def limpiar_monto(valor):
            if pd.isna(valor): return 0
            valor_limpio = str(valor).replace('.', '').strip()
            try:
                return int(valor_limpio)
            except:
                return 0
                
        df['Costo Monetario Num'] = df['Costo Monetario'].apply(limpiar_monto)
        
        for col in ['Estado Actual', 'Responsable', 'Región']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
                df[col] = df[col].replace('NAN', 'NO ESPECIFICADO')
                
        return df

    try:
        df_multas = load_data_multas()
    except Exception as e:
        st.error(f"❌ Error al leer la pestaña 'Multas'. Detalles: {e}")
        st.stop()

    st.sidebar.header("Filtros de Multas")
    anios = ["Todos"] + sorted(list(df_multas['Año'].dropna().unique()), reverse=True)
    anio_sel = st.sidebar.selectbox("Año de la Multa:", anios)

    resp = ["Todos"] + list(df_multas['Responsable'].dropna().unique())
    resp_sel = st.sidebar.selectbox("Área Responsable:", resp)

    df_filtrado_multas = df_multas.copy()
    if anio_sel != "Todos": df_filtrado_multas = df_filtrado_multas[df_filtrado_multas['Año'] == anio_sel]
    if resp_sel != "Todos": df_filtrado_multas = df_filtrado_multas[df_filtrado_multas['Responsable'] == resp_sel]

    st.markdown("### Resumen Financiero")
    col1, col2, col3 = st.columns(3)
    
    total_multas = len(df_filtrado_multas)
    costo_total = df_filtrado_multas['Costo Monetario Num'].sum()
    multas_pagadas = len(df_filtrado_multas[df_filtrado_multas['Estado Actual'] == 'PAGADA'])
    
    costo_formateado = f"${costo_total:,.0f}".replace(",", ".")

    col1.metric("Total de Infracciones", total_multas)
    col2.metric("💸 Costo Monetario Total", costo_formateado)
    col3.metric("✅ Multas Pagadas", multas_pagadas)

    st.markdown("---")
    
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.markdown("#### Estado Actual de las Multas")
        fig_estado_m = px.pie(df_filtrado_multas, names='Estado Actual', hole=0.4, color_discrete_sequence=colores_tafca)
        fig_estado_m.update_layout(font_family="Times New Roman") 
        st.plotly_chart(fig_estado_m, use_container_width=True)

    with col_graf2:
        st.markdown("#### Costo Total por Área Responsable")
        costo_por_area = df_filtrado_multas.groupby('Responsable')['Costo Monetario Num'].sum().reset_index()
        fig_area = px.bar(costo_por_area, x='Responsable', y='Costo Monetario Num', text='Costo Monetario Num', color='Responsable', color_discrete_sequence=colores_tafca)
        fig_area.update_traces(texttemplate='$%{text:,.0f}')
        fig_area.update_layout(font_family="Times New Roman", showlegend=False) 
        st.plotly_chart(fig_area, use_container_width=True)

    st.markdown("### 📋 Detalle de Infracciones")
    columnas_multas = [c for c in df_filtrado_multas.columns if c != 'Costo Monetario Num']
    st.dataframe(df_filtrado_multas[columnas_multas], use_container_width=True, hide_index=True)

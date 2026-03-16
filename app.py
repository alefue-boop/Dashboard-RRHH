import os
import re
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# --- 1. CONFIGURACIÓN GENERAL ---
st.set_page_config(page_title="Portal RRHH - Constructora Tafca SPA", layout="wide")

# --- 2. IDENTIDAD CORPORATIVA (CSS SEGURO) ---
# Aplicamos CSS SOLO a los títulos y métricas para NO romper las tablas de datos
st.markdown("""
    <style>
    /* Títulos en color Burdeo corporativo y letra Times New Roman */
    h1, h2, h3, h4 {
        font-family: 'Times New Roman', Times, serif !important;
        color: #800020 !important; 
    }
    
    /* Números de los KPIs en color Verde corporativo */
    [data-testid="stMetricValue"] {
        font-family: 'Times New Roman', Times, serif !important;
        color: #228B22 !important;
    }

    /* Textos debajo de los KPIs en color Plomo */
    [data-testid="stMetricLabel"] p {
        color: #7A7A7A !important;
        font-size: 16px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Paleta corporativa estricta para los gráficos (Burdeo, Verde, Plomo)
colores_tafca = ['#800020', '#228B22', '#7A7A7A', '#4A0010', '#1E592F', '#A3A3A3']

# --- 3. MENÚ DE NAVEGACIÓN ---
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

    @st.cache_data
    def load_data_contratos():
        df = pd.read_csv("Base_Datos_Vigencia_RRHH.csv.csv", sep=";")
        
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str

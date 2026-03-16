import os
import re
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# 1. CONFIGURACIÓN GENERAL (Aplica para toda la app)
st.set_page_config(page_title="Portal RRHH - Constructora Tafca SPA", layout="wide")

# 2. MENÚ DE NAVEGACIÓN
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135692.png", width=100) # Puedes poner el logo de Tafca aquí
st.sidebar.title("Menú Principal")
opcion = st.sidebar.radio("Seleccione el panel que desea visualizar:", 
                          ("Vigencia de Contratos", "Control de Multas"))

st.sidebar.markdown("---") # Línea divisoria

# ==========================================
# SECCIÓN 1: VIGENCIA DE CONTRATOS
# ==========================================
if opcion == "Vigencia de Contratos":
    st.title("📊 Dashboard de Vigencia de Contratos")
    st.markdown("Plataforma de consulta online para Gerencia General.")
    
    # --- Aquí pegas exactamente la función load_data() que ya teníamos ---
    @st.cache_data
    def load_data_contratos():
        df = pd.read_csv("Base_Datos_Vigencia_RRHH.csv.csv", sep=";")
        # ... (todo tu código de limpieza de contratos) ...
        return df

    try:
        df_contratos = load_data_contratos()
    except Exception as e:
        st.error(f"Error cargando contratos: {e}")
        st.stop()
        
    # --- Aquí pegas el resto de tu código de filtros, KPIs y gráficos de contratos ---
    # (Asegúrate de que los filtros de la barra lateral queden dentro de este bloque "if")


# ==========================================
# SECCIÓN 2: CONTROL DE MULTAS
# ==========================================
elif opcion == "Control de Multas":
    st.title("🚨 Dashboard de Control de Multas")
    st.markdown("Visualización de multas de vehículos, seguridad o inspecciones.")
    
    # --- Función para cargar los datos de las multas ---
    @st.cache_data
    def load_data_multas():
        # Asegúrate de subir este nuevo archivo a tu GitHub
        df = pd.read_csv("Base_Datos_Multas.csv", sep=";") 
        return df
        
    try:
        df_multas = load_data_multas()
    except Exception as e:
        st.error(f"Error cargando multas. ¿Subiste el archivo a GitHub? Detalles: {e}")
        st.stop()
        
    # --- Aquí puedes construir los KPIs y gráficos para las multas ---
    # Ejemplo básico:
    st.markdown("### Resumen de Multas")
    col1, col2 = st.columns(2)
    col1.metric("Total Multas Registradas", len(df_multas))
    # col2.metric("Monto Total ($)", df_multas['MONTO'].sum()) 
    
    st.dataframe(df_multas, use_container_width=True)

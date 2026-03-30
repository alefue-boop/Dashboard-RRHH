import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración
st.set_page_config(page_title="Dashboard RRHH", page_icon="📊", layout="wide")
st.title("📊 Dashboard Integrado de RRHH y Control de Gestión")

# =====================================================================
# PEGA AQUÍ TU ENLACE NORMAL DE GOOGLE DRIVE O GOOGLE SHEETS
# =====================================================================
URL_MULTAS = "https://docs.google.com/spreadsheets/d/18cMneau8DxF6FCzMQmeY0EPoCrSXYt8-dSmbC1USa-s/edit?usp=sharing"
URL_CONTRATOS = "https://docs.google.com/spreadsheets/d/18cMneau8DxF6FCzMQmeY0EPoCrSXYt8-dSmbC1USa-s/edit?usp=sharing"

def formato_clp(valor):
    if pd.isna(valor): return "$0"
    return f"${valor:,.0f}".replace(",", ".")

def arreglar_numeros(val):
    val = str(val).strip()
    if val in ['nan', 'None', '', 'NaN']: return None
    if ',' in val and '.' in val:
        if val.rfind(',') > val.rfind('.'): val = val.replace('.', '').replace(',', '.')
        else: val = val.replace(',', '')
    elif ',' in val: val = val.replace(',', '.')
    elif '.' in val:
        partes = val.split('.')
        if len(partes) == 2 and len(partes[1]) <= 2: pass 
        else: val = val.replace('.', '')
    try: return float(val)
    except: return None

@st.cache_data
def cargar_desde_drive(url, tipo="multas"):
    if "PEGA_AQUI" in url or url.strip() == "":
        return pd.DataFrame(), "⚠️ Falta que pegues el enlace de Google Drive en el código."
    
    # TRADUCTOR AUTOMÁTICO DE LINKS MEJORADO (Sheets y Drive normal)
    if "drive.google.com/file/d/" in url:
        file_id = url.split("/file/d/")[1].split("/")[0]
        url = f"https://drive.google.com/uc?id={file_id}&export=download"

import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración
st.set_page_config(page_title="Dashboard RRHH", page_icon="📊", layout="wide")
st.title("📊 Dashboard Integrado de RRHH y Control de Gestión")

# =====================================================================
# PEGA AQUÍ TU ENLACE NORMAL DE GOOGLE DRIVE O GOOGLE SHEETS
# =====================================================================
URL_MULTAS = "PEGA_AQUI_EL_ENLACE"
URL_CONTRATOS = "PEGA_AQUI_EL_ENLACE"

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
    elif "docs.google.com/spreadsheets/d/" in url and "/edit" in url:
        url = url.split("/edit")[0] + "/export?format=csv"
        
    try:
        # Primero intentamos con formato estándar (UTF-8)
        try:
            df = pd.read_csv(url, encoding="utf-8", on_bad_lines="skip")
        except UnicodeDecodeError:
            # Si falla, usamos formato latino (muy común con archivos)
            df = pd.read_csv(url, encoding="latin-1", on_bad_lines="skip")
        
        if len(df.columns) > 0 and str(df.columns[0]).strip().startswith('<'):
            return pd.DataFrame(), "🔒 **Tu archivo está Privado.** Cambia el acceso a 'Cualquier persona con el enlace' en Google Drive."
            
        df.columns = df.columns.str.strip()
        
        if tipo == "multas":
            for col in df.columns:
                if 'A' in col and 'o' in col and len(col) <= 4: 
                    df.rename(columns={col: 'Año'}, inplace=True)
            if 'Costo Monetario' in df.columns and 'Año' in df.columns:
                df = df.dropna(subset=['Costo Monetario', 'Año']).copy()
                df['Año'] = pd.to_numeric(df['Año'], errors='coerce').fillna(0).astype(int).astype(str)
                df['Estado Actual'] = df['Estado Actual'].astype(str).str.upper().str.strip().replace({'PAGADO': 'PAGADA', 'SIN EFECTO': 'DEJA SIN EFECTO'})
                df['Responsable'] = df['Responsable'].astype(str).str.upper().str.strip()

import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(page_title="Dashboard RRHH", page_icon="📊", layout="wide")
st.title("📊 Dashboard Integrado de RRHH y Control de Gestión")

# =====================================================================
# PEGA AQUÍ TUS ENLACES DE GOOGLE DRIVE (Publicados como CSV)
# =====================================================================
URL_MULTAS = "PEGA_AQUI_TU_ENLACE_CSV_DE_MULTAS"
URL_CONTRATOS = "PEGA_AQUI_TU_ENLACE_CSV_DE_CONTRATOS"


# ---------------- FUNCIONES DE LIMPIEZA ----------------
def formato_clp(valor):
    if pd.isna(valor): return "$0"
    return f"${valor:,.0f}".replace(",", ".")

def arreglar_numeros(val):
    val = str(val).strip()
    if val in ['nan', 'None', '', 'NaN']: return None
    if ',' in val and '.' in val:
        if val.rfind(',') > val.rfind('.'):
            val = val.replace('.', '').replace(',', '.')
        else:
            val = val.replace(',', '')
    elif ',' in val:
        val = val.replace(',', '.')
    elif '.' in val:
        partes = val.split('.')
        if len(partes) == 2 and len(partes[1]) <= 2: pass 
        else: val = val.replace('.', '')
    try: return float(val)
    except: return None

# ---------------- CARGA DE DATOS DESDE GOOGLE DRIVE ----------------
@st.cache_data
def cargar_multas_drive(url):
    if url == "PEGA_AQUI_TU_ENLACE_CSV_DE_MULTAS" or url == "":
        return pd.DataFrame() # Retorna vacío si no han puesto el link
    
    opciones_formato = [
        {"skiprows": 4, "sep": ",", "encoding": "utf-8"},
        {"skiprows": 4, "sep": ",", "encoding": "latin-1"},
        {"skiprows": 0, "sep": ",", "encoding": "utf-8"}
    ]
    
    for config in opciones_formato:
        try:
            # Pandas lee directamente el enlace de Google Drive
            df = pd.read_csv(url, skiprows=config["skiprows"], sep=config["sep"], encoding=config["encoding"], on_bad_lines="skip")
            df.columns = df.columns.str.strip()
            
            for col in df.columns:
                if 'A' in col and 'o' in col and len(col) <= 4: df.rename(columns={col: 'Año'}, inplace=True)
                
            if 'Costo Monetario' in df.columns and 'Año' in df.columns:
                df = df.dropna(subset=['Costo Monetario', 'Año']).copy()
                df['Año'] = pd.to_numeric(df['Año'], errors='coerce').fillna(0).astype(int).astype(str)
                df['Estado Actual'] = df['Estado Actual'].astype(str).str.upper().str.strip().replace({'PAGADO': 'PAGADA', 'SIN EFECTO': 'DEJA SIN EFECTO'})
                df['Responsable'] = df['Responsable'].astype(str).str.upper().str.strip()
                df['Costo Monetario Real'] = df['Costo Monetario'].apply(arreglar_numeros)
                df = df.dropna(subset=['Costo Monetario Real'])
                df['Costo en Millones (MM$)'] = df['Costo Monetario Real'] / 1000000
                return df
        except: continue
    return pd.DataFrame()

@st.cache_data
def cargar_contratos_drive(url):
    if url == "PEGA_AQUI_TU_ENLACE_CSV_DE_CONTRATOS" or url == "":
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(url, encoding="utf-8", on_bad_lines="skip")
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# Cargar ambas bases directamente desde la nube
df_multas = cargar_multas_drive(URL_MULTAS)
df_contratos = cargar_contratos_drive(URL_CONTRATOS)

# ---------------- CREACIÓN DE PESTAÑAS (TABS) ----------------
tab1, tab2 = st.tabs(["📑 Control de Multas (Insp. del Trabajo)", "📄 Control de Vigencia de Contratos"])

# =====================================================================
# PESTAÑA 1: MULTAS
# =====================================================================
with tab1:
    if df_multas.empty:
        st.info("⚠️ Ingresa el enlace correcto de Google Drive en la variable URL_MULTAS dentro del código.")
    else:
        st.sidebar.header("Filtros: Multas")
        anio_filtro = st.sidebar.multiselect("Seleccionar Año:", options=sorted(df_multas['Año'].unique()), default=sorted(df_multas['Año'].unique()), key="filtro_anio")
        resp_filtro = st.sidebar.multiselect("Responsable:", options=df_multas['Responsable'].dropna().unique(), default=df_multas['Responsable'].dropna().unique(), key="filtro_resp")
        
        df_filtrado = df_multas[(df_multas['Año'].isin(anio_filtro)) & (df_multas['Responsable'].isin(resp_filtro))]

        # KPIs Multas
        col1, col2, col3 = st.columns(3)
        col1.metric("Gasto Total (CLP)", formato_clp(df_filtrado['Costo Monetario Real'].sum()))
        col2.metric("Cantidad de Infracciones", len(df_filtrado))
        col3.metric("Costo Promedio", formato_clp(df_filtrado['Costo Monetario Real'].mean() if len(df_filtrado) > 0 else 0))

        st.divider()

        # Gráficos Multas
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            gasto_anio = df_filtrado.groupby('Año')['Costo en Millones (MM$)'].sum().reset_index()
            st.plotly_chart(px.bar(gasto_anio, x='Año', y='Costo en Millones (MM$)', title="Gasto Total por Año (Millones de Pesos)", text_auto='.1f'), use_container_width=True)
        with col_g2:
            gasto_resp = df_filtrado.groupby('Responsable')['Costo en Millones (MM$)'].sum().reset_index()
            st.plotly_chart(px.pie(gasto_resp, values='Costo en Millones (MM$)', names='Responsable', title="Distribución por Departamento", hole=0.4), use_container_width=True)

        st.subheader("📑 Detalle Histórico de Multas")
        cols_multas = [col for col in ['Año', 'Región', 'Ciudad', 'Resolución', 'Tipo de Infracción', 'Estado Actual', 'Responsable', 'Costo Monetario Real'] if col in df_filtrado.columns]
        df_tabla = df_filtrado[cols_multas].copy()
        if 'Costo Monetario Real' in df_tabla.columns: df_tabla['Costo Monetario Real'] = df_tabla['Costo Monetario Real'].apply(formato_clp)
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)

# =====================================================================
# PESTAÑA 2: CONTRATOS
# =====================================================================
with tab2:
    st.header("📄 Visor de Vigencia de Contratos")
    
    if df_contratos.empty:
        st.info("ℹ️ Ingresa el enlace correcto de Google Drive en la variable URL_CONTRATOS dentro del código.")
    else:
        st.sidebar.divider()
        st.sidebar.header("Filtros: Contratos")

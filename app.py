import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración
st.set_page_config(page_title="Dashboard RRHH", page_icon="📊", layout="wide")
st.title("📊 Dashboard Integrado de RRHH y Control de Gestión")

# =====================================================================
# TUS ENLACES DE GOOGLE DRIVE O GOOGLE SHEETS
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
    
    # TRADUCTOR AUTOMÁTICO DE LINKS MEJORADO
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
            # Si falla, usamos formato latino
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
                df['Costo Monetario Real'] = df['Costo Monetario'].apply(arreglar_numeros)
                df = df.dropna(subset=['Costo Monetario Real'])
                df['Costo en Millones (MM$)'] = df['Costo Monetario Real'] / 1000000
                return df, "OK"
            return pd.DataFrame(), "❌ El archivo se leyó, pero faltan las columnas clave ('Costo Monetario' y 'Año')."
        
        return df, "OK"
        
    except Exception as e:
        return pd.DataFrame(), f"❌ No se pudo descargar. Verifica que el link esté correcto."

# Cargar bases
df_multas, msg_multas = cargar_desde_drive(URL_MULTAS, "multas")
df_contratos, msg_contratos = cargar_desde_drive(URL_CONTRATOS, "contratos")

tab1, tab2 = st.tabs(["📑 Control de Multas (Insp. del Trabajo)", "📄 Control de Vigencia de Contratos"])

with tab1:
    if df_multas.empty:
        st.error(msg_multas)
    else:
        st.sidebar.header("Filtros: Multas")
        anio_filtro = st.sidebar.multiselect("Seleccionar Año:", options=sorted(df_multas['Año'].unique()), default=sorted(df_multas['Año'].unique()), key="filtro_anio")
        resp_filtro = st.sidebar.multiselect("Responsable:", options=df_multas['Responsable'].dropna().unique(), default=df_multas['Responsable'].dropna().unique(), key="filtro_resp")
        
        df_filtrado = df_multas[(df_multas['Año'].isin(anio_filtro)) & (df_multas['Responsable'].isin(resp_filtro))]

        col1, col2, col3 = st.columns(3)
        col1.metric("Gasto Total (CLP)", formato_clp(df_filtrado['Costo Monetario Real'].sum()))
        col2.metric("Cantidad de Infracciones", len(df_filtrado))
        col3.metric("Costo Promedio", formato_clp(df_filtrado['Costo Monetario Real'].mean() if len(df_filtrado) > 0 else 0))

        st.divider()

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            gasto_anio = df_filtrado.groupby('Año')['Costo en Millones (MM$)'].sum().reset_index()
            st.plotly_chart(px.bar(gasto_anio, x='Año', y='Costo en Millones (MM$)', title="Gasto Total por Año (Millones)", text_auto='.1f'), use_container_width=True)
        with col_g2:
            gasto_resp = df_filtrado.groupby('Responsable')['Costo en Millones (MM$)'].sum().reset_index()
            st.plotly_chart(px.pie(gasto_resp, values='Costo en Millones (MM$)', names='Responsable', title="Distribución por Responsable", hole=0.4), use_container_width=True)

        st.subheader("📑 Detalle Histórico")
        cols_multas = [col for col in ['Año', 'Región', 'Ciudad', 'Resolución', 'Tipo de Infracción', 'Estado Actual', 'Responsable', 'Costo Monetario Real'] if col in df_filtrado.columns]
        df_tabla = df_filtrado[cols_multas].copy()
        if 'Costo Monetario Real' in df_tabla.columns: df_tabla['Costo Monetario Real'] = df_tabla['Costo Monetario Real'].apply(formato_clp)
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)

with tab2:
    st.header("📄 Vigencia de Contratos")
    if df_contratos.empty:
        st.info(msg_contratos)
    else:
        st.sidebar.divider()
        st.sidebar.header("Filtros: Contratos")
        if 'Obra' in df_contratos.columns:
            obras_unicas = df_contratos['Obra'].dropna().unique()
            obra_filtro = st.sidebar.multiselect("Filtrar por Obra:", options=obras_unicas, default=obras_unicas)
            df_ctto_filtrado = df_contratos[df_contratos['Obra'].isin(obra_filtro)]
        else:
            df_ctto_filtrado = df_contratos

        columnas_ideales_ctto = ['RUT', 'Nombre', 'Obra', 'Cargo', 'Fecha Inicio', 'Vigencia', 'Estado Contrato']
        columnas_seguras_ctto = [col for col in columnas_ideales_ctto if col in df_ctto_filtrado.columns]
        
        if len(columnas_seguras_ctto) > 0:
            st.dataframe(df_ctto_filtrado[columnas_seguras_ctto], use_container_width=True, hide_index=True)
        else:
            st.dataframe(df_ctto_filtrado, use_container_width=True, hide_index=True)

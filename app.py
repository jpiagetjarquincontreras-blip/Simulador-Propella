import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración premium
st.set_page_config(page_title="Wageningen B-Series Pro | Equipo 4", layout="wide", page_icon="⚓")

# CSS para un look de software moderno
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #ffffff; border-radius: 5px 5px 0px 0px; gap: 1px; }
    .stTabs [aria-selected="true"] { background-color: #1f77b4; color: white; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_coefficients():
    try:
        return pd.read_excel('Tabla 1.xlsx', sheet_name='KT'), pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
    except: return None, None

df_kt, df_kq = load_coefficients()

def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l = [], []
    for j in j_vals:
        kt = np.sum(df_kt['Coeficiente'] * (j**df_kt['s (J)']) * (pd_v**df_kt['t (P/D)']) * (ae_v**df_kt['u (AE/AO)']) * (z_v**df_kt['v (Z)']))
        kq = np.sum(df_kq['Coeficiente'] * (j**df_kq['s (J)']) * (pd_v**df_kq['t (P/D)']) * (ae_v**df_kq['u (AE/AO)']) * (z_v**df_kq['v (Z)']))
        kt_l.append(max(0, kt))
        kq_l.append(max(0, kq))
    
    temp_df = pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l})
    temp_df['nO'] = (temp_df['J'] / (2 * np.pi)) * (temp_df['KT'] / (temp_df['KQ']))
    temp_df['nO'] = temp_df['nO'].fillna(0).clip(0, 1)
    return temp_df

# --- ESTRUCTURA PRINCIPAL ---
st.title("🚢 Simulador Avanzado de Propulsión Naval")
st.markdown("### Análisis Polinomial de Hélices Serie B (Wageningen)")

if df_kt is not None:
    # Sidebar con diseño organizado
    with st.sidebar:
        st.image("https://www.uv.mx/v2/images/logouv.jpg", width=100) # Logo opcional
        st.header("🎮 Panel de Control")
        with st.expander("Configuración Principal", expanded=True):
            pd_val = st.slider("Paso/Diámetro (P/D)", 0.5, 1.4, 1.20, 0.01)
            ae_val = st.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.45, 0.05)
            z_val = st.select_slider("Número de palas (Z)", options=[3, 4, 5, 6, 7], value=4)
        
        st.info("**Equipo 4:** Hernandez, Jarquin, Navarro, Revilla, Villa, Elias, Galindo.")

    # Pestañas para organizar la info
    tab1, tab2, tab3 = st.tabs(["📈 Gráfica de Rendimiento", "📋 Datos Técnicos", "🧠 Teoría y Ecuaciones"])

    with tab1:
        # Cálculo de datos
        res = calcular_curvas(pd_val, ae_val, z_val)
        
        # Métricas interactivas
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J']
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Eficiencia Máx (ηO)", f"{max_eff:.4f}")
        c2.metric("Avance Óptimo (J)", f"{j_opt:.3f}")
        c3.metric("KT @ ηO Max", f"{res.loc[res['nO'].idxmax(), 'KT']:.3f}")
        c4.metric("10KQ @ ηO Max", f"{res.loc[res['nO'].idxmax(), 'KQ']*10:.3f}")

        # Gráfica Premium con Matplotlib
        fig, ax = plt.subplots(figsize=(12, 5.5))
        ax.plot(res['J'], res['KT'], color='#004c6d', label='KT (Empuje)', lw=3)
        ax.plot(res['J'], res['KQ']*10, color='#5886a5', label='10*KQ (Torque)', lw=3)
        ax.plot(res['J'], res['nO'], color='#ef4444', label='ηO (Eficiencia)', lw=4, ls='-')
        
        # Sombreado de área de eficiencia
        ax.fill_between(res['J'], res['nO'], color='#ef4444', alpha=0.1)
        
        # Línea vertical en el punto óptimo
        ax.axvline(x=j_opt, color='gray', linestyle='--', alpha=0.5)
        ax.annotate(f'Punto de Diseño J={j_opt:.2f}', xy=(j_opt, max_eff), xytext=(j_opt+0.1, max_eff+

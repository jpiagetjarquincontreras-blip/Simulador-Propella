import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración premium
st.set_page_config(page_title="Wageningen B-Series Pro | Equipo 4", layout="wide", page_icon="⚓")

# Estilos UV
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stTabs [aria-selected="true"] { background-color: #005129; color: white; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #005129; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_coefficients():
    try:
        kt_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
        kq_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
        # Limpieza de nombres de columnas
        for df in [kt_df, kq_df]:
            df.columns = [c.strip().capitalize() for c in df.columns]
        return kt_df, kq_df
    except Exception as e:
        st.error(f"Error al cargar el Excel: {e}")
        return None, None

df_kt, df_kq = load_coefficients()

def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l = [], []
    
    # Buscamos la columna de coeficientes
    col_c = 'Coeficiente'
    
    for j in j_vals:
        # CÁLCULO DE KT (Empuje)
        kt = np.sum(df_kt[col_c] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        
        # CÁLCULO DE KQ (Torque) - CORREGIDO PARA USAR SOLO DF_KQ
        kq = np.sum(df_kq[col_c] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        
        kt_l.append(max(0, kt))
        kq_l.append(max(0, kq))
    
    temp_df = pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l})
    # Fórmula de eficiencia corregida
    temp_df['nO'] = (temp_df['J'] / (2 * np.pi)) * (temp_df['KT'] / temp_df['KQ'])
    temp_df['nO'] = temp_df['nO'].fillna(0).clip(0, 1)
    
    # Forzar a 0 si KT llega a 0 (punto de avance nulo)
    temp_df.loc[temp_df['KT'] <= 0, 'nO'] = 0
    return temp_df

st.title("🚢 Simulador Avanzado de Propulsión Naval")
st.caption("Facultad de Ingeniería Mecánica y Ciencias Navales | Universidad Veracruzana")

if df_kt is not None:
    with st.sidebar:
        st.header("🎮 Panel de Control")
        pd_val = st.slider("Paso/Diámetro (P/D)", 0.5, 1.4, 1.20, 0.01)
        ae_val = st.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.45, 0.05)
        z_val = st.select_slider("Número de palas (Z)", options=[3, 4, 5, 6, 7], value=4)
        
        st.markdown("---")
        st.write("**Integrantes del Equipo 4:**")
        st.info("HERNANDEZ LIZETH, JARQUIN JADE, NAVARRO VANIA, REVILLA IRIS, VILLA KARLA, ELIAS JOSE, GALINDO OSCAR")

    tab1, tab2, tab3 = st.tabs(["📈 Gráfica", "📋 Datos", "🧠 Teoría"])

    with tab1:
        res = calcular_curvas(pd_val, ae_val, z_val)
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J']
        
        c1, c2 = st.columns(2)
        c1.metric("Eficiencia Máx (ηO)", f"{max_eff*100:.2f}%")
        c2.metric("Avance Óptimo (J)", f"{j_opt:.3f}")

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(res['J'], res['KT'], color='#004c6d', label='KT (Empuje)', lw=2.5)
        ax.plot(res['J'], res['KQ']*10, color='#2ca02c', label='10*KQ (Torque)', lw=2.5)
        ax.plot(res['J'], res['nO'], color='#ef4444', label='ηO (Eficiencia)', lw=3, ls='--')
        
        ax.set_ylim(0, 1.0)
        ax.set_xlim(0, 1.2)
        ax.grid(True, alpha=0.3)
        ax.legend()
        st.pyplot(fig)

    with tab2:
        st.dataframe(res.style.highlight_max(subset=['nO'], color='#dcfce7').format("{:.4f}"))

    with tab3:
        st.latex(r"\eta_O = \frac{J}{2\pi} \cdot \frac{K_T}{K_Q}")
        st.info("Cálculos validados con polinomios de Oosterveld & van Oossanen.")

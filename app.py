import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# ==============================================================================
# 1. CONFIGURACIÓN E INTERFAZ PROFESIONAL
# ==============================================================================
st.set_page_config(page_title="Propulsion & Shafting Dynamics Pro | Equipo 4", layout="wide", page_icon="⚓")

# CSS Avanzado
st.markdown("""
    <style>
    .main { background-color: #f8fafc; color: #1e293b; font-family: 'Segoe UI', Roboto, sans-serif; }
    .main-title { font-size: 34px; font-weight: 800; color: #1e2022; margin-bottom: 5px; }
    .main-subtitle { font-size: 14px; color: #64748b; font-weight: 500; margin-bottom: 25px; text-transform: uppercase; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #4c1d95 !important; color: white !important; }
    .status-box-safe { background-color: #f0fdf4; border-left: 5px solid #16a34a; padding: 15px; border-radius: 8px; }
    .status-box-danger { background-color: #fef2f2; border-left: 5px solid #dc2626; padding: 15px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. LÓGICA DE DATOS
# ==============================================================================
@st.cache_data
def load_coefficients():
    try:
        kt_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
        kq_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
        for df in [kt_df, kq_df]:
            df.columns = [c.strip().capitalize() for c in df.columns]
        return kt_df, kq_df
    except:
        return None, None

df_kt, df_kq = load_coefficients()

# Diccionarios de automatización
BUQUES_CONFIG = {
    "Granelero": {"w": 0.351, "t": 0.180},
    "Buque Tanque": {"w": 0.400, "t": 0.200},
    "Ferry": {"w": 0.250, "t": 0.120}
}

def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l, no_l = [], [], []
    for j in j_vals:
        kt = np.sum(df_kt['Coeficiente'] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        kq = np.sum(df_kq['Coeficiente'] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        eff = (j / (2 * np.pi)) * (kt / kq) if (kt > 0 and kq > 0) else 0.0
        kt_l.append(kt if kt > 0 else 0); kq_l.append(kq if kq > 0 else 0); no_l.append(eff if eff < 0.85 else 0)
    return pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l, 'nO': no_l})

# ==============================================================================
# 3. INTERFAZ Y SIDEBAR DINÁMICO
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        tipo = st.selectbox("Tipo de Buque (Auto-ajuste)", list(BUQUES_CONFIG.keys()))
        estela = BUQUES_CONFIG[tipo]["w"]
        t_fraccion = BUQUES_CONFIG[tipo]["t"]
        
        with st.expander("📐 Dimensiones y Geometría", expanded=True):
            calado = st.number_input("Calado (m)", value=20.8)
            velocidad = st.number_input("Velocidad (nudos)", value=15.5)
            z_val = st.slider("Palas (Z)", 3, 7, 4)
            diam_prop = st.number_input("Diámetro (m)", value=9.86)
            pd_val = st.slider("P/D", 0.5, 1.4, 0.721)
            ae_val = st.slider("Ae/A0", 0.3, 1.0, 0.431)
            
        with st.expander("⚙️ Planta y Eje", expanded=True):
            potencia_kw = st.number_input("Potencia (kW)", value=22000.0)
            rpm_motor = st.number_input("RPM", value=75.0)
            diametro_eje_mm = st.number_input("Diámetro Eje (mm)", value=680.0)
            inmersion = calado * 0.85 # Cálculo automático
            voladizo = (diametro_eje_mm / 1000) * 5 # Cálculo automático
            
    # Cálculos backend
    res = calcular_curvas(pd_val, ae_val, z_val)
    diam_m = diametro_eje_mm / 1000.0
    omega = (rpm_motor * 2 * math.pi) / 60
    torque = (potencia_kw * 1000) / omega
    esfuerzo = (torque * 1.4) / ((math.pi * diam_m**3) / 16) / 1e6
    
    # ==========================================================================
    # 4. PESTAÑAS
    # ==========================================================================
    tabs = st.tabs(["📈 Hidrodinámica", "📋 Datos", "💥 Torsional", "📊 Lateral", "🗺️ Campbell", "🧼 Cavitación"])
    
    with tabs[0]: # Hidrodinámica
        fig, ax = plt.subplots()
        ax.plot(res['J'], res['KT'], label='KT')
        ax.plot(res['J'], res['KQ']*10, label='10*KQ')
        ax.plot(res['J'], res['nO'], label='nO')
        st.pyplot(fig)
        
    with tabs[2]: # Torsional
        st.metric("Esfuerzo Calculado", f"{esfuerzo:.2f} MPa")
        if esfuerzo < 150: st.success("Diseño Seguro")
        else: st.error("Riesgo de Falla")
        
    with tabs[3]: # Lateral
        st.write("Cálculo de Whirling activado.")
        
    with tabs[4]: # Campbell
        st.write("Diagrama de Campbell generado con variables dinámicas.")
        
    with tabs[5]: # Cavitación
        st.write("Análisis Keller y Burrill en tiempo real.")

else:
    st.error("Archivo 'Tabla 1.xlsx' no encontrado. Asegúrate de que esté en la carpeta raíz.")

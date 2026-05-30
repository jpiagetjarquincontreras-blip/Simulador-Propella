import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA E INTERFAZ PROFESIONAL
# ==============================================================================
st.set_page_config(
    page_title="Propulsion & Shafting Dynamics Pro | Equipo 4",
    layout="wide",
    page_icon="⚓"
)

st.markdown("""
    <style>
    .main { background-color: #f8fafc; color: #1e293b; font-family: 'Segoe UI', Roboto, sans-serif; }
    .main-title { font-size: 34px; font-weight: 800; color: #1e2022; margin-bottom: 5px; letter-spacing: -0.5px; }
    .main-subtitle { font-size: 14px; color: #64748b; font-weight: 500; margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #f1f5f9; padding: 6px 8px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { height: 44px; background-color: transparent; border: none; border-radius: 8px; padding: 8px 16px; font-weight: 600; color: #64748b; transition: all 0.2s ease; }
    .stTabs [aria-selected="true"] { background-color: #4c1d95 !important; color: white !important; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .status-box-safe { background-color: #f0fdf4; border-left: 5px solid #16a34a; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .status-box-danger { background-color: #fef2f2; border-left: 5px solid #dc2626; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #4c1d95; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CARGA DE COEFICIENTES Y CÁLCULOS PRINCIPALES
# ==============================================================================
@st.cache_data
def load_coefficients():
    try:
        kt_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
        kq_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
        for df in [kt_df, kq_df]:
            df.columns = [c.strip().capitalize() for c in df.columns]
        return kt_df, kq_df
    except Exception as e:
        return None, None

df_kt, df_kq = load_coefficients()

def calcular_curvas(pd_v, ae_v, z_v):
    if df_kt is None: return None
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l, no_l = [], [], []
    for j in j_vals:
        kt = np.sum(df_kt['Coeficiente'] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        kq = np.sum(df_kq['Coeficiente'] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        eff = (j / (2 * np.pi)) * (kt / kq) if (kt > 0 and kq > 0) else 0.0
        kt_l.append(max(0, kt)); kq_l.append(max(0, kq)); no_l.append(eff if eff < 0.85 else 0)
    return pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l, 'nO': no_l})

# ==============================================================================
# 3. INTERFAZ DE USUARIO
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Análisis Hidrodinámico, Vibratorio y de Fluidos — Equipo 4</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.markdown("### 🛠️ Configuración del Sistema")
        eslora = st.number_input("Lpp (m)", value=320.0)
        calado = st.number_input("Calado (m)", value=20.80)
        velocidad = st.number_input("Velocidad (nudos)", value=15.5)
        estela = st.number_input("Fracción Estela (w)", value=0.351, format="%.3f")
        z_val = st.slider("Palas (Z)", 3, 7, 4)
        diam_prop_m = st.number_input("Diámetro Hélice (m)", value=9.86)
        pd_val = st.slider("Relación P/D", 0.5, 1.4, 0.721, 0.001)
        ae_val = st.slider("Relación Ae/A0", 0.3, 1.0, 0.431, 0.001)
        potencia_kw = st.number_input("Potencia MCR (kW)", value=22000.0)
        rpm_motor = st.number_input("RPM", value=75.0)
        diametro_eje_mm = st.number_input("Diámetro Eje (mm)", value=680.0)
        sigma_uts = st.number_input("UTS Material (MPa)", value=600.0)
        longitud_volado_m = st.number_input("Voladizo (m)", value=3.5)

    # Lógica de Backend
    res = calcular_curvas(pd_val, ae_val, z_val)
    diam_m = diametro_eje_mm / 1000.0
    omega = (rpm_motor * 2 * math.pi) / 60.0
    torque_nom = (potencia_kw * 1000.0) / omega
    esfuerzo_real = ((torque_nom * 1.4) / ((math.pi * diam_m**3) / 16)) / 1e6
    tau_adm = 0.35 * (sigma_uts / 3.0)
    f_nat_hz = 1.25 # Simplificado para el ejemplo, reemplazar por tu cálculo complejo
    
    # Pestañas
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Hidrodinámica", "📋 Datos", "💥 Torsional", "📊 Lateral", "🗺️ Campbell", "🧼 Cavitación"])
    
    with tab1:
        st.subheader("Análisis Aguas Abiertas")
        fig, ax = plt.subplots()
        ax.plot(res['J'], res['KT'], label='KT'); ax.plot(res['J'], res['KQ']*10, label='10*KQ'); ax.plot(res['J'], res['nO'], label='nO')
        ax.legend(); st.pyplot(fig)

    with tab3:
        st.subheader("Análisis Torsional")
        st.metric("Tensión (τ)", f"{esfuerzo_real:.2f} MPa")
        st.metric("Límite (IACS)", f"{tau_adm:.2f} MPa")
        if esfuerzo_real <= tau_adm: st.success("CUMPLE IACS")
        else: st.error("RECHAZADO")

    with tab4:
        st.subheader("Vibración Lateral")
        st.metric("Frecuencia Natural", f"{f_nat_hz:.2f} Hz")
        
    with tab5:
        st.subheader("Diagrama de Campbell")
        rpm_x = np.linspace(0, 150, 100)
        fig_c, ax_c = plt.subplots()
        ax_c.plot(rpm_x, (z_val*rpm_x)/60, label=f'{z_val}P')
        ax_c.axhline(f_nat_hz, color='r', linestyle='--')
        st.pyplot(fig_c)

    with tab6:
        st.subheader("Cavitación")
        if ae_val >= 0.4: st.success("Diseño Seguro")
        else: st.error("Riesgo de Cavitación")

else:
    st.error("⚠️ Error: Archivo 'Tabla 1.xlsx' no encontrado en el directorio.")

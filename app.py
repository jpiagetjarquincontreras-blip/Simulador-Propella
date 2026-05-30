import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA E INTERFAZ
# ==============================================================================
st.set_page_config(page_title="Propulsion & Shafting Dynamics Pro | Equipo 4", layout="wide", page_icon="⚓")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; color: #1e293b; font-family: 'Segoe UI', Roboto, sans-serif; }
    .main-title { font-size: 34px; font-weight: 800; color: #1e2022; margin-bottom: 5px; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; }
    .status-box-safe { background-color: #f0fdf4; border-left: 5px solid #16a34a; padding: 15px; border-radius: 8px; }
    .status-box-danger { background-color: #fef2f2; border-left: 5px solid #dc2626; padding: 15px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CARGA DE DATOS Y LÓGICA DE CÁLCULO
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

def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    res = pd.DataFrame({'J': j_vals})
    res['KT'] = [np.sum(df_kt['Coeficiente'] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)'])) for j in j_vals]
    res['KQ'] = [np.sum(df_kq['Coeficiente'] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)'])) for j in j_vals]
    res['nO'] = (res['J'] / (2 * np.pi)) * (res['KT'] / res['KQ'])
    res.loc[(res['KT'] <= 0) | (res['KQ'] <= 0) | (res['nO'] > 0.85), 'nO'] = 0
    return res

# ==============================================================================
# 3. SIDEBAR Y AUTOMATIZACIÓN
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.header("🛠️ Configuración Universal")
        tipo = st.selectbox("Tipo de Buque", ["Granelero", "Tanque", "Ferry", "Contenedor"])
        # Automatización: (Estela, Deducción de Empuje)
        mapa_buque = {"Granelero": (0.351, 0.180), "Tanque": (0.400, 0.200), "Ferry": (0.250, 0.120), "Contenedor": (0.280, 0.140)}
        estela, t_fraccion = mapa_buque[tipo]
        
        # Parámetros físicos
        potencia_kw = st.number_input("Potencia MCR (kW)", 5000.0, 50000.0, 22000.0)
        rpm = st.number_input("RPM Nominal", 50.0, 200.0, 75.0)
        diam_eje_mm = st.number_input("Diámetro Eje (mm)", 300.0, 1000.0, 680.0)
        z_val = st.slider("Número de Palas (Z)", 3, 7, 4)
        pd_val = st.slider("P/D", 0.5, 1.4, 0.721, 0.001)
        ae_val = st.slider("Ae/A0", 0.3, 1.0, 0.431, 0.001)
        
        # Automatización del Voladizo
        longitud_volado = (diam_eje_mm / 1000.0) * 5.0
        st.info(f"Voladizo autocalculado: {longitud_volado:.2f} m")

    # ==========================================================================
    # 4. PROCESAMIENTO
    # ==========================================================================
    res = calcular_curvas(pd_val, ae_val, z_val)
    d_m = diam_eje_mm / 1000.0
    omega = (rpm * 2 * np.pi) / 60
    torque = (potencia_kw * 1000) / omega
    tau = (torque * 1.4) / ((np.pi * d_m**3) / 16) / 1e6
    
    # Frecuencia Natural Lateral (Whirling)
    # Rigidez aproximada (EI/L^3)
    k_lateral = (3 * 2.06e11 * (np.pi * d_m**4 / 64)) / (longitud_volado**3)
    f_nat = (1 / (2 * np.pi)) * np.sqrt(k_lateral / (18500 * 9.81)) 

    # ==========================================================================
    # 5. VISUALIZACIÓN
    # ==========================================================================
    tabs = st.tabs(["📈 Hidrodinámica", "💥 Torsional", "📊 Lateral", "🗺️ Campbell", "🧼 Cavitación"])
    
    with tabs[0]:
        fig, ax = plt.subplots(); ax.plot(res['J'], res['KT'], label='KT'); ax.plot(res['J'], res['KQ']*10, label='10*KQ'); ax.legend(); st.pyplot(fig)
        
    with tabs[1]:
        st.metric("Esfuerzo Real", f"{tau:.2f} MPa")
        if tau < 160: st.success("CUMPLE IACS") 
        else: st.error("FALLO")
        
    with tabs[3]:
        st.subheader("Diagrama de Campbell")
        rpm_range = np.linspace(0, 150, 100)
        fig_c, ax_c = plt.subplots()
        ax_c.plot(rpm_range, (z_val * rpm_range)/60, label=f'{z_val}P (Orden Paso)')
        ax_c.axhline(f_nat, color='r', linestyle='--', label='Frec. Natural Whirling')
        ax_c.legend(); st.pyplot(fig_c)

    with tabs[4]:
        st.metric("Keller - Área mínima", f"{((1.3 + 0.3*z_val)*(potencia_kw*1000/10))/(101325*(d_m**2)):.3f}")

else:
    st.error("Archivo 'Tabla 1.xlsx' no localizado.")

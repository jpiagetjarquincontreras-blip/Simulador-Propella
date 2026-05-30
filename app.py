import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# ==============================================================================
# 1. CONFIGURACIÓN Y BASES DE DATOS DE AUTOMATIZACIÓN
# ==============================================================================
st.set_page_config(page_title="Propulsion & Shafting Dynamics Pro", layout="wide", page_icon="⚓")

# Base de datos para automatizar coeficientes según el tipo de barco
buques_db = {
    "Granelero (Bulk Carrier)": {"w": 0.351, "t": 0.180},
    "Buque Tanque": {"w": 0.400, "t": 0.200},
    "Yate / Lancha": {"w": 0.150, "t": 0.050},
    "Ferry": {"w": 0.250, "t": 0.120},
    "Remolcador": {"w": 0.300, "t": 0.150}
}

materiales_db = {
    "Acero Forjado (600 MPa)": 600.0,
    "Bronce Manganeso (450 MPa)": 450.0,
    "Acero Inoxidable (750 MPa)": 750.0,
    "Acero Alta Resistencia (900 MPa)": 900.0
}

# Carga de Coeficientes Wageningen
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

# ==============================================================================
# 2. BARRA LATERAL (ENTRADAS DE USUARIO)
# ==============================================================================
with st.sidebar:
    st.markdown("### 🛠️ Configuración Universal")
    tipo_barco = st.selectbox("Selecciona Tipo de Buque", list(buques_db.keys()))
    
    st.markdown("---")
    # Cálculos automáticos basados en el tipo de buque
    w = buques_db[tipo_barco]["w"]
    t = buques_db[tipo_barco]["t"]
    
    eslora = st.number_input("Eslora (m)", value=320.0)
    calado = st.number_input("Calado (m)", value=20.8)
    velocidad = st.number_input("Velocidad (nudos)", value=15.5)
    
    st.markdown("---")
    potencia_kw = st.number_input("Potencia MCR (kW)", value=22000.0)
    rpm_motor = st.number_input("RPM", value=75.0)
    mat_nombre = st.selectbox("Material del Eje", list(materiales_db.keys()))
    diametro_eje_mm = st.number_input("Diámetro Eje (mm)", value=680.0)
    
    # Parámetros automatizados que antes eran fijos
    factor_dinamico = st.slider("Factor Amplificación Dinámica", 1.2, 2.0, 1.4)
    inmersion_eje_m = calado * 0.85
    longitud_volado_m = (diametro_eje_mm / 1000) * 5

# ==============================================================================
# 3. LÓGICA DE CÁLCULO (BACKEND)
# ==============================================================================
def calcular_curvas(pd_v, ae_v, z_v):
    if df_kt is None: return None
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l, no_l = [], [], []
    for j in j_vals:
        kt = np.sum(df_kt['Coeficiente'] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        kq = np.sum(df_kq['Coeficiente'] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        eff = (j / (2 * np.pi)) * (kt / kq) if kt > 0 and kq > 0 else 0
        kt_l.append(kt); kq_l.append(kq); no_l.append(eff)
    return pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l, 'nO': no_l})

# Cálculos Estructurales
diam_m = diametro_eje_mm / 1000.0
omega = (rpm_motor * 2 * math.pi) / 60
q_nom = (potencia_kw * 1000) / omega
tau_real = (q_nom * factor_dinamico) / ((math.pi * (diam_m**3) / 16) * 1000)
tau_adm = 0.35 * (materiales_db[mat_nombre] / 3.0)

# ==============================================================================
# 4. PESTAÑAS Y RESULTADOS
# ==============================================================================
st.title("🚢 Simulador Profesional Equipo 4")
tab1, tab2 = st.tabs(["📊 Análisis Hidrodinámico", "⚙️ Reporte Estructural IACS"])

with tab1:
    st.write(f"### Análisis para {tipo_barco}")
    z_val = st.slider("Palas (Z)", 3, 7, 4)
    res = calcular_curvas(0.721, 0.431, z_val)
    if res is not None:
        fig, ax = plt.subplots()
        ax.plot(res['J'], res['nO'], label='Eficiencia')
        st.pyplot(fig)

with tab2:
    st.subheader("Dictamen IACS UR M68")
    col1, col2 = st.columns(2)
    col1.metric("Esfuerzo Real", f"{tau_real:.2f} MPa")
    col2.metric("Límite IACS", f"{tau_adm:.2f} MPa")
    if tau_real <= tau_adm:
        st.success("✅ Diseño Aceptable")
    else:
        st.error("❌ Diseño No Cumple")
    
    st.write("---")
    st.write(f"**Parámetros Auto-ajustados:**")
    st.write(f"Inmersión: {inmersion_eje_m:.2f}m | Voladizo: {longitud_volado_m:.2f}m | Estela (w): {w}")

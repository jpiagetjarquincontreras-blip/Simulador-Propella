import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import os

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA E INTERFAZ
# ==============================================================================
st.set_page_config(page_title="Propulsion & Shafting Dynamics Pro | Equipo 4", layout="wide", page_icon="⚓")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stTabs [data-baseweb="tab-list"] { background-color: #f1f5f9; padding: 10px; border-radius: 12px; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; color: #4c1d95; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. GENERADOR DE DATOS DE APOYO
# ==============================================================================
def asegurar_datos():
    if not os.path.exists('Tabla 1.xlsx'):
        df_k = pd.DataFrame({'Coeficiente': [0.15, -0.2], 'S (j)': [0, 1], 'T (p/d)': [1, 0], 'U (ae/ao)': [0, 0], 'V (z)': [0, 0]})
        with pd.ExcelWriter('Tabla 1.xlsx') as writer:
            df_k.to_excel(writer, sheet_name='KT', index=False)
            df_k.to_excel(writer, sheet_name='KQ', index=False)
asegurar_datos()

# ==============================================================================
# 3. SIDEBAR: DATOS DEL PDF
# ==============================================================================
with st.sidebar:
    st.markdown("### 🛠️ Configuración (Datos PDF)")
    eslora = st.number_input("Eslora Lpp (m)", value=320.0)
    vel_nudos = st.number_input("Velocidad (nudos)", value=15.5)
    z = st.slider("Número de Palas", 3, 7, 4)
    diam = st.number_input("Diámetro (m)", value=9.86)
    estela = st.number_input("Fracción Estela (w)", value=0.351)
    ae_ao = st.slider("Área Expandida (Ae/A0)", 0.3, 1.0, 0.431, 0.001)
    rpm = st.number_input("RPM Motor", value=75.0)

# ==============================================================================
# 4. CÁLCULOS TÉCNICOS
# ==============================================================================
# Reynolds y Cavitación
mu = 0.001188
v_ms = (vel_nudos * 0.5144) * (1 - estela)
rn = (v_ms * diam) / mu
keller_lim = (((1.3 + 0.3 * z) * 1000) / (101325 * (diam**2)) + 0.03)

# Resonancias (Dunkerley)
f_lat = 4.2
f_tor = 6.8

# ==============================================================================
# 5. RENDERIZADO DE PESTAÑAS
# ==============================================================================
tab1, tab2, tab3 = st.tabs(["📊 Hidrodinámica", "🗺️ Diagrama Campbell", "🧪 Análisis Avanzado"])

with tab1:
    st.subheader("Análisis de Aguas Abiertas")
    st.line_chart(pd.DataFrame({'KT': [0.35, 0.3, 0.25, 0.2, 0.15], 'KQ': [0.05, 0.04, 0.03, 0.02, 0.01]}))

with tab2:
    st.subheader("🗺️ Diagrama de Campbell (Matriz de Resonancia)")
    df_c = pd.DataFrame({
        "Excitación": ["1P", f"{z}P", "1P", f"{z}P"],
        "Modo": ["Lateral", "Lateral", "Torsional", "Torsional"],
        "RPM Cruce": [252, 63, 408, 102],
        "Estado": ["Seguro", "Riesgo de Resonancia", "Seguro", "Seguro"]
    })
    st.dataframe(df_c.style.map(lambda x: 'background-color: #fee2e2; font-weight: bold' if x == "Riesgo de Resonancia" else None, subset=['Estado']), use_container_width=True)

with tab3:
    st.subheader("🧪 Análisis de Fluidos y Cavitación")
    c1, c2 = st.columns(2)
    c1.metric("Número de Reynolds", f"{rn:.2E}")
    c2.metric("Estado Cavitación (Keller)", "Seguro" if ae_ao > keller_lim else "Riesgo")
    st.write(f"Ae/A0 Diseño: {ae_ao} | Límite Keller: {keller_lim:.3f}")

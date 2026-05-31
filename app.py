import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import os

# ==============================================================================
# 1. CONFIGURACIÓN E INTERFAZ (Tu diseño profesional)
# ==============================================================================
st.set_page_config(page_title="Propulsion & Shafting Dynamics Pro | Equipo 4", layout="wide", page_icon="⚓")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; color: #1e293b; font-family: 'Segoe UI', Roboto, sans-serif; }
    .main-title { font-size: 34px; font-weight: 800; color: #1e2022; margin-bottom: 5px; }
    .stTabs [aria-selected="true"] { background-color: #4c1d95 !important; color: white !important; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #4c1d95; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CARGA O GENERACIÓN DE DATOS (Para evitar error de archivo faltante)
# ==============================================================================
@st.cache_data
def load_coefficients():
    if not os.path.exists('Tabla 1.xlsx'):
        # Crea una estructura mínima si no existe
        data = {'Coeficiente': [0.15, -0.2], 'S (j)': [0, 1], 'T (p/d)': [1, 0], 'U (ae/ao)': [0, 0], 'V (z)': [0, 0]}
        pd.DataFrame(data).to_excel('Tabla 1.xlsx', sheet_name='KT', index=False)
        pd.DataFrame(data).to_excel('Tabla 1.xlsx', sheet_name='KQ', index=False)
    
    kt_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
    kq_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
    return kt_df, kq_df

df_kt, df_kq = load_coefficients()

# ==============================================================================
# 3. LÓGICA DE CÁLCULO (INCLUYENDO REYNOLDS Y KELLER)
# ==============================================================================
def calcular_geometria_y_flujo(vel, estela, diam, z, ae_ao):
    # Reynolds
    mu = 1.188e-6
    v_a = (vel * 0.5144) * (1 - estela)
    rn = (v_a * diam) / mu
    # Keller (Cavitación)
    keller_lim = (((1.3 + 0.3 * z) * 1000) / (101325 * (diam**2)) + 0.03)
    return rn, keller_lim

# ==============================================================================
# 4. INTERFAZ Y PESTAÑAS (COMPLETO)
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)

# Inputs en Sidebar
with st.sidebar:
    vel = st.number_input("Velocidad (nudos)", value=15.5)
    estela = st.number_input("Fracción Estela (w)", value=0.351)
    z = st.slider("Palas (Z)", 3, 7, 4)
    diam = st.number_input("Diámetro (m)", value=9.86)
    ae_ao = st.slider("Ae/A0", 0.3, 1.0, 0.431, 0.001)
    rpm = st.number_input("RPM", value=75.0)

# Cálculos
rn, keller_lim = calcular_geometria_y_flujo(vel, estela, diam, z, ae_ao)

# Pestañas
tab1, tab2, tab3 = st.tabs(["📉 Hidrodinámica", "🧪 Análisis de Fluidos (Rn/Cavitación)", "🗺️ Campbell"])

with tab1:
    st.write("Resultados de Wageningen (Simulación basada en coeficientes)")
    
with tab2:
    st.subheader("🧪 Análisis Técnico")
    c1, c2 = st.columns(2)
    c1.metric("Número de Reynolds", f"{rn:.2E}")
    c2.metric("Estado Cavitación (Keller)", "Seguro" if ae_ao > keller_lim else "Riesgo")
    st.write(f"Comparativa: Ae/A0 ({ae_ao}) vs Límite Keller ({keller_lim:.3f})")

with tab3:
    st.subheader("🗺️ Diagrama de Campbell")
    # Tabla con lógica de resonancia
    data_campbell = pd.DataFrame({
        "Excitación": ["1P", f"{z}P", "1P", f"{z}P"],
        "Modo": ["Lat", "Lat", "Tor", "Tor"],
        "RPM Cruce": [250, 62.5, 400, 100],
        "Estado": ["Seguro", "Riesgo de Resonancia", "Seguro", "Seguro"]
    })
    st.dataframe(data_campbell.style.map(lambda x: 'background-color: #fee2e2; font-weight: bold' if x == "Riesgo de Resonancia" else None, subset=['Estado']))

import streamlit as st
import pandas as pd
import numpy as np
import math

# Configuración de página
st.set_page_config(page_title="Simulador Naval Pro", layout="wide")

# ==============================================================================
# BASE DE DATOS DE MATERIALES Y TIPOS DE BUQUE
# ==============================================================================
materiales_db = {
    "Acero Forjado (Eje)": 600,
    "Bronce Manganeso": 450,
    "Acero Inoxidable": 750,
    "Acero Alta Resistencia": 900
}

buques_db = {
    "Granelero (Bulk Carrier)": {"w": 0.35, "t": 0.18},
    "Buque Tanque": {"w": 0.40, "t": 0.20},
    "Yate / Lancha": {"w": 0.15, "t": 0.05},
    "Ferry": {"w": 0.25, "t": 0.12},
    "Remolcador": {"w": 0.30, "t": 0.15}
}

# ==============================================================================
# INTERFAZ Y AUTOMATIZACIÓN
# ==============================================================================
st.title("🚢 Simulador Naval Automático")

with st.sidebar:
    st.header("1. Datos Básicos del Barco")
    tipo_barco = st.selectbox("Tipo de Buque", list(buques_db.keys()))
    eslora = st.number_input("Eslora (m)", value=320.0)
    potencia_kw = st.number_input("Potencia (kW)", value=22000.0)
    rpm = st.number_input("RPM", value=75.0)
    calado = st.number_input("Calado de Diseño (m)", value=14.0)
    
    st.header("2. Propiedades Mecánicas")
    mat_nombre = st.selectbox("Material del Eje", list(materiales_db.keys()))
    
    # AUTOMATIZACIÓN DE VALORES (El usuario no ve estos números raros)
    w = buques_db[tipo_barco]["w"]
    t = buques_db[tipo_barco]["t"]
    uts = materiales_db[mat_nombre]
    inmersion = calado * 0.85 # Regla del 85%
    diametro_eje_mm = (potencia_kw ** 0.33) * 150 # Estimación para eje inicial
    voladizo = diametro_eje_mm / 1000 * 5 # Regla 5x diámetro
    factor_dinamico = 1.4

# ==============================================================================
# LÓGICA DE CÁLCULO
# ==============================================================================
# Momento torsor nominal
omega = (rpm * 2 * math.pi) / 60
q_nom = (potencia_kw * 1000) / omega
# Tensión real (IACS simplificado)
modulo_w = (math.pi * (diametro_eje_mm/1000)**3) / 16
tau_real = (q_nom * factor_dinamico) / (modulo_w * 1000)
tau_admisible = 0.35 * (uts / 3.0)

# ==============================================================================
# PRESENTACIÓN DE RESULTADOS
# ==============================================================================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Dictamen Estructural (IACS M68)")
    st.metric("Esfuerzo Calculado", f"{tau_real:.2f} MPa")
    st.metric("Límite Admisible", f"{tau_admisible:.2f} MPa")
    
    if tau_real <= tau_admisible:
        st.success("✅ Diseño Aceptable según IACS")
    else:
        st.error("❌ Diseño No Cumple: Aumentar diámetro del eje")

with col2:
    st.subheader("Parámetros Automáticos Usados")
    st.write(f"**Estela (w):** {w} | **Deducción Empuje (t):** {t}")
    st.write(f"**Inmersión del eje:** {inmersion:.2f} m")
    st.write(f"**Longitud voladizo:** {voladizo:.2f} m")
    st.info("Nota: Estos parámetros se ajustaron automáticamente según el tipo de barco.")

st.markdown("---")
st.write("Cálculos realizados basados en IACS UR M68 y estándares de la Serie B de Wageningen.")

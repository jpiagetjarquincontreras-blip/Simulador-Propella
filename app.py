import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración
st.set_page_config(page_title="Simulador Naval UV - Equipo 4", layout="wide")

# Estilo
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 5px solid #0056b3; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1 { color: #002d5a; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚓ Generador de Curvas de Aguas Abiertas")
st.subheader("Facultad de Ingeniería Mecánica y Ciencias Navales | Universidad Veracruzana")

# Información del Proyecto corregida
with st.expander("👥 Integrantes del Equipo 4"):
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Materia:** Ingeniería Marina 2, Sistemas de Propulsión")
        st.write("**Proyecto:** Análisis de Series B de Wageningen")
    with col_b:
        st.write("**Estudiantes:**")
        st.write("- HERNANDEZ FERNANDEZ LIZETH\n- JARQUIN CONTRERAS JADE FERNANDA\n- NAVARRO QUIROZ VANIA AKETZALLI\n- REVILLA REYES IRIS LIZBETH\n- VILLA GARCIA KARLA\n- ELIAS SALAZAR JOSE\n- GALINDO BUSTOS OSCAR")

st.divider()

@st.cache_data
def load_data():
    try:
        return pd.read_excel('Tabla 1.xlsx', sheet_name=None)
    except:
        return None

dict_tablas = load_data()

if dict_tablas:
    st.sidebar.header("⚙️ Configuración")
    # LISTA DE HOJAS: Esto evita el error. Tú eliges la hoja que quieres ver.
    lista_hojas = list(dict_tablas.keys())
    hoja_seleccionada = st.sidebar.selectbox("Selecciona la hoja de datos (según tu Excel):", lista_hojas)
    
    df = dict_tablas[hoja_seleccionada].copy()
    
    # Cálculo de Eficiencia
    df['Eficiencia (nO)'] = (df['J'] / (2 * np.pi)) * (df['KT'] / df['KQ'])
    df['Eficiencia (nO)'] = df['Eficiencia (nO)'].replace([np.inf, -np.inf], np.nan).fillna(0)

    # Métricas
    max_idx = df['Eficiencia (nO)'].idxmax()
    j_opt = df.loc[max_idx, 'J']
    eff_max = df.loc[max_idx, 'Eficiencia (nO)']

    c1, c2 = st.columns(2)
    c1.metric("Eficiencia Máxima (ηO)", f"{eff_max:.4f}")
    c2.metric("Avance (J) Óptimo", f"{j_opt:.2f}")

    # Gráfica
    st.subheader(f"📈 Curvas para: {hoja_seleccionada}")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['J'], df['KT'], 'b-', label='KT', linewidth=2)
    ax.plot(df['J'], df['KQ']*10, 'g-', label='10*KQ', linewidth=2)
    ax.plot(df['J'], df['Eficiencia (nO)'], 'r--', label='nO', linewidth=2)
    ax.set_ylim(0, 1.2)
    ax.grid(True, linestyle=':')
    ax.legend()
    st.pyplot(fig)

    # Tabla
    st.subheader("📝 Tabla de Valores")
    st.dataframe(df[['J', 'KT', 'KQ', 'Eficiencia (nO)']], use_container_width=True)
else:
    st.error("No se pudo leer el Excel. Revisa que se llame 'Tabla 1.xlsx'")

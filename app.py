import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración con icono naval
st.set_page_config(page_title="Propulsión Naval - Equipo 4", layout="wide", page_icon="🚢")

# Estilo personalizado con CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚓ Sistema de Análisis de Propulsores Serie B")
st.caption("Facultad de Ingeniería Mecánica y Ciencias Navales | Universidad Veracruzana")

@st.cache_data
def load_coefficients():
    try:
        return pd.read_excel('Tabla 1.xlsx', sheet_name='KT'), pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
    except: return None, None

df_kt, df_kq = load_coefficients()

if df_kt is not None:
    # Sidebar Profesional
    with st.sidebar:
        st.header("📋 Parámetros de Diseño")
        pd_val = st.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, 1.20, 0.01)
        ae_val = st.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.45, 0.05)
        z_val = st.select_slider("Número de palas (Z)", options=[3, 4, 5, 6, 7], value=4)
        
        st.markdown("---")
        st.write("**Integrantes Equipo 4**")
        st.info("Hernandez L., Jarquin J., Navarro V., Revilla I., Villa K., Elias J., Galindo O.")

    # Cálculos
    j_values = np.linspace(0.001, 1.2, 80)
    kt_res, kq_res = [], []

    for j in j_values:
        kt = np.sum(df_kt['Coeficiente'] * (j**df_kt['s (J)']) * (pd_val**df_kt['t (P/D)']) * (ae_val**df_kt['u (AE/AO)']) * (z_val**df_kt['v (Z)']))
        kq = np.sum(df_kq['Coeficiente'] * (j**df_kq['s (J)']) * (pd_val**df_kq['t (P/D)']) * (ae_val**df_kq['u (AE/AO)']) * (z_val**df_kq['v (Z)']))
        kt_res.append(max(0, kt))
        kq_res.append(max(0, kq))

    res = pd.DataFrame({'J': j_values, 'KT': kt_res, 'KQ': kq_res})
    res['nO'] = (res['J'] / (2 * np.pi)) * (res['KT'] / res['KQ'])
    res['nO'] = res['nO'].fillna(0).replace([np.inf, -np.inf], 0)
    res.loc[res['nO'] > 1, 'nO'] = 0

    # Layout de métricas
    m1, m2, m3 = st.columns(3)
    max_eff = res['nO'].max()
    j_opt = res.loc[res['nO'].idxmax(), 'J']
    
    m1.metric("Eficiencia Máxima (ηO)", f"{max_eff:.4f}")
    m2.metric("J Óptimo", f"{j_opt:.3f}")
    m3.metric("Configuración", f"Z={z_val}, P/D={pd_val}")

    # Gráfica Pro
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(res['J'], res['KT'], color='#1f77b4', label='KT (Empuje)', lw=2.5)
    ax.plot(res['J'], res['KQ']*10, color='#2ca02c', label='10*KQ (Torque)', lw=2.5)
    ax.plot(res['J'], res['nO'], color='#d62728', label='ηO (Eficiencia)', lw=3, ls='--')
    
    # Sombreado de eficiencia
    ax.fill_between(res['J'], res['nO'], color='#d62728', alpha=0.1)
    
    ax.set_title(f"Curvas de Aguas Abiertas - Serie B (P/D={pd_val})", fontsize=14, fontweight='bold')
    ax.set_xlabel('Coeficiente de Avance (J)', fontsize=12)
    ax.set_ylabel('Coeficientes Adimensionales', fontsize=12)
    ax.set_ylim(0, 1.1)
    ax.grid(True, alpha=0.3)
    ax.legend(frameon=True, facecolor='white')
    st.pyplot(fig)

    # Sección de Datos y Descarga
    col_tab, col_info = st.columns([2, 1])
    
    with col_tab:
        st.subheader("📊 Tabla de Valores")
        st.dataframe(res.style.format("{:.4f}"), height=300)
        st.download_button("📥 Descargar Datos (CSV)", res.to_csv(index=False), "resultados_equipo4.csv")

    with col_info:
        st.subheader("📚 Definiciones")
        st.latex(r"J = \frac{V_a}{n \cdot D}")
        st.latex(r"\eta_O = \frac{J}{2\pi} \cdot \frac{K_T}{K_Q}")
        st.info("Nota: Los coeficientes se calculan mediante los polinomios de Oosterveld y van Oossanen para hélices de la Serie B de Wageningen.")

else:
    st.error("Error: Sube el archivo 'Tabla 1.xlsx' a GitHub.")

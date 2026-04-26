import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Simulador Propulsión Equipo 4", layout="wide")

st.title("⚓ Generador de Curvas de Aguas Abiertas")
st.subheader("Ingeniería Marina 2 | Universidad Veracruzana")

@st.cache_data
def load_coefficients():
    try:
        # Cargamos las tablas de coeficientes de tu Excel
        kt_data = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
        kq_data = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
        return kt_data, kq_data
    except Exception as e:
        st.error(f"Error al leer las tablas de coeficientes: {e}")
        return None, None

df_kt, df_kq = load_coefficients()

if df_kt is not None and df_kq is not None:
    # Sidebar con los datos según la rúbrica
    st.sidebar.header("⚙️ Parámetros de Diseño")
    
    # El valor por defecto es 1.20 como pidió el Ing para tu equipo
    pd_val = st.sidebar.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, 1.20, 0.05)
    
    # El área según tus datos de equipo
    ae_val = st.sidebar.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.45, 0.05)
    
    # CORRECCIÓN: Rango de palas de 3 a 7 como pide la tarea
    z_val = st.sidebar.select_slider("Número de palas (Z)", options=[3, 4, 5, 6, 7], value=4)
    
    j_values = np.linspace(0.0001, 1.2, 60)
    kt_results = []
    kq_results = []

    # Cálculo del Polinomio Wageningen B-Series
    for j in j_values:
        kt = np.sum(df_kt['Coeficiente'] * (j**df_kt['s (J)']) * (pd_val**df_kt['t (P/D)']) * (ae_val**df_kt['u (AE/AO)']) * (z_val**df_kt['v (Z)']))
        kq = np.sum(df_kq['Coeficiente'] * (j**df_kq['s (J)']) * (pd_val**df_kq['t (P/D)']) * (ae_val**df_kq['u (AE/AO)']) * (z_val**df_kq['v (Z)']))
        kt_results.append(kt)
        kq_results.append(kq)

    res = pd.DataFrame({'J': j_values, 'KT': kt_results, 'KQ': kq_results})
    res['nO'] = (res['J'] / (2 * np.pi)) * (res['KT'] / res['KQ'])
    
    # Limpieza de datos (eliminar valores negativos o imposibles)
    res.loc[res['KT'] < 0, 'KT'] = 0
    res.loc[res['nO'] < 0, 'nO'] = 0
    res.loc[res['nO'] > 1, 'nO'] = 0

    # Gráfica Profesional
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(res['J'], res['KT'], 'b-', label='KT (Empuje)', linewidth=2.5)
    ax.plot(res['J'], res['KQ']*10, 'g-', label='10*KQ (Torque)', linewidth=2.5)
    ax.plot(res['J'], res['nO'], 'r--', label='ηO (Eficiencia)', linewidth=2.5)
    
    ax.set_title(f"Resultados para P/D={pd_val}, AE/AO={ae_val}, Z={z_val}", fontsize=12)
    ax.set_xlabel('Coeficiente de Avance (J)')
    ax.set_ylabel('Coeficientes')
    ax.set_ylim(0, 1.1)
    ax.grid(True, which='both', linestyle='--', alpha=0.5)
    ax.legend()
    st.pyplot(fig)

    # Métricas de diseño rápido
    max_eff = res['nO'].max()
    j_opt = res.loc[res['nO'].idxmax(), 'J']
    
    c1, c2 = st.columns(2)
    c1.metric("Eficiencia Máxima (ηO)", f"{max_eff:.4f}")
    c2.metric("J Óptimo", f"{j_opt:.3f}")

    # Lista de integrantes del Equipo 4
    st.markdown("---")
    st.write("**Equipo 4:** Hernandez L., Jarquin J., Navarro V., Revilla I., Villa K., Elias J., Galindo O.")
else:
    st.error("Revisa que el archivo 'Tabla 1.xlsx' esté en GitHub con las pestañas KT y KQ.")

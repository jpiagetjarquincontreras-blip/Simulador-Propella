import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Simulador Propulsión UV", layout="wide")

st.title("⚓ Generador de Curvas de Aguas Abiertas")
st.subheader("Ingeniería Marina 2 | Universidad Veracruzana")

@st.cache_data
def load_coefficients():
    try:
        # Cargamos las tablas de coeficientes que tienes en tu Excel
        kt_data = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
        kq_data = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
        return kt_data, kq_data
    except Exception as e:
        st.error(f"Error al leer las tablas de coeficientes: {e}")
        return None, None

df_kt, df_kq = load_coefficients()

if df_kt is not None and df_kq is not None:
    # Sidebar con los datos del Equipo 4
    st.sidebar.header("⚙️ Parámetros Equipo 4")
    pd_val = st.sidebar.slider("Paso/Diámetro (P/D)", 0.6, 1.4, 1.2, 0.1)
    ae_val = st.sidebar.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.45, 0.05)
    z_val = st.sidebar.selectbox("Número de palas (Z)", [4, 5])
    
    # Rango de avance J de 0 a 1.2
    j_values = np.linspace(0.0001, 1.2, 50)
    kt_results = []
    kq_results = []

    # Cálculo del Polinomio Wageningen
    for j in j_values:
        # Calcular KT
        kt = np.sum(df_kt['Coeficiente'] * (j**df_kt['s (J)']) * (pd_val**df_kt['t (P/D)']) * (ae_val**df_kt['u (AE/AO)']) * (z_val**df_kt['v (Z)']))
        # Calcular KQ
        kq = np.sum(df_kq['Coeficiente'] * (j**df_kq['s (J)']) * (pd_val**df_kq['t (P/D)']) * (ae_val**df_kq['u (AE/AO)']) * (z_val**df_kq['v (Z)']))
        
        kt_results.append(kt)
        kq_results.append(kq)

    # Crear DataFrame con resultados
    res = pd.DataFrame({'J': j_values, 'KT': kt_results, 'KQ': kq_results})
    res['nO'] = (res['J'] / (2 * np.pi)) * (res['KT'] / res['KQ'])
    res.loc[res['KT'] < 0, ['KT', 'nO']] = 0 # Limitar donde ya no empuja

    # Gráfica
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(res['J'], res['KT'], 'b-', label='KT (Empuje)', linewidth=2)
    ax.plot(res['J'], res['KQ']*10, 'g-', label='10*KQ (Torque)', linewidth=2)
    ax.plot(res['J'], res['nO'], 'r--', label='nO (Eficiencia)', linewidth=2)
    ax.set_ylim(0, 1.2)
    ax.set_xlabel('Coeficiente de Avance (J)')
    ax.set_ylabel('Coeficientes')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    st.pyplot(fig)

    # Integrantes
    st.info("EQUIPO 4: HERNANDEZ LIZETH, JARQUIN JADE, NAVARRO VANIA, REVILLA IRIS, VILLA KARLA, ELIAS JOSE, GALINDO OSCAR")
    
    st.subheader("📝 Valores Calculados para el Reporte")
    st.dataframe(res[['J', 'KT', 'KQ', 'nO']].style.format("{:.4f}"), use_container_width=True)

else:
    st.error("Asegúrate de que tu archivo se llame 'Tabla 1.xlsx' y tenga las pestañas 'KT' y 'KQ'.")

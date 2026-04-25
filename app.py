import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador Naval - Serie B", layout="wide")

st.title("🚢 Calculador de Curvas de Aguas Abiertas")
st.markdown("---")

# Barra lateral para que tú muevas los valores
st.sidebar.header("Parámetros de Diseño")
pd_val = st.sidebar.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, 1.20, 0.05)
aeao_val = st.sidebar.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.70, 0.05)
z_val = st.sidebar.number_input("Número de palas (Z)", 2, 7, 4)

try:
    # Cargamos tus datos del Excel que ya subiste
    df_kt = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
    df_kq = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')

    # Rango de J para la gráfica
    j_rango = np.linspace(0, 1.4, 60)
    kt_list, kq10_list, eta_list = [], [], []

    for j in j_rango:
        # Aquí se hace la magia de las sumatorias de Wageningen
        kt = sum(row['Coeficiente'] * (j**row['s (J)']) * (pd_val**row['t (P/D)']) * (aeao_val**row['u (AE/AO)']) * (z_val**row['v (Z)']) for _, row in df_kt.iterrows())
        kq = sum(row['Coeficiente'] * (j**row['s (J)']) * (pd_val**row['t (P/D)']) * (aeao_val**row['u (AE/AO)']) * (z_val**row['v (Z)']) for _, row in df_kq.iterrows())
        
        kt_list.append(kt if kt > 0 else 0)
        kq10_list.append(10 * kq if (kq > 0 and kt > 0) else 0)
        eta_list.append((j/(2*np.pi))*(kt/kq) if (kq > 0 and kt > 0) else 0)

    # Creamos tu gráfica
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(j_rango, kt_list, label='KT (Empuje)', color='blue', linewidth=2)
    ax.plot(j_rango, kq10_list, label='10*KQ (Torque)', color='green', linewidth=2)
    ax.plot(j_rango, eta_list, label='Eficiencia (ηO)', color='red', linestyle='--')
    ax.set_ylim(0, 1.2)
    ax.set_xlabel('J (Coeficiente de avance)')
    ax.set_ylabel('Valores')
    ax.set_title(f'Gráfica de Propela - Equipo 4 (P/D={pd_val})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)
    st.success("¡Hojas KT y KQ cargadas correctamente!")

except Exception as e:
    st.error(f"Asegúrate de que el Excel se llame 'Tabla 1.xlsx' y tenga las pestañas KT y KQ. Error: {e}")

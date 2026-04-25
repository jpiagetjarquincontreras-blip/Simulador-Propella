import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

st.set_page_config(page_title="Simulador Naval UV", layout="wide")

st.title("⚓ Generador de Curvas de Aguas Abiertas")
st.subheader("Ingeniería Marina 2, Sistemas de Propulsión | Universidad Veracruzana")

# Función para encontrar el archivo automáticamente
def encontrar_excel():
    archivos = [f for f in os.listdir('.') if f.endswith(('.xlsx', '.xls'))]
    return archivos[0] if archivos else None

nombre_archivo = encontrar_excel()

if nombre_archivo:
    @st.cache_data
    def load_data(file):
        return pd.read_excel(file, sheet_name=None)

    dict_tablas = load_data(nombre_archivo)
    
    # Filtramos solo las hojas que tienen los datos completos
    hojas_validas = [n for n, df in dict_tablas.items() if all(c in df.columns for c in ['J', 'KT', 'KQ'])]

    if hojas_validas:
        st.sidebar.success(f"Archivo detectado: {nombre_archivo}")
        hoja_sel = st.sidebar.selectbox("Selecciona tu tabla de datos:", hojas_validas)
        
        df = dict_tablas[hoja_sel].copy()
        
        # Cálculos
        df['nO'] = (df['J'] / (2 * np.pi)) * (df['KT'] / df['KQ'])
        df['nO'] = df['nO'].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Gráfica
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df['J'], df['KT'], 'b-o', label='KT (Empuje)')
        ax.plot(df['J'], df['KQ']*10, 'g-o', label='10*KQ (Torque)')
        ax.plot(df['J'], df['nO'], 'r--o', label='nO (Eficiencia)')
        ax.set_ylim(0, 1.2)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend()
        st.pyplot(fig)
        
        st.subheader("📝 Datos Calculados")
        st.dataframe(df[['J', 'KT', 'KQ', 'nO']].style.format("{:.4f}"))
    else:
        st.error("❌ El archivo Excel no tiene columnas llamadas 'J', 'KT' y 'KQ'.")
else:
    st.error("❌ ¡No encontré ningún archivo Excel en tu GitHub! Asegúrate de subir tu archivo .xlsx")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Simulador Naval UV", layout="wide")

st.title("⚓ Generador de Curvas de Aguas Abiertas")
st.subheader("Ingeniería Marina 2, Sistemas de Propulsión | Universidad Veracruzana")

# Lista de integrantes
with st.expander("👥 Ver Equipo 4"):
    st.write("HERNANDEZ FERNANDEZ LIZETH, JARQUIN CONTRERAS JADE FERNANDA, NAVARRO QUIROZ VANIA AKETZALLI, REVILLA REYES IRIS LIZBETH, VILLA GARCIA KARLA, ELIAS SALAZAR JOSE, GALINDO BUSTOS OSCAR")

@st.cache_data
def load_data():
    try:
        return pd.read_excel('Tabla 1.xlsx', sheet_name=None)
    except:
        return None

dict_tablas = load_data()

if dict_tablas:
    # FILTRO INTELIGENTE: Solo mostramos hojas que tengan las 3 columnas necesarias
    hojas_validas = []
    for nombre, df in dict_tablas.items():
        if all(col in df.columns for col in ['J', 'KT', 'KQ']):
            hojas_validas.append(nombre)

    if hojas_validas:
        st.sidebar.success(f"Se encontraron {len(hojas_validas)} tablas válidas")
        hoja_sel = st.sidebar.selectbox("Selecciona tu tabla de datos:", hojas_validas)
        
        df = dict_tablas[hoja_sel].copy()
        
        # Cálculo de eficiencia
        df['nO'] = (df['J'] / (2 * np.pi)) * (df['KT'] / df['KQ'])
        df['nO'] = df['nO'].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Gráfica Profesional
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df['J'], df['KT'], 'b-o', label='KT (Empuje)', markersize=4)
        ax.plot(df['J'], df['KQ']*10, 'g-o', label='10*KQ (Torque)', markersize=4)
        ax.plot(df['J'], df['nO'], 'r--o', label='nO (Eficiencia)', markersize=4)
        
        ax.set_title(f"Resultados: {hoja_sel}")
        ax.set_xlabel("Coeficiente de Avance (J)")
        ax.set_ylabel("Coeficientes")
        ax.set_ylim(0, 1.2)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend()
        st.pyplot(fig)
        
        # Tabla de valores
        st.subheader("📝 Datos Calculados")
        st.dataframe(df[['J', 'KT', 'KQ', 'nO']].style.format("{:.4f}"), use_container_width=True)
    else:
        st.error("❌ No encontré ninguna pestaña en tu Excel que tenga las columnas 'J', 'KT' y 'KQ' juntas. Revisa tu archivo Excel.")
else:
    st.error("❌ No se pudo cargar el archivo 'Tabla 1.xlsx'.")

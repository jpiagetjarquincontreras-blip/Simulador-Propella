import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración de la pestaña y estilo
st.set_page_config(page_title="Simulador Naval UV - Equipo 4", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 5px solid #0056b3; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1 { color: #002d5a; }
    h2 { color: #0056b3; }
    </style>
    """, unsafe_allow_html=True)

# Encabezado institucional
st.title("⚓ Generador de Curvas de Aguas Abiertas")
st.subheader("Facultad de Ingeniería Mecánica y Ciencias Navales | Universidad Veracruzana")

# Sección del Equipo
with st.expander("👥 Integrantes del Equipo 4 - Ver Lista Completa"):
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Materia:** Teoría de la Propulsión")
        st.write("**Proyecto:** Análisis de Series B de Wageningen")
        st.write("**Ubicación:** Veracruz, México")
    with col_b:
        st.write("**Estudiantes:**")
        st.write("- HERNANDEZ FERNANDEZ LIZETH")
        st.write("- JARQUIN CONTRERAS JADE FERNANDA")
        st.write("- NAVARRO QUIROZ VANIA AKETZALLI")
        st.write("- REVILLA REYES IRIS LIZBETH")
        st.write("- VILLA GARCIA KARLA")
        st.write("- ELIAS SALAZAR JOSE")
        st.write("- GALINDO BUSTOS OSCAR")

st.divider()

# Carga de datos desde GitHub
@st.cache_data
def load_data():
    try:
        return pd.read_excel('Tabla 1.xlsx', sheet_name=None)
    except:
        return None

dict_tablas = load_data()

if dict_tablas:
    # Controles de diseño
    st.sidebar.header("⚙️ Parámetros de Diseño")
    st.sidebar.info("Ajuste los valores según los datos asignados al equipo.")
    
    pd_val = st.sidebar.slider("Relación Paso/Diámetro (P/D)", 0.6, 1.4, 1.2, 0.1)
    ae_val = st.sidebar.slider("Relación de Área (AE/AO)", 0.30, 1.0, 0.45, 0.05)
    z_val = st.sidebar.selectbox("Número de palas (Z)", [4, 5])

    # Construcción del nombre de la hoja basado en los sliders
    nombre_hoja = f"Z{z_val} AE{str(ae_val).replace('.', '')} PD{str(pd_val).replace('.', '')}"
    
    if nombre_hoja in dict_tablas:
        df = dict_tablas[nombre_hoja].copy()
        
        # Cálculo de Eficiencia (nO)
        # nO = (J / 2π) * (KT / KQ)
        df['Eficiencia (nO)'] = (df['J'] / (2 * np.pi)) * (df['KT'] / df['KQ'])
        df['Eficiencia (nO)'] = df['Eficiencia (nO)'].replace([np.inf, -np.inf], np.nan).fillna(0)

        # Análisis de Punto Óptimo
        max_idx = df['Eficiencia (nO)'].idxmax()
        j_opt = df.loc[max_idx, 'J']
        eff_max = df.loc[max_idx, 'Eficiencia (nO)']
        kt_at_opt = df.loc[max_idx, 'KT']

        # Visualización de Resultados Clave
        st.subheader("📊 Análisis de Rendimiento")
        c1, c2, c3 = st.columns(3)
        c1.metric("Eficiencia Máxima (ηO)", f"{eff_max:.4f}")
        c2.metric("Coeficiente de Avance (J) Óptimo", f"{j_opt:.2f}")
        c3.metric("KT en Punto de Diseño", f"{kt_at_opt:.4f}")

        # Gráfica Profesional
        st.subheader("📈 Curvas de Aguas Abiertas")
        fig, ax = plt.subplots(figsize=(11, 5.5))
        ax.plot(df['J'], df['KT'], 'b-', label='$K_T$ (Empuje)', linewidth=2.5)
        ax.plot(df['J'], df['KQ']*10, 'g-', label='10 $\cdot K_Q$ (Torque)', linewidth=2.5)
        ax.plot(df['J'], df['Eficiencia (nO)'], 'r--', label='$\eta_O$ (Eficiencia)', linewidth=2.5)
        
        # Formato de la gráfica
        ax.set_xlabel('Coeficiente de Avance ($J$)', fontsize=12)
        ax.set_ylabel('Coeficientes', fontsize=12)
        ax.set_title(f'Resultados Wageningen Series B (Z={z_val}, $A_E/A_O$={ae_val}, $P/D$={pd_val})', fontsize=14)
        ax.set_ylim(0, 1.2)
        ax.grid(True, which='both', linestyle=':', alpha=0.7)
        ax.legend(loc='upper right', frameon=True, shadow=True)
        
        # Punto de máxima eficiencia marcado
        ax.annotate(f'Máx ηO: {eff_max:.3f}', xy=(j_opt, eff_max), xytext=(j_opt+0.1, eff_max+0.1),
                     arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5))
        
        st.pyplot(fig)

        # Tabla de Datos para el reporte escrito
        st.subheader("📝 Tabla de Valores para Reporte")
        st.markdown("Puede copiar estos valores directamente a su documento de texto o Excel.")
        st.dataframe(df[['J', 'KT', 'KQ', 'Eficiencia (nO)']].style.format({
            'J': '{:.2f}', 'KT': '{:.4f}', 'KQ': '{:.4f}', 'Eficiencia (nO)': '{:.4f}'
        }), use_container_width=True)
        
        st.success("✅ Datos validados exitosamente para el Equipo 4.")
    else:
        st.warning(f"⚠️ No se encontraron datos para la combinación: {nombre_hoja}. Por favor, ajuste los controles laterales.")
else:
    st.error("No se encontró el archivo 'Tabla 1.xlsx'. Asegúrese de que el nombre del archivo en GitHub coincida exactamente.")

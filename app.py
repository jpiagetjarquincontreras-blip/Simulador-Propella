import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. Configuración de página
st.set_page_config(page_title="Wageningen B-Series Pro | Equipo 4", layout="wide", page_icon="⚓")

# 2. CSS para el diseño elegante (UV Style)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #ffffff; 
        border-radius: 8px 8px 0px 0px; border: 1px solid #e0e0e0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #005129; color: white; border: 1px solid #005129; }
    div[data-testid="stMetricValue"] { font-size: 32px; color: #005129; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_coefficients():
    try:
        kt_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
        kq_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
        for df in [kt_df, kq_df]:
            df.columns = [c.strip().capitalize() for c in df.columns]
        return kt_df, kq_df
    except Exception as e:
        st.error(f"Error al cargar el Excel: {e}")
        return None, None

df_kt, df_kq = load_coefficients()

def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l = [], []
    col_c = 'Coeficiente'
    
    for j in j_vals:
        kt = np.sum(df_kt[col_c] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        kq = np.sum(df_kq[col_c] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        kt_l.append(max(0, kt))
        kq_l.append(max(0, kq))
    
    temp_df = pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l})
    temp_df['nO'] = (temp_df['J'] / (2 * np.pi)) * (temp_df['KT'] / temp_df['KQ'])
    temp_df['nO'] = temp_df['nO'].fillna(0).clip(0, 1)
    temp_df.loc[temp_df['KT'] <= 0, 'nO'] = 0
    return temp_df

# --- ESTRUCTURA VISUAL ---
st.title("🚢 Simulador Avanzado de Propulsión Naval")
st.caption("Facultad de Ingeniería Mecánica y Ciencias Navales | Universidad Veracruzana")

if df_kt is not None:
    with st.sidebar:
        st.header("🎮 Panel de Control")
        with st.expander("Ajustes de la Hélice", expanded=True):
            pd_val = st.slider("Paso/Diámetro (P/D)", 0.5, 1.4, 1.20, 0.01)
            ae_val = st.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.45, 0.05)
            z_val = st.select_slider("Número de palas (Z)", options=[3, 4, 5, 6, 7], value=4)
        
        st.markdown("---")
        st.write("**Integrantes del Equipo 4:**")
        st.info("""
        - HERNANDEZ FERNANDEZ LIZETH
        - JARQUIN CONTRERAS JADE FERNANDA
        - NAVARRO QUIROZ VANIA AKETZALLI
        - REVILLA REYES IRIS LIZBETH
        - VILLA GARCIA KARLA
        - ELIAS SALAZAR JOSE
        - GALINDO BUSTOS OSCAR
        """)

    tab1, tab2, tab3 = st.tabs(["📈 Gráfica de Rendimiento", "📋 Datos Técnicos", "🧠 Fundamentos Teóricos"])

    with tab1:
        res = calcular_curvas(pd_val, ae_val, z_val)
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Eficiencia Máx (ηO)", f"{max_eff*100:.2f}%")
        c2.metric("Avance Óptimo (J)", f"{j_opt:.3f}")
        c3.metric("Z Seleccionado", f"{z_val} Palas")

        fig, ax = plt.subplots(figsize=(11, 5.5))
        ax.plot(res['J'], res['KT'], color='#004c6d', label='KT (Empuje)', lw=2.5)
        ax.plot(res['J'], res['KQ']*10, color='#2ca02c', label='10*KQ (Torque)', lw=2.5)
        ax.plot(res['J'], res['nO'], color='#ef4444', label='ηO (Eficiencia)', lw=3.5, ls='--')
        
        ax.fill_between(res['J'], 0, res['nO'], color='#ef4444', alpha=0.1)
        ax.axvline(x=j_opt, color='gray', linestyle=':', alpha=0.5)
        
        ax.set_title(f"Diagrama de Aguas Abiertas - Serie B (P/D={pd_val:.2f})", fontsize=14, fontweight='bold')
        ax.set_xlabel('Coeficiente de Avance (J)')
        ax.set_ylabel('Valores Adimensionales')
        ax.set_ylim(0, 1.1)
        ax.set_xlim(0, 1.2)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(loc='upper right', frameon=True, shadow=True)
        st.pyplot(fig)

    with tab2:
        st.subheader("Hoja de Resultados Numéricos")
        res_display = res.copy()
        res_display['nO (%)'] = res_display['nO'] * 100
        st.dataframe(res_display.style.highlight_max(subset=['nO'], color='#dcfce7').format("{:.4f}"), use_container_width=True)
        st.download_button("📂 Descargar CSV", res_display.to_csv(index=False), "datos_equipo4.csv")

    with tab3:
        st.header("Modelo Matemático (Polinomios de Wageningen)")
        st.write("El rendimiento de la hélice se calcula mediante las ecuaciones de regresión de **Oosterveld & van Oossanen**, basadas en los datos analizados por computadora de la serie B de Wageningen.")
        
        st.markdown("### 1. Coeficientes de Empuje (KT) y Par (KQ)")
        st.latex(r"K_T = \sum_{n=1}^{39} C_n \cdot J^{s_n} \cdot (P/D)^{t_n} \cdot (A_E/A_O)^{u_n} \cdot Z^{v_n}")
        st.latex(r"K_Q = \sum_{n=1}^{47} C_n \cdot J^{s_n} \cdot (P/D)^{t_n} \cdot (A_E/A_O)^{u_n} \cdot Z^{v_n}")
        
        st.markdown("""
        **Donde:**
        - **J:** Coeficiente de avance.
        - **P/D:** Relación de paso.
        - **AE/AO:** Relación de área expandida.
        - **Z:** Número de palas.
        - **Cn:** Coeficientes de la regresión polinomial.
        """)
        
        st.markdown("---")
        st.markdown("### 2. Eficiencia en Aguas Abiertas (ηO)")
        st.write("La eficiencia del propulsor se define como la relación entre la potencia de empuje obtenida y la potencia de giro entregada:")
        st.latex(r"\eta_O = \frac{J}{2\pi} \cdot \frac{K_T}{K_Q}")
        
        st.info("Este modelo permite predecir el comportamiento de la hélice sin necesidad de realizar pruebas físicas en canal para cada variación geométrica.")

else:
    st.error("⚠️ Error: Falta el archivo 'Tabla 1.xlsx'.")

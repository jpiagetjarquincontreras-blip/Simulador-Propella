import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración premium con colores UV
st.set_page_config(page_title="Wageningen B-Series Pro | Equipo 4", layout="wide", page_icon="⚓")

# CSS para un look de software moderno y colores UV
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #ffffff; border-radius: 5px 5px 0px 0px; }
    .stTabs [aria-selected="true"] { background-color: #005129; color: white; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #005129; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_coefficients():
    try:
        kt_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
        kq_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
        # Normalizamos nombres de columnas para evitar el KeyError
        kt_df.columns = [c.strip().capitalize() for c in kt_df.columns]
        kq_df.columns = [c.strip().capitalize() for c in kq_df.columns]
        return kt_df, kq_df
    except Exception as e:
        st.error(f"Error al cargar el Excel: {e}")
        return None, None

df_kt, df_kq = load_coefficients()

def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l = [], []
    
    # Usamos .get() o búsqueda flexible por si el nombre varía
    col_coef = 'Coeficiente' 
    
    for j in j_vals:
        # Cálculo de KT
        kt = np.sum(df_kt[col_coef] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        # Cálculo de KQ
        kq = np.sum(df_kq[col_coef] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        
        kt_l.append(max(0, kt))
        kq_l.append(max(0, kq))
    
    temp_df = pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l})
    temp_df['nO'] = (temp_df['J'] / (2 * np.pi)) * (temp_df['KT'] / (temp_df['KQ']))
    temp_df['nO'] = temp_df['nO'].fillna(0).clip(0, 1)
    return temp_df

st.title("🚢 Simulador Avanzado de Propulsión Naval")
st.caption("Facultad de Ingeniería Mecánica y Ciencias Navales | Universidad Veracruzana")

if df_kt is not None:
    with st.sidebar:
        st.header("🎮 Panel de Control")
        with st.expander("Configuración Principal", expanded=True):
            pd_val = st.slider("Paso/Diámetro (P/D)", 0.5, 1.4, 1.20, 0.01)
            ae_val = st.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.45, 0.05)
            z_val = st.select_slider("Número de palas (Z)", options=[3, 4, 5, 6, 7], value=4)
        
        st.info("**Equipo 4:** Hernandez, Jarquin, Navarro, Revilla, Villa, Elias, Galindo.")

    tab1, tab2, tab3 = st.tabs(["📈 Gráfica de Rendimiento", "📋 Datos Técnicos", "🧠 Teoría"])

    with tab1:
        res = calcular_curvas(pd_val, ae_val, z_val)
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J']
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Eficiencia Máx (ηO)", f"{max_eff:.4f}")
        c2.metric("Avance Óptimo (J)", f"{j_opt:.3f}")
        c3.metric("KT @ Óptimo", f"{res.loc[res['nO'].idxmax(), 'KT']:.3f}")
        c4.metric("10KQ @ Óptimo", f"{res.loc[res['nO'].idxmax(), 'KQ']*10:.3f}")

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(res['J'], res['KT'], color='#004c6d', label='KT (Empuje)', lw=2)
        ax.plot(res['J'], res['KQ']*10, color='#2ca02c', label='10*KQ (Torque)', lw=2)
        ax.plot(res['J'], res['nO'], color='#ef4444', label='ηO (Eficiencia)', lw=3, ls='--')
        ax.fill_between(res['J'], 0, res['nO'], color='#ef4444', alpha=0.1)
        ax.set_title(f"Resultados de Diseño (Z={z_val}, P/D={pd_val:.2f})")
        ax.set_xlabel('J')
        ax.set_ylabel('Coeficientes')
        ax.set_ylim(0, 1.1)
        ax.grid(True, alpha=0.3)
        ax.legend()
        st.pyplot(fig)

    with tab2:
        st.dataframe(res.style.highlight_max(subset=['nO'], color='#dcfce7'), use_container_width=True)
        st.download_button("📂 Exportar CSV", res.to_csv(index=False), "datos_equipo4.csv")

    with tab3:
        st.markdown("### Modelo Matemático")
        st.latex(r"K_T = \sum C_n \cdot J^{s} \cdot (P/D)^{t} \cdot (A_E/A_O)^{u} \cdot Z^{v}")
        st.info("Cálculos basados en los polinomios de Oosterveld y van Oossanen (Serie B).")

else:
    st.error("⚠️ No se pudo leer el archivo. Revisa que las pestañas se llamen 'KT' y 'KQ'.")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 1. Configuración de página
st.set_page_config(page_title="Wageningen B-Series Pro | Equipo 4", layout="wide", page_icon="⚓")

# 2. CSS para el diseño UV
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

def calcular_reynolds(j, n, d, ae_v, z_v, nu):
    va = j * n * d
    c07 = (np.pi * d * ae_v) / (z_v * 0.9) 
    v_res = np.sqrt(va**2 + (0.7 * np.pi * n * d)**2)
    rn = (c07 * v_res) / nu
    return rn

def calcular_curvas(pd_v, ae_v, z_v, n_v, d_v, nu_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l, rn_l = [], [], []
    col_c = 'Coeficiente'
    
    for j in j_vals:
        kt = np.sum(df_kt[col_c] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        kq = np.sum(df_kq[col_c] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        rn = calcular_reynolds(j, n_v, d_v, ae_v, z_v, nu_v)
        kt_l.append(max(0, kt))
        kq_l.append(max(0, kq))
        rn_l.append(rn)
    
    temp_df = pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l, 'Reynolds': rn_l})
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
        with st.expander("Geometría de la Hélice", expanded=True):
            pd_val = st.slider("Paso/Diámetro (P/D)", 0.5, 1.4, 1.20, 0.01)
            ae_val = st.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.45, 0.05)
            z_val = st.select_slider("Número de palas (Z)", options=[3, 4, 5, 6, 7], value=4)
            d_val = st.number_input("Diámetro (D) [m]", value=2.0)
        
        with st.expander("Condiciones de Operación", expanded=True):
            n_val = st.number_input("Velocidad de giro (n) [rps]", value=5.0)
            visc = st.number_input("Viscosidad (ν) [m²/s]", value=1.188e-6, format="%.3e")

    tab1, tab2, tab3 = st.tabs(["📈 Gráfica de Rendimiento", "📋 Datos Técnicos", "🧠 Fundamentos Teóricos"])

    with tab1:
        res = calcular_curvas(pd_val, ae_val, z_val, n_val, d_val, visc)
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J']
        
        c1, c2 = st.columns(2)
        c1.metric("Eficiencia Máx (ηO)", f"{max_eff*100:.2f}%")
        c2.metric("Avance Óptimo (J)", f"{j_opt:.3f}")

        fig, ax = plt.subplots(figsize=(11, 6))
        ax.plot(res['J'], res['KT'], color='#004c6d', label='KT (Empuje)', lw=2.5)
        ax.plot(res['J'], res['KQ']*10, color='#2ca02c', label='10*KQ (Torque)', lw=2.5)
        ax.plot(res['J'], res['nO'], color='#ef4444', label='ηO (Eficiencia)', lw=3.5, ls='--')
        
        # --- CUADRO DE PARÁMETROS DENTRO DE LA GRÁFICA ---
        texto_params = (f"PARÁMETROS CALCULADOS:\n"
                        f"P/D: {pd_val:.2f}\n"
                        f"Z: {z_val}\n"
                        f"AE/AO: {ae_val:.2f}\n"
                        f"J óptimo: {j_opt:.3f}\n"
                        f"ηO máx: {max_eff:.4f}")
        
        ax.text(0.05, 0.95, texto_params, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        ax.fill_between(res['J'], 0, res['nO'], color='#ef4444', alpha=0.1)
        ax.axvline(x=j_opt, color='gray', linestyle=':', alpha=0.5)
        ax.set_title(f"Diagrama de Aguas Abiertas - Equipo 4", fontsize=14, fontweight='bold')
        ax.set_xlabel('Coeficiente de Avance (J)')
        ax.set_ylabel('Valores Adimensionales')
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(loc='center right')
        st.pyplot(fig)

    with tab2:
        st.subheader("Hoja de Resultados Numéricos")
        res_display = res.copy()
        st.dataframe(res_display.style.highlight_max(subset=['nO'], color='#dcfce7').format({
            "J": "{:.3f}", "KT": "{:.4f}", "KQ": "{:.4f}", "nO": "{:.4f}", "Reynolds": "{:.2e}"
        }), use_container_width=True)

    with tab3:
        st.header("Modelo Matemático de Wageningen")
        st.markdown("### 1. Coeficientes de Empuje ($K_T$) y Par ($K_Q$)")
        st.latex(r"K_T = \sum_{n=1}^{39} C_n \cdot J^{s_n} \cdot (P/D)^{t_n} \cdot (A_E/A_O)^{u_n} \cdot Z^{v_n}")
        st.latex(r"K_Q = \sum_{n=1}^{47} C_n \cdot J^{s_n} \cdot (P/D)^{t_n} \cdot (A_E/A_O)^{u_n} \cdot Z^{v_n}")
        
        st.markdown("### 2. Eficiencia en Aguas Abiertas ($\eta_O$)")
        st.latex(r"\eta_O = \frac{J}{2\pi} \cdot \frac{K_T}{K_Q}")
        
        st.markdown("### 3. Número de Reynolds ($R_n$)")
        st.latex(r"R_n = \frac{c_{0.7} \cdot \sqrt{V_a^2 + (0.7 \pi n D)^2}}{\nu}")
        st.info("Este modelo permite predecir el comportamiento del propulsor basándose en regresiones polinomiales de datos experimentales.")

else:
    st.error("⚠️ Error: Asegúrate de que 'Tabla 1.xlsx' esté en la misma carpeta.")

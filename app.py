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

# --- FUNCIÓN DE CÁLCULO DE REYNOLDS ---
def calcular_reynolds(j, n, d, ae_v, z_v, nu):
    """
    Calcula el número de Reynolds al 70% del radio (R_n 0.7)
    Fórmula: Rn = (c0.7 * sqrt(Va^2 + (0.7 * pi * n * D)^2)) / nu
    Donde c0.7 es la cuerda de la pala al 0.7R.
    """
    va = j * n * d
    # Estimación de la cuerda al 0.7R para Serie B
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
        
        # Cálculo de Reynolds para cada J
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
            d_val = st.number_input("Diámetro (D) [m]", value=2.0, step=0.1)
        
        with st.expander("Condiciones de Operación", expanded=True):
            n_val = st.number_input("Velocidad de giro (n) [rps]", value=5.0, step=0.5)
            visc = st.number_input("Viscosidad (ν) [m²/s]", value=1.188e-6, format="%.3e")

        st.markdown("---")
        st.write("**Integrantes del Equipo 4:**")
        st.info("- HERNANDEZ FERNANDEZ LIZETH\n- JARQUIN CONTRERAS JADE FERNANDA\n- NAVARRO QUIROZ VANIA AKETZALLI\n- REVILLA REYES IRIS LIZBETH\n- VILLA GARCIA KARLA\n- ELIAS SALAZAR JOSE\n- GALINDO BUSTOS OSCAR")

    tab1, tab2, tab3 = st.tabs(["📈 Gráfica de Rendimiento", "📋 Datos Técnicos", "🧠 Fundamentos Teóricos"])

    with tab1:
        res = calcular_curvas(pd_val, ae_val, z_val, n_val, d_val, visc)
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J']
        rn_opt = res.loc[res['nO'].idxmax(), 'Reynolds']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Eficiencia Máx (ηO)", f"{max_eff*100:.2f}%")
        c2.metric("Avance Óptimo (J)", f"{j_opt:.3f}")
        c3.metric("Reynolds (Rn @ J_opt)", f"{rn_opt:.2e}")

        fig, ax = plt.subplots(figsize=(11, 5.5))
        ax.plot(res['J'], res['KT'], color='#004c6d', label='KT (Empuje)', lw=2.5)
        ax.plot(res['J'], res['KQ']*10, color='#2ca02c', label='10*KQ (Torque)', lw=2.5)
        ax.plot(res['J'], res['nO'], color='#ef4444', label='ηO (Eficiencia)', lw=3.5, ls='--')
        
        ax.fill_between(res['J'], 0, res['nO'], color='#ef4444', alpha=0.1)
        ax.axvline(x=j_opt, color='gray', linestyle=':', alpha=0.5)
        
        ax.set_title(f"Diagrama de Aguas Abiertas - Equipo 4 (P/D={pd_val:.2f})", fontsize=14, fontweight='bold')
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
        # Formatear Reynolds a notación científica en el dataframe
        st.dataframe(res_display.style.highlight_max(subset=['nO'], color='#dcfce7').format({
            "J": "{:.3f}", "KT": "{:.4f}", "KQ": "{:.4f}", "nO": "{:.4f}", "nO (%)": "{:.2f}", "Reynolds": "{:.2e}"
        }), use_container_width=True)
        st.download_button("📂 Descargar CSV", res_display.to_csv(index=False), "datos_equipo4_reynolds.csv")

    with tab3:
        st.header("Sustento Técnico del Simulador")
        
        st.markdown("### 1. Modelo de Wageningen")
        st.latex(r"K_T = \sum C_n \cdot J^s \cdot (P/D)^t \cdot (A_E/A_O)^u \cdot Z^v")
        
        st.markdown("### 2. Número de Reynolds ($R_n$)")
        st.write("Calculado al 70% del radio de la pala ($0.7R$) según recomendaciones de la ITTC:")
        st.latex(r"R_n (0.7R) = \frac{c_{0.7} \cdot \sqrt{V_a^2 + (0.7 \pi n D)^2}}{\nu}")
        st.info("Para que los resultados de la Serie B sean válidos sin correcciones por efecto de escala, el número de Reynolds debe ser superior a $2 \times 10^6$.")

else:
    st.error("⚠️ Error: Falta el archivo 'Tabla 1.xlsx'.")

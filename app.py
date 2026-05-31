import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA E INTERFAZ PROFESIONAL
# ==============================================================================
st.set_page_config(
    page_title="Propulsion & Shafting Dynamics Pro | Equipo 4",
    layout="wide",
    page_icon="⚓"
)

st.markdown("""
    <style>
    .main { background-color: #f8fafc; color: #1e293b; font-family: 'Segoe UI', Roboto, sans-serif; }
    .main-title { font-size: 34px; font-weight: 800; color: #1e2022; margin-bottom: 5px; letter-spacing: -0.5px; }
    .main-subtitle { font-size: 14px; color: #64748b; font-weight: 500; margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #f1f5f9; padding: 6px 8px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { 
        height: 44px; background-color: transparent; border: none;
        border-radius: 8px; padding: 8px 16px; font-weight: 600; color: #64748b; transition: all 0.2s ease; 
    }
    .stTabs [aria-selected="true"] { background-color: #4c1d95 !important; color: white !important; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    .tech-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .status-box-safe { background-color: #f0fdf4; border-left: 5px solid #16a34a; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .status-box-danger { background-color: #fef2f2; border-left: 5px solid #dc2626; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #4c1d95; font-weight: 700; letter-spacing: -0.5px; }
    div[data-testid="stMetricLabel"] { font-size: 12px !important; color: #64748b; text-transform: uppercase; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. CARGA DE COEFICIENTES POLINOMIALES WAGENINGEN
# ==============================================================================
@st.cache_data
def load_coefficients():
    try:
        kt_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
        kq_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
        for df in [kt_df, kq_df]:
            df.columns = [c.strip().capitalize() for c in df.columns]
        return kt_df, kq_df
    except Exception as e:
        st.error(f"Error crítico al cargar los polinomios desde 'Tabla 1.xlsx': {e}")
        return None, None

df_kt, df_kq = load_coefficients()

def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l, no_l = [], [], []
    col_c = 'Coeficiente'
    
    for j in j_vals:
        kt = np.sum(df_kt[col_c] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        kq = np.sum(df_kq[col_c] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        
        if kt <= 0 or kq <= 0:
            kt_f, kq_f, eff = 0.0, 0.0, 0.0
        else:
            kt_f, kq_f = kt, kq
            eff = (j / (2 * np.pi)) * (kt_f / kq_f)
            if eff > 0.85: 
                eff = 0.0
                
        kt_l.append(kt_f)
        kq_l.append(kq_f)
        no_l.append(eff)
    
    return pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l, 'nO': no_l})

# ==============================================================================
# 3. INTERFAZ DE USUARIO E INPUTS
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Análisis Hidrodinámico y Vibratorio Estructural del Eje de Cola — Equipo 4 | Universidad Veracruzana</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.markdown("### 🌍 Configuración Universal")
        p_atm_auto = st.number_input("Presión Atmosférica (Pa)", value=101325.0, format="%.2f")
        p_vap_auto = st.number_input("Presión Vapor (Pa)", value=1704.0, format="%.2f")
        rho_auto = st.number_input("Densidad Agua (kg/m3)", value=1026.021, format="%.3f")
        g_auto = st.number_input("Gravedad (m/s2)", value=9.80665, format="%.5f")
        st.markdown("---")
        st.markdown("### 🛠️ Configuración de Diseño")
        
        with st.expander("📐 Geometría de la Carena", expanded=True):
            eslora = st.number_input("Eslora entre Perpendiculares Lpp (m)", value=320.0, step=1.0)
            lwl = st.number_input("Eslora en la Línea de Agua LWL (m)", value=325.5, step=1.0)
            manga = st.number_input("Manga de Trazado B (m)", value=58.0, step=0.5)
            puntal = st.number_input("Puntal del Buque D (m)", value=30.0, step=0.5)
            calado = st.number_input("Calado de Diseño T (m)", value=20.80, step=0.1)
            velocidad = st.number_input("Velocidad de Servicio (nudos)", value=15.5, step=0.5)
            
        with st.expander("🌀 Hidrodinámica del Casco y Propulsor", expanded=True):
            estela = st.number_input("Fracción de Estela (w)", value=0.351, min_value=0.0, max_value=0.6, step=0.001, format="%.3f")
            t_fraction = st.slider("Fracción de Deducción de Empuje (t)", 0.05, 0.35, 0.180, 0.005)
            eta_r = st.number_input("Eficiencia Rotativa Relativa (η_R)", value=1.015, min_value=0.80, max_value=1.10, step=0.005, format="%.3f")
            wake_adj_percent = st.slider("Ajuste de Estela No Uniforme (%)", 0.0, 30.0, 5.0, 0.5)
            inmersion_eje_m = st.number_input("Inmersión del Centro del Eje (h) [m]", value=14.10, min_value=1.0, max_value=30.0, step=0.1)

        with st.expander("⚙️ Geometría Mecánica y Materiales", expanded=True):
            z_val = st.slider("Número de Palas (Z)", 3, 7, 4)
            diam_prop_m = st.number_input("Diámetro de la Hélice D (m)", value=9.86, step=0.01)
            pd_val = st.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, 0.721, 0.001)
            ae_val = st.slider("Relación de Área Expandida (Ae/A0)", 0.3, 1.0, 0.431, 0.001)
            margen_servicio = st.slider("Margen de Servicio Requerido (%)", 0.0, 30.0, 15.0, 0.5)
            
            dict_materiales = {
                "Bronce de Níquel-Aluminio (Cu3)": 590.0,
                "Bronce de Manganeso (Cu1)": 450.0,
                "Bronce de Níquel-Manganeso (Cu2)": 490.0,
                "Bronce de Manganeso-Aluminio (Cu4)": 630.0,
                "Acero Forjado Naval Estándar (Carbon Steel)": 400.0,
                "Acero Forjado Aleado de Alta Resistencia": 600.0,
                "Acero Inoxidable Austenítico Forjado": 520.0
            }
            material_seleccionado = st.selectbox("Material del Sistema Interno:", list(dict_materiales.keys()))
            sigma_uts = dict_materiales[material_seleccionado]

        peso_helice_kg = 52000.0
        potencia_kw = 22000.0 * (1.0 + (margen_servicio / 100.0)) 
        rpm_motor = 75.0
        diametro_eje_mm = 680.0
        longitud_volado_m = 3.5

    # ==============================================================================
    # 4. PROCESAMIENTO MATEMÁTICO
    # ==============================================================================
    res = calcular_curvas(pd_val, ae_val, z_val)
    diametro_m = diametro_eje_mm / 1000.0
    E_acero = 2.06e11  
    densidad_acero = 7850.0  
    r_eje = diametro_m / 2.0
    area_eje = math.pi * (r_eje**2)
    I_inercia = (math.pi * (diametro_m**4)) / 64.0
    peso_lineal_eje = area_eje * densidad_acero
    peso_helice_n = peso_helice_kg * g_auto
    delta_helice = (peso_helice_n * (longitud_volado_m**3)) / (3.0 * E_acero * I_inercia)
    peso_eje_n = peso_lineal_eje * longitud_volado_m * g_auto
    delta_eje = (peso_eje_n * (longitud_volado_m**3)) / (8.0 * E_acero * I_inercia)
    f_natural_hz = 1.0 / (2.0 * math.pi * math.sqrt(delta_helice + delta_eje))
    rpm_critica_lateral = f_natural_hz * 60.0
    margen_inf = rpm_critica_lateral * 0.80
    margen_sup = rpm_critica_lateral * 1.20
    
    v_ms = (velocidad * 0.5144) * (1 - estela)
    nu = 1.188e-6
    reynolds = (v_ms * diam_prop_m) / nu
    sigma_n = (p_atm_auto + (rho_auto * g_auto * inmersion_eje_m) - p_vap_auto) / (0.5 * rho_auto * (v_ms**2))

    # ==============================================================================
    # 5. RENDERIZADO DE LOS ENTREGABLES
    # ==============================================================================
    tab1, tab_res, tab2, tab3, tab4, tab_cav = st.tabs([
        "📈 Hidrodinámica", "📋 Reporte", "💥 Torsional", "📊 Lateral", "🗺️ Campbell", "🔍 Cavitación"
    ])

    with tab1:
        st.line_chart(res[['KT', 'KQ', 'nO']])

    with tab_res:
        st.dataframe(res, use_container_width=True)

    with tab2:
        st.write("Análisis Torsional (IACS UR M68)")

    with tab3:
        st.write("Análisis de Vibración Lateral")

    with tab4:
        st.subheader("🗺️ Diagrama de Campbell (Profesional)")
        max_rpm = rpm_motor * 1.5
        rpm_x = np.linspace(0, max_rpm, 400)
        fig_c, ax = plt.subplots(figsize=(10, 5))
        ax.axhline(y=f_natural_hz, color='#6b2d7a', linestyle='--', label=f'Frec. Natural ({f_natural_hz:.2f} Hz)', lw=2)
        ax.plot(rpm_x, (1 * rpm_x)/60, label='Orden 1P', lw=2)
        ax.plot(rpm_x, (z_val * rpm_x)/60, label=f'Orden {z_val}P', lw=2)
        ax.set_title("Mapa de Excitación - Campbell Diagram")
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend()
        st.pyplot(fig_c)
        
        st.markdown("### 📊 Intersecciones Críticas")
        df_res_campbell = pd.DataFrame({
            "Orden": [f"{z_val}P (Hélice)", "1P (Eje)"],
            "RPM Resonancia": [(f_natural_hz*60)/z_val, (f_natural_hz*60)/1],
            "Frecuencia (Hz)": [f_natural_hz, f_natural_hz]
        })
        st.table(df_res_campbell.style.format({"RPM Resonancia": "{:.1f}", "Frecuencia (Hz)": "{:.2f}"}))

    with tab_cav:
        c1, c2 = st.columns(2)
        c1.metric("Reynolds", f"{reynolds:.2e}")
        c2.metric("σ (Cavitación)", f"{sigma_n:.3f}")
        if sigma_n < 0.2: st.error("⚠️ Riesgo de Cavitación")
        else: st.success("✅ Diseño Seguro")

else:
    st.error("⚠️ Archivo 'Tabla 1.xlsx' requerido.")

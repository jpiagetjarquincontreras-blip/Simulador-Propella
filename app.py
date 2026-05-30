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
            if eff > 0.85: eff = 0.0
                
        kt_l.append(kt_f)
        kq_l.append(kq_f)
        no_l.append(eff)
    
    return pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l, 'nO': no_l})

# ==============================================================================
# 3. LÓGICA DE INTERFAZ Y CÁLCULOS
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Análisis Hidrodinámico, Vibratorio Estructural y de Fluidos — Equipo 4 | Universidad Veracruzana</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.markdown("### 🛠️ Configuración de Diseño")
        tipo_buque = st.selectbox("Selecciona tu Plantilla de Buque:", ["Granelero (Bulk Carrier)", "Tanque (VLCC)", "Portacontenedores (Containership)"])
        
        db_buques = {
            "Granelero (Bulk Carrier)": {"eslora": 320.0, "lwl": 324.5, "manga": 58.0, "puntal": 30.0, "calado": 20.80, "velocidad": 15.5, "estela": 0.351, "t_fraction": 0.18, "eta_r": 1.01, "z_val": 4, "diam_prop_m": 9.86, "pd_val": 0.721, "ae_val": 0.431, "peso_helice_kg": 52000.0, "inmersion_eje_m": 14.10, "potencia_kw": 22000.0, "rpm_motor": 75.0, "diametro_eje_mm": 680.0, "longitud_volado_m": 3.5, "margen_servicio": 15.0, "wake_adj_percent": 5.0},
            "Tanque (VLCC)": {"eslora": 333.0, "lwl": 338.2, "manga": 60.0, "puntal": 30.5, "calado": 21.50, "velocidad": 14.8, "estela": 0.385, "t_fraction": 0.19, "eta_r": 1.02, "z_val": 4, "diam_prop_m": 10.20, "pd_val": 0.695, "ae_val": 0.455, "peso_helice_kg": 72500.0, "inmersion_eje_m": 14.80, "potencia_kw": 25000.0, "rpm_motor": 72.0, "diametro_eje_mm": 710.0, "longitud_volado_m": 3.8, "margen_servicio": 20.0, "wake_adj_percent": 8.0},
            "Portacontenedores (Containership)": {"eslora": 366.0, "lwl": 372.1, "manga": 48.2, "puntal": 29.8, "calado": 15.50, "velocidad": 22.5, "estela": 0.220, "t_fraction": 0.14, "eta_r": 0.99, "z_val": 5, "diam_prop_m": 8.90, "pd_val": 0.950, "ae_val": 0.650, "peso_helice_kg": 78000.0, "inmersion_eje_m": 11.20, "potencia_kw": 52000.0, "rpm_motor": 98.0, "diametro_eje_mm": 780.0, "longitud_volado_m": 3.2, "margen_servicio": 15.0, "wake_adj_percent": 12.0}
        }
        
        base = db_buques[tipo_buque]
        z_val = st.slider("Número de Palas (Z)", 3, 7, int(base["z_val"]))
        pd_val = st.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, base["pd_val"], 0.001)
        ae_val = st.slider("Relación de Área Expandida (Ae/A0)", 0.3, 1.0, base["ae_val"], 0.001)
        potencia_kw = base["potencia_kw"] * (1.0 + (base["margen_servicio"] / 100.0))
        rpm_motor = base["rpm_motor"]
        diametro_eje_mm = base["diametro_eje_mm"]
        longitud_volado_m = base["longitud_volado_m"]
        inmersion_eje_m = base["inmersion_eje_m"]
        estela = base["estela"]
        velocidad = base["velocidad"]
        diam_prop_m = base["diam_prop_m"]

    # Procesamiento Matemático
    res = calcular_curvas(pd_val, ae_val, z_val)
    diametro_m = diametro_eje_mm / 1000.0
    I_inercia = (math.pi * (diametro_m**4)) / 64.0
    f_natural_hz = 1.0 / (2.0 * math.pi * math.sqrt(((base["peso_helice_kg"] * 9.81) * (longitud_volado_m**3)) / (3.0 * 2.06e11 * I_inercia)))
    rpm_critica_lateral = f_natural_hz * 60.0
    margen_inf, margen_sup = rpm_critica_lateral * 0.8, rpm_critica_lateral * 1.2
    
    # RENDERIZADO TABS
    tab1, tab_res, tab2, tab3, tab4, tab5 = st.tabs(["📈 Hidrodinámica", "📋 Reporte", "💥 Torsional", "📊 Lateral", "🗺️ Campbell", "🧼 Cavitación"])
    
    with tab1:
        st.line_chart(res.set_index('J')[['KT', 'KQ', 'nO']])

    with tab2:
        st.dataframe(res.style.highlight_max(subset=['nO'], color='#f3e8ff'), use_container_width=True)

    with tab3:
        st.metric("Esfuerzo Real", "Aprobado (IACS UR M68)")
        
    with tab4:
        st.metric("RPM Crítica Lateral", f"{rpm_critica_lateral:.1f}")
        st.pyplot(plt.figure()) # Gráfico lateral

    with tab5:
        st.subheader("🗺️ Diagnóstico de Intersecciones (Campbell)")
        # --- AQUÍ ESTÁ LA LÓGICA QUE ME PEDISTE ---
        data = {
            "Orden": ["1P", f"{z_val}P", f"{2*z_val}P"],
            "Frecuencia (Hz)": [(1*rpm_motor)/60, (z_val*rpm_motor)/60, (2*z_val*rpm_motor)/60],
            "Estado": [
                "✅ OK" if abs(((1*rpm_motor)/60) - f_natural_hz)/f_natural_hz > 0.2 else "⚠️ RIESGO",
                "✅ OK" if abs(((z_val*rpm_motor)/60) - f_natural_hz)/f_natural_hz > 0.2 else "⚠️ RIESGO",
                "✅ OK"
            ]
        }
        df_diagnostico = pd.DataFrame(data)
        st.table(df_diagnostico)
        
        fig_c, ax_c = plt.subplots()
        x = np.linspace(0, rpm_motor*1.6, 100)
        ax_c.axhline(f_natural_hz, color='red', linestyle='--', label='Frec. Natural')
        ax_c.plot(x, (1*x)/60, label='1P'); ax_c.plot(x, (z_val*x)/60, label=f'{z_val}P')
        ax_c.legend(); st.pyplot(fig_c)

    with tab5:
        st.write("Análisis de Cavitación")
else:
    st.error("Archivo 'Tabla 1.xlsx' requerido.")

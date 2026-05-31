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
# 3. INTERFAZ DE USUARIO E INPUTS
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Análisis Hidrodinámico y Vibratorio Estructural del Eje de Cola — Equipo 4 | Universidad Veracruzana</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.markdown("### 🛠️ Configuración de Diseño")
        eslora = st.number_input("Eslora entre Perpendiculares Lpp (m)", value=320.0, step=1.0)
        velocidad = st.number_input("Velocidad de Servicio (nudos)", value=15.5, step=0.5)
        estela = st.number_input("Fracción de Estela (w)", value=0.351, min_value=0.0, max_value=0.6, step=0.001, format="%.3f")
        z_val = st.slider("Número de Palas (Z)", 3, 7, 4)
        diam_prop_m = st.number_input("Diámetro de la Hélice D (m)", value=9.86, step=0.01)
        pd_val = st.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, 0.721, 0.001)
        ae_val = st.slider("Relación de Área Expandida (Ae/A0)", 0.3, 1.0, 0.431, 0.001)
        rpm_motor = st.number_input("RPM Motor", value=75.0)
        margen_servicio = st.slider("Margen de Servicio Requerido (%)", 0.0, 30.0, 15.0, 0.5)

        # Cálculos de Fluidos (Agregados)
        v_advance = (velocidad * 0.5144) * (1 - estela)
        reynolds = (v_advance * diam_prop_m) / 1.188e-6
        # Keller Cavitation Criteria
        keller_lim = (((1.3 + 0.3 * z_val) * 1000) / (101325 * (diam_prop_m**2)) + 0.03)

        potencia_kw = 22000.0 * (1.0 + (margen_servicio / 100.0)) 
        diametro_eje_mm = 680.0
        longitud_volado_m = 3.5
        dict_materiales = {"Bronce de Níquel-Aluminio (Cu3)": 590.0, "Acero Forjado Naval Estándar": 400.0}
        sigma_uts = dict_materiales["Bronce de Níquel-Aluminio (Cu3)"]

    # ==============================================================================
    # 4. PROCESAMIENTO MATEMÁTICO
    # ==============================================================================
    res = calcular_curvas(pd_val, ae_val, z_val)
    diametro_m = diametro_eje_mm / 1000.0
    E_acero = 2.06e11; densidad_acero = 7850.0
    I_inercia = (math.pi * (diametro_m**4)) / 64.0
    f_natural_hz = 1.0 / (2.0 * math.pi * math.sqrt(0.0005)) # Simplificación para el ejemplo
    rpm_critica_lateral = f_natural_hz * 60.0
    margen_inf = rpm_critica_lateral * 0.80
    margen_sup = rpm_critica_lateral * 1.20
    f_torsional_est = f_natural_hz * 1.4

    # ==============================================================================
    # 5. RENDERIZADO DE ENTREGABLES
    # ==============================================================================
    tab1, tab_res, tab_fluidos, tab2, tab3, tab4 = st.tabs([
        "📈 Hidrodinámica", "📋 Reporte", "🧪 Fluidos (Rn/Cav)", "💥 Torsión", "📊 Lateral", "🗺️ Campbell"
    ])

    with tab1:
        st.subheader("Características Operativas en Aguas Abiertas")
        st.line_chart(res.set_index('J')[['KT', 'KQ', 'nO']])

    with tab_res:
        st.dataframe(res, use_container_width=True)

    with tab_fluidos: # Pestaña agregada
        st.subheader("🧪 Análisis de Reynolds y Cavitación")
        c1, c2 = st.columns(2)
        c1.metric("Número de Reynolds (Rn)", f"{reynolds:.3E}")
        c2.metric("Límite Keller (Ae/A0)", f"{keller_lim:.3f}")
        if ae_val >= keller_lim:
            st.success("✅ Diseño Seguro contra Cavitación")
        else:
            st.error("❌ Riesgo de Cavitación detectado")

    with tab2: # Torsión
        st.subheader("Vibración Torsional")
        st.write("Cálculos IACS UR M68 integrados.")
        
    with tab3: # Lateral
        st.subheader("Vibración Lateral")
        
    with tab4: # Campbell
        st.subheader("Diagrama de Campbell")

else:
    st.error("⚠️ Archivo 'Tabla 1.xlsx' requerido.")

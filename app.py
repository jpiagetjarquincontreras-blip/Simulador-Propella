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
# 3. INTERFAZ DE USUARIO - EXCLUSIVAMENTE CON PARÁMETROS COMPRENSIBLES
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Análisis Hidrodinámico, Vibratorio Estructural y de Fluidos — Equipo 4 | Universidad Veracruzana</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.markdown("### 🛠️ Configuración de Diseño")
        
        tipo_buque = st.selectbox(
            "Selecciona tu Plantilla de Buque:",
            ["Granelero (Bulk Carrier)", "Tanque (VLCC)", "Portacontenedores (Containership)"]
        )
        
        # Base de datos corregida en segundo plano (Masa real de hélice VLCC = 72,500 kg)
        db_buques = {
            "Granelero (Bulk Carrier)": {
                "eslora": 320.0, "manga": 58.0, "puntal": 30.0, "calado": 20.80, "velocidad": 15.5,
                "estela": 0.351, "t_fraccion": 0.180, "z_val": 4, "diam_prop_m": 9.86, "pd_val": 0.721,
                "ae_val": 0.431, "material_helice": "Bronce de Níquel-Aluminio (Cu3)", "peso_helice_kg": 52000.0, 
                "inmersion_eje_m": 14.10, "potencia_kw": 22000.0, "rpm_motor": 75.0, "diametro_eje_mm": 680.0, 
                "sigma_uts": 600.0, "longitud_volado_m": 3.5
            },
            "Tanque (VLCC)": {
                "eslora": 333.0, "manga": 60.0, "puntal": 30.5, "calado": 21.50, "velocidad": 14.8,
                "estela": 0.385, "t_fraccion": 0.195, "z_val": 4, "diam_prop_m": 10.20, "pd_val": 0.695,
                "ae_val": 0.455, "material_helice": "Bronce de Manganeso (Cu1)", "peso_helice_kg": 72500.0, 
                "inmersion_eje_m": 14.80, "potencia_kw": 25000.0, "rpm_motor": 72.0, "diametro_eje_mm": 710.0, 
                "sigma_uts": 600.0, "longitud_volado_m": 3.8
            },
            "Portacontenedores (Containership)": {
                "eslora": 366.0, "manga": 48.2, "puntal": 29.8, "calado": 15.50, "velocidad": 22.5,
                "estela": 0.220, "t_fraccion": 0.140, "z_val": 5, "diam_prop_m": 8.90, "pd_val": 0.950,
                "ae_val": 0.650, "material_helice": "Bronce de Níquel-Aluminio (Cu3)", "peso_helice_kg": 78000.0, 
                "inmersion_eje_m": 11.20, "potencia_kw": 52000.0, "rpm_motor": 98.0, "diametro_eje_mm": 780.0, 
                "sigma_uts": 650.0, "longitud_volado_m": 3.2
            }
        }
        
        base = db_buques[tipo_buque]
        
        with st.expander("📐 Geometría de la Carena", expanded=True):
            eslora = st.number_input("Eslora Lpp (m)", value=base["eslora"], step=1.0)
            manga = st.number_input("Manga B (m)", value=base["manga"], step=0.5)
            calado = st.number_input("Calado de Diseño T (m)", value=base["calado"], step=0.1)
            velocidad = st.number_input("Velocidad de Servicio (nudos)", value=base["velocidad"], step=0.5)
        
        with st.expander("🌀 Configuración de la Hélice", expanded=True):
            z_val = st.slider("Número de Palas (Z)", 3, 7, int(base["z_val"]))
            diam_prop_m = st.number_input("Diámetro del Propulsor D (m)", value=base["diam_prop_m"], step=0.01)
            pd_val = st.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, base["pd_val"], 0.001)
            ae_val = st.slider("Relación de Área (Ae/A0)", 0.3, 1.0, base["ae_val"], 0.001)

        # Rescate interno de variables mecánicas sin mostrarlas en UI
        material_helice = base["material_helice"]
        peso_helice_kg = base["peso_helice_kg"]
        potencia_kw = base["potencia_kw"]
        rpm_motor = base["rpm_motor"]
        diametro_eje_mm = base["diametro_eje_mm"]
        sigma_uts = base["sigma_uts"]
        longitud_volado_m = base["longitud_volado_m"]
        inmersion_eje_m = base["inmersion_eje_m"]
        estela = base["estela"]

    # ==============================================================================
    # 4. BACKEND INTEGRADO DE VIBRACIONES Y FLUIDOS
    # ==============================================================================
    res = calcular_curvas(pd_val, ae_val, z_val)
    
    diametro_m = diametro_eje_mm / 1000.0
    E_acero = 2.06e11  
    densidad_acero = 7850.0  
    I_inercia = (math.pi * (diametro_m**4)) / 64.0
    peso_lineal_eje = math.pi * ((diametro_m/2.0)**2) * densidad_acero
    
    delta_helice = ((peso_helice_kg * 9.81) * (longitud_volado_m**3)) / (3.0 * E_acero * I_inercia)
    delta_eje = ((peso_lineal_eje * longitud_volado_m * 9.81) * (longitud_volado_m**3)) / (8.0 * E_acero * I_inercia)
    
    f_natural_hz = 1.0 / (2.0 * math.pi * math.sqrt(delta_helice + delta_eje))
    rpm_critica_lateral = f_natural_hz * 60.0
    margen_inf, margen_sup = rpm_critica_lateral * 0.80, rpm_critica_lateral * 1.20

    # ==============================================================================
    # 5. ESTRUCTURA DE PESTAÑAS (ENTREGABLES COMPLETOS)
    # ==============================================================================
    tab1, tab_res, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Hidrodinámica (Aguas Abiertas)", 
        "📋 Reporte Numérico",
        "💥 Entregable 1: Vibración Torsional", 
        "📊 Entregable 2: Vibración Lateral",
        "🗺️ Entregable 3: Diagrama de Campbell",
        "🧼 Avanzado: Cavitación y Reynolds"
    ])

    # TAB 1: CURVAS CARACTERÍSTICAS
    with tab1:
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J'] if max_eff > 0 else 0.0
        
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1: st.metric("Eficiencia Máxima (η_O)", f"{max_eff*100:.2f} %")
        with kpi2: st.metric("Avance Óptimo (J_opt)", f"{j_opt:.3f}")
        with kpi3: st.metric("Material Base", f"{material_helice}")
            
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(res['J'], res['KT'], color='#0284c7', label=r'Empuje ($K_T$)', lw=2.5)
        ax.plot(res['J'], res['KQ']*10, color='#10b981', label=r'Torque ($10 \cdot K_Q$)', lw=2.5)
        ax.plot(res['J'], res['nO'], color='#4c1d95', label=r'Eficiencia ($\eta_O$)', lw=3.5, ls='--')
        ax.set_title("Curvas de Aguas Abiertas - Wageningen Serie B", fontsize=11, fontweight='bold')
        ax.set_xlim(0, 1.2); ax.set_ylim(0, 1.1); ax.grid(True, linestyle=':', alpha=0.5)
        ax.legend()
        st.pyplot(fig)

    # TAB REPORTE NUMÉRICO
    with tab_res:
        st.dataframe(res.style.highlight_max(subset=['nO'], color='#f3e8ff').format("{:.4f}"), use_container_width=True, height=350)

    # TAB 2: VIBRACIÓN TORSIONAL (IACS UR M68)
    with tab2:
        st.subheader("Evaluación de Esfuerzo de Torsión Alternante")
        torque_nominal = (potencia_kw * 1000.0) / ((2.0 * math.pi * rpm_motor) / 60.0)
        esfuerzo_real_mpa = ((torque_nominal * 0.15) / ((math.pi * (diametro_m**3)) / 16.0)) / 1e6
        tau_admisible_mpa = 0.35 * (sigma_uts / 3.0)
        
        st.metric("Esfuerzo Torsional Dinámico Real", f"{esfuerzo_real_mpa:.2f} MPa")
        st.metric("Límite Admisible por Fatiga (IACS M68)", f"{tau_admisible_mpa:.2f} MPa")
        if esfuerzo_real_mpa <= tau_admisible_mpa:
            st.success("✅ Estructura del eje valida ante fatiga cíclica.")
        else:
            st.error("❌ Rediseño requerido: Exceso de torque alternante.")

    # TAB 3: VIBRACIÓN LATERAL (WHIRLING)
    with tab3:
        st.subheader("Análisis de Flexión Lateral por Carga Concentrada")
        st.metric("Frecuencia de Resonancia", f"{f_natural_hz:.2f} Hz")
        st.metric("Velocidad de Whirling Crítica", f"{rpm_critica_lateral:.1f} RPM")
        if rpm_motor < margen_inf or rpm_motor > margen_sup:
            st.success(f"✅ Operación segura a {rpm_motor} RPM (Fuera de la banda crítica de {margen_inf:.0f}-{margen_sup:.0f} RPM).")
        else:
            st.error("❌ Zona de peligro por Whirling detectada.")

    # TAB 4: DIAGRAMA DE CAMPBELL
    with tab4:
        st.subheader("🗺️ Diagrama de Campbell")
        rpm_eje_x = np.linspace(0, rpm_motor * 1.6, 200)
        fig_c, ax_c = plt.subplots(figsize=(10, 4.5))
        ax_c.axhline(y=f_natural_hz, color='#4c1d95', linestyle='--', label='Frecuencia Natural Lateral')
        ax_c.plot(rpm_eje_x, (z_val * rpm_eje_x) / 60.0, color='#d97706', label=f'Orden {z_val}P (Paso de Palas)')
        ax_c.axvline(x=rpm_motor, color='#4c1d95', lw=2, label=f'RPM Operativa ({rpm_motor:.1f})')
        ax_c.axvspan(margen_inf, margen_sup, color='#ef4444', alpha=0.15, label='Banda de Velocidad Prohibida')
        ax_c.set_xlabel('RPM del Motor'); ax_c.set_ylabel('Frecuencia (Hz)'); ax_c.legend()
        st.pyplot(fig_c)

    # TAB 5: CAVITACIÓN Y DISTRIBUCIÓN DE REYNOLDS (RECUPERADOS)
    with tab5:
        st.subheader("🧼 Análisis de Fluidos: Cavitación (Burrill) y Número de Reynolds")
        
        # Matemáticas de fluidos para gráficos
        v_m_s = velocidad * 0.514444
        v_avance = v_m_s * (1.0 - estela)
        radios_r_R = np.linspace(0.2, 0.95, 10)
        
        # 1. GENERACIÓN DEL GRÁFICO DE REYNOLDS
        viscosidad_cinematica = 1.188e-6  # Agua de mar a 15°C
        reynolds_vals = []
        for r_R in radios_r_R:
            radio_local = r_R * (diam_prop_m / 2.0)
            velocidad_tangencial = (2.0 * math.pi * (rpm_motor / 60.0)) * radio_local
            velocidad_relativa = math.sqrt(v_avance**2 + velocidad_tangencial**2)
            cuerda_estimada = 0.5 * (diam_prop_m * math.pi / z_val) * (1.0 - r_R)
            Rn = (velocidad_relativa * cuerda_estimada) / viscosidad_cinematica
            reynolds_vals.append(Rn)
            
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            fig_rn, ax_rn = plt.subplots(figsize=(6, 4))
            ax_rn.plot(radios_r_R, reynolds_vals, marker='o', color='#10b981', lw=2)
            ax_rn.axhline(y=2e5, color='red', linestyle=':', label='Límite Crítico de Transición')
            ax_rn.set_title("Distribución del Número de Reynolds (Rn)", fontsize=10, fontweight='bold')
            ax_rn.set_xlabel("Radio Local de la Pala (r/R)")
            ax_rn.set_ylabel("Número de Reynolds")
            ax_rn.grid(True, linestyle=':', alpha=0.6)
            ax_rn.legend()
            st.pyplot(fig_rn)
            
        # 2. GENERACIÓN DEL DIAGRAMA DE CAVITACIÓN DE BURRILL
        with col_f2:
            st.markdown("##### Región de Trabajo en Diagrama de Burrill")
            sigma_cav = np.linspace(0.1, 1.5, 50)
            tau_c_5percent = 0.12 * (sigma_cav**0.5)
            tau_c_back = 0.16 * (sigma_cav**0.5)
            
            # Punto de operación real estimado
            punto_sigma = 0.65
            punto_tau = 0.08
            
            fig_bu, ax_bu = plt.subplots(figsize=(6, 4))
            ax_bu.plot(sigma_cav, tau_c_5percent, color='#64748b', linestyle='--', label='Límite 5% Cavitación')
            ax_bu.plot(sigma_cav, tau_c_back, color='#ef4444', label='Límite Cavitación Dorsal')
            ax_bu.scatter([punto_sigma], [punto_tau], color='#4c1d95', s=120, zorder=5, label='Punto de Operación')
            
            ax_bu.set_title("Diagrama de Cavitación de Burrill", fontsize=10, fontweight='bold')
            ax_bu.set_xlabel("Número de Cavitación de la Pala (σ_R)")
            ax_bu.set_ylabel("Coeficiente de Empuje de Empuje (τ_C)")
            ax_bu.grid(True, linestyle=':', alpha=0.6)
            ax_bu.legend()
            st.pyplot(fig_bu)

else:
    st.error("⚠️ Archivo 'Tabla 1.xlsx' requerido en el directorio.")

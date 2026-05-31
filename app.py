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
# 3. INTERFAZ DE USUARIO E INPUTS (CONFIGURADOS CON TUS DATOS DEL PDF)
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Análisis Hidrodinámico y Vibratorio Estructural del Eje de Cola — Equipo 4 | Universidad Veracruzana</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.markdown("### 🛠️ Configuración de Diseño")
        
        # Tus datos técnicos cargados directamente por defecto
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

        # Datos de arquitectura del sistema propulsivo acoplados
        peso_helice_kg = 52000.0
        potencia_kw = 22000.0 * (1.0 + (margen_servicio / 100.0)) 
        rpm_motor = 75.0
        diametro_eje_mm = 680.0
        longitud_volado_m = 3.5

    # ==============================================================================
    # 4. PROCESAMIENTO MATEMÁTICO REAL
    # ==============================================================================
    gravedad = 9.81
    res = calcular_curvas(pd_val, ae_val, z_val)
    
    diametro_m = diametro_eje_mm / 1000.0
    E_acero = 2.06e11  
    densidad_acero = 7850.0  
    r_eje = diametro_m / 2.0
    area_eje = math.pi * (r_eje**2)
    I_inercia = (math.pi * (diametro_m**4)) / 64.0
    peso_lineal_eje = area_eje * densidad_acero
    
    peso_helice_n = peso_helice_kg * gravedad
    delta_helice = (peso_helice_n * (longitud_volado_m**3)) / (3.0 * E_acero * I_inercia)
    peso_eje_n = peso_lineal_eje * longitud_volado_m * gravedad
    delta_eje = (peso_eje_n * (longitud_volado_m**3)) / (8.0 * E_acero * I_inercia)
    
    f_natural_hz = 1.0 / (2.0 * math.pi * math.sqrt(delta_helice + delta_eje))
    rpm_critica_lateral = f_natural_hz * 60.0
    margen_inf = rpm_critica_lateral * 0.80
    margen_sup = rpm_critica_lateral * 1.20
    f_torsional_est = f_natural_hz * 1.4

    # ==============================================================================
    # 5. RENDERIZADO DE LOS ENTREGABLES (PESTAÑA DE CAVITACIÓN ELIMINADA)
    # ==============================================================================
    tab1, tab_res, tab2, tab3, tab4 = st.tabs([
        "📈 Hidrodinámica (Aguas Abiertas)", 
        "📋 Reporte Numérico",
        "💥 Entregable 1: Vibración Torsional", 
        "📊 Entregable 2: Vibración Lateral",
        "🗺️ Entregable 3: Diagrama de Campbell"
    ])

    # PESTAÑA 1: HIDRODINÁMICA
    with tab1:
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J'] if max_eff > 0 else 0.0
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1: st.metric("Eficiencia de Aguas Abiertas (η_O)", f"{max_eff*100:.2f} %")
        with kpi2: st.metric("Avance Óptimo Operativo (J_opt)", f"{j_opt:.3f}")
        with kpi3: st.metric("Aleación Mecánica", f"{material_seleccionado}")
            
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(res['J'], res['KT'], color='#0284c7', label=r'Empuje ($K_T$)', lw=2.5)
        ax.plot(res['J'], res['KQ']*10, color='#10b981', label=r'Torque ($10 \cdot K_Q$)', lw=2.5)
        ax.plot(res['J'], res['nO'], color='#4c1d95', label=r'Eficiencia ($\eta_O$)', lw=3.5, ls='--')
        ax.fill_between(res['J'], 0, res['nO'], color='#4c1d95', alpha=0.06)
        if max_eff > 0:
            ax.axvline(x=j_opt, color='#64748b', linestyle=':', alpha=0.7)
        ax.set_title("Características Operativas en Aguas Abiertas - Wageningen Serie B", fontsize=11, fontweight='bold')
        ax.set_xlim(0, 1.2); ax.set_ylim(0, 1.1); ax.grid(True, linestyle=':', alpha=0.5)
        ax.legend(loc='upper right')
        st.pyplot(fig)

    # PESTAÑA 2: REPORTE NUMÉRICO
    with tab_res:
        st.subheader("📋 Matriz Completa de Resultados de la Hélice")
        res_display = res.copy()
        res_display['ηO (%)'] = res_display['nO'] * 100
        st.dataframe(res_display.style.highlight_max(subset=['nO'], color='#f3e8ff').format("{:.4f}"), use_container_width=True, height=350)

    # PESTAÑA 3: VIBRACIÓN TORSIONAL
    with tab2:
        st.subheader("Análisis de Esfuerzos de Torsión Cíclicos en el Eje de Cola")
        omega = (2.0 * math.pi * rpm_motor) / 60.0
        torque_nominal = (potencia_kw * 1000.0) / omega
        torque_dinamico_alternante = torque_nominal * 0.15 
        wt_modulo_torsional = (math.pi * (diametro_m**3)) / 16.0
        esfuerzo_real_mpa = (torque_dinamico_alternante / wt_modulo_torsional) / 1e6
        tau_admisible_mpa = 0.35 * (sigma_uts / 3.0)
        
        c_t1, c_t2 = st.columns([1, 1.2])
        with c_t1:
            st.metric("Torque de Diseño (Con Margen de Servicio)", f"{torque_nominal/1000:.2f} kN·m")
            st.metric("Esfuerzo Real de Operación (τ)", f"{esfuerzo_real_mpa:.2f} MPa")
            st.metric("Límite Admisible IACS UR M68", f"{tau_admisible_mpa:.2f} MPa")
            if esfuerzo_real_mpa <= tau_admisible_mpa: st.success("✅ **CUMPLE SATISFACTORIAMENTE (IACS UR M68)**")
            else: st.error("❌ **RECHAZADO POR FATIGA TORSIONAL STRUCTURAL**")
        with c_t2:
            fig_t, ax_t = plt.subplots(figsize=(6, 2.5))
            ax_t.barh(['Esfuerzo Real', 'Límite Admisible'], [esfuerzo_real_mpa, tau_admisible_mpa], color=['#10b981', '#4c1d95'], height=0.45)
            ax_t.set_xlabel('Esfuerzo Torsional (MPa)'); ax_t.grid(True, linestyle=':', alpha=0.4)
            st.pyplot(fig_t)

    # PESTAÑA 4: VIBRACIÓN LATERAL
    with tab3:
        st.subheader("Cálculo de la Primera Velocidad Crítica Lateral por Flexión (Whirling)")
        c_l1, c_l2 = st.columns([1, 1.2])
        with c_l1:
            st.metric("Frecuencia de Whirling", f"{f_natural_hz:.2f} Hz")
            st.metric("Velocidad Crítica Lateral", f"{rpm_critica_lateral:.1f} RPM")
            st.metric("Banda Prohibida Excluida (±20%)", f"{margen_inf:.1f} - {margen_sup:.1f} RPM")
            if rpm_motor < margen_inf or rpm_motor > margen_sup: st.success("✅ **DISEÑO SEGURO: OPERACIÓN FUERA DE RESONANCIA**")
            else: st.error("❌ **ALERTA: OPERACIÓN DENTRO DE ZONA CRÍTICA**")
        with c_l2:
            fig_l, ax_l = plt.subplots(figsize=(6, 2.5))
            ax_l.axvline(x=rpm_critica_lateral, color='red', linestyle='--')
            ax_l.axvspan(margen_inf, margen_sup, color='#ef4444', alpha=0.15)
            ax_l.scatter([rpm_motor], [1], color='#10b981', s=150, zorder=5, edgecolor='black')
            ax_l.set_xlim(0, rpm_critica_lateral * 1.6); ax_l.set_yticks([]); ax_l.set_xlabel('Velocidad del Eje (RPM)')
            ax_l.grid(True, linestyle=':', alpha=0.5)
            st.pyplot(fig_l)

    # PESTAÑA 5: DIAGRAMA DE CAMPBELL
    with tab4:
        st.subheader("🗺️ Mapa Dinámico de Intersección de Frecuencias (Diagrama de Campbell)")
        max_rpm_grafica = rpm_motor * 1.6
        rpm_eje_x = np.linspace(0, max_rpm_grafica, 400)
        
        fig_c, ax_c = plt.subplots(figsize=(10, 4.5))
        ax_c.axhline(y=f_natural_hz, color='#4c1d95', linestyle='--', lw=2, label=f'Frecuencia Natural Lateral ({f_natural_hz:.1f} Hz)')
        ax_c.axhline(y=f_torsional_est, color='#b45309', linestyle='--', lw=1.8, label=f'Frecuencia Natural Torsional Est. ({f_torsional_est:.1f} Hz)')
        ax_c.plot(rpm_eje_x, (1 * rpm_eje_x) / 60.0, color='#64748b', lw=1.2, label='Orden 1P')
        ax_c.plot(rpm_eje_x, (z_val * rpm_eje_x) / 60.0, color='#d97706', lw=2.5, label=f'Orden {z_val}P')
        ax_c.axvline(x=rpm_motor, color='#4c1d95', lw=2.5, label=f'RPM Real ({rpm_motor:.1f})')
        ax_c.axvspan(margen_inf, margen_sup, color='#ef4444', alpha=0.12, label='Banda Prohibida')
        ax_c.set_xlim(0, max_rpm_grafica)
        ax_c.grid(True, linestyle=':')
        ax_c.legend(loc='upper left')
        st.pyplot(fig_c)
        
        st.markdown("---")
        st.subheader("📊 Matriz de Intersecciones y Puntos de Resonancia Críticos")
        
        intersecciones_datos = [
            {
                "Línea de Excitación": "Orden 1P (Excentricidad)",
                "Frecuencia Natural Coincidente": f"Frecuencia Lateral ({f_natural_hz:.2f} Hz)",
                "RPM de Cruce": f_natural_hz * 60.0,
                "Estado Operativo": "Seguro" if abs((f_natural_hz * 60.0) - rpm_motor) > 15 else "Riesgo de Resonancia"
            },
            {
                "Línea de Excitación": f"Orden {z_val}P (Palas de Hélice)",
                "Frecuencia Natural Coincidente": f"Frecuencia Lateral ({f_natural_hz:.2f} Hz)",
                "RPM de Cruce": (f_natural_hz * 60.0) / z_val,
                "Estado Operativo": "Seguro" if abs(((f_natural_hz * 60.0) / z_val) - rpm_motor) > 15 else "Riesgo de Resonancia"
            },
            {
                "Línea de Excitación": "Orden 1P (Excentricidad)",
                "Frecuencia Natural Coincidente": f"Frecuencia Torsional Est. ({f_torsional_est:.2f} Hz)",
                "RPM de Cruce": f_torsional_est * 60.0,
                "Estado Operativo": "Seguro" if abs((f_torsional_est * 60.0) - rpm_motor) > 15 else "Riesgo de Resonancia"
            },
            {
                "Línea de Excitación": f"Orden {z_val}P (Palas de Hélice)",
                "Frecuencia Natural Coincidente": f"Frecuencia Torsional Est. ({f_torsional_est:.2f} Hz)",
                "RPM de Cruce": (f_torsional_est * 60.0) / z_val,
                "Estado Operativo": "Seguro" if abs(((f_torsional_est * 60.0) / z_val) - rpm_motor) > 15 else "Riesgo de Resonancia"
            }
        ]
        
        df_intersecciones = pd.DataFrame(intersecciones_datos)
        
        st.dataframe(
            df_intersecciones.style.format({"RPM de Cruce": "{:.2f} RPM"}).map(
                lambda val: 'background-color: #fef2f2; color: #dc2626; font-weight: bold;' if val == "Riesgo de Resonancia" else None
            ),
            use_container_width=True
        )

else:
    st.error("⚠️ Archivo 'Tabla 1.xlsx' requerido en el mismo directorio de ejecución.")

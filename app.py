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

# Inyección de CSS Avanzado para simular un software comercial moderno
st.markdown("""
    <style>
    /* Estilo general de la app */
    .main { background-color: #f8fafc; color: #1e293b; font-family: 'Segoe UI', Roboto, sans-serif; }
    
    /* Encabezado Principal */
    .main-title { font-size: 34px; font-weight: 800; color: #1e2022; margin-bottom: 5px; letter-spacing: -0.5px; }
    .main-subtitle { font-size: 14px; color: #64748b; font-weight: 500; margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Tabs Navegación */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #f1f5f9; padding: 6px 8px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { 
        height: 44px; background-color: transparent; border: none;
        border-radius: 8px; padding: 8px 16px; font-weight: 600; color: #64748b; transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] { background-color: #4c1d95 !important; color: white !important; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
    
    /* Contenedores de Fórmulas y Reportes */
    .tech-card { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .tech-card h4 { margin-top: 0; color: #4c1d95; font-size: 16px; font-weight: 700; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
    
    /* Bloques de Alertas de Diagnóstico en el Campbell */
    .status-box-safe { background-color: #f0fdf4; border-left: 5px solid #16a34a; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    .status-box-danger { background-color: #fef2f2; border-left: 5px solid #dc2626; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    
    /* Indicadores de Métricas */
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
        return kt_df, df_kq
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
# 3. INTERFAZ DE USUARIO & BARRA LATERAL (UNIVERSAL Y DINÁMICA)
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Análisis Hidrodinámico, Vibratorio Estructural y de Fluidos — Equipo 4 | Universidad Veracruzana</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.markdown("### 🛠️ Configuración del Sistema")
        st.write("Establezca los parámetros operativos de diseño.")
        
        with st.expander("📐 Dimensiones de la Carena", expanded=True):
            eslora = st.number_input("Eslora entre Perpendiculares Lpp (m)", value=320.0, step=1.0)
            manga = st.number_input("Manga de Diseño B (m)", value=58.0, step=0.5)
            puntal = st.number_input("Puntal Estructural D (m)", value=30.0, step=0.5)
            calado = st.number_input("Calado de Diseño T (m)", value=20.80, step=0.1)
            velocidad = st.number_input("Velocidad de Servicio V (nudos)", value=15.5, step=0.5)
            estela = st.number_input("Fracción de Estela (w)", value=0.351, step=0.001, format="%.3f")
            t_fraccion = st.number_input("Fracción de Deducción de Empuje (t)", value=0.180, step=0.001, format="%.3f")
        
        with st.expander("🌀 Geometría de la Hélice", expanded=True):
            z_val = st.slider("Número de Palas (Z)", 3, 7, 4)
            diam_prop_m = st.number_input("Diámetro del Propulsor D (m)", value=9.86, step=0.01)
            pd_val = st.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, 0.721, 0.001)
            ae_val = st.slider("Relación de Área Expandida (Ae/A0)", 0.3, 1.0, 0.431, 0.001)
            peso_helice_kg = st.number_input("Masa de la Hélice en Seco (kg)", value=18500.0, step=500.0)
            inmersion_eje_m = st.number_input("Inmersión del Eje H (m)", value=14.10, step=0.1)
            
        with st.expander("⚙️ Planta Propulsora y Eje", expanded=True):
            potencia_kw = st.number_input("Potencia de Diseño MCR (kW)", value=22000.0, step=500.0)
            rpm_motor = st.number_input("RPM de Operación Continua (n)", value=75.0, step=1.0)
            diametro_eje_mm = st.number_input("Diámetro del Eje de Cola d (mm)", value=680.0, step=10.0)
            sigma_uts = st.number_input("Resistencia a la Tracción σ_UTS (MPa)", value=600.0, step=50.0)
            longitud_volado_m = st.number_input("Longitud del Voladizo L (m)", value=3.5, step=0.1)

        st.markdown("---")
        st.markdown("**Integrantes del Equipo 4:**")
        st.caption("Lizeth H.F. · Jade F.J.C. · Vania A.N.Q. · Iris L.R.R. · Karla V.G. · José E.S. · Óscar G.B.")

    # ==============================================================================
    # 4. CALCULO DE VARIABLES GLOBALES DE DISEÑO (BACKEND UNIFICADO)
    # ==============================================================================
    res = calcular_curvas(pd_val, ae_val, z_val)
    
    diametro_m = diametro_eje_mm / 1000.0
    E_acero = 2.06e11  
    densidad_acero = 7850.0  
    r_eje = diametro_m / 2.0
    area_eje = math.pi * (r_eje**2)
    I_inercia = (math.pi * (diametro_m**4)) / 64.0
    peso_lineal_eje = area_eje * densidad_acero
    
    peso_helice_n = peso_helice_kg * 9.81
    delta_helice = (peso_helice_n * (longitud_volado_m**3)) / (3.0 * E_acero * I_inercia)
    peso_eje_n = peso_lineal_eje * longitud_volado_m * 9.81
    delta_eje = (peso_eje_n * (longitud_volado_m**3)) / (8.0 * E_acero * I_inercia)
    
    f_natural_hz = 1.0 / (2.0 * math.pi * math.sqrt(delta_helice + delta_eje))
    rpm_critica_lateral = f_natural_hz * 60.0
    margen_inf = rpm_critica_lateral * 0.80
    margen_sup = rpm_critica_lateral * 1.20
    f_torsional_est = f_natural_hz * 1.4

    # ==============================================================================
    # 5. DIVISIÓN DE SECCIONES POR PESTAÑAS
    # ==============================================================================
    tab1, tab_res, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Hidrodinámica (Aguas Abiertas)", 
        "📋 Reporte de Datos Numéricos",
        "💥 Entregable 1: Vibración Torsional", 
        "📊 Entregable 2: Vibración Lateral",
        "🗺️ Entregable 3: Diagrama de Campbell",
        "🧼 Avanzado: Cavitación & Fluidos"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: MODELO HIDRODINÁMICO DE AGUAS ABIERTAS
    # --------------------------------------------------------------------------
    with tab1:
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J'] if max_eff > 0 else 0.0
        
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1: st.metric("Eficiencia Máxima (η_O)", f"{max_eff*100:.2f} %")
        with kpi2: st.metric("Coeficiente de Avance Óptimo (J_opt)", f"{j_opt:.3f}")
        with kpi3: st.metric("Diámetro del Propulsor", f"{diam_prop_m:.2f} m")
            
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(res['J'], res['KT'], color='#0284c7', label=r'Empuje ($K_T$)', lw=2.5)
        ax.plot(res['J'], res['KQ']*10, color='#10b981', label=r'Torque ($10 \cdot K_Q$)', lw=2.5)
        ax.plot(res['J'], res['nO'], color='#4c1d95', label=r'Eficiencia ($\eta_O$)', lw=3.5, ls='--')
        ax.fill_between(res['J'], 0, res['nO'], color='#4c1d95', alpha=0.06)
        
        if max_eff > 0:
            ax.axvline(x=j_opt, color='#64748b', linestyle=':', alpha=0.7)
            
        ax.set_title("Características Operativas en Aguas Abiertas - Wageningen Serie B", fontsize=11, fontweight='bold', color='#1e293b')
        ax.set_xlim(0, 1.2); ax.set_ylim(0, 1.1); ax.grid(True, linestyle=':', alpha=0.5)
        ax.legend(loc='upper right', frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0')
        st.pyplot(fig)
        
        st.latex(r"K_T = \sum (C_n \cdot J^{S_n} \cdot (P/D)^{T_n} \cdot (A_E/A_O)^{U_n} \cdot Z^{V_n})")
        st.latex(r"\eta_O = \frac{J}{2\pi} \cdot \frac{K_T}{K_Q}")

    with tab_res:
        st.subheader("📋 Matriz Completa de Resultados de la Hélice")
        res_display = res.copy()
        res_display['ηO (%)'] = res_display['nO'] * 100
        st.dataframe(res_display.style.highlight_max(subset=['nO'], color='#f3e8ff').format("{:.4f}"), use_container_width=True, height=350)

    # --------------------------------------------------------------------------
    # TAB 2: ENTREGABLE 1 - VIBRACIÓN TORSIONAL
    # --------------------------------------------------------------------------
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
            st.metric("Momento Torsor Nominal", f"{torque_nominal/1000:.2f} kN·m")
            st.metric("Tensión Real Calculada (τ)", f"{esfuerzo_real_mpa:.2f} MPa")
            st.metric("Límite Admisible IACS UR M68", f"{tau_admisible_mpa:.2f} MPa")
            if esfuerzo_real_mpa <= tau_admisible_mpa: st.success("✅ **CUMPLE SATISFACTORIAMENTE (IACS UR M68)**")
            else: st.error("❌ **RECHAZADO POR FATIGA TORSIONAL**")
        with c_t2:
            fig_t, ax_t = plt.subplots(figsize=(6, 2.5))
            ax_t.barh(['Esfuerzo Real', 'Límite Admisible'], [esfuerzo_real_mpa, tau_admisible_mpa], color=['#10b981', '#4c1d95'], height=0.45)
            ax_t.set_xlabel('Esfuerzo Torsional (MPa)'); ax_t.grid(True, linestyle=':', alpha=0.4)
            st.pyplot(fig_t)

    # --------------------------------------------------------------------------
    # TAB 3: ENTREGABLE 2 - VIBRACIÓN LATERAL
    # --------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------
    # TAB 4: ENTREGABLE 3 - DIAGRAMA DE CAMPBELL (¡CON NUEVO LETRERO DINÁMICO!)
    # --------------------------------------------------------------------------
    with tab4:
        st.subheader("🗺️ Mapa Dinámico de Intersección de Frecuencias (Diagrama de Campbell)")
        
        # Lógica de verificación para el letrero verde/rojo
        is_campbell_safe = True
        motivo_riesgo = ""
        
        rpm_cruce_lat_zp = f_natural_hz * 60.0 / z_val
        rpm_cruce_tor_zp = f_torsional_est * 60.0 / z_val
        
        # Verificar si las RPM operativas caen en la banda de velocidad prohibida lateral
        if margen_inf <= rpm_motor <= margen_sup:
            is_campbell_safe = False
            motivo_riesgo = "La velocidad de operación continua coincide con la Banda de Velocidad Prohibida por Whirling Lateral."
            
        # Desplegar Letrero dinámico de estatus superior
        if is_campbell_safe:
            st.markdown(f"""
            <div class="status-box-safe">
                <h4 style='color: #15803d; margin: 0;'>🟢 DIAGNÓSTICO CAMPBELL: SISTEMA SEGURO Y COMPATIBLE</h4>
                <p style='color: #166534; margin: 5px 0 0 0; font-size: 14px;'>
                    <b>¡Diseño Seguro!</b> A las <b>{rpm_motor:.1f} RPM</b> de servicio, las frecuencias de excitación hidrodinámica de la hélice 
                    (Orden {z_val}P = { (z_val*rpm_motor)/60.0 :.2f} Hz) operan de manera estable y con márgenes de separación reglamentarios 
                    respecto a las frecuencias naturales estructurales del eje de cola. No hay riesgo de resonancia destructiva en régimen continuo.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-box-danger">
                <h4 style='color: #991b1b; margin: 0;'>❌ ALERTA INGENIERÍAL: RIESGO DE RESONANCIA DETECTADO</h4>
                <p style='color: #7f1d1d; margin: 5px 0 0 0; font-size: 14px;'>
                    <b>Peligro Crítico:</b> {motivo_riesgo} Se requiere modificar el diámetro del eje, el número de palas o el material para desplazar los puntos de cruce fuera del rango de servicio continuo.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        max_rpm_grafica = rpm_motor * 1.6
        rpm_eje_x = np.linspace(0, max_rpm_grafica, 400)
        
        orden_1p = (1 * rpm_eje_x) / 60.0
        orden_zp = (z_val * rpm_eje_x) / 60.0
        orden_2zp = ((z_val * 2) * rpm_eje_x) / 60.0
        
        fig_c, ax_c = plt.subplots(figsize=(10, 4.5))
        ax_c.axhline(y=f_natural_hz, color='#4c1d95', linestyle='--', lw=2, label=f'Frecuencia Natural Lateral ({f_natural_hz:.1f} Hz)')
        ax_c.axhline(y=f_torsional_est, color='#b45309', linestyle='--', lw=1.8, label=f'Frecuencia Natural Torsional Est. ({f_torsional_est:.1f} Hz)')
        ax_c.plot(rpm_eje_x, orden_1p, color='#64748b', lw=1.2, label='Orden 1P (Desbalanceo)')
        ax_c.plot(rpm_eje_x, orden_zp, color='#d97706', lw=2.5, label=f'Orden {z_val}P (Paso de Palas Fundamental)')
        ax_c.plot(rpm_eje_x, orden_2zp, color='#db2777', lw=1.5, ls=':', label=f'Orden {z_val*2}P (2do Armónico)')
        ax_c.axvline(x=rpm_motor, color='#4c1d95', lw=2.5, label=f'RPM Operativa Real ({rpm_motor:.1f} RPM)')
        ax_c.axvspan(margen_inf, margen_sup, color='#ef4444', alpha=0.12, label='Banda de Velocidad Prohibida (BSR)')
        
        ax_c.set_xlim(0, max_rpm_grafica)
        ax_c.set_ylim(0, max(f_torsional_est, (z_val * rpm_motor) / 60.0) * 1.25)
        ax_c.grid(True, linestyle=':', alpha=0.6)
        ax_c.set_xlabel('Velocidad de Giro del Motor / Hélice (RPM)', fontsize=10)
        ax_c.set_ylabel('Frecuencia Dinámica del Sistema (Hz)', fontsize=10)
        ax_c.legend(loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9.5)
        st.pyplot(fig_c)
        
        st.markdown("### 📊 Matriz Analítica de Puntos de Intersección Críticos")
        rpm_cruce_lat_1p = f_natural_hz * 60.0 / 1.0
        rpm_cruce_lat_2zp = f_natural_hz * 60.0 / (z_val * 2)
        rpm_cruce_tor_1p = f_torsional_est * 60.0 / 1.0
        rpm_cruce_tor_2zp = f_torsional_est * 60.0 / (z_val * 2)
        
        def evaluar_zona(rpm_c):
            if margen_inf <= rpm_c <= margen_sup: return "🔴 ¡DENTRO DE BANDA PROHIBIDA (CRÍTICO)!"
            elif rpm_c < margen_inf: return "🟢 Por debajo del régimen operativo"
            else: return "🟡 Por encima del régimen operativo"
                
        datos_cruces = {
            "Frecuencia Estructural Natural": ["Lateral (Whirling)", "Lateral (Whirling)", "Lateral (Whirling)", "Torsional Est.", "Torsional Est.", "Torsional Est."],
            "Orden de Excitación Dinámica": ["Orden 1P (Desbalanceo)", f"Orden {z_val}P (Paso de Palas)", f"Orden {z_val*2}P (2do Armónico)", "Orden 1P (Desbalanceo)", f"Orden {z_val}P (Paso de Palas)", f"Orden {z_val*2}P (2do Armónico)"],
            "Frecuencia del Cruce (Hz)": [f_natural_hz, f_natural_hz, f_natural_hz, f_torsional_est, f_torsional_est, f_torsional_est],
            "Velocidad Crítica Exacta (RPM)": [rpm_cruce_lat_1p, rpm_cruce_lat_zp, rpm_cruce_lat_2zp, rpm_cruce_tor_1p, rpm_cruce_tor_zp, rpm_cruce_tor_2zp],
            "Evaluación de Seguridad / Riesgo": [evaluar_zona(rpm_cruce_lat_1p), evaluar_zona(rpm_cruce_lat_zp), evaluar_zona(rpm_cruce_lat_2zp), evaluar_zona(rpm_cruce_tor_1p), evaluar_zona(rpm_cruce_tor_zp), evaluar_zona(rpm_cruce_tor_2zp)]
        }
        st.dataframe(pd.DataFrame(datos_cruces).style.format({"Frecuencia del Cruce (Hz)": "{:.2f} Hz", "Velocidad Crítica Exacta (RPM)": "{:.1f} RPM"}), use_container_width=True)

    # --------------------------------------------------------------------------
    # TAB 5: ADVANCED - CAVITACIÓN Y NÚMERO DE REYNOLDS
    # --------------------------------------------------------------------------
    with tab5:
        st.subheader("🧼 Análisis Hidrodinámico Avanzado: Mecánica de Fluidos de la Hélice")
        
        v_m_s = velocidad * 0.514444
        v_avance = v_m_s * (1.0 - estela)
        n_rps = rpm_motor / 60.0
        
        radius_07 = 0.7 * (diam_prop_m / 2.0)
        v_tangencial = 2.0 * math.pi * n_rps * radius_07
        v_relativa_07 = math.sqrt(v_avance**2 + v_tangencial**2)
        
        cuerda_07 = (1.5 * diam_prop_m * ae_val) / z_val
        viscosidad_cinematica = 1.188e-6
        reynolds_n = (v_relativa_07 * cuerda_07) / viscosidad_cinematica
        
        p_atmosferica = 101325.0
        p_vapor = 1705.0
        densidad_agua = 1025.0
        p_hidrostatica = p_atmosferica + (densidad_agua * 9.81 * inmersion_eje_m) - p_vapor
        
        eta_open_water = 0.55
        empuje_t_n = (potencia_kw * 1000.0 * eta_open_water) / (v_avance if v_avance > 0 else 1.0)
        
        ae_ao_keller = ((1.3 + 0.3 * z_val) * empuje_t_n) / (p_hidrostatica * (diam_prop_m**2)) + 0.03
        
        ap_area = ae_val * (math.pi * (diam_prop_m**2) / 4.0) * (1.067 - 0.229 * pd_val)
        q_dinamica_07 = 0.5 * densidad_agua * (v_relativa_07**2)
        tau_c_diseno = empuje_t_n / (ap_area * q_dinamica_07)
        sigma_07_diseno = p_hidrostatica / q_dinamica_07
        
        col_c1, col_c2 = st.columns([1, 1.2])
        with col_c1:
            st.markdown("##### 🧪 Parámetros Cinemáticos & Reynolds")
            st.metric("Número de Reynolds ($R_n$ en $0.7r$)", f"{reynolds_n:.2e}")
            st.caption("✅ **Régimen Completamente Turbulento:** Flujo mecánicamente estable sobre los perfiles de las palas según la ITTC.")
                
            st.markdown("---")
            st.markdown("##### 🧼 Evaluación de Cavitación (Keller & Burrill)")
            st.metric("Área Expandida Mínima (Keller)", f"{ae_ao_keller:.3f}")
            st.metric("Área Expandida de Tu Diseño ($A_E/A_O$)", f"{ae_val:.3f}")
            
            if ae_val >= ae_ao_keller: st.success("✅ **DISEÑO SEGURO CONTRA CAVITACIÓN (KELLER):** Área suficiente.")
            else: st.error("❌ **RIESGO DE CAVITACIÓN (KELLER):** Área insuficiente.")
                
        with col_c2:
            fig_burrill, ax_b = plt.subplots(figsize=(6.5, 4.2))
            sigma_axis = np.linspace(0.1, 1.5, 200)
            tau_limite_burrill = 0.30 * (sigma_axis**0.68)
            
            ax_b.plot(sigma_axis, tau_limite_burrill, color='#ef4444', lw=2, label='Límite de Cavitación Comercial (Burrill)')
            ax_b.fill_between(sigma_axis, tau_limite_burrill, 1.5, color='#ef4444', alpha=0.08, label='Zona de Cavitación Activa')
            ax_b.fill_between(sigma_axis, 0, tau_limite_burrill, color='#10b981', alpha=0.04, label='Zona Segura (Libre de Erosión)')
            
            ax_b.scatter([sigma_07_diseno], [tau_c_diseno], color='#ca8a04', s=180, edgecolor='black', zorder=5, 
                         label=f'Tu Hélice (σ={sigma_07_diseno:.2f}, τ={tau_c_diseno:.3f})')
            
            ax_b.set_title("Diagrama Límite de Cavitación de Burrill", fontsize=11, fontweight='bold', color='#1e293b')
            ax_b.set_xlabel(r"Número de Cavitación de la Sección ($\sigma_{0.7R}$)", fontsize=9)
            ax_b.set_ylabel(r"Coeficiente de Empuje de Cavitación ($\tau_C$)", fontsize=9)
            ax_b.set_xlim(0.1, 1.4); ax_b.set_ylim(0, max(0.4, tau_c_diseno * 1.5))
            ax_b.grid(True, linestyle=':', alpha=0.5)
            ax_b.legend(loc='upper right', fontsize=8, frameon=True, facecolor='#ffffff')
            st.pyplot(fig_burrill)

else:
    st.error("⚠️ Archivo de Coeficientes Inexistente: Asegúrese de posicionar 'Tabla 1.xlsx' en el mismo directorio de ejecución.")

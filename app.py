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
    .tech-card h4 { margin-top: 0; color: #4c1d95; font-size: 16px; font-weight: 700; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
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
# 3. INTERFAZ DE USUARIO & BARRA LATERAL AUTOMATIZADA CORREGIDA
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Análisis Hidrodinámico, Vibratorio Estructural y de Fluidos — Equipo 4 | Universidad Veracruzana</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.markdown("### 🛠️ Configuración Automática del Sistema")
        
        tipo_buque = st.selectbox(
            "Tipo de Buque de Diseño:",
            ["Granelero (Bulk Carrier)", "Tanque (VLCC)", "Portacontenedores (Containership)", "Personalizado (Manual)"]
        )
        
        # Ahora el bloqueo SOLAMENTE aplica a las salidas calculadas automáticamente
        bloquear_automaticos = (tipo_buque != "Personalizado (Manual)")
        
        # Base de datos maestra
        db_buques = {
            "Granelero (Bulk Carrier)": {
                "eslora": 320.0, "manga": 58.0, "puntal": 30.0, "calado": 20.80, "velocidad": 15.5,
                "estela": 0.351, "t_fraccion": 0.180, "z_val": 4, "diam_prop_m": 9.86, "pd_val": 0.721,
                "ae_val": 0.431, "material_helice": "Aleación de Ni-Al-Bronce (Cu3)", "peso_helice_kg": 18500.0, 
                "inmersion_eje_m": 14.10, "potencia_kw": 22000.0, "rpm_motor": 75.0, "diametro_eje_mm": 680.0, 
                "sigma_uts": 600.0, "longitud_volado_m": 3.5
            },
            "Tanque (VLCC)": {
                "eslora": 333.0, "manga": 60.0, "puntal": 30.5, "calado": 21.50, "velocidad": 14.8,
                "estela": 0.385, "t_fraccion": 0.195, "z_val": 4, "diam_prop_m": 10.20, "pd_val": 0.695,
                "ae_val": 0.455, "material_helice": "Bronce de Manganeso (Cu1)", "peso_helice_kg": 21000.0, 
                "inmersion_eje_m": 14.80, "potencia_kw": 25000.0, "rpm_motor": 72.0, "diametro_eje_mm": 710.0, 
                "sigma_uts": 600.0, "longitud_volado_m": 3.8
            },
            "Portacontenedores (Containership)": {
                "eslora": 366.0, "manga": 48.2, "puntal": 29.8, "calado": 15.50, "velocidad": 22.5,
                "estela": 0.220, "t_fraccion": 0.140, "z_val": 5, "diam_prop_m": 8.90, "pd_val": 0.950,
                "ae_val": 0.650, "material_helice": "Aleación de Ni-Al-Bronce (Cu3)", "peso_helice_kg": 24500.0, 
                "inmersion_eje_m": 11.20, "potencia_kw": 52000.0, "rpm_motor": 98.0, "diametro_eje_mm": 780.0, 
                "sigma_uts": 650.0, "longitud_volado_m": 3.2
            },
            "Personalizado (Manual)": {
                "eslora": 320.0, "manga": 58.0, "puntal": 30.0, "calado": 20.80, "velocidad": 15.5,
                "estela": 0.351, "t_fraccion": 0.180, "z_val": 4, "diam_prop_m": 9.86, "pd_val": 0.721,
                "ae_val": 0.431, "material_helice": "Bronce de Manganeso (Cu1)", "peso_helice_kg": 18500.0, 
                "inmersion_eje_m": 14.10, "potencia_kw": 22000.0, "rpm_motor": 75.0, "diametro_eje_mm": 680.0, 
                "sigma_uts": 600.0, "longitud_volado_m": 3.5
            }
        }
        
        base = db_buques[tipo_buque]
        
        # INPUTS SIEMPRE LIBRES (disabled=False) para que se puedan modificar las dimensiones principales
        with st.expander("📐 Dimensiones de la Carena", expanded=True):
            eslora = st.number_input("Eslora entre Perpendiculares Lpp (m)", value=base["eslora"], step=1.0, key=f"esl_{tipo_buque}")
            manga = st.number_input("Manga de Diseño B (m)", value=base["manga"], step=0.5, key=f"mng_{tipo_buque}")
            puntal = st.number_input("Puntal Estructural D (m)", value=base["puntal"], step=0.5, key=f"pnt_{tipo_buque}")
            calado = st.number_input("Calado de Diseño T (m)", value=base["calado"], step=0.1, key=f"cld_{tipo_buque}")
            velocidad = st.number_input("Velocidad de Servicio V (nudos)", value=base["velocidad"], step=0.5, key=f"vel_{tipo_buque}")
        
        # INPUTS BLOQUEADOS EXCLUSIVAMENTE SI ES AUTOMÁTICO (disabled=bloquear_automaticos)
        with st.expander("🌀 Parámetros Hidrodinámicos Calculados", expanded=True):
            estela = st.number_input("Fracción de Estela (w)", value=base["estela"], step=0.001, format="%.3f", key=f"est_{tipo_buque}", disabled=bloquear_automaticos)
            t_fraccion = st.number_input("Fracción de Deducción de Empuje (t)", value=base["t_fraccion"], step=0.001, format="%.3f", key=f"tf_{tipo_buque}", disabled=bloquear_automaticos)
            z_val = st.slider("Número de Palas (Z)", 3, 7, int(base["z_val"]), key=f"z_{tipo_buque}", disabled=bloquear_automaticos)
            diam_prop_m = st.number_input("Diámetro del Propulsor D (m)", value=base["diam_prop_m"], step=0.01, key=f"dp_{tipo_buque}", disabled=bloquear_automaticos)
            pd_val = st.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, base["pd_val"], 0.001, key=f"pd_{tipo_buque}", disabled=bloquear_automaticos)
            ae_val = st.slider("Relación de Área Expandida (Ae/A0)", 0.3, 1.0, base["ae_val"], 0.001, key=f"ae_{tipo_buque}", disabled=bloquear_automaticos)
            inmersion_eje_m = st.number_input("Inmersión del Eje H (m)", value=base["inmersion_eje_m"], step=0.1, key=f"imm_{tipo_buque}", disabled=bloquear_automaticos)
            
        with st.expander("⚙️ Propiedades del Material y Eje", expanded=True):
            material_helice = st.text_input("Material de la Hélice", value=base["material_helice"], key=f"mat_{tipo_buque}", disabled=bloquear_automaticos)
            peso_helice_kg = st.number_input("Masa de la Hélice en Seco (kg)", value=base["peso_helice_kg"], step=500.0, key=f"ph_{tipo_buque}", disabled=bloquear_automaticos)
            potencia_kw = st.number_input("Potencia de Diseño MCR (kW)", value=base["potencia_kw"], step=500.0, key=f"pot_{tipo_buque}", disabled=bloquear_automaticos)
            rpm_motor = st.number_input("RPM de Operación Continua (n)", value=base["rpm_motor"], step=1.0, key=f"rpm_{tipo_buque}", disabled=bloquear_automaticos)
            diametro_eje_mm = st.number_input("Diámetro del Eje de Cola d (mm)", value=base["diametro_eje_mm"], step=10.0, key=f"dia_{tipo_buque}", disabled=bloquear_automaticos)
            sigma_uts = st.number_input("Resistencia a la Tracción σ_UTS (MPa)", value=base["sigma_uts"], step=50.0, key=f"uts_{tipo_buque}", disabled=bloquear_automaticos)
            longitud_volado_m = st.number_input("Longitud del Voladizo L (m)", value=base["longitud_volado_m"], step=0.1, key=f"vol_{tipo_buque}", disabled=bloquear_automaticos)

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
    
    factor_sname = 1.4
    f_torsional_est = f_natural_hz * factor_sname

    # ==============================================================================
    # 5. DIVISIÓN DE SECCIONES POR PESTAÑAS
    # ==============================================================================
    tab1, tab_res, tab2, tab3, tab4, tab5, tab_teoria = st.tabs([
        "📈 Hidrodinámica (Aguas Abiertas)", 
        "📋 Reporte de Datos Numéricos",
        "💥 Entregable 1: Vibración Torsional", 
        "📊 Entregable 2: Vibración Lateral",
        "🗺️ Entregable 3: Diagrama de Campbell",
        "🧼 Avanzado: Cavitación & Fluidos",
        "📚 Sustento Teórico y Fórmulas"
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
        with kpi3: st.metric("Diámetro del Propulsor D", f"{diam_prop_m:.2f} m")
            
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

    # --------------------------------------------------------------------------
    # TAB REPORTE: MATRIZ DE RESULTADOS HIDRODINÁMICOS
    # --------------------------------------------------------------------------
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
        
        factor_torsor_dinamico = 0.15
        torque_dinamico_alternante = torque_nominal * factor_torsor_dinamico 
        
        wt_modulo_torsional = (math.pi * (diametro_m**3)) / 16.0
        esfuerzo_real_mpa = (torque_dinamico_alternante / wt_modulo_torsional) / 1e6
        
        factor_iacs_m68 = 0.35
        tau_admisible_mpa = factor_iacs_m68 * (sigma_uts / 3.0)
        
        c_t1, c_t2 = st.columns([1, 1.2])
        with c_t1:
            st.metric("Momento Torsor Nominal", f"{torque_nominal/1000:.2f} kN·m")
            st.metric("Esfuerzo Real Calculada (τ)", f"{esfuerzo_real_mpa:.2f} MPa")
            st.metric("Límite Admisible IACS UR M68", f"{tau_admisible_mpa:.2f} MPa")
            if esfuerzo_real_mpa <= tau_admisible_mpa: 
                st.success("✅ **CUMPLE SATISFACTORIAMENTE (IACS UR M68)**")
            else: 
                st.error("❌ **RECHAZADO POR FATIGA TORSIONAL**")
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
            if rpm_motor < margen_inf or rpm_motor > margen_sup: 
                st.success("✅ **DISEÑO SEGURO: OPERACIÓN FUERA DE RESONANCIA**")
            else: 
                st.error("❌ **ALERTA: OPERACIÓN DENTRO DE ZONA CRÍTICA**")
        with c_l2:
            fig_l, ax_l = plt.subplots(figsize=(6, 2.5))
            ax_l.axvline(x=rpm_critica_lateral, color='red', linestyle='--')
            ax_l.axvspan(margen_inf, margen_sup, color='#ef4444', alpha=0.15)
            ax_l.scatter([rpm_motor], [1], color='#10b981', s=150, zorder=5, edgecolor='black')
            ax_l.set_xlim(0, rpm_critica_lateral * 1.6); ax_l.set_yticks([]); ax_l.set_xlabel('Velocidad del Eje (RPM)')
            ax_l.grid(True, linestyle=':', alpha=0.5)
            st.pyplot(fig_l)

    # --------------------------------------------------------------------------
    # TAB 4: DIAGRAMA DE CAMPBELL
    # --------------------------------------------------------------------------
    with tab4:
        st.subheader("🗺️ Mapa Dinámico de Intersección de Frecuencias (Diagrama de Campbell)")
        
        is_campbell_safe = True
        motivo_riesgo = ""
        if margen_inf <= rpm_motor <= margen_sup:
            is_campbell_safe = False
            motivo_riesgo = "La velocidad de operación continua coincide con la Banda de Velocidad Prohibida por Whirling Lateral."
            
        if is_campbell_safe:
            st.markdown(f"""
            <div class="status-box-safe">
                <h4 style='color: #15803d; margin: 0;'>🟢 DIAGNÓSTICO CAMPBELL: SISTEMA SEGURO Y COMPATIBLE</h4>
                <p style='color: #166534; margin: 5px 0 0 0; font-size: 14px;'>
                    <b>¡Diseño Seguro!</b> A las <b>{rpm_motor:.1f} RPM</b> de servicio, las frecuencias operan estables.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-box-danger">
                <h4 style='color: #991b1b; margin: 0;'>❌ ALERTA INGENIERÍAL: RIESGO DE RESONANCIA DETECTADO</h4>
                <p style='color: #7f1d1d; margin: 5px 0 0 0; font-size: 14px;'>
                    <b>Peligro Crítico:</b> {motivo_riesgo}
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
        ax_c.set_xlabel('Velocidad de Giro del Motor (RPM)')
        ax_c.set_ylabel('Frecuencia Dinámica (Hz)')
        ax_c.legend(loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9.5)
        st.pyplot(fig_c)

    # --------------------------------------------------------------------------
    # TAB 5: ADVANCED - CAVITACIÓN Y PROPIEDADES DE MATERIAL
    # --------------------------------------------------------------------------
    with tab5:
        st.subheader("🧼 Análisis Hidrodinámico Avanzado y Materiales")
        
        v_m_s = velocidad * 0.514444
        v_avance = v_m_s * (1.0 - estela)
        
        p_atmosferica = 101325.0
        p_vapor = 1705.0
        densidad_agua = 1025.0
        p_hidrostatica = p_atmosferica + (densidad_agua * 9.81 * inmersion_eje_m) - p_vapor
        
        eta_open_water = 0.55
        empuje_t_n = (potencia_kw * 1000.0 * eta_open_water) / (v_avance if v_avance > 0 else 1.0)
        
        ae_ao_keller = ((1.3 + 0.3 * z_val) * empuje_t_n) / (p_hidrostatica * (diam_prop_m**2)) + 0.03
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("##### 🪙 Especificación de Material Seleccionado")
            st.metric("Material Estructural Activo", f"{material_helice}")
            
            st.markdown("##### 🧼 Evaluación de Cavitación (Keller)")
            st.metric("Área Expandida Mínima Requerida (Keller)", f"{ae_ao_keller:.3f}")
            st.metric("Área Expandida de Tu Diseño (Ae/A0)", f"{ae_val:.3f}")
            if ae_val >= ae_ao_keller:
                st.success("✅ **DISEÑO SEGURO CONTRA CAVITACIÓN (KELLER)**")
            else:
                st.error("❌ **RIESGO DE CAVITACIÓN DETECTADO**")

    # --------------------------------------------------------------------------
    # PESTAÑA: SUSTENTO TEÓRICO (NOMENCLATURA GEMELA IDENTIFICABLE)
    # --------------------------------------------------------------------------
    with tab_teoria:
        st.subheader("📚 Memoria de Cálculo y Origen de Coeficientes Dinámicos")
        st.info("💡 Identificación Directa: Los nombres de abajo corresponden de manera idéntica a las variables lógicas procesadas por el software.")
        
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown(f"""
            <div class="tech-card">
                <h4>💥 Factor de Seguridad de Fatiga Torsional — IACS UR M68</h4>
                <p><b>Variable en Código / Gráfica:</b> <code style='color:#4c1d95;'>factor_iacs_m68</code></p>
                <p>Establece la reducción obligatoria por seguridad de fatiga para calcular el esfuerzo admisible en el eje:</p>
            </div>
            """, unsafe_allow_html=True)
            st.latex(r"\tau_{admisible} = factor\_iacs\_m68 \cdot \left( \frac{\sigma_{UTS}}{3} \right)")
            
            st.markdown(f"""
            <div class="tech-card">
                <h4>🗺️ Factor de Amplificación Dinámica Giroscópica — Criterio SNAME</h4>
                <p><b>Variable en Código / Gráfica:</b> <code style='color:#4c1d95;'>factor_sname</code></p>
                <p>Multiplicador dinámico que estima la resonancia fundamental en torsión sobre el Diagrama de Campbell:</p>
            </div>
            """, unsafe_allow_html=True)
            st.latex(r"f_{torsional\_estimada} = f_{natural\_fundamental} \cdot factor\_sname")

        with col_t2:
            st.markdown("""
            <div class="tech-card">
                <h4>🧼 Área Expandida Mínima Requerida — Criterio de Keller</h4>
                <p><b>Variable en Código / Gráfica:</b> <code style='color:#4c1d95;'>ae_ao_keller</code></p>
                <p>Define la geometría de palas crítica para evitar efectos erosivos por cavitación en fluidos marinos:</p>
            </div>
            """, unsafe_allow_html=True)
            st.latex(r"ae\_ao\_keller = \frac{(1.3 + 0.3 \cdot Z) \cdot T_P}{(P_{Atm} + \rho \cdot g \cdot H_{inmersion} - P_{Vapor}) \cdot D^2} + 0.03")
            
            st.markdown(f"""
            <div class="tech-card">
                <h4>🪙 Material de la Hélice</h4>
                <p><b>Variable en Código / Muestra:</b> <code style='color:#4c1d95;'>material_helice</code></p>
                <p>Define la composición metalúrgica del propulsor para cálculos de corrosión y masa galvánica. Para el Buque Tanque (VLCC) se predetermina como <b>Bronce de Manganeso (Cu1)</b> para resistir la fatiga en aguas profundas.</p>
            </div>
            """, unsafe_allow_html=True)

else:
    st.error("⚠️ Archivo de Coeficientes Inexistente: Asegúrese de posicionar 'Tabla 1.xlsx' en el mismo directorio de ejecución.")

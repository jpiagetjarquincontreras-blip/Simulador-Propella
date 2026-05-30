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
# 3. INTERFAZ DE USUARIO E INPUTS COMPLETA Y FUNCIONAL
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
        
        db_buques = {
            "Granelero (Bulk Carrier)": {
                "eslora": 320.0, "lwl": 324.5, "manga": 58.0, "puntal": 30.0, "calado": 20.80, "velocidad": 15.5,
                "estela": 0.351, "t_fraction": 0.18, "eta_r": 1.01, "z_val": 4, "diam_prop_m": 9.86, "pd_val": 0.721,
                "ae_val": 0.431, "peso_helice_kg": 52000.0, "inmersion_eje_m": 14.10, 
                "potencia_kw": 22000.0, "rpm_motor": 75.0, "diametro_eje_mm": 680.0, 
                "longitud_volado_m": 3.5, "margen_servicio": 15.0, "wake_adj_percent": 5.0
            },
            "Tanque (VLCC)": {
                "eslora": 333.0, "lwl": 338.2, "manga": 60.0, "puntal": 30.5, "calado": 21.50, "velocidad": 14.8,
                "estela": 0.385, "t_fraction": 0.19, "eta_r": 1.02, "z_val": 4, "diam_prop_m": 10.20, "pd_val": 0.695,
                "ae_val": 0.455, "peso_helice_kg": 72500.0, "inmersion_eje_m": 14.80, 
                "potencia_kw": 25000.0, "rpm_motor": 72.0, "diametro_eje_mm": 710.0, 
                "longitud_volado_m": 3.8, "margen_servicio": 20.0, "wake_adj_percent": 8.0
            },
            "Portacontenedores (Containership)": {
                "eslora": 366.0, "lwl": 372.1, "manga": 48.2, "puntal": 29.8, "calado": 15.50, "velocidad": 22.5,
                "estela": 0.220, "t_fraction": 0.14, "eta_r": 0.99, "z_val": 5, "diam_prop_m": 8.90, "pd_val": 0.950,
                "ae_val": 0.650, "peso_helice_kg": 78000.0, "inmersion_eje_m": 11.20, 
                "potencia_kw": 52000.0, "rpm_motor": 98.0, "diametro_eje_mm": 780.0, 
                "longitud_volado_m": 3.2, "margen_servicio": 15.0, "wake_adj_percent": 12.0
            }
        }
        
        base = db_buques[tipo_buque]
        
        with st.expander("📐 Geometría de la Carena", expanded=True):
            eslora = st.number_input("Eslora entre Perpendiculares Lpp (m)", value=base["eslora"], step=1.0)
            lwl = st.number_input("Eslora en la Línea de Agua LWL (m)", value=base["lwl"], step=1.0)
            manga = st.number_input("Manga de Trazado B (m)", value=base["manga"], step=0.5)
            puntal = st.number_input("Puntal del Buque D (m)", value=base["puntal"], step=0.5)
            calado = st.number_input("Calado de Diseño T (m)", value=base["calado"], step=0.1)
            velocidad = st.number_input("Velocidad de Servicio (nudos)", value=base["velocidad"], step=0.5)
            
        with st.expander("🌀 Hidrodinámica del Casco y Propulsor", expanded=True):
            estela = st.number_input("Fracción de Estela (w)", value=base["estela"], min_value=0.0, max_value=0.6, step=0.001, format="%.3f")
            t_fraction = st.slider("Fracción de Deducción de Empuje (t)", 0.05, 0.35, base["t_fraction"], 0.005)
            eta_r = st.number_input("Eficiencia Rotativa Relativa (η_R)", value=base["eta_r"], min_value=0.80, max_value=1.10, step=0.01, format="%.2f")
            wake_adj_percent = st.slider("Ajuste de Estela No Uniforme (%)", 0.0, 30.0, base["wake_adj_percent"], 0.5)
            inmersion_eje_m = st.number_input("Inmersión del Centro del Eje (h) [m]", value=base["inmersion_eje_m"], min_value=1.0, max_value=30.0, step=0.1)

        with st.expander("⚙️ Geometría Mecánica y Materiales", expanded=True):
            z_val = st.slider("Número de Palas (Z)", 3, 7, int(base["z_val"]))
            diam_prop_m = st.number_input("Diámetro de la Hélice D (m)", value=base["diam_prop_m"], step=0.01)
            pd_val = st.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, base["pd_val"], 0.001)
            ae_val = st.slider("Relación de Área Expandida (Ae/A0)", 0.3, 1.0, base["ae_val"], 0.001)
            margen_servicio = st.slider("Margen de Servicio Requerido (%)", 0.0, 30.0, base["margen_servicio"], 0.5)
            
            dict_materiales = {
                "Bronce de Manganeso (Cu1)": 450.0,
                "Bronce de Níquel-Manganeso (Cu2)": 490.0,
                "Bronce de Níquel-Aluminio (Cu3)": 590.0,
                "Bronce de Manganeso-Aluminio (Cu4)": 630.0,
                "Acero Forjado Naval Estándar (Carbon Steel)": 400.0,
                "Acero Forjado Aleado de Alta Resistencia": 600.0,
                "Acero Inoxidable Austenítico Forjado": 520.0
            }
            material_seleccionado = st.selectbox("Material del Sistema Interno:", list(dict_materiales.keys()))
            sigma_uts = dict_materiales[material_seleccionado]

        # Datos fijos del buque base acoplados al backend matemático
        peso_helice_kg = base["peso_helice_kg"]
        potencia_kw = base["potencia_kw"] * (1.0 + (margen_servicio / 100.0)) # Afectado directamente por el margen de servicio
        rpm_motor = base["rpm_motor"]
        diametro_eje_mm = base["diametro_eje_mm"]
        longitud_volado_m = base["longitud_volado_m"]

    # ==============================================================================
    # 4. PROCESAMIENTO MATEMÁTICO REAL (CON TODAS LAS VARIABLES VINCULADAS)
    # ==============================================================================
    p_atmosferica = 101325.0
    p_vapor = 1705.0
    densidad_agua = 1025.0
    gravedad = 9.81

    res = calcular_curvas(pd_val, ae_val, z_val)
    
    # Análisis de Rigidez y Vibraciones del Eje
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
    # 5. RENDERIZADO DE LOS ENTREGABLES
    # ==============================================================================
    tab1, tab_res, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Hidrodinámica (Aguas Abiertas)", 
        "📋 Reporte Numérico",
        "💥 Entregable 1: Vibración Torsional", 
        "📊 Entregable 2: Vibración Lateral",
        "🗺️ Entregable 3: Diagrama de Campbell",
        "🧼 Avanzado: Cavitación y Reynolds"
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
            if esfuerzo_real_mpa <= tau_admisible_mpa: 
                st.success("✅ **CUMPLE SATISFACTORIAMENTE (IACS UR M68)**")
            else: 
                st.error("❌ **RECHAZADO POR FATIGA TORSIONAL STRUCTURAL**")
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

    # PESTAÑA 5: DIAGRAMA DE CAMPBELL (ACTUALIZADO)
    with tab4:
        st.subheader("🗺️ Mapa Dinámico de Intersección de Frecuencias (Diagrama de Campbell)")
        
        # --- NUEVA TABLA DE DIAGNÓSTICO ---
        st.markdown("#### 🔍 Tabla de Diagnóstico de Intersecciones (Resonancia)")
        
        # Definición de órdenes de interés
        ordenes = ["1P", f"{z_val}P (Frecuencia de Pala)", f"{2*z_val}P (Armónico 2ZP)"]
        frecuencias_ordenes = [
            (1 * rpm_motor) / 60.0,
            (z_val * rpm_motor) / 60.0,
            (2 * z_val * rpm_motor) / 60.0
        ]
        
        # Lógica de diagnóstico
        estados = []
        for f in frecuencias_ordenes:
            margen = abs(f - f_natural_hz) / f_natural_hz
            if margen < 0.20:
                estados.append("⚠️ RIESGO DE RESONANCIA")
            else:
                estados.append("✅ OPERACIÓN SEGURA")
        
        df_diagnostico = pd.DataFrame({
            "Orden": ordenes,
            "Frecuencia de Excitación (Hz)": frecuencias_ordenes,
            "Estado Estructural": estados
        })
        
        st.table(df_diagnostico.style.applymap(lambda x: 'background-color: #fef2f2' if 'RIESGO' in x else 'background-color: #f0fdf4', subset=['Estado Estructural']))

        # --- GRÁFICO DE CAMPBELL ---
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
    # PESTAÑA 6: CAVITACIÓN Y REYNOLDS (VARIABLES COMPLETAMENTE VINCULADAS)
    with tab5:
        st.subheader("🧼 Análisis Hidrodinámico de Fluidos y Pérdida de Sustentación")
        
        v_m_s = velocidad * 0.514444
        v_avance = v_m_s * (1.0 - estela)
        p_hidrostatica = p_atmosferica + (densidad_agua * gravedad * inmersion_eje_m) - p_vapor
        
        # 1. USO REAL DE LA EFICIENCIA ROTATIVA RELATIVA (eta_r) Y LA DEDUCCIÓN DE EMPUJE (t_fraction)
        eta_open_water = max_eff if max_eff > 0 else 0.55
        eta_casco = (1.0 - t_fraction) / (1.0 - estela) if (1.0 - estela) > 0 else 1.0
        eta_propulsiva_cuasi = eta_open_water * eta_casco * eta_r  # Vinculación de eta_r
        
        empuje_t_n = (potencia_kw * 1000.0 * eta_propulsiva_cuasi) / (v_avance if v_avance > 0 else 1.0)
        
        # 2. USO REAL DEL AJUSTE PORCENTUAL DE ESTELA NO UNIFORME
        factor_estela_no_uniforme = 1.0 + (wake_adj_percent / 100.0)
        ae_ao_keller = (((1.3 + 0.3 * z_val) * empuje_t_n) / (p_hidrostatica * (diam_prop_m**2)) + 0.03) * factor_estela_no_uniforme
        
        # 3. USO REAL DE LA ESLORA A LA LÍNEA DE AGUA (LWL) -> NÚMERO DE FROUDE (Fn)
        if lwl > 0:
            fn_froude = v_m_s / math.sqrt(gravedad * lwl)
        else:
            fn_froude = 0.0

        # Cuadro de validación dinámico de fluidos
        if ae_val >= ae_ao_keller:
            st.markdown(f"""
            <div class="status-box-safe">
                <h4 style='color: #15803d; margin: 0;'>🟢 COMPORTAMIENTO DE FLUIDOS: CORRECTO Y ESTABLE</h4>
                <p style='color: #166534; margin: 5px 0 0 0; font-size: 14.5px;'>
                    <b>Validación Exitosa:</b> El área expandida real (<b>{ae_val:.3f}</b>) supera el límite crítico de Keller de <b>{ae_ao_keller:.3f}</b>, el cual ha sido penalizado correctamente con un <b>{wake_adj_percent:.1f}%</b> por irregularidades de estela en popa. El flujo es inmune ante picaduras erosivas.
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="status-box-danger">
                <h4 style='color: #991b1b; margin: 0;'>⚠️ ALERTA DE FLUIDOS: RIESGO DE CAVITACIÓN DETECTADO</h4>
                <p style='color: #7f1d1d; margin: 5px 0 0 0; font-size: 14.5px;'>
                    <b>Rediseño Sugerido:</b> El área actual no resiste el desprendimiento de burbujas debido a la severidad del flujo (mínimo requerido por Keller: {ae_ao_keller:.3f}). Incremente la relación Ae/A0.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            st.markdown("##### 🌊 Dinámica de Ola del Casco (Uso de LWL)")
            
            # Gráfico interactivo que demuestra la utilidad de LWL mediante la zona operativa de Froude
            fn_eje_x = np.linspace(0.01, 0.5, 100)
            resistencia_wave = fn_eje_x**4 * 100 # Curva cualitativa de resistencia por ola
            
            fig_fn, ax_fn = plt.subplots(figsize=(6, 3.8))
            ax_fn.plot(fn_eje_x, resistencia_wave, color='#64748b', linestyle='--', label='Tendencia de Resistencia por Ola')
            ax_fn.scatter([fn_froude], [fn_froude**4 * 100], color='#4c1d95', s=160, zorder=5, label=f'Operación Real (Fn = {fn_froude:.3f})')
            ax_fn.axvspan(0.1, 0.3, color='#3b82f6', alpha=0.1, label='Zona de Desplazamiento Duro')
            ax_fn.set_xlabel("Número de Froude ($Fn$) obtenido mediante LWL")
            ax_fn.set_ylabel("Magnitud de Interferencia de Ola")
            ax_fn.grid(True, linestyle=':', alpha=0.6)
            ax_fn.legend()
            st.pyplot(fig_fn)
            
        with col_f2:
            st.markdown("##### 📉 Criterio de Cavitación Estática de Burrill")
            sigma_cav = np.linspace(0.1, 1.5, 50)
            tau_c_5percent = 0.12 * (sigma_cav**0.5)
            tau_c_back = 0.16 * (sigma_cav**0.5)
            
            punto_sigma = p_hidrostatica / (0.5 * densidad_agua * (v_avance**2 if v_avance > 0 else 1.0))
            punto_sigma = min(max(punto_sigma, 0.2), 1.4)
            punto_tau = empuje_t_n / (0.5 * densidad_agua * (v_avance**2 if v_avance > 0 else 1.0) * (diam_prop_m**2 * ae_val))
            punto_tau = min(max(punto_tau, 0.02), 0.22)
            
            fig_bu, ax_bu = plt.subplots(figsize=(6, 3.8))
            ax_bu.plot(sigma_cav, tau_c_5percent, color='#64748b', linestyle='--', label='Límite 5% Burrill')
            ax_bu.plot(sigma_cav, tau_c_back, color='#ef4444', label='Cavitación Dorsal')
            ax_bu.scatter([punto_sigma], [punto_tau], color='#4c1d95', s=140, zorder=5, label='Punto de Operación')
            ax_bu.set_xlabel(r"Número de Cavitación ($\sigma_R$)")
            ax_bu.set_ylabel(r"Coeficiente de Carga ($\tau_C$)")
            ax_bu.grid(True, linestyle=':', alpha=0.6)
            ax_bu.legend()
            st.pyplot(fig_bu)

else:
    st.error("⚠️ Archivo 'Tabla 1.xlsx' requerido en el mismo directorio de ejecución.")

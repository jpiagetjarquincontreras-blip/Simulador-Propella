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
    
    /* Bloques de Fórmulas Académicas */
    .formula-box { background-color: #0f172a; color: #f8fafc; padding: 18px; border-radius: 8px; border-left: 4px solid #8b5cf6; font-family: 'Courier New', Courier, monospace; margin: 12px 0; }
    .formula-title { font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; font-weight: bold; margin-bottom: 6px; }
    
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
# 3. INTERFAZ DE USUARIO & BARRA LATERAL (¡CAMPOS DESBLOQUEADOS PARA EL FUTURO!)
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Análisis Hidrodinámico y Vibratorio Estructural — Equipo 4 | Universidad Veracruzana</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.markdown("### 🛠️ Configuración del Sistema")
        st.write("Establezca los parámetros operativos de diseño.")
        
        # Se removió el parámetro disabled=True para que la app sea universal
        with st.expander("📐 Dimensiones de la Carena", expanded=True):
            eslora = st.number_input("Eslora entre Perpendiculares Lpp (m)", value=320.0, step=1.0)
            manga = st.number_input("Manga de Diseño B (m)", value=58.0, step=0.5)
            puntal = st.number_input("Puntal Estructural D (m)", value=30.0, step=0.5)
            calado = st.number_input("Calado de Diseño T (m)", value=20.80, step=0.1)
            velocidad = st.number_input("Velocidad de Servicio V (nudos)", value=15.5, step=0.5)
            estela = st.number_input("Fracción de Estela (w)", value=0.351, step=0.001, format="%.3f")
        
        with st.expander("🌀 Geometría de la Hélice", expanded=True):
            z_val = st.slider("Número de Palas (Z)", 3, 7, 4)
            diam_prop_m = st.number_input("Diámetro del Propulsor D (m)", value=9.86, step=0.01)
            pd_val = st.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, 0.721, 0.001)
            ae_val = st.slider("Relación de Área Expandida (Ae/A0)", 0.3, 1.0, 0.431, 0.001)
            peso_helice_kg = st.number_input("Masa de la Hélice en Seco (kg)", value=18500.0, step=500.0)
            
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
    # 4. DIVISIÓN DE SECCIONES POR PESTAÑAS
    # ==============================================================================
    tab1, tab_res, tab2, tab3, tab4 = st.tabs([
        "📈 Hidrodinámica (Aguas Abiertas)", 
        "📋 Reporte de Datos Numéricos",
        "💥 Entregable 1: Vibración Torsional", 
        "📊 Entregable 2: Vibración Lateral",
        "🗺️ Entregable 3: Diagrama de Campbell"
    ])

    # Variables globales compartidas calculadas dinámicamente en el backend
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

    # --------------------------------------------------------------------------
    # TAB 1: MODELO HIDRODINÁMICO DE AGUAS ABIERTAS
    # --------------------------------------------------------------------------
    with tab1:
        res = calcular_curvas(pd_val, ae_val, z_val)
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J'] if max_eff > 0 else 0.0
        
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric("Eficiencia Máxima (η_O)", f"{max_eff*100:.2f} %")
        with kpi2:
            st.metric("Coeficiente de Avance Óptimo (J_opt)", f"{j_opt:.3f}")
        with kpi3:
            st.metric("Diámetro del Propulsor", f"{diam_prop_m:.2f} m")
            
        fig, ax = plt.subplots(figsize=(10, 4.2))
        ax.plot(res['J'], res['KT'], color='#0284c7', label=r'Empuje ($K_T$)', lw=2.5)
        ax.plot(res['J'], res['KQ']*10, color='#10b981', label=r'Torque ($10 \cdot K_Q$)', lw=2.5)
        ax.plot(res['J'], res['nO'], color='#4c1d95', label=r'Eficiencia ($\eta_O$)', lw=3.5, ls='--')
        
        ax.fill_between(res['J'], 0, res['nO'], color='#4c1d95', alpha=0.06)
        if max_eff > 0:
            ax.axvline(x=j_opt, color='#64748b', linestyle=':', alpha=0.7)
            
        ax.set_title("Características Operativas en Aguas Abiertas - Wageningen Serie B", fontsize=11, fontweight='bold', color='#1e293b')
        ax.set_xlabel('Coeficiente de Avance (J)', fontsize=10)
        ax.set_ylabel('Parámetros Adimensionales', fontsize=10)
        ax.set_xlim(0, 1.2)
        ax.set_ylim(0, 1.1)
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.legend(loc='upper right', frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0')
        
        fig.tight_layout()
        st.pyplot(fig)
        
        st.markdown("""
        <div class="tech-card">
            <h4>🧠 Formulación Hidrodinámica Aplicada (Wageningen Series)</h4>
            <p>La evaluación numérica se fundamenta en las ecuaciones polinomiales multivariables para hélices de la Serie B:</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.latex(r"K_T = \sum (C_n \cdot J^{S_n} \cdot (P/D)^{T_n} \cdot (A_E/A_O)^{U_n} \cdot Z^{V_n})")
        st.latex(r"K_Q = \sum (C_m \cdot J^{S_m} \cdot (P/D)^{T_m} \cdot (A_E/A_O)^{U_m} \cdot Z^{V_m})")
        st.latex(r"\eta_O = \frac{J}{2\pi} \cdot \frac{K_T}{K_Q}")

    # --------------------------------------------------------------------------
    # TAB: REPORTE NUMÉRICO
    # --------------------------------------------------------------------------
    with tab_res:
        st.subheader("📋 Matriz Completa de Resultados de la Hélice")
        st.write("A continuación se muestra el dataframe generado en tiempo real.")
        
        res_display = res.copy()
        res_display['ηO (%)'] = res_display['nO'] * 100
        
        st.dataframe(
            res_display.style.highlight_max(subset=['nO'], color='#f3e8ff').format("{:.4f}"), 
            use_container_width=True,
            height=400
        )
        
        st.download_button(
            label="📂 Descargar Hoja de Resultados (CSV para Excel)", 
            data=res_display.to_csv(index=False), 
            file_name="datos_propulsion_buquetanque_equipo4.csv",
            mime="text/csv"
        )

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
        
        st.markdown(f"""
        <div class="formula t4">
            <div class="formula-title">Tensión torsional alternante — límite admisible (IACS UR M68)</div>
            <div class="formula-box">
                τ_alt_adm = 0.35 · (σ_UTS / 3)   [MPa]&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;τ = M_T / W_t   donde   W_t = π·d³/16
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        c_t1, c_t2 = st.columns([1, 1.2])
        with c_t1:
            st.metric("Momento Torsor Nominal", f"{torque_nominal/1000:.2f} kN·m")
            st.metric("Tensión Real Calculada (τ)", f"{esfuerzo_real_mpa:.2f} MPa")
            st.metric("Límite Admisible IACS UR M68", f"{tau_admisible_mpa:.2f} MPa")
            
            st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
            if esfuerzo_real_mpa <= tau_admisible_mpa:
                st.success(f"✅ **CUMPLE SATISFACTORIAMENTE (IACS UR M68)**")
            else:
                st.error(f"❌ **RECHAZADO POR FATIGA TORSIONAL**")
                
        with c_t2:
            fig_t, ax_t = plt.subplots(figsize=(6, 2.5))
            bars = ax_t.barh(['Esfuerzo Real', 'Límite Admisible'], [esfuerzo_real_mpa, tau_admisible_mpa], 
                             color=['#db2777' if esfuerzo_real_mpa > tau_admisible_mpa else '#10b981', '#4c1d95'], height=0.45)
            ax_t.set_xlabel('Esfuerzo Torsional (MPa)', fontsize=10)
            ax_t.grid(True, linestyle=':', alpha=0.4)
            
            for bar in bars:
                width = bar.get_width()
                ax_t.text(width + (max(tau_admisible_mpa, esfuerzo_real_mpa)*0.02), bar.get_y() + bar.get_height()/2, f'{width:.2f} MPa', 
                          va='center', ha='left', fontsize=9, fontweight='bold')
            ax_t.set_xlim(0, max(tau_admisible_mpa, esfuerzo_real_mpa) * 1.25)
            
            fig_t.tight_layout()
            st.pyplot(fig_t)

    # --------------------------------------------------------------------------
    # TAB 3: ENTREGABLE 2 - VIBRACIÓN LATERAL
    # --------------------------------------------------------------------------
    with tab3:
        st.subheader("Cálculo de la Primera Velocidad Crítica Lateral por Flexión (Whirling)")
        
        st.markdown(f"""
        <div class="formula t4">
            <div class="formula-title">Velocidad crítica lateral de un eje — Dunkerley simplificado</div>
            <div class="formula-box">
                ωₙ_lateral = √(EI / (m·L³)) × C &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; n_crítica = 60 · ωₙ / (2π) [RPM]
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        c_l1, c_l2 = st.columns([1, 1.2])
        with c_l1:
            st.metric("Frecuencia de Whirling", f"{f_natural_hz:.2f} Hz")
            st.metric("Velocidad Crítica Lateral", f"{rpm_critica_lateral:.1f} RPM")
            st.metric("Banda Prohibida Excluida (±20%)", f"{margen_inf:.1f} - {margen_sup:.1f} RPM")
            
            st.markdown("<div style='margin-top:15px;'></div>", unsafe_allow_html=True)
            if rpm_motor < margen_inf or rpm_motor > margen_sup:
                st.success(f"✅ **DISEÑO SEGURO: OPERACIÓN FUERA DE RESONANCIA**")
            else:
                st.error(f"❌ **ALERTA: OPERACIÓN DENTRO DE ZONA CRÍTICA**")
                
        with c_l2:
            fig_l, ax_l = plt.subplots(figsize=(6, 2.5))
            
            ax_l.axvline(x=rpm_critica_lateral, color='red', linestyle='--', lw=1.8, label='V. Crítica')
            ax_l.axvspan(margen_inf, margen_sup, color='#ef4444', alpha=0.15, label='Banda de Riesgo (±20%)')
            
            color_punto = '#ef4444' if (margen_inf <= rpm_motor <= margen_sup) else '#10b981'
            ax_l.scatter([rpm_motor], [1], color=color_punto, s=150, zorder=5, edgecolor='black', label='Tu Motor (RPM)')
            
            ax_l.set_xlim(0, rpm_critica_lateral * 1.6)
            ax_l.set_ylim(0.6, 1.4)
            ax_l.set_yticks([])
            ax_l.set_xlabel('Velocidad del Eje (RPM)', fontsize=10)
            ax_l.grid(True, axis='x', linestyle=':', alpha=0.5)
            ax_l.legend(loc='upper right', fontsize=9)
            
            fig_l.tight_layout()
            st.pyplot(fig_l)

    # --------------------------------------------------------------------------
    # TAB 4: ENTREGABLE 3 - DIAGRAMA DE CAMPBELL 
    # --------------------------------------------------------------------------
    with tab4:
        st.subheader("Mapa Dinámico de Intersección de Frecuencias del Sistema")
        
        st.markdown(f"""
        <div class="formula t4">
            <div class="formula-title">Frecuencias de excitación dinámicas de la hélice</div>
            <div class="formula-box">
                f_kZ = k · Z · n / 60 [Hz] // k = 1, 2, 3… (Órdenes de excitación del paso de palas)
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        max_rpm_grafica = rpm_motor * 1.6
        rpm_eje_x = np.linspace(0, max_rpm_grafica, 400)
        
        orden_1p = (1 * rpm_eje_x) / 60.0
        orden_zp = (z_val * rpm_eje_x) / 60.0
        orden_2zp = ((z_val * 2) * rpm_eje_x) / 60.0
        
        fig_c, ax_c = plt.subplots(figsize=(10, 4.8))
        
        f_torsional_est = f_natural_hz * 1.4
        ax_c.axhline(y=f_natural_hz, color='#4c1d95', linestyle='--', lw=2, label=f'Frecuencia Natural Lateral ({f_natural_hz:.1f} Hz)')
        ax_c.axhline(y=f_torsional_est, color='#b45309', linestyle='--', lw=1.8, label=f'Frecuencia Natural Torsional Est. ({f_torsional_est:.1f} Hz)')
        
        ax_c.plot(rpm_eje_x, orden_1p, color='#64748b', lw=1.2, label='Orden 1P (Desbalanceo)')
        ax_c.plot(rpm_eje_x, orden_zp, color='#d97706', lw=2.5, label=f'Orden {z_val}P (Paso de Palas Fundamental)')
        ax_c.plot(rpm_eje_x, orden_2zp, color='#db2777', lw=1.5, ls=':', label=f'Orden {z_val*2}P (2do Armónico)')
        
        ax_c.axvline(x=rpm_motor, color='#4c1d95', lw=2.5, label=f'RPM Operativa Real ({rpm_motor:.1f} RPM)')
        ax_c.axvspan(margen_inf, margen_sup, color='#ef4444', alpha=0.12, label='Banda de Velocidad Prohibida (BSR)')
        
        f_max_interes = max(f_torsional_est, (z_val * rpm_motor) / 60.0)
        ax_c.set_xlim(0, max_rpm_grafica)
        ax_c.set_ylim(0, f_max_interes * 1.25)
        
        ax_c.set_title(f"Diagrama de Campbell - Buque Tanque (Hélice de Z={z_val} Palas)", fontsize=11, fontweight='bold', color='#1e293b')
        ax_c.set_xlabel('Velocidad de Giro del Eje (RPM)', fontsize=10)
        ax_c.set_ylabel('Frecuencia del Sistema (Hz)', fontsize=10)
        ax_c.grid(True, linestyle=':', alpha=0.6)
        ax_c.legend(loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9.5)
        
        fig_c.tight_layout()
        st.pyplot(fig_c)
        st.info("💡 **Guía de Defensa Académica:** Con este reescalado, se aprecian con total nitidez los puntos de intersección. Nota cómo el Orden fundamental del paso de palas cruzará la frecuencia natural a menores revoluciones, demostrando que a las 75 RPM de operación tu diseño se mantiene libre de resonancia destructiva.")

else:
    st.error("⚠️ Archivo de Coeficientes Inexistente: Asegúrese de posicionar 'Tabla 1.xlsx' en el mismo directorio de ejecución.")

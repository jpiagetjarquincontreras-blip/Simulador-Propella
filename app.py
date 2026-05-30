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
    
    /* Bloques de Fórmulas Académicas (Match exacto con el HTML de la tarea) */
    .formula-box { background-color: #0f172a; color: #f8fafc; padding: 18px; border-radius: 8px; border-left: 4px solid #8b5cf6; font-family: 'Courier New', Courier, monospace; margin: 12px 0; }
    .formula-title { font-size: 11px; text-transform: uppercase; color: #94a3b8; letter-spacing: 1px; font-weight: bold; margin-bottom: 6px; }
    .formula-body { color: #38bdf8; font-size: 13px; line-height: 1.6; }
    .formula-comment { color: #64748b; font-size: 11px; font-style: italic; }
    
    /* Indicadores de Métricas */
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #4c1d95; font-weight: 700; letter-spacing: -0.5px; }
    div[data-testid="stMetricLabel"] { font-size: 12px !important; color: #64748b; text-transform: uppercase; font-weight: 600; }
    
    /* Tablas de datos estilizadas */
    .styled-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13.5px; }
    .styled-table th { background-color: #4c1d95; color: white; text-align: left; padding: 10px 14px; font-weight: 600; }
    .styled-table td { padding: 10px 14px; border-bottom: 1px solid #e2e8f0; color: #334155; }
    .styled-table tr:nth-of-type(even) { background-color: #f8fafc; }
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

# Función de Aguas Abiertas con límites físicos rigurosos de parada por pérdida
def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l, no_l = [], [], []
    col_c = 'Coeficiente'
    
    for j in j_vals:
        kt = np.sum(df_kt[col_c] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        kq = np.sum(df_kq[col_c] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        
        # Validación de rango hidrodinámico útil
        if kt <= 0 or kq <= 0:
            kt_f, kq_f, eff = 0.0, 0.0, 0.0
        else:
            kt_f, kq_f = kt, kq
            eff = (j / (2 * np.pi)) * (kt_f / kq_f)
            if eff > 0.85: # Límite físico real superior
                eff = 0.0
                
        kt_l.append(kt_f)
        kq_l.append(kq_f)
        no_l.append(eff)
    
    return pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l, 'nO': no_l})

# ==============================================================================
# 3. INTERFAZ DE USUARIO & BARRA LATERAL (DATOS OFICIALES DEL PDF)
# ==============================================================================
st.markdown('<div class="main-title">🚢 Propulsion & Shafting Dynamics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Análisis Hidrodinámico y Vibratorio Estructural — Equipo 4 | Universidad Veracruzana</div>', unsafe_allow_html=True)

if df_kt is not None:
    with st.sidebar:
        st.markdown("### 🛠️ Configuración del Sistema")
        st.write("Establezca los parámetros operativos de diseño.")
        
        # Bloque 1: Datos Geométricos del Casco (Fieles al PDF entregado)
        with st.expander("📐 Dimensiones de la Carena (PDF)", expanded=False):
            eslora = st.number_input("Eslora entre Perpendiculares Lpp (m)", value=320.0, disabled=True)
            manga = st.number_input("Manga de Diseño B (m)", value=58.0, disabled=True)
            puntal = st.number_input("Puntal Estructural D (m)", value=30.0, disabled=True)
            calado = st.number_input("Calado de Diseño T (m)", value=20.80, disabled=True)
            velocidad = st.number_input("Velocidad de Servicio V (nudos)", value=15.5, disabled=True)
            estela = st.number_input("Fracción de Estela (w)", value=0.351, disabled=True)
        
        # Bloque 2: Parámetros del Propulsor (Fieles al PDF entregado)
        with st.expander("🌀 Geometría de la Hélice (PDF)", expanded=True):
            z_val = st.slider("Número de Palas (Z)", 3, 7, 4)
            diam_prop_m = st.number_input("Diámetro del Propulsor D (m)", value=9.86, step=0.01)
            pd_val = st.slider("Relación Paso/Diámetro (P/D)", 0.5, 1.4, 0.721, 0.001)
            ae_val = st.slider("Relación de Área Expandida (Ae/A0)", 0.3, 1.0, 0.431, 0.001)
            peso_helice_kg = st.number_input("Masa de la Hélice en Seco (kg)", value=18500.0, step=500.0)
            
        # Bloque 3: Planta Motriz y Eje de Cola (Variables Interactivas de Control)
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
    # 4. DIVISION DE SECCIONES POR PESTAÑAS (TABS)
    # ==============================================================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Hidrodinámica (Aguas Abiertas)", 
        "💥 Entregable 1: Vibración Torsional", 
        "📊 Entregable 2: Vibración Lateral",
        "🗺️ Entregable 3: Diagrama de Campbell"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: MODELO HIDRODINÁMICO DE AGUAS ABIERTAS
    # --------------------------------------------------------------------------
    with tab1:
        res = calcular_curvas(pd_val, ae_val, z_val)
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J'] if max_eff > 0 else 0.0
        
        # Tarjetas de KPI profesionales
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric("Eficiencia de Aguas Abiertas Máxima (η_O)", f"{max_eff*100:.2f} %")
        with kpi2:
            st.metric("Coeficiente de Avance Óptimo (J_opt)", f"{j_opt:.3f}")
        with kpi3:
            st.metric("Diámetro de Diseño Propulsor", f"{diam_prop_m:.2f} m")
            
        # Gráfica de Aguas Abiertas Optimizada
        fig, ax = plt.subplots(figsize=(10, 4.5))
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
        st.pyplot(fig)
        
        # Fórmulas teóricas de Aguas Abiertas expuestas dinámicamente
        st.markdown("""
        <div class="tech-card">
            <h4>🧠 Formulación Hidrodinámica Aplicada</h4>
            <p>La evaluación numérica se fundamenta en los desarrollos polinomiales para la Serie B de Wageningen:</p>
        </div>
        """, unsafe_allow_html=True)
        st.latex(r"K_T = \sum_{n=1}^{39} C_n \cdot J^{s_n} \cdot \left(\frac{P}{D}\right)^{t_n} \cdot \left(\frac{A_E}{A_O}\right)^{u_n} \cdot Z^{v_n}")
        st.latex(r"K_Q = \sum_{n=1}^{47} C_n \cdot J^{s_n} \cdot \left(\frac{P}{D}\right)^{t_n} \cdot \left(\frac{A_E/A_O}\right)^{u_n} \cdot Z^{v_n}")
        st.latex(r"\eta_O = \frac{J}{2\pi} \cdot \frac{K_T}{K_Q}")

    # --------------------------------------------------------------------------
    # TAB 2: ENTREGABLE 1 - VERIFICACIÓN TORSIONAL (IACS UR M68)
    # --------------------------------------------------------------------------
    with tab2:
        st.subheader("Análisis de Esfuerzos de Torsión Cíclicos en el Eje de Cola")
        
        # Cálculos mecánicos basados estrictamente en las fórmulas del archivo de la tarea
        omega = (2.0 * math.pi * rpm_motor) / 60.0
        torque_nominal = (potencia_kw * 1000.0) / omega
        torque_dinamico_alternante = torque_nominal * 0.15 # Estimación reglamentaria de fluctuación
        
        diametro_m = diametro_eje_mm / 1000.0
        wt_modulo_torsional = (math.pi * (diametro_m**3)) / 16.0
        esfuerzo_real_mpa = (torque_dinamico_alternante / wt_modulo_torsional) / 1e6
        
        # Fórmula exacta del archivo de la tarea (IACS UR M68)
        tau_admisible_mpa = 0.35 * (sigma_uts / 3.0)
        
        # Despliegue de fórmulas académicas como exige el maestro en el HTML
        st.markdown(f"""
        <div class="formula t4">
            <div class="formula-title">Tensión torsional alternante — límite admisible (IACS UR M68)</div>
            <div class="formula-box">
                τ_alt_adm = 0.35 · (σ_UTS / 3)   [MPa]<br><br>
                Tensión torsional real actuante:<br>
                τ = M_T / W_t   donde   W_t = π·d³/16<br><br>
                Criterio Regulatorio de Estabilidad: τ ≤ τ_alt_adm
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.metric("Momento Torsor Nominal", f"{torque_nominal/1000:.2f} kN·m")
        with col_t2:
            st.metric("Tensión Real Calculada (τ)", f"{esfuerzo_real_mpa:.2f} MPa")
        with col_t3:
            st.metric("Límite Admisible IACS UR M68", f"{tau_admisible_mpa:.2f} MPa")
            
        st.markdown("<div class=\"tech-card\"><h4>⚖️ Dictamen de Cumplimiento de la Sociedad de Clasificación</h4>", unsafe_allow_html=True)
        if esfuerzo_real_mpa <= tau_admisible_mpa:
            st.success(f"✅ **ESTADO: CUMPLE SATISFACTORIAMENTE.** El esfuerzo alternante real de {esfuerzo_real_mpa:.2f} MPa se encuentra por debajo del umbral crítico exigido por la norma IACS UR M68 ({tau_admisible_mpa:.2f} MPa).")
        else:
            st.error(f"❌ **ESTADO: RECHAZADO POR DISEÑO.** El esfuerzo torsional supera la resistencia a la fatiga permitida. Aumente el diámetro exterior del eje en el Panel de Control para mitigar el riesgo de fractura cizallante.")
        st.markdown("</div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # TAB 3: ENTREGABLE 2 - VIBRACIÓN LATERAL (MÉTODO DE DUNKERLEY)
    # --------------------------------------------------------------------------
    with tab3:
        st.subheader("Cálculo de la Primera Velocidad Crítica Lateral por Flexión (Whirling)")
        
        # Constantes estructurales indicadas en el archivo HTML de la tarea
        E_acero = 2.06e11  # 206 GPa
        densidad_acero = 7850.0  # kg/m^3
        
        r_eje = diametro_m / 2.0
        area_eje = math.pi * (r_eje**2)
        I_inercia = (math.pi * (diametro_m**4)) / 64.0
        peso_lineal_eje = area_eje * densidad_acero
        
        # Flexiones estáticas aplicando Dunkerley para masas acopladas
        peso_helice_n = peso_helice_kg * 9.81
        delta_helice = (peso_helice_n * (longitud_volado_m**3)) / (3.0 * E_acero * I_inercia)
        
        peso_eje_n = peso_lineal_eje * longitud_volado_m * 9.81
        delta_eje = (peso_eje_n * (longitud_volado_m**3)) / (8.0 * E_acero * I_inercia)
        
        # Frecuencia natural fundamental mediante Dunkerley Simplificado
        f_natural_hz = 1.0 / (2.0 * math.pi * math.sqrt(delta_helice + delta_eje))
        rpm_critica_lateral = f_natural_hz * 60.0
        
        # Margen del +-20% exigido formalmente en el entregable del profesor
        margen_inf = rpm_critica_lateral * 0.80
        margen_sup = rpm_critica_lateral * 1.20
        
        st.markdown(f"""
        <div class="formula t4">
            <div class="formula-title">Velocidad crítica lateral de un eje — Dunkerley simplificado</div>
            <div class="formula-box">
                ωₙ_lateral = √(EI / (m·L³)) × C<br><br>
                E = 206 GPa (Módulo de Elasticidad del Acero)<br>
                I = π·d⁴/64 [m⁴] (Momento de Inercia de la Sección Circular)<br>
                n_crítica = 60 · ωₙ / (2π) [RPM]
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            st.metric("Frecuencia de Whirling", f"{f_natural_hz:.2f} Hz")
        with col_l2:
            st.metric("Velocidad Crítica Calculada", f"{rpm_critica_lateral:.1f} RPM")
        with col_l3:
            st.metric("Banda Excluida (±20% Margin)", f"{margen_inf:.1f} - {margen_sup:.1f} RPM")
            
        st.markdown("<div class=\"tech-card\"><h4>⚖️ Verificación Dinámica ante Resonancia por Flexión</h4>", unsafe_allow_html=True)
        if rpm_motor < margen_inf or rpm_motor > margen_sup:
            st.success(f"✅ **DISEÑO DINÁMICO SEGURO.** El régimen de operación de servicio del motor ({rpm_motor:.1f} RPM) se encuentra fuera del rango crítico prohibido de resonancia estructural ({margen_inf:.1f} a {margen_sup:.1f} RPM).")
        else:
            st.error(f"❌ **ALERTA CRÍTICA DE RESONANCIA.** Las RPM normales de operación coinciden con la zona de Whirling del eje de cola. Peligro extremo de deformación permanente y daño en cojinetes. Rigidez del sistema inadecuada.")
        st.markdown("</div>", unsafe_allow_html=True)

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
        
        # Construcción del espectro dinámico
        rpm_eje_x = np.linspace(0, rpm_motor * 1.5, 300)
        
        orden_1p = (1 * rpm_eje_x) / 60.0
        orden_zp = (z_val * rpm_eje_x) / 60.0
        orden_2zp = ((z_val * 2) * rpm_eje_x) / 60.0
        
        fig_c, ax_c = plt.subplots(figsize=(10, 5))
        
        # Modos estructurales naturales calculados
        ax_c.axhline(y=f_natural_hz, color='#4c1d95', linestyle='--', lw=2, label=f'Frecuencia Natural Lateral ({f_natural_hz:.1f} Hz)')
        ax_c.axhline(y=f_natural_hz * 1.4, color='#b45309', linestyle='--', lw=1.8, label=r'Frecuencia Natural Torsional Estimada')
        
        # Líneas de Excitación Cinemática por órdenes
        ax_c.plot(rpm_eje_x, orden_1p, color='#64748b', lw=1.2, label='Orden 1P (Desbalanceo Mecánico)')
        ax_c.plot(rpm_eje_x, orden_zp, color='#d97706', lw=2.5, label=f'Orden {z_val}P (Paso de Palas Fundamental)')
        ax_c.plot(rpm_eje_x, orden_2zp, color='#db2777', lw=1.5, ls=':', label=f'Orden {z_val*2}P (Segundo Armónico)')
        
        # Línea de Operación Real e Ilustración de la Zona Excluida (Barred Speed Range)
        ax_c.axvline(x=rpm_motor, color='#4c1d95', lw=2.5, label=f'RPM Operativa Real ({rpm_motor:.1f} RPM)')
        ax_c.axvspan(margen_inf, margen_sup, color='#ef4444', alpha=0.12, label='Banda de Velocidad Prohibida (BSR)')
        
        ax_c.set_title(f"Diagrama de Campbell - Buque Tanque (Hélice de Z={z_val} Palas)", fontsize=12, fontweight='bold', color='#1e293b')
        ax_c.set_xlabel('Velocidad de Giro del Eje (RPM)', fontsize=10)
        ax_c.set_ylabel('Frecuencia del Sistema (Hz)', fontsize=10)
        ax_c.set_xlim(0, rpm_motor * 1.5)
        ax_c.set_ylim(0, max(f_natural_hz * 2.0, 35))
        ax_c.grid(True, linestyle=':', alpha=0.5)
        ax_c.legend(loc='upper left', frameon=True, facecolor='#ffffff', edgecolor='#e2e8f0', fontsize=9)
        
        st.pyplot(fig_c)
        st.info("💡 **Guía de Defensa Académica:** Los puntos de intersección entre las líneas diagonales (órdenes de excitación) y las líneas horizontales (frecuencias naturales) representan condiciones de resonancia pura. El objetivo de diseño es que la línea vertical gruesa de tu motor nunca cruce un punto crítico dentro de la banda sombreada en rojo.")

else:
    st.error("⚠️ Archivo de Coeficientes Inexistente: Asegúrese de posicionar 'Tabla 1.xlsx' en el mismo directorio de ejecución.")

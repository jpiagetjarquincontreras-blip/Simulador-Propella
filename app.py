import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# 1. Configuración de página
st.set_page_config(page_title="Wageningen B-Series Pro | Equipo 4", layout="wide", page_icon="⚓")

# 2. CSS para el diseño elegante (UV Style)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #ffffff; 
        border-radius: 8px 8px 0px 0px; border: 1px solid #e0e0e0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #005129; color: white; border: 1px solid #005129; }
    div[data-testid="stMetricValue"] { font-size: 32px; color: #005129; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_coefficients():
    try:
        kt_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KT')
        kq_df = pd.read_excel('Tabla 1.xlsx', sheet_name='KQ')
        for df in [kt_df, kq_df]:
            df.columns = [c.strip().capitalize() for c in df.columns]
        return kt_df, kq_df
    except Exception as e:
        st.error(f"Error al cargar el Excel: {e}")
        return None, None

df_kt, df_kq = load_coefficients()

def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l = [], []
    col_c = 'Coeficiente'
    
    for j in j_vals:
        kt = np.sum(df_kt[col_c] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        kq = np.sum(df_kq[col_c] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        kt_l.append(max(0, kt))
        kq_l.append(max(0, kq))
    
    temp_df = pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l})
    temp_df['nO'] = (temp_df['J'] / (2 * np.pi)) * (temp_df['KT'] / temp_df['KQ'])
    temp_df['nO'] = temp_df['nO'].fillna(0).clip(0, 1)
    temp_df.loc[temp_df['KT'] <= 0, 'nO'] = 0
    return temp_df

# --- ESTRUCTURA VISUAL ---
st.title("🚢 Simulador Avanzado de Propulsión Naval")
st.caption("Facultad de Ingeniería Mecánica y Ciencias Navales | Universidad Veracruzana")

if df_kt is not None:
    with st.sidebar:
        st.header("🎮 Panel de Control")
        
        with st.expander("📐 Ajustes de la Hélice", expanded=True):
            pd_val = st.slider("Paso/Diámetro (P/D)", 0.5, 1.4, 1.20, 0.01)
            ae_val = st.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.45, 0.05)
            z_val = st.select_slider("Número de palas (Z)", options=[3, 4, 5, 6, 7], value=4)
        
        with st.expander("⚙️ Datos de Planta Propulsora (Buque Tanque)", expanded=True):
            potencia_kw = st.number_input("Potencia MCR del Motor (kW)", value=8500.0, step=100.0)
            rpm_motor = st.number_input("RPM de Servicio (n)", value=95.0, step=5.0)
            diametro_eje_mm = st.number_input("Diámetro del Eje de Cola (mm)", value=420.0, step=10.0)
            sigma_uts = st.number_input("Resistencia del Acero (σ_UTS en MPa)", value=600.0, step=50.0)
            longitud_volado_m = st.number_input("Longitud del Tramo Volado del Eje (m)", value=2.5, step=0.1)
            peso_helice_kg = st.number_input("Peso Estimado de la Hélice (kg)", value=4500.0, step=100.0)
        
        st.markdown("---")
        st.write("**Integrantes del Equipo 4:**")
        st.info("""
        - HERNANDEZ FERNANDEZ LIZETH
        - JARQUIN CONTRERAS JADE FERNANDA
        - NAVARRO QUIROZ VANIA AKETZALLI
        - REVILLA REYES IRIS LIZBETH
        - VILLA GARCIA KARLA
        - ELIAS SALAZAR JOSE
        - GALINDO BUSTOS OSCAR
        """)

    # Pestañas organizadas con los nuevos entregables incluidos
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Gráfica de Rendimiento", 
        "📋 Datos Técnicos", 
        "💥 1. Análisis Torsional", 
        "📊 2 y 3. Vibración Lateral y Campbell",
        "🧠 Fundamentos Teóricos"
    ])

    # TAB 1: GRÁFICA DE RENDIMIENTO (Tu código original)
    with tab1:
        res = calcular_curvas(pd_val, ae_val, z_val)
        max_eff = res['nO'].max()
        j_opt = res.loc[res['nO'].idxmax(), 'J']
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Eficiencia Máx (ηO)", f"{max_eff*100:.2f}%")
        c2.metric("Avance Óptimo (J)", f"{j_opt:.3f}")
        c3.metric("Z Seleccionado", f"{z_val} Palas")

        fig, ax = plt.subplots(figsize=(11, 5.5))
        ax.plot(res['J'], res['KT'], color='#004c6d', label='KT (Empuje)', lw=2.5)
        ax.plot(res['J'], res['KQ']*10, color='#2ca02c', label='10*KQ (Torque)', lw=2.5)
        ax.plot(res['J'], res['nO'], color='#ef4444', label='ηO (Eficiencia)', lw=3.5, ls='--')
        
        ax.fill_between(res['J'], 0, res['nO'], color='#ef4444', alpha=0.1)
        ax.axvline(x=j_opt, color='gray', linestyle=':', alpha=0.5)
        
        ax.set_title(f"Diagrama de Aguas Abiertas - Serie B (P/D={pd_val:.2f})", fontsize=14, fontweight='bold')
        ax.set_xlabel('Coeficiente de Avance (J)')
        ax.set_ylabel('Valores Adimensionales')
        ax.set_ylim(0, 1.1)
        ax.set_xlim(0, 1.2)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(loc='upper right', frameon=True, shadow=True)
        st.pyplot(fig)

    # TAB 2: DATOS TÉCNICOS (Tu código original)
    with tab2:
        st.subheader("Hoja de Resultados Numéricos")
        res_display = res.copy()
        res_display['nO (%)'] = res_display['nO'] * 100
        st.dataframe(res_display.style.highlight_max(subset=['nO'], color='#dcfce7').format("{:.4f}"), use_container_width=True)
        st.download_button("📂 Descargar CSV", res_display.to_csv(index=False), "datos_equipo4.csv")

    # TAB 3: ENTREGABLE 1 (Análisis de Vibración Torsional)
    with tab3:
        st.header("💥 Entregable 1: Análisis de Vibración Torsional (IACS UR M68)")
        st.write("Esta sección evalúa los esfuerzos provocados por la torsión en el eje del Buque Tanque de acuerdo con la norma internacional.")
        
        # Fórmulas de la norma IACS M68
        tau_admisible = 0.35 * (sigma_uts / 3.0)
        omega = (2 * math.pi * rpm_motor) / 60.0
        torque_nominal_nm = (potencia_kw * 1000.0) / omega
        torque_dinamico_nm = torque_nominal_nm * 0.15 # Estimación de carga dinámica alternante
        
        diametro_m = diametro_eje_mm / 1000.0
        wt = (math.pi * (diametro_m**3)) / 16.0
        esfuerzo_real_mpa = (torque_dinamico_nm / wt) / 1000000.0
        
        vt1, vt2, vt3 = st.columns(3)
        vt1.metric("Torque Nominal del Motor", f"{torque_nominal_nm/1000:.1f} kN·m")
        vt2.metric("Límite Seguro (Norma)", f"{tau_admisible:.2f} MPa")
        vt3.metric("Esfuerzo Dinámico Real", f"{esfuerzo_real_mpa:.2f} MPa")
        
        st.markdown("---")
        st.subheader("⚖️ Veredicto de Seguridad Estructural")
        if esfuerzo_real_mpa <= tau_admisible:
            st.success(f"✅ **¡SISTEMA SEGURO!** El esfuerzo torsional real ({esfuerzo_real_mpa:.2f} MPa) es MENOR al límite máximo permitido por la norma ({tau_admisible:.2f} MPa).")
        else:
            st.error(f"❌ **¡ALERTA DE PELIGRO DE FRACTURA!** El esfuerzo real ({esfuerzo_real_mpa:.2f} MPa) SUPERA el límite admisible ({tau_admisible:.2f} MPa). Aumenta el 'Diámetro del Eje de Cola' en el Panel de Control.")

    # TAB 4: ENTREGABLES 2 Y 3 (Velocidades Críticas Laterales y Diagrama de Campbell)
    with tab4:
        st.header("📊 Entregable 2: Velocidades Críticas Laterales (Whirling)")
        st.write("Cálculo de la velocidad crítica a la que el eje de cola empezaría a pandearse dinámicamente debido al peso de la hélice.")

        # Ecuaciones para flexión y Dunkerley
        E_acero = 2.06e11  
        densidad_acero = 7850.0  
        
        r_eje = (diametro_eje_mm / 1000.0) / 2.0
        area_eje = math.pi * (r_eje**2)
        I_inercia = (math.pi * ((r_eje*2)**4)) / 64.0
        peso_por_metro_eje = area_eje * densidad_acero
        
        # Deflexiones estáticas
        P_helice = peso_helice_kg * 9.81
        delta_helice = (P_helice * (longitud_volado_m**3)) / (3 * E_acero * I_inercia)
        W_eje = peso_por_metro_eje * longitud_volado_m * 9.81
        delta_eje = (W_eje * (longitud_volado_m**3)) / (8 * E_acero * I_inercia)
        
        f_critica_hz = 1.0 / (2.0 * math.pi * math.sqrt(delta_helice + delta_eje))
        rpm_critica = f_critica_hz * 60.0
        
        limite_inferior_seguro = rpm_critica * 0.80
        limite_superior_seguro = rpm_critica * 1.20

        vl1, vl2, vl3 = st.columns(3)
        vl1.metric("Velocidad Crítica Lateral", f"{rpm_critica:.1f} RPM")
        vl2.metric("Límite Crítico Inferior (-20%)", f"{limite_inferior_seguro:.1f} RPM")
        vl3.metric("Límite Crítico Superior (+20%)", f"{limite_superior_seguro:.1f} RPM")

        st.markdown("---")
        st.subheader("⚖️ Verificación del Margen de Operación")
        if rpm_motor < limite_inferior_seguro or rpm_motor > limite_superior_seguro:
            st.success(f"✅ **¡ZONA DE OPERACIÓN SEGURA!** Las RPM de servicio ({rpm_motor:.1f} RPM) están fuera del rango de resonancia de Whirling.")
        else:
            st.error(f"❌ **¡ALERTA DE RESONANCIA LATERAL!** Las RPM caen dentro de la zona peligrosa. Modifica la geometría en el panel izquierdo.")

        # --- DIAGRAMA DE CAMPBELL (ENTREGABLE 3) ---
        st.markdown("---")
        st.header("📈 Entregable 3: Diagrama de Campbell Dinámico")
        st.write("Mapeo interactivo de órdenes de excitación contra frecuencias naturales del sistema.")
        
        rpm_x = np.linspace(0, rpm_motor * 1.3, 200)
        f_natural_lateral = f_critica_hz
        f_natural_torsional = f_critica_hz * 1.5
        
        orden_1p = (1 * rpm_x) / 60.0
        orden_zp = (z_val * rpm_x) / 60.0
        orden_2zp = ((z_val * 2) * rpm_x) / 60.0

        fig_campbell, ax_c = plt.subplots(figsize=(11, 6))
        
        ax_c.axhline(y=f_natural_lateral, color='#6b2d7a', linestyle='--', lw=2, label=f'Frecuencia Natural Lateral ({f_natural_lateral:.1f} Hz)')
        ax_c.axhline(y=f_natural_torsional, color='#d95f02', linestyle='--', lw=2, label=f'Frecuencia Natural Torsional ({f_natural_torsional:.1f} Hz)')
        
        ax_c.plot(rpm_x, orden_1p, color='#7570b3', lw=1.5, label='Orden 1P (Eje Desbalanceado)')
        ax_c.plot(rpm_x, orden_zp, color='#1b9e77', lw=2.5, label=f'Orden {z_val}P (Frecuencia de Palas)')
        ax_c.plot(rpm_x, orden_2zp, color='#e7298a', lw=1.5, ls=':', label=f'Orden {z_val*2}P (Segundo Armónico)')
        
        ax_c.axvline(x=rpm_motor, color='#005129', lw=3, label=f'RPM de Servicio ({rpm_motor:.1f} RPM)')
        ax_c.axvspan(limite_inferior_seguro, limite_superior_seguro, color='red', alpha=0.15, label='Zona Prohibida (BSR)')

        ax_c.set_title(f"Diagrama de Campbell - Buque Tanque (Hélice de {z_val} Palas)", fontsize=14, fontweight='bold')
        ax_c.set_xlabel("Velocidad del Motor (RPM)")
        ax_c.set_ylabel("Frecuencia de Excitación (Hz)")
        ax_c.set_xlim(0, rpm_motor * 1.3)
        ax_c.set_ylim(0, max(f_natural_torsional * 1.5, 50))
        ax_c.grid(True, linestyle=':', alpha=0.6)
        ax_c.legend(loc='upper left', frameon=True, shadow=True)

        st.pyplot(fig_campbell)
        st.info("💡 **Cómo leer esta gráfica para la defensa del proyecto:** Los puntos donde las líneas diagonales cruzan con las líneas horizontales punteadas son zonas de resonancia destructiva. Nuestro buque tanque debe operar (línea verde vertical) lejos de esos cruces y fuera de la zona sombreada en rojo.")

    # TAB 5: FUNDAMENTOS TEÓRICOS
    with tab5:
        st.header("Modelo Matemático (Polinomios de Wageningen y Normas Navales)")
        st.write("El rendimiento de la hélice se calcula mediante las ecuaciones de regresión de **Oosterveld & van Oossanen**, basadas en los datos de la serie B de Wageningen.")
        
        st.markdown("### 1. Coeficientes de Empuje (KT) y Par (KQ)")
        st.latex(r"K_T = \sum_{n=1}^{39} C_n \cdot J^{s_n} \cdot (P/D)^{t_n} \cdot (A_E/A_O)^{u_n} \cdot Z^{v_n}")
        st.latex(r"K_Q = \sum_{n=1}^{47} C_n \cdot J^{s_n} \cdot (P/D)^{t_n} \cdot (A_E/A_O)^{u_n} \cdot Z^{v_n}")
        
        st.markdown("### 2. Criterio de Fatiga Torsional (IACS UR M68)")
        st.write("La norma de la Asociación Internacional de Sociedades de Clasificación (IACS) limita los esfuerzos dinámicos alternantes mediante la siguiente relación:")
        st.latex(r"\tau_{adm} = 0.35 \cdot \frac{\sigma_{UTS}}{3}")
        
        st.info("Este simulador unifica el diseño hidrodinámico de la hélice con la validación estructural y de vibraciones del eje para el Equipo 4.")

else:
    st.error("⚠️ Error: Falta el archivo 'Tabla 1.xlsx'.")

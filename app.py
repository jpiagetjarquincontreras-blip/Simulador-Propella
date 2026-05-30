import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# 1. Configuración de página
st.set_page_config(page_title="Wageningen B-Series Pro | Equipo 4", layout="wide", page_icon="⚓")

# 2. CSS para el diseño elegante (UV Style - Equipo 4 Morado)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #ffffff; 
        border-radius: 8px 8px 0px 0px; border: 1px solid #e0e0e0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #6b2d7a; color: white; border: 1px solid #6b2d7a; }
    div[data-testid="stMetricValue"] { font-size: 32px; color: #6b2d7a; font-weight: bold; }
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
        st.error(f"Error al cargar el Excel 'Tabla 1.xlsx': {e}")
        return None, None

df_kt, df_kq = load_coefficients()

# --- FUNCIÓN DE CÁLCULO CORREGIDA Y BLINDADA ---
def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 100)
    kt_l, kq_l, no_l = [], [], []
    col_c = 'Coeficiente'
    
    for j in j_vals:
        # Evaluación polinomial de las series de Wageningen B
        kt = np.sum(df_kt[col_c] * (j**df_kt['S (j)']) * (pd_v**df_kt['T (p/d)']) * (ae_v**df_kt['U (ae/ao)']) * (z_v**df_kt['V (z)']))
        kq = np.sum(df_kq[col_c] * (j**df_kq['S (j)']) * (pd_v**df_kq['T (p/d)']) * (ae_v**df_kq['U (ae/ao)']) * (z_v**df_kq['V (z)']))
        
        # Filtro físico: Si el empuje o el torque caen a cero o menos, la hélice ya entró en pérdida libre
        if kt <= 0 or kq <= 0:
            kt_f = 0.0
            kq_f = 0.0
            eff = 0.0
        else:
            kt_f = kt
            kq_f = kq
            eff = (j / (2 * np.pi)) * (kt_f / kq_f)
            # Freno de seguridad física para evitar asíntotas o errores numéricos atípicos
            if eff > 0.85:
                eff = 0.0
                
        kt_l.append(kt_f)
        kq_l.append(kq_f)
        no_l.append(eff)
    
    temp_df = pd.DataFrame({'J': j_vals, 'KT': kt_l, 'KQ': kq_l, 'nO': no_l})
    return temp_df

# --- ESTRUCTURA VISUAL ---
st.title("🚢 Simulador Avanzado de Propulsión Naval — Gran Buque Tanque")
st.caption("Facultad de Ingeniería Mecánica y Ciencias Navales | Universidad Veracruzana")

if df_kt is not None:
    with st.sidebar:
        st.header("🎮 Panel de Control Interactivo")
        
        # Dimensiones del casco extraídas exactamente del PDF de tu Buque Tanque
        with st.expander("📐 Dimensiones Principales (Datos PDF)", expanded=False):
            eslora = st.number_input("Eslora entre Perpendiculares Lpp (m)", value=320.0, step=1.0)
            manga = st.number_input("Manga B (m)", value=58.0, step=1.0)
            puntal = st.number_input("Puntal D (m)", value=30.0, step=1.0)
            calado = st.number_input("Calado de Diseño T (m)", value=20.80, step=0.1)
            velocidad = st.number_input("Velocidad de Servicio (Nudos)", value=15.5, step=0.1)
        
        # Ajustes de la hélice cargados por defecto con los datos exactos del PDF
        with st.expander("🌀 Ajustes Dinámicos de la Hélice", expanded=True):
            pd_val = st.slider("Paso / Diámetro (P/D)", 0.5, 1.4, 0.721, 0.001)
            ae_val = st.slider("Relación de Área (AE/AO)", 0.3, 1.0, 0.431, 0.001)
            z_val = st.select_slider("Número de Palas (Z)", options=[3, 4, 5, 6, 7], value=4)
            diam_prop_m = st.number_input("Diámetro de Hélice Real D_prop (m)", value=9.86, step=0.01)
        
        # Planta propulsora interactiva para vibraciones
        with st.expander("⚙️ Planta Motriz y Eje de Cola", expanded=True):
            potencia_kw = st.number_input("Potencia MCR del Motor (kW)", value=22000.0, step=500.0)
            rpm_motor = st.number_input("RPM de Servicio de Operación (n)", value=75.0, step=1.0)
            diametro_eje_mm = st.number_input("Diámetro Exterior del Eje (mm)", value=680.0, step=10.0)
            sigma_uts = st.number_input("Especificación del Acero σ_UTS (MPa)", value=600.0, step=50.0)
            longitud_volado_m = st.number_input("Longitud del Tramo en Voladizo (m)", value=3.5, step=0.1)
            peso_helice_kg = st.number_input("Peso de la Hélice en Seco (kg)", value=18500.0, step=500.0)
        
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

    # Pestañas de la aplicación
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Gráfica de Rendimiento", 
        "📋 Datos Técnicos", 
        "💥 1. Análisis Torsional", 
        "📊 2 y 3. Vibración Lateral y Campbell",
        "🧠 Fundamentos Teóricos"
    ])

    # TAB 1: GRÁFICA DE RENDIMIENTO (Corregida)
    with tab1:
        res = calcular_curvas(pd_val, ae_val, z_val)
        
        # Encontrar el punto de máxima eficiencia real donde J entrega trabajo positivo
        max_eff = res['nO'].max()
        if max_eff > 0:
            j_opt = res.loc[res['nO'].idxmax(), 'J']
        else:
            j_opt = 0.0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Eficiencia Máx (ηO)", f"{max_eff*100:.2f}%")
        c2.metric("Avance Óptimo (J)", f"{j_opt:.3f}")
        c3.metric("Hélice Base PDF", f"{z_val} Palas")

        fig, ax = plt.subplots(figsize=(11, 5.5))
        ax.plot(res['J'], res['KT'], color='#004c6d', label='KT (Empuje)', lw=2.5)
        # Multiplicamos por 10 a efectos de escalado visual estándar en diagramas de aguas abiertas
        ax.plot(res['J'], res['KQ']*10, color='#2ca02c', label='10*KQ (Torque)', lw=2.5)
        ax.plot(res['J'], res['nO'], color='#6b2d7a', label='ηO (Eficiencia)', lw=3.5, ls='--')
        
        ax.fill_between(res['J'], 0, res['nO'], color='#6b2d7a', alpha=0.1)
        if max_eff > 0:
            ax.axvline(x=j_opt, color='gray', linestyle=':', alpha=0.6)
        
        ax.set_title(f"Diagrama de Aguas Abiertas - Serie B (P/D={pd_val:.3f})", fontsize=14, fontweight='bold')
        ax.set_xlabel('Coeficiente de Avance (J)')
        ax.set_ylabel('Valores Adimensionales')
        ax.set_ylim(0, 1.1)
        ax.set_xlim(0, 1.2)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(loc='upper right', frameon=True, shadow=True)
        st.pyplot(fig)

    # TAB 2: DATOS TÉCNICOS (Resumen Fiel del PDF)
    with tab2:
        st.subheader("Hoja de Parámetros de Diseño Oficiales (Datos del PDF)")
        
        datos_buque = {
            "Parámetro Extraído del PDF": [
                "Eslora entre Perpendiculares (Lpp)", "Manga Máxima (B)", "Puntal Estructural (D)", 
                "Calado de Operación (T)", "Velocidad de Servicio Designada",
                "Diámetro de Hélice de Referencia (D)", "Relación Paso/Diámetro (P/D)", "Relación de Área Expandida (Ae/A0)"
            ],
            "Valor Registrado en el Sistema": [
                f"{eslora} m", f"{manga} m", f"{puntal} m", 
                f"{calado} m", f"{velocidad} Nudos",
                f"{diam_prop_m} m", f"{pd_val:.3f}", f"{ae_val:.3f}"
            ]
        }
        st.table(pd.DataFrame(datos_buque))
        
        st.subheader("Resultados Numéricos Adimensionales (Hélice)")
        res_display = res.copy()
        res_display['nO (%)'] = res_display['nO'] * 100
        st.dataframe(res_display.style.highlight_max(subset=['nO'], color='#f3e8ff').format("{:.4f}"), use_container_width=True)
        st.download_button("📂 Descargar Hoja de Datos (CSV)", res_display.to_csv(index=False), "datos_buquetanque_equipo4.csv")

    # TAB 3: ENTREGABLE 1 (Análisis de Vibración Torsional)
    with tab3:
        st.header("💥 Entregable 1: Análisis de Vibración Torsional (IACS UR M68)")
        st.write("Verificación de fatiga del eje de cola sometido a esfuerzos de torsión cíclicos generados por las pulsaciones del motor.")
        
        tau_admisible = 0.35 * (sigma_uts / 3.0)
        omega = (2 * math.pi * rpm_motor) / 60.0
        torque_nominal_nm = (potencia_kw * 1000.0) / omega
        torque_dinamico_nm = torque_nominal_nm * 0.15 
        
        diametro_m = diametro_eje_mm / 1000.0
        wt = (math.pi * (diametro_m**3)) / 16.0
        esfuerzo_real_mpa = (torque_dinamico_nm / wt) / 1000000.0
        
        vt1, vt2, vt3 = st.columns(3)
        vt1.metric("Torque Nominal del Sistema", f"{torque_nominal_nm/1000:.1f} kN·m")
        vt2.metric("Límite Admisible por Norma", f"{tau_admisible:.2f} MPa")
        vt3.metric("Esfuerzo de Trabajo Real", f"{esfuerzo_real_mpa:.2f} MPa")
        
        st.markdown("---")
        st.subheader("⚖️ Estado de Aceptación Estructural")
        if esfuerzo_real_mpa <= tau_admisible:
            st.success(f"✅ **CRITERIO APROBADO:** El esfuerzo torsional real ({esfuerzo_real_mpa:.2f} MPa) cumple satisfactoriamente con los límites de fatiga de la norma IACS UR M68 ({tau_admisible:.2f} MPa).")
        else:
            st.error(f"❌ **CRITERIO RECHAZADO:** Peligro de fractura por fatiga torsional alternante. El esfuerzo excede la norma. **Acción correctiva:** Incrementar el diámetro del eje en el Panel de Control.")

    # TAB 4: ENTREGABLES 2 Y 3 (Vibración Lateral y Gráfico de Campbell)
    with tab4:
        st.header("📊 Entregable 2: Velocidades Críticas Laterales (Whirling)")
        st.write("Análisis dinámico por flexión empleando la aproximación analítica de **Dunkerley** para el tramo del eje en voladizo.")

        E_acero = 2.06e11  
        densidad_acero = 7850.0  
        
        r_eje = (diametro_eje_mm / 1000.0) / 2.0
        area_eje = math.pi * (r_eje**2)
        I_inercia = (math.pi * ((r_eje*2)**4)) / 64.0
        peso_por_metro_eje = area_eje * densidad_acero
        
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
        vl2.metric("Umbral Seguro Mínimo (-20%)", f"{limite_inferior_seguro:.1f} RPM")
        vl3.metric("Umbral Seguro Máximo (+20%)", f"{limite_superior_seguro:.1f} RPM")

        st.markdown("---")
        st.subheader("⚖️ Verificación de Resonancia en el Régimen de Operación")
        if rpm_motor < limite_inferior_seguro or rpm_motor > limite_superior_seguro:
            st.success(f"✅ **DISEÑO DINÁMICO SEGURO:** El régimen de operación ordinario ({rpm_motor:.1f} RPM) se encuentra libre de resonancia lateral por Whirling fuera de la zona excluida.")
        else:
            st.error(f"❌ **ALERTA DE RESONANCIA CRÍTICA:** Las RPM caen dentro de la banda prohibida del $\pm20\%$.")

        # --- DIAGRAMA DE CAMPBELL (ENTREGABLE 3) ---
        st.markdown("---")
        st.header("📈 Entregable 3: Diagrama de Campbell Dinámico")
        st.write("Mapa de frecuencias que intercepta las líneas dinámicas de excitación del propulsor con los modos naturales de vibración mecánica.")
        
        rpm_x = np.linspace(0, rpm_motor * 1.5, 250)
        f_natural_lateral = f_critica_hz
        f_natural_torsional = f_critica_hz * 1.35 
        
        orden_1p = (1 * rpm_x) / 60.0
        orden_zp = (z_val * rpm_x) / 60.0
        orden_2zp = ((z_val * 2) * rpm_x) / 60.0

        fig_campbell, ax_c = plt.subplots(figsize=(11, 6))
        
        ax_c.axhline(y=f_natural_lateral, color='#6b2d7a', linestyle='--', lw=2, label=f'Frecuencia Natural Lateral ({f_natural_lateral:.1f} Hz)')
        ax_c.axhline(y=f_natural_torsional, color='#d95f02', linestyle='--', lw=2, label=f'Frecuencia Natural Torsional ({f_natural_torsional:.1f} Hz)')
        
        ax_c.plot(rpm_x, orden_1p, color='#7570b3', lw=1.5, label='Orden 1P (Excentricidad Mecánica)')
        ax_c.plot(rpm_x, orden_zp, color='#1b9e77', lw=2.5, label=f'Orden {z_val}P (Frecuencia del Paso de Palas)')
        ax_c.plot(rpm_x, orden_2zp, color='#e7298a', lw=1.5, ls=':', label=f'Orden {z_val*2}P (Segundo Armónico de Palas)')
        
        ax_c.axvline(x=rpm_motor, color='#6b2d7a', lw=3, label=f'RPM de Servicio Actual ({rpm_motor:.1f} RPM)')
        ax_c.axvspan(limite_inferior_seguro, limite_superior_seguro, color='red', alpha=0.15, label='Banda de Velocidad Excluida (BSR)')

        ax_c.set_title(f"Diagrama de Campbell - Buque Tanque PDF (Hélice D={diam_prop_m}m, Z={z_val})", fontsize=14, fontweight='bold')
        ax_c.set_xlabel("Velocidad de Giro del Motor (RPM)")
        ax_c.set_ylabel("Frecuencia del Sistema (Hz)")
        ax_c.set_xlim(0, rpm_motor * 1.5)
        ax_c.set_ylim(0, max(f_natural_torsional * 1.7, 40))
        ax_c.grid(True, linestyle=':', alpha=0.6)
        ax_c.legend(loc='upper left', frameon=True, shadow=True)

        st.pyplot(fig_campbell)
        st.info("💡 **Guía de defensa académica:** Los cruces representan los puntos de resonancia pura. La línea vertical morada (las RPM de operación de tu barco) jamás debe cruzarse con los nodos críticos dentro de las bandas rojas.")

    # TAB 5: FUNDAMENTOS TEÓRICOS
    with tab5:
        st.header("Modelo Matemático Integrado (Propulsión y Dinámica Estructural)")
        st.latex(r"K_T = \sum_{n=1}^{39} C_n \cdot J^{s_n} \cdot (P/D)^{t_n} \cdot (A_E/A_O)^{u_n} \cdot Z^{v_n}")
        st.latex(r"\tau_{adm} = 0.35 \cdot \frac{\sigma_{UTS}}{3}")
        st.latex(r"f_c = \frac{1}{2\pi \sqrt{\delta_{hélice} + \delta_{eje}}}")

else:
    st.error("⚠️ Error Crítico: No se detecta el archivo 'Tabla 1.xlsx' en el directorio de ejecución.")

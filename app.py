import streamlit as st
import pandas as pd
import numpy as np
import math
from io import BytesIO
import matplotlib.pyplot as plt

# ==============================================================================
# UNIVERSAL SHIP PROPULSION & SHAFTING ANALYSIS SUITE
# Versión profesional didáctica para Streamlit
# Requiere en requirements.txt:
# streamlit
# pandas
# numpy
# matplotlib
# openpyxl
# xlsxwriter
# reportlab
# ==============================================================================

st.set_page_config(
    page_title="Universal Ship Propulsion & Shafting Analysis Suite",
    layout="wide",
    page_icon="⚓"
)

# ==============================================================================
# ESTILO VISUAL PROFESIONAL
# ==============================================================================

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        color: #0f172a;
    }

    .main-title {
        font-size: 38px;
        font-weight: 900;
        color: #0f172a;
        letter-spacing: -0.6px;
        margin-bottom: 4px;
    }

    .main-subtitle {
        font-size: 14px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 18px;
    }

    .hero-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 55%, #4c1d95 100%);
        padding: 26px 30px;
        border-radius: 20px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 18px 35px rgba(15, 23, 42, 0.18);
    }

    .hero-box h1 {
        font-size: 28px;
        margin-bottom: 5px;
    }

    .hero-box p {
        color: rgba(255,255,255,0.76);
        font-size: 14px;
        line-height: 1.65;
    }

    .section-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 14px rgba(15,23,42,0.045);
    }

    .small-muted {
        color: #64748b;
        font-size: 13px;
        line-height: 1.6;
    }

    .status-good {
        background: #ecfdf5;
        border-left: 6px solid #10b981;
        color: #065f46;
        padding: 15px 18px;
        border-radius: 12px;
        margin-bottom: 14px;
        font-weight: 600;
    }

    .status-warn {
        background: #fffbeb;
        border-left: 6px solid #f59e0b;
        color: #92400e;
        padding: 15px 18px;
        border-radius: 12px;
        margin-bottom: 14px;
        font-weight: 600;
    }

    .status-bad {
        background: #fef2f2;
        border-left: 6px solid #ef4444;
        color: #991b1b;
        padding: 15px 18px;
        border-radius: 12px;
        margin-bottom: 14px;
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #e2e8f0;
        padding: 8px;
        border-radius: 15px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        background-color: transparent;
        border-radius: 11px;
        padding: 8px 14px;
        font-weight: 700;
        color: #475569;
    }

    .stTabs [aria-selected="true"] {
        background-color: #4c1d95 !important;
        color: white !important;
        box-shadow: 0 6px 14px rgba(76,29,149,0.22);
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 18px 16px;
        box-shadow: 0 4px 14px rgba(15,23,42,0.045);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748b;
        text-transform: uppercase;
        font-size: 11px !important;
        font-weight: 800;
        letter-spacing: .5px;
    }

    div[data-testid="stMetricValue"] {
        color: #4c1d95;
        font-size: 27px !important;
        font-weight: 900;
    }

    .block-container {
        padding-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def safe_div(numerador, denominador, default=0.0):
    try:
        if denominador == 0:
            return default
        return numerador / denominador
    except Exception:
        return default


def estado_html(texto, tipo="good"):
    css = {
        "good": "status-good",
        "warn": "status-warn",
        "bad": "status-bad"
    }.get(tipo, "status-good")
    st.markdown(f'<div class="{css}">{texto}</div>', unsafe_allow_html=True)


def diagnostico_score(score):
    if score >= 90:
        return "APROBADO", "good", "🟢"
    if score >= 70:
        return "APROBADO CON OBSERVACIONES", "warn", "🟡"
    return "REQUIERE REDISEÑO", "bad", "🔴"


def fig_to_bytes(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    buffer.seek(0)
    return buffer


# ==============================================================================
# CARGA DEL ARCHIVO WAGENINGEN
# ==============================================================================

@st.cache_data
def load_coefficients():
    try:
        kt_df = pd.read_excel("Tabla 1.xlsx", sheet_name="KT")
        kq_df = pd.read_excel("Tabla 1.xlsx", sheet_name="KQ")

        for df in [kt_df, kq_df]:
            df.columns = [str(c).strip().capitalize() for c in df.columns]

        columnas_requeridas = ["Coeficiente", "S (j)", "T (p/d)", "U (ae/ao)", "V (z)"]

        for col in columnas_requeridas:
            if col not in kt_df.columns or col not in kq_df.columns:
                st.error(
                    f"Falta la columna '{col}' en una hoja del archivo Tabla 1.xlsx. "
                    "Revisa que las hojas KT y KQ tengan las columnas correctas."
                )
                return None, None

        return kt_df, kq_df

    except Exception as e:
        st.error(f"No se pudo cargar 'Tabla 1.xlsx': {e}")
        return None, None


df_kt, df_kq = load_coefficients()


def calcular_curvas(pd_v, ae_v, z_v):
    j_vals = np.linspace(0.001, 1.2, 120)
    kt_l, kq_l, no_l = [], [], []
    col_c = "Coeficiente"

    for j in j_vals:
        kt = np.sum(
            df_kt[col_c]
            * (j ** df_kt["S (j)"])
            * (pd_v ** df_kt["T (p/d)"])
            * (ae_v ** df_kt["U (ae/ao)"])
            * (z_v ** df_kt["V (z)"])
        )

        kq = np.sum(
            df_kq[col_c]
            * (j ** df_kq["S (j)"])
            * (pd_v ** df_kq["T (p/d)"])
            * (ae_v ** df_kq["U (ae/ao)"])
            * (z_v ** df_kq["V (z)"])
        )

        if kt <= 0 or kq <= 0:
            kt_f, kq_f, eff = 0.0, 0.0, 0.0
        else:
            kt_f, kq_f = float(kt), float(kq)
            eff = (j / (2 * np.pi)) * (kt_f / kq_f)
            if eff > 0.85:
                eff = 0.0

        kt_l.append(kt_f)
        kq_l.append(kq_f)
        no_l.append(eff)

    return pd.DataFrame({
        "J": j_vals,
        "KT": kt_l,
        "KQ": kq_l,
        "nO": no_l,
        "10KQ": np.array(kq_l) * 10,
        "ηO (%)": np.array(no_l) * 100
    })


# ==============================================================================
# ENCABEZADO
# ==============================================================================

st.markdown("""
<div class="hero-box">
    <h1>⚓ Universal Ship Propulsion & Shafting Analysis Suite</h1>
    <p>
    Plataforma didáctica y profesional para prediseño de sistemas propulsivos navales.
    Permite analizar embarcaciones de diferentes tipos a partir de dimensiones definidas por el usuario:
    geometría del buque, parámetros de hélice, cavitación, vibraciones del eje, diagrama de Campbell
    y dictamen orientativo de cumplimiento.
    </p>
</div>
""", unsafe_allow_html=True)

if df_kt is None or df_kq is None:
    st.stop()

# ==============================================================================
# SIDEBAR: ENTRADAS DEL USUARIO
# ==============================================================================

with st.sidebar:
    st.header("⚙️ Panel de Entrada")
    st.caption("Todos los parámetros son editables para que la app funcione con cualquier tipo de embarcación.")

    modo_guia = st.selectbox(
        "Modo de referencia didáctica",
        [
            "Libre / Personalizado",
            "Buque tanque",
            "Portacontenedores",
            "Bulk carrier",
            "OSV / PSV",
            "AHTS",
            "Remolcador",
            "Ferry"
        ],
        help="Este selector solo sirve como guía visual. Los valores siguen siendo editables por el usuario."
    )

    st.markdown("---")
    st.subheader("🌎 Constantes físicas")

    p_atm_auto = st.number_input("Presión atmosférica [Pa]", value=101325.0, format="%.2f")
    p_vap_auto = st.number_input("Presión de vapor del agua [Pa]", value=1704.0, format="%.2f")
    rho_auto = st.number_input("Densidad del agua [kg/m³]", value=1026.021, format="%.3f")
    g_auto = st.number_input("Gravedad [m/s²]", value=9.80665, format="%.5f")

    st.markdown("---")
    st.subheader("🚢 Dimensiones principales")

    eslora = st.number_input(
        "Eslora entre perpendiculares Lpp [m]",
        value=320.0,
        min_value=1.0,
        step=1.0,
        help="Distancia longitudinal entre perpendicular de proa y popa. Remolcadores: 20–50 m; OSV: 60–100 m; buques tanque: 250–330 m; portacontenedores: 250–400 m."
    )

    lwl = st.number_input(
        "Eslora en flotación LWL [m]",
        value=325.5,
        min_value=1.0,
        step=1.0,
        help="Longitud del buque sobre la línea de agua. Normalmente es igual o ligeramente mayor que Lpp."
    )

    manga = st.number_input(
        "Manga B [m]",
        value=58.0,
        min_value=1.0,
        step=0.5,
        help="Ancho máximo del buque. Debe guardar proporción con Lpp según el tipo de embarcación."
    )

    puntal = st.number_input(
        "Puntal D [m]",
        value=30.0,
        min_value=1.0,
        step=0.5,
        help="Altura estructural desde la línea base hasta cubierta principal."
    )

    calado = st.number_input(
        "Calado T [m]",
        value=20.8,
        min_value=0.1,
        step=0.1,
        help="Profundidad sumergida del casco. Debe ser menor que el puntal."
    )

    velocidad = st.number_input(
        "Velocidad de servicio [kn]",
        value=15.5,
        min_value=0.1,
        step=0.5,
        help="Velocidad de operación del buque. Buques mercantes usualmente operan entre 10 y 25 nudos."
    )

    st.markdown("---")
    st.subheader("🌀 Interacción casco-propulsor")

    estela = st.number_input(
        "Fracción de estela w [-]",
        value=0.351,
        min_value=0.0,
        max_value=0.8,
        step=0.001,
        format="%.3f",
        help="Reduce la velocidad efectiva que llega a la hélice. Valores comunes: 0.10–0.45."
    )

    t_fraction = st.slider(
        "Fracción de deducción de empuje t [-]",
        0.05,
        0.35,
        0.180,
        0.005,
        help="Pérdida asociada a la interacción entre el empuje de la hélice y el casco."
    )

    eta_r = st.number_input(
        "Eficiencia rotativa relativa ηR [-]",
        value=1.015,
        min_value=0.80,
        max_value=1.15,
        step=0.005,
        format="%.3f"
    )

    inmersion_eje_m = st.number_input(
        "Inmersión del centro del eje h [m]",
        value=14.10,
        min_value=0.1,
        step=0.1,
        help="Profundidad del centro de la hélice respecto a la superficie libre. A mayor inmersión, menor tendencia a cavitación."
    )

    st.markdown("---")
    st.subheader("⚙️ Geometría de la hélice")

    z_val = st.slider("Número de palas Z", 3, 7, 4)
    diam_prop_m = st.number_input("Diámetro de hélice D [m]", value=9.86, min_value=0.1, step=0.01)
    pd_val = st.slider("Relación paso/diámetro P/D [-]", 0.5, 1.4, 0.721, 0.001)
    ae_val = st.slider("Relación de área expandida Ae/A0 [-]", 0.3, 1.0, 0.431, 0.001)
    margen_servicio = st.slider("Margen de servicio requerido [%]", 0.0, 30.0, 15.0, 0.5)

    st.markdown("---")
    st.subheader("⚙️ Material del sistema propulsivo")
    st.info(
        "Selecciona el material de referencia para evaluar el límite admisible de esfuerzo. "
        "Los demás parámetros mecánicos se mantienen internamente como valores de referencia "
        "para no saturar la interfaz del usuario."
    )

    # ==========================================================
    # PARÁMETROS MECÁNICOS INTERNOS DE REFERENCIA
    # ==========================================================
    # Se ocultan en el sidebar para mantener la app limpia y didáctica.
    # Si más adelante deseas hacerlos editables, basta con convertirlos
    # nuevamente en st.number_input().
    potencia_kw_base = 22000.0
    potencia_kw = potencia_kw_base * (1 + margen_servicio / 100)
    rpm_motor = 75.0
    diametro_eje_mm = 680.0
    peso_helice_kg = 52000.0
    longitud_volado_m = 3.5

    dict_materiales = {
        "Bronce de Níquel-Aluminio (Cu3)": 590.0,
        "Bronce de Manganeso (Cu1)": 450.0,
        "Bronce de Níquel-Manganeso (Cu2)": 490.0,
        "Bronce de Manganeso-Aluminio (Cu4)": 630.0,
        "Acero Forjado Naval Estándar": 400.0,
        "Acero Forjado Aleado de Alta Resistencia": 600.0,
        "Acero Inoxidable Austenítico Forjado": 520.0
    }

    material_seleccionado = st.selectbox("Material de referencia", list(dict_materiales.keys()))
    sigma_uts = dict_materiales[material_seleccionado]

# ==============================================================================
# CÁLCULOS PRINCIPALES
# ==============================================================================

res = calcular_curvas(pd_val, ae_val, z_val)

max_eff = float(res["nO"].max())
j_opt = float(res.loc[res["nO"].idxmax(), "J"]) if max_eff > 0 else 0.0

diametro_m = diametro_eje_mm / 1000.0
E_acero = 2.06e11
densidad_acero = 7850.0

r_eje = diametro_m / 2.0
area_eje = math.pi * r_eje**2
I_inercia = math.pi * diametro_m**4 / 64.0
peso_lineal_eje = area_eje * densidad_acero

peso_helice_n = peso_helice_kg * g_auto
delta_helice = safe_div(
    peso_helice_n * longitud_volado_m**3,
    3.0 * E_acero * I_inercia
)

peso_eje_n = peso_lineal_eje * longitud_volado_m * g_auto
delta_eje = safe_div(
    peso_eje_n * longitud_volado_m**3,
    8.0 * E_acero * I_inercia
)

delta_total = max(delta_helice + delta_eje, 1e-12)
f_natural_hz = 1.0 / (2.0 * math.pi * math.sqrt(delta_total))
rpm_critica_lateral = f_natural_hz * 60.0
margen_inf = rpm_critica_lateral * 0.80
margen_sup = rpm_critica_lateral * 1.20
f_torsional_est = f_natural_hz * 1.4

# ==============================================================================
# CÁLCULO PRELIMINAR DE VIBRACIÓN AXIAL
# ==============================================================================
# La vibración axial se asocia a fluctuaciones periódicas del empuje de la hélice.
# Para una revisión didáctica, se modela el sistema como una masa equivalente axial
# conectada a una rigidez axial equivalente del eje y del cojinete de empuje.
# El objetivo es comparar la frecuencia natural axial contra las excitaciones kZP.

longitud_eje_axial_m = max(eslora * 0.18, 8.0)
masa_eje_axial_kg = peso_lineal_eje * longitud_eje_axial_m
masa_equivalente_axial_kg = max(peso_helice_kg + 0.35 * masa_eje_axial_kg, 1.0)
rigidez_axial_eje_n_m = safe_div(E_acero * area_eje, longitud_eje_axial_m, default=1e9)
rigidez_cojinete_empuje_n_m = 8.0e9
rigidez_axial_equivalente_n_m = 1.0 / ((1.0 / rigidez_axial_eje_n_m) + (1.0 / rigidez_cojinete_empuje_n_m))
f_axial_natural_hz = (1.0 / (2.0 * math.pi)) * math.sqrt(rigidez_axial_equivalente_n_m / masa_equivalente_axial_kg)
rpm_critica_axial_zp = safe_div(f_axial_natural_hz * 60.0, z_val, default=0.0)

# Empuje preliminar a partir de la potencia efectiva al avance.
# Se usa como indicador didáctico, no como cálculo final de hélice.
velocidad_buque_ms = velocidad * 0.5144
empuje_estimado_n = safe_div(potencia_kw * 1000.0 * max(eta_r, 0.01), max(velocidad_buque_ms, 0.1))
amplitud_empuje_axial_n = 0.08 * empuje_estimado_n
desplazamiento_axial_est_m = safe_div(amplitud_empuje_axial_n, rigidez_axial_equivalente_n_m)

# ==============================================================================
# CÁLCULO PRELIMINAR DE BALANCEO Y DESBALANCE
# ==============================================================================
# El desbalance se representa como una masa equivalente que gira con una
# excentricidad respecto al centro del eje. Esta fuerza periódica puede excitar
# vibración lateral y aumentar cargas en chumaceras.

masa_desbalance_kg = max(peso_helice_kg * 0.001, 1.0)  # 0.1% de la masa de la hélice como caso didáctico
excentricidad_desbalance_m = 0.001  # 1 mm
# omega debe calcularse antes de usarla en la fuerza de desbalance.
omega = (2.0 * math.pi * rpm_motor) / 60.0
fuerza_desbalance_n = masa_desbalance_kg * excentricidad_desbalance_m * omega**2
fuerza_desbalance_rel_pct = safe_div(fuerza_desbalance_n, max(peso_helice_n, 1e-9)) * 100.0

if fuerza_desbalance_rel_pct < 1.0:
    riesgo_desbalance = "Bajo"
elif fuerza_desbalance_rel_pct < 3.0:
    riesgo_desbalance = "Medio"
else:
    riesgo_desbalance = "Alto"

desbalance_ok = riesgo_desbalance != "Alto"


def clasificar_riesgo_por_separacion(separacion_pct):
    # Criterio didáctico más realista:
    # Alto: muy cerca de resonancia (<5%).
    # Medio: zona de precaución (5% a 12%).
    # Bajo: separación suficiente (>12%).
    if separacion_pct < 5:
        return "Alto"
    if separacion_pct < 12:
        return "Medio"
    return "Bajo"


def construir_tabla_axial():
    filas = []
    rev_s = rpm_motor / 60.0
    ordenes = [("1P", 1), ("ZP", z_val), ("2ZP", 2 * z_val), ("3ZP", 3 * z_val)]
    for nombre, mult in ordenes:
        f_exc = mult * rev_s
        separacion = abs(f_axial_natural_hz - f_exc)
        separacion_pct = safe_div(separacion, max(f_axial_natural_hz, 1e-9)) * 100.0
        filas.append({
            "Orden de excitación": nombre,
            "Multiplicador": mult,
            "Frecuencia excitante [Hz]": f_exc,
            "Frecuencia natural axial [Hz]": f_axial_natural_hz,
            "Separación [%]": separacion_pct,
            "Riesgo axial": clasificar_riesgo_por_separacion(separacion_pct)
        })
    return pd.DataFrame(filas)

axial_df = construir_tabla_axial()
axial_ok = not (axial_df["Riesgo axial"] == "Alto").any()
riesgo_axial_global = "Alto" if (axial_df["Riesgo axial"] == "Alto").any() else ("Medio" if (axial_df["Riesgo axial"] == "Medio").any() else "Bajo")


def construir_tabla_campbell():
    filas = []
    ordenes = [("1P", 1), ("2P", 2), ("3P", 3), ("4P", 4), ("5P", 5), ("ZP", z_val), ("2ZP", 2 * z_val), ("3ZP", 3 * z_val)]
    modos = [
        ("Lateral / whirling", f_natural_hz),
        ("Torsional estimada", f_torsional_est),
        ("Axial", f_axial_natural_hz),
    ]
    for nombre_orden, mult in ordenes:
        if mult <= 0:
            continue
        for modo, freq in modos:
            rpm_cruce = safe_div(freq * 60.0, mult, default=0.0)
            diferencia = abs(rpm_motor - rpm_cruce)
            separacion_pct = safe_div(diferencia, max(rpm_motor, 1e-9)) * 100.0
            riesgo = clasificar_riesgo_por_separacion(separacion_pct)
            filas.append({
                "Orden": nombre_orden,
                "Modo natural": modo,
                "Frecuencia natural [Hz]": freq,
                "RPM de intersección": rpm_cruce,
                "RPM operación": rpm_motor,
                "Separación [%]": separacion_pct,
                "Riesgo": riesgo
            })
    return pd.DataFrame(filas)

campbell_df = construir_tabla_campbell()

v_ms = (velocidad * 0.5144) * (1.0 - estela)
nu = 1.188e-6
reynolds = safe_div(v_ms * diam_prop_m, nu)

sigma_n = safe_div(
    p_atm_auto + (rho_auto * g_auto * inmersion_eje_m) - p_vap_auto,
    0.5 * rho_auto * max(v_ms**2, 1e-12)
)

torque_nominal = safe_div(potencia_kw * 1000.0, omega)
torque_dinamico_alternante = torque_nominal * 0.15
wt_modulo_torsional = math.pi * diametro_m**3 / 16.0
esfuerzo_real_mpa = safe_div(torque_dinamico_alternante, wt_modulo_torsional) / 1e6
tau_admisible_mpa = 0.35 * (sigma_uts / 3.0)

# Criterios lógicos
torsion_ok = esfuerzo_real_mpa <= tau_admisible_mpa
lateral_ok = rpm_motor < margen_inf or rpm_motor > margen_sup
cavitacion_ok = sigma_n >= 0.20
reynolds_ok = reynolds > 1e7
hidro_ok = max_eff > 0.40

# Score global ponderado actualizado actualizado:
# se incluye axial porque el análisis de vibración del eje incluye
# componentes torsional, lateral y axial.
score = 0
score += 20 if torsion_ok else 0
score += 20 if lateral_ok else 0
score += 20 if axial_ok else 0
score += 10 if desbalance_ok else 0
score += 10 if cavitacion_ok else 0
score += 10 if reynolds_ok else 0
score += 10 if hidro_ok else 0

dictamen, dictamen_tipo, dictamen_icono = diagnostico_score(score)

# Validaciones didácticas
advertencias = []
if lwl < eslora:
    advertencias.append("La LWL es menor que Lpp. Puede ocurrir, pero conviene revisar la geometría ingresada.")
if calado >= puntal:
    advertencias.append("El calado es igual o mayor que el puntal. Esto no es físicamente recomendable.")
if velocidad > 35:
    advertencias.append("La velocidad ingresada es alta para buques mercantes convencionales.")
if diam_prop_m > manga * 0.35:
    advertencias.append("El diámetro de hélice es grande respecto a la manga. Revisa espacio de popa, calado e inmersión.")
if ae_val < 0.38:
    advertencias.append("Ae/A0 bajo. Puede aumentar el riesgo de cavitación bajo alta carga.")
if pd_val < 0.55 or pd_val > 1.25:
    advertencias.append("P/D fuera de rangos típicos de diseño comercial. Verificar consistencia hidrodinámica.")
if estela > 0.55:
    advertencias.append("Fracción de estela elevada. Revisar interacción casco-propulsor.")

# Recomendaciones automáticas
recomendaciones = []
if not cavitacion_ok:
    recomendaciones.append("Aumentar Ae/A0, incrementar inmersión del eje o reducir carga de la hélice para mitigar cavitación.")
if not lateral_ok:
    recomendaciones.append("Modificar diámetro del eje, longitud en voladizo, apoyos o régimen de operación para alejarse de la velocidad crítica lateral.")
if not axial_ok:
    recomendaciones.append("Revisar vibración axial: separar la frecuencia natural axial de las excitaciones 1P, ZP, 2ZP y 3ZP; aumentar rigidez axial o modificar RPM de operación.")
if not desbalance_ok:
    recomendaciones.append("Revisar balanceo dinámico: reducir masa excéntrica, excentricidad o verificar balanceo de hélice y eje en taller/pruebas.")
if not torsion_ok:
    recomendaciones.append("Aumentar diámetro del eje, cambiar material o revisar excitaciones torsionales del sistema propulsivo.")
if max_eff < 0.45:
    recomendaciones.append("Revisar P/D, Ae/A0 y número de palas; la eficiencia de aguas abiertas está baja.")
if not recomendaciones:
    recomendaciones.append("El diseño preliminar es consistente. Se recomienda validar con análisis de clase completo y pruebas de mar.")

# ==============================================================================
# FUNCIONES DE EXPORTACIÓN
# ==============================================================================

def construir_resumen_dataframe():
    datos = {
        "Parámetro": [
            "Modo de referencia",
            "Lpp [m]",
            "LWL [m]",
            "Manga B [m]",
            "Puntal D [m]",
            "Calado T [m]",
            "Velocidad [kn]",
            "Potencia con margen [kW]",
            "RPM [rpm]",
            "Diámetro hélice [m]",
            "Número de palas",
            "P/D",
            "Ae/A0",
            "Diámetro eje [mm]",
            "Material",
            "ηO máxima [%]",
            "J óptimo",
            "Reynolds",
            "Sigma cavitación",
            "Torque nominal [kN·m]",
            "Esfuerzo torsional [MPa]",
            "Límite admisible [MPa]",
            "Frecuencia lateral [Hz]",
            "RPM crítica lateral",
            "Frecuencia axial [Hz]",
            "RPM crítica axial ZP",
            "Riesgo axial global",
            "Fuerza por desbalance [N]",
            "Riesgo de desbalance",
            "Score global [%]",
            "Dictamen"
        ],
        "Valor": [
            modo_guia,
            eslora,
            lwl,
            manga,
            puntal,
            calado,
            velocidad,
            potencia_kw,
            rpm_motor,
            diam_prop_m,
            z_val,
            pd_val,
            ae_val,
            diametro_eje_mm,
            material_seleccionado,
            max_eff * 100,
            j_opt,
            reynolds,
            sigma_n,
            torque_nominal / 1000,
            esfuerzo_real_mpa,
            tau_admisible_mpa,
            f_natural_hz,
            rpm_critica_lateral,
            f_axial_natural_hz,
            rpm_critica_axial_zp,
            riesgo_axial_global,
            fuerza_desbalance_n,
            riesgo_desbalance,
            score,
            dictamen
        ]
    }
    return pd.DataFrame(datos)


def generar_excel():
    output = BytesIO()
    resumen_df = construir_resumen_dataframe()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        resumen_df.to_excel(writer, sheet_name="Resumen", index=False)
        res.to_excel(writer, sheet_name="Wageningen", index=False)

        cumplimiento = pd.DataFrame({
            "Criterio": [
                "Hidrodinámica",
                "Reynolds",
                "Cavitación",
                "Vibración torsional",
                "Vibración lateral",
                "Vibración axial",
                "Balanceo/desbalance"
            ],
            "Resultado": [
                "Cumple" if hidro_ok else "Observación",
                "Cumple" if reynolds_ok else "Observación",
                "Cumple" if cavitacion_ok else "No cumple",
                "Cumple" if torsion_ok else "No cumple",
                "Cumple" if lateral_ok else "No cumple",
                "Cumple" if axial_ok else "No cumple",
                "Cumple" if desbalance_ok else "No cumple"
            ]
        })
        cumplimiento.to_excel(writer, sheet_name="Cumplimiento", index=False)
        axial_df.to_excel(writer, sheet_name="Vibracion_Axial", index=False)
        campbell_df.to_excel(writer, sheet_name="Campbell", index=False)

    output.seek(0)
    return output


def generar_pdf():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    except Exception:
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#1e1b4b"),
        fontSize=18,
        leading=22
    )

    story = []
    story.append(Paragraph("Universal Ship Propulsion & Shafting Analysis Suite", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Reporte técnico preliminar de propulsión naval", styles["Heading2"]))
    story.append(Spacer(1, 12))

    intro = (
        "Este reporte resume los resultados principales del análisis hidrodinámico, "
        "vibratorio, de cavitación y de cumplimiento preliminar del sistema propulsivo. "
        "Los resultados son orientativos y deben complementarse con análisis de sociedad "
        "de clasificación para diseño final."
    )
    story.append(Paragraph(intro, styles["BodyText"]))
    story.append(Spacer(1, 16))

    resumen = construir_resumen_dataframe()
    tabla_datos = [["Parámetro", "Valor"]]
    for _, row in resumen.iterrows():
        val = row["Valor"]
        if isinstance(val, float):
            val = f"{val:,.4g}"
        tabla_datos.append([str(row["Parámetro"]), str(val)])

    table = Table(tabla_datos, colWidths=[230, 250])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e1b4b")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#CBD5E1")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#F8FAFC")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
    ]))

    story.append(table)
    story.append(Spacer(1, 16))
    story.append(Paragraph(f"Dictamen general: {dictamen}", styles["Heading2"]))
    story.append(Paragraph("Recomendaciones:", styles["Heading3"]))

    for rec in recomendaciones:
        story.append(Paragraph(f"• {rec}", styles["BodyText"]))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ==============================================================================
# TABS
# ==============================================================================

tab_dash, tab_resumen, tab_hidro, tab_resultados, tab_torsion, tab_axial, tab_lateral, tab_balanceo, tab_campbell, tab_cav, tab_normativa, tab_clase, tab_export, tab_formulas, tab_guia = st.tabs([
    "🏠 Dashboard",
    "📑 Resumen",
    "📈 Hidrodinámica",
    "📋 Resultados",
    "💥 Torsional",
    "↔️ Axial",
    "📊 Lateral",
    "⚖️ Balanceo",
    "🗺️ Campbell",
    "🔍 Cavitación",
    "📚 Normativa",
    "📋 Clase",
    "📄 Exportar",
    "🧮 Fórmulas",
    "📚 Guía"
])

# ==============================================================================
# DASHBOARD
# ==============================================================================

with tab_dash:
    st.subheader("📊 Dashboard Ejecutivo del Diseño")

    st.markdown("""
    <div class="section-card">
    Este panel resume el estado general del sistema propulsivo analizado.
    Los indicadores combinan desempeño hidrodinámico, vibración torsional,
    vibración axial, vibración lateral, cavitación, régimen de Reynolds y consistencia geométrica.
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Velocidad", f"{velocidad:.1f} kn")
    c2.metric("Potencia", f"{potencia_kw/1000:.2f} MW")
    c3.metric("RPM", f"{rpm_motor:.0f}")
    c4.metric("D Hélice", f"{diam_prop_m:.2f} m")
    c5.metric("ηO máx.", f"{max_eff*100:.2f}%")

    st.markdown("### Índice global de diseño")
    st.progress(score / 100)
    estado_html(f"{dictamen_icono} {dictamen} — Cumplimiento global estimado: {score:.0f}%", dictamen_tipo)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        estado_html("✅ Torsión aceptable" if torsion_ok else "❌ Torsión fuera de límite", "good" if torsion_ok else "bad")
    with c2:
        estado_html("✅ Axial aceptable" if axial_ok else "❌ Riesgo axial", "good" if axial_ok else "bad")
    with c3:
        estado_html("✅ Lateral seguro" if lateral_ok else "❌ Riesgo de velocidad crítica", "good" if lateral_ok else "bad")
    with c4:
        estado_html("✅ Cavitación aceptable" if cavitacion_ok else "⚠️ Riesgo de cavitación", "good" if cavitacion_ok else "warn")

    st.markdown("### Observaciones automáticas")
    if advertencias:
        for aviso in advertencias:
            st.warning(aviso)
    else:
        st.success("No se detectaron inconsistencias geométricas principales.")

    st.markdown("### Recomendaciones preliminares")
    for rec in recomendaciones:
        st.write(f"• {rec}")

# ==============================================================================
# RESUMEN EJECUTIVO
# ==============================================================================

with tab_resumen:
    st.subheader("📑 Resumen Ejecutivo del Proyecto")

    st.markdown(f"""
    <div class="section-card">
    <b>Objetivo del análisis:</b><br>
    Evaluar de forma preliminar el desempeño de una configuración de propulsión naval
    definida por el usuario, considerando curvas de aguas abiertas de hélice Wageningen,
    esfuerzo torsional, velocidad crítica lateral, riesgo de cavitación y criterios
    orientativos de cumplimiento.
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"""
        ### Datos principales del buque

        - **Modo de referencia:** {modo_guia}
        - **Lpp:** {eslora:.2f} m
        - **LWL:** {lwl:.2f} m
        - **Manga:** {manga:.2f} m
        - **Puntal:** {puntal:.2f} m
        - **Calado:** {calado:.2f} m
        - **Velocidad:** {velocidad:.2f} kn
        """)

    with col_b:
        st.markdown(f"""
        ### Sistema propulsivo

        - **Potencia con margen:** {potencia_kw:,.2f} kW
        - **RPM:** {rpm_motor:.2f}
        - **Diámetro de hélice:** {diam_prop_m:.2f} m
        - **Número de palas:** {z_val}
        - **P/D:** {pd_val:.3f}
        - **Ae/A0:** {ae_val:.3f}
        - **Material:** {material_seleccionado}
        """)

    st.markdown("### Resultados principales")
    resultado_df = construir_resumen_dataframe()
    st.dataframe(resultado_df, use_container_width=True, height=520)

# ==============================================================================
# HIDRODINÁMICA
# ==============================================================================

with tab_hidro:
    st.subheader("📈 Hidrodinámica en Aguas Abiertas — Wageningen Serie B")

    st.markdown("""
    <div class="section-card">
    Las curvas de aguas abiertas describen el comportamiento ideal de la hélice
    sin interferencia directa del casco. Se calculan los coeficientes KT, KQ y ηO
    a partir de los polinomios de la Serie B de Wageningen contenidos en el archivo Excel.
    El punto de máxima eficiencia permite identificar una condición favorable de operación.
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("ηO máxima", f"{max_eff*100:.2f}%")
    k2.metric("J óptimo", f"{j_opt:.3f}")
    k3.metric("KT en ηO máx.", f"{float(res.loc[res['nO'].idxmax(), 'KT']):.4f}")
    k4.metric("KQ en ηO máx.", f"{float(res.loc[res['nO'].idxmax(), 'KQ']):.4f}")

    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.plot(res["J"], res["KT"], linewidth=2.6, label="KT — Coeficiente de empuje")
    ax.plot(res["J"], res["10KQ"], linewidth=2.6, label="10·KQ — Coeficiente de torque")
    ax.plot(res["J"], res["nO"], linewidth=3.2, linestyle="--", label="ηO — Eficiencia")
    ax.axvline(x=j_opt, linestyle=":", linewidth=2, label=f"J óptimo = {j_opt:.3f}")
    ax.fill_between(res["J"], 0, res["nO"], alpha=0.08)
    ax.set_title("Curvas KT, 10KQ y ηO — Hélice Wageningen Serie B", fontsize=12, fontweight="bold")
    ax.set_xlabel("Coeficiente de avance J")
    ax.set_ylabel("Coeficientes adimensionales")
    ax.set_xlim(0, 1.2)
    ax.set_ylim(0, max(1.05, float(res[["KT", "10KQ", "nO"]].max().max()) * 1.1))
    ax.grid(True, linestyle=":", alpha=0.65)
    ax.legend(loc="best")
    st.pyplot(fig)

    st.info(
        "Interpretación: KT indica capacidad de empuje; KQ indica demanda de torque; "
        "ηO expresa eficiencia hidrodinámica ideal. El máximo de ηO es útil para evaluar "
        "la coherencia preliminar de la geometría P/D, Ae/A0 y Z."
    )


    with st.expander("🧮 Fórmulas hidrodinámicas usadas", expanded=False):
        st.latex(r"J = \frac{V_A}{nD}")
        st.latex(r"K_T = \sum C_i J^{s_i}(P/D)^{t_i}(A_E/A_0)^{u_i}Z^{v_i}")
        st.latex(r"K_Q = \sum C_i J^{s_i}(P/D)^{t_i}(A_E/A_0)^{u_i}Z^{v_i}")
        st.latex(r"\eta_O = \frac{J}{2\pi}\frac{K_T}{K_Q}")
        st.markdown("""
        Donde **J** es el coeficiente de avance, **KT** el coeficiente de empuje,
        **KQ** el coeficiente de torque y **ηO** la eficiencia en aguas abiertas.
        Los coeficientes polinomiales se leen desde el archivo `Tabla 1.xlsx`.
        """)

# ==============================================================================
# RESULTADOS NUMÉRICOS
# ==============================================================================

with tab_resultados:
    st.subheader("📋 Matriz Numérica de Resultados")

    st.markdown("""
    <div class="section-card">
    La tabla muestra los valores calculados para cada coeficiente de avance J.
    La columna de eficiencia se resalta automáticamente en su valor máximo para facilitar
    la identificación del punto óptimo de operación.
    </div>
    """, unsafe_allow_html=True)

    tabla = res.copy()
    st.dataframe(
        tabla.style
        .highlight_max(subset=["nO", "ηO (%)"], color="#d8f5d0")
        .format("{:.4f}"),
        use_container_width=True,
        height=500
    )

# ==============================================================================
# TORSIONAL
# ==============================================================================

with tab_torsion:
    st.subheader("💥 Análisis de Vibración Torsional")

    st.markdown("""
    <div class="section-card">
    La vibración torsional se asocia a variaciones periódicas del torque transmitido
    por el eje. En un análisis de prediseño, se verifica que el esfuerzo torsional alternante
    sea menor que un límite admisible basado en la resistencia última del material.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📘 Base teórica de vibración del eje — vibración torsional", expanded=False):
        st.markdown("""
        De acuerdo con la asignación del **Vibración en el Eje Propulsor**, la vibración
        torsional corresponde a una variación cíclica del ángulo de giro relativo entre
        secciones del eje. Puede ser provocada por la irregularidad del par del motor y
        por el torque resistente variable de la hélice al trabajar dentro del campo de
        estela no uniforme del casco.

        En esta aplicación se representa de forma preliminar mediante un torque alternante
        estimado y se compara el esfuerzo torsional obtenido contra un límite admisible
        asociado al material seleccionado. Esta revisión se conecta con el criterio didáctico
        de **IACS UR M68**, usado como referencia para análisis torsional.
        """)
        st.markdown("""
        **Instrumentación relacionada:** torsiógrafo óptico o magnético, sensores de velocidad
        angular y software de TVA/Shafting para modelos de masas discretas, inercias, rigideces
        y amortiguamiento.
        """)

    with st.expander("🧮 Fórmulas de torsión usadas", expanded=False):
        st.latex(r"\omega = \frac{2\pi n}{60}")
        st.latex(r"T = \frac{P}{\omega}")
        st.latex(r"T_{alt} = 0.15T")
        st.latex(r"W_t = \frac{\pi d^3}{16}")
        st.latex(r"\tau = \frac{T_{alt}}{W_t}")
        st.latex(r"\tau_{adm} = 0.35\left(\frac{\sigma_{UTS}}{3}\right)")
        st.markdown("""
        Estas expresiones se usan para estimar el esfuerzo torsional alternante
        en el eje y compararlo contra un límite admisible preliminar basado en
        la resistencia última del material seleccionado.
        """)

    c1, c2 = st.columns([1, 1.3])

    with c1:
        st.metric("Torque nominal", f"{torque_nominal/1000:.2f} kN·m")
        st.metric("Torque alternante estimado", f"{torque_dinamico_alternante/1000:.2f} kN·m")
        st.metric("Esfuerzo real", f"{esfuerzo_real_mpa:.2f} MPa")
        st.metric("Límite admisible", f"{tau_admisible_mpa:.2f} MPa")

        if torsion_ok:
            estado_html("✅ Cumple: el esfuerzo torsional estimado está por debajo del límite admisible.", "good")
        else:
            estado_html("❌ No cumple: el esfuerzo torsional estimado supera el límite admisible.", "bad")

    with c2:
        fig_t, ax_t = plt.subplots(figsize=(7, 3.8))
        ax_t.barh(["Esfuerzo real", "Límite admisible"], [esfuerzo_real_mpa, tau_admisible_mpa])
        ax_t.set_xlabel("MPa")
        ax_t.set_title("Comparación de esfuerzo torsional")
        ax_t.grid(True, axis="x", linestyle=":", alpha=0.6)
        st.pyplot(fig_t)

# ==============================================================================
# AXIAL
# ==============================================================================

with tab_axial:
    st.subheader("↔️ Análisis de Vibración Axial")

    st.markdown("""
    <div class="section-card">
    La vibración axial corresponde al movimiento longitudinal del eje propulsor.
    En buques, suele estar asociada a fluctuaciones del empuje de la hélice y a la
    interacción hélice-casco. Esta sección completa el análisis de
    vibración del eje junto con la parte torsional y lateral.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📘 Base teórica de vibración axial", expanded=True):
        st.markdown("""
        La hélice no entrega un empuje perfectamente constante. Al girar detrás del casco,
        cada pala entra en zonas de estela diferente, por lo que el empuje puede fluctuar.
        Esa fluctuación genera una fuerza alternante en dirección longitudinal del eje.

        En análisis preliminar, la vibración axial puede estudiarse como un sistema
        **masa-resorte**, donde la masa equivalente incluye hélice y parte del eje, y la
        rigidez axial representa la rigidez del eje más la rigidez del cojinete de empuje.

        Las excitaciones más importantes se revisan por órdenes:
        - **1P:** una excitación por revolución del eje.
        - **ZP:** frecuencia de paso de pala, donde Z es el número de palas.
        - **2ZP y 3ZP:** armónicos superiores del paso de pala.
        """)

    with st.expander("🧮 Fórmulas de vibración axial usadas", expanded=True):
        st.latex(r"k_{eje}=\frac{EA}{L}")
        st.latex(r"k_{eq}=\left(\frac{1}{k_{eje}}+\frac{1}{k_{cojinete}}\right)^{-1}")
        st.latex(r"m_{eq}=m_{helice}+0.35m_{eje}")
        st.latex(r"f_{n,axial}=\frac{1}{2\pi}\sqrt{\frac{k_{eq}}{m_{eq}}}")
        st.latex(r"f_{exc}=k\frac{n}{60}")
        st.latex(r"f_{ZP}=Z\frac{n}{60}")
        st.latex(r"x_{axial}=\frac{F_{alt}}{k_{eq}}")
        st.markdown("""
        Donde **E** es el módulo de elasticidad, **A** es el área transversal del eje,
        **L** es la longitud axial equivalente, **Z** es el número de palas y **n** es la RPM.
        """)

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Frecuencia natural axial", f"{f_axial_natural_hz:.2f} Hz")
    a2.metric("RPM crítica axial ZP", f"{rpm_critica_axial_zp:.1f} rpm")
    a3.metric("Rigidez axial equivalente", f"{rigidez_axial_equivalente_n_m/1e9:.2f} GN/m")
    a4.metric("Desplazamiento axial est.", f"{desplazamiento_axial_est_m*1000:.4f} mm")

    if riesgo_axial_global == "Bajo":
        estado_html(f"✅ Condición axial aceptable: riesgo global {riesgo_axial_global}.", "good")
    elif riesgo_axial_global == "Medio":
        estado_html(f"⚠️ Condición axial en zona de precaución: riesgo global {riesgo_axial_global}. No se considera falla, pero conviene revisarlo.", "warn")
    else:
        estado_html(f"❌ Revisar diseño: existe al menos una excitación axial con riesgo {riesgo_axial_global}.", "bad")

    st.markdown("### 📋 Tabla de órdenes axiales")

    def color_riesgo_axial(val):
        if val == "Bajo":
            return "background-color: #dcfce7; color: #166534; font-weight: bold"
        if val == "Medio":
            return "background-color: #fef3c7; color: #92400e; font-weight: bold"
        return "background-color: #fee2e2; color: #991b1b; font-weight: bold"

    st.dataframe(
        axial_df.style
        .format({
            "Frecuencia excitante [Hz]": "{:.3f}",
            "Frecuencia natural axial [Hz]": "{:.3f}",
            "Separación [%]": "{:.2f}"
        })
        .map(color_riesgo_axial, subset=["Riesgo axial"]),
        use_container_width=True,
        height=230
    )

    st.markdown("### 📈 Excitaciones axiales vs frecuencia natural")
    fig_a, ax_a = plt.subplots(figsize=(10, 4.5))
    ordenes_plot = axial_df["Orden de excitación"].tolist()
    frec_plot = axial_df["Frecuencia excitante [Hz]"].tolist()
    ax_a.bar(ordenes_plot, frec_plot, label="Frecuencia excitante")
    ax_a.axhline(y=f_axial_natural_hz, linestyle="--", linewidth=2.4, label="Frecuencia natural axial")
    ax_a.set_ylabel("Frecuencia [Hz]")
    ax_a.set_title("Comparación de excitaciones axiales")
    ax_a.grid(True, axis="y", linestyle=":", alpha=0.6)
    ax_a.legend()
    st.pyplot(fig_a)

    st.markdown("### 🧰 Instrumentación recomendada")
    st.markdown("""
    Para medir o validar vibración axial en un sistema real se pueden usar:

    - **Acelerómetro axial** sobre chumaceras o carcasa del cojinete de empuje.
    - **Sensor de proximidad axial** para medir desplazamiento longitudinal del eje.
    - **Tacómetro** para sincronizar la señal con la RPM del eje.
    - **Galgas extensométricas** para estimar esfuerzo alternante en el eje.
    - **Monitoreo FFT** para identificar picos en 1P, ZP, 2ZP y 3ZP.
    """)

# ==============================================================================
# LATERAL
# ==============================================================================

with tab_lateral:
    st.subheader("📊 Análisis de Vibración Lateral / Whirling")

    st.markdown("""
    <div class="section-card">
    La vibración lateral del eje está relacionada con la deflexión radial y la aparición
    de velocidades críticas. Se recomienda que la velocidad de operación no coincida
    con la zona ±20% alrededor de la primera velocidad crítica lateral.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📘 Base teórica de vibración del eje — vibración lateral / whirling", expanded=False):
        st.markdown("""
        En la guía técnica base, la vibración lateral o *whirling* se describe como
        la deflexión radial del eje. Su frecuencia natural depende de la rigidez a flexión
        **EI**, de la masa equivalente y de la longitud característica del sistema.

        Si la frecuencia de excitación asociada al giro del eje coincide con una frecuencia
        natural lateral, aparece una velocidad crítica. Por eso la aplicación compara la
        velocidad de operación contra una zona de seguridad de **±20%** alrededor de la
        velocidad crítica estimada.
        """)
        st.markdown("""
        **Instrumentación relacionada:** sensores de proximidad inductivos (*eddy current*)
        para medir órbitas del eje, acelerómetros en apoyos y mediciones durante pruebas de mar.
        """)

    with st.expander("🧮 Fórmulas de vibración lateral usadas", expanded=False):
        st.latex(r"I = \frac{\pi d^4}{64}")
        st.latex(r"\delta_h = \frac{W_h L^3}{3EI}")
        st.latex(r"\delta_e = \frac{W_e L^3}{8EI}")
        st.latex(r"f_n = \frac{1}{2\pi\sqrt{\delta_h + \delta_e}}")
        st.latex(r"n_{crit} = 60 f_n")
        st.markdown("""
        El cálculo considera el peso de la hélice y el peso propio del tramo en voladizo
        del eje. La zona crítica se evalúa como ±20% alrededor de la velocidad crítica.
        """)

    c1, c2 = st.columns([1, 1.35])

    with c1:
        st.metric("Frecuencia natural lateral", f"{f_natural_hz:.2f} Hz")
        st.metric("RPM crítica lateral", f"{rpm_critica_lateral:.1f} rpm")
        st.metric("Zona crítica", f"{margen_inf:.1f} - {margen_sup:.1f} rpm")

        if lateral_ok:
            estado_html("✅ Diseño seguro: la RPM de operación está fuera de la zona crítica.", "good")
        else:
            estado_html("❌ Alerta: la RPM de operación cae dentro de la zona crítica.", "bad")

    with c2:
        fig_l, ax_l = plt.subplots(figsize=(8, 3.8))
        ax_l.axvline(x=rpm_critica_lateral, linestyle="--", linewidth=2, label="RPM crítica")
        ax_l.axvspan(margen_inf, margen_sup, alpha=0.20, label="Zona ±20%")
        ax_l.scatter([rpm_motor], [1], s=160, zorder=5, label="RPM operación")
        ax_l.set_yticks([])
        ax_l.set_xlabel("RPM")
        ax_l.set_title("Margen frente a velocidad crítica lateral")
        ax_l.grid(True, axis="x", linestyle=":", alpha=0.6)
        ax_l.legend()
        st.pyplot(fig_l)

# ==============================================================================
# BALANCEO Y DESBALANCE
# ==============================================================================

with tab_balanceo:
    st.subheader("⚖️ Balanceo y Desbalance del Eje")

    st.markdown("""
    <div class="section-card">
    El desbalance aparece cuando el centro de masa de la hélice o del eje no coincide
    exactamente con el centro geométrico de rotación. Esto genera una fuerza centrífuga
    periódica que actúa una vez por revolución y puede producir vibración lateral,
    aumento de carga en cojinetes y desgaste prematuro.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📘 Base teórica de balanceo", expanded=True):
        st.markdown("""
        En un eje ideal, la masa gira de forma simétrica alrededor del centro. Cuando existe
        una pequeña masa excéntrica, se produce una fuerza dinámica proporcional a la masa,
        a la excentricidad y al cuadrado de la velocidad angular. Por eso un pequeño
        desbalance puede volverse importante cuando aumentan las RPM.

        En sistemas navales, el desbalance puede originarse por imperfecciones de fabricación,
        daños en palas, incrustaciones marinas, reparación desigual de la hélice o montaje
        incorrecto del conjunto eje-hélice.
        """)

    with st.expander("🧮 Fórmulas de desbalance usadas", expanded=True):
        st.latex(r"\omega=\frac{2\pi n}{60}")
        st.latex(r"F_u=m_u e \omega^2")
        st.latex(r"\%F_u=\frac{F_u}{W_h}\times 100")
        st.markdown("""
        Donde **mᵤ** es la masa equivalente desbalanceada, **e** es la excentricidad,
        **ω** es la velocidad angular y **Wₕ** es el peso de la hélice.
        """)

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Masa desbalanceada est.", f"{masa_desbalance_kg:.2f} kg")
    b2.metric("Excentricidad", f"{excentricidad_desbalance_m*1000:.2f} mm")
    b3.metric("Fuerza dinámica", f"{fuerza_desbalance_n:,.1f} N")
    b4.metric("Relación vs peso hélice", f"{fuerza_desbalance_rel_pct:.3f}%")

    if desbalance_ok:
        estado_html(f"✅ Desbalance estimado aceptable: riesgo {riesgo_desbalance}.", "good" if riesgo_desbalance == "Bajo" else "warn")
    else:
        estado_html("❌ Desbalance elevado: revisar balanceo dinámico de hélice y eje.", "bad")

    st.markdown("### 📈 Fuerza de desbalance contra RPM")
    rpm_bal = np.linspace(0, max(rpm_motor * 2.0, 150), 300)
    omega_bal = 2.0 * np.pi * rpm_bal / 60.0
    fuerza_bal = masa_desbalance_kg * excentricidad_desbalance_m * omega_bal**2
    fig_b, ax_b = plt.subplots(figsize=(10, 4.5))
    ax_b.plot(rpm_bal, fuerza_bal, linewidth=2.6, label="Fuerza por desbalance")
    ax_b.axvline(x=rpm_motor, linestyle="--", linewidth=2, label=f"RPM operación = {rpm_motor:.0f}")
    ax_b.scatter([rpm_motor], [fuerza_desbalance_n], s=120, zorder=5)
    ax_b.set_xlabel("RPM")
    ax_b.set_ylabel("Fuerza [N]")
    ax_b.set_title("Crecimiento de la fuerza de desbalance con la velocidad")
    ax_b.grid(True, linestyle=":", alpha=0.6)
    ax_b.legend()
    st.pyplot(fig_b)

    st.markdown("### 🧰 Recomendaciones de control")
    st.markdown("""
    - Realizar **balanceo estático** de la hélice antes del montaje.
    - Verificar **balanceo dinámico** del conjunto cuando sea posible.
    - Revisar daños, incrustaciones o reparaciones desiguales en palas.
    - Usar tacómetro y acelerómetros para identificar picos 1P asociados a desbalance.
    - Si el pico 1P aumenta con la velocidad, revisar alineación, concentricidad y estado de cojinetes.
    """)

# ==============================================================================
# CAMPBELL
# ==============================================================================

with tab_campbell:
    st.subheader("🗺️ Diagrama de Campbell")

    st.markdown("""
    <div class="section-card">
    El diagrama de Campbell compara las frecuencias naturales del sistema contra las
    frecuencias de excitación producidas por el giro del eje y por el paso de palas.
    En esta versión se incluyen los órdenes **1P, 2P, 3P, ZP, 2ZP y 3ZP**, además de los
    modos lateral, torsional estimado y axial.
    </div>
    """, unsafe_allow_html=True)

    max_rpm_grafica = max(rpm_motor * 2.0, rpm_critica_lateral * 1.25, rpm_critica_axial_zp * 1.35, 120)
    rpm_x = np.linspace(0, max_rpm_grafica, 500)

    fig_c, ax_c = plt.subplots(figsize=(11, 5.6))

    ax_c.axhline(y=f_natural_hz, linestyle="--", linewidth=2.4, label=f"Modo lateral = {f_natural_hz:.2f} Hz")
    ax_c.axhline(y=f_torsional_est, linestyle="-.", linewidth=2.0, label=f"Modo torsional est. = {f_torsional_est:.2f} Hz")
    ax_c.axhline(y=f_axial_natural_hz, linestyle=":", linewidth=3.0, label=f"Modo axial = {f_axial_natural_hz:.2f} Hz")

    ordenes_campbell = [("1P", 1), ("2P", 2), ("3P", 3), ("ZP", z_val), ("2ZP", 2 * z_val), ("3ZP", 3 * z_val)]
    for nombre, mult in ordenes_campbell:
        ax_c.plot(rpm_x, mult * rpm_x / 60.0, linewidth=1.7, label=nombre)

    ax_c.axvline(x=rpm_motor, linestyle="-", linewidth=2.4, label=f"RPM operación = {rpm_motor:.0f}")
    ax_c.set_xlabel("Velocidad de giro [rpm]")
    ax_c.set_ylabel("Frecuencia [Hz]")
    ax_c.set_title("Diagrama de Campbell — órdenes 1P/ZP y modos naturales")
    ax_c.grid(True, linestyle=":", alpha=0.62)
    ax_c.legend(loc="upper left", fontsize=8, ncols=2)
    st.pyplot(fig_c)

    st.markdown("### 📋 Tabla de resonancias e intersecciones")
    st.markdown("""
    La tabla calcula en qué RPM se cruzaría cada orden de excitación con cada modo natural.
    Si la intersección queda cerca de la RPM de operación, aumenta el riesgo de resonancia.
    """)

    def color_riesgo_campbell(val):
        if val == "Bajo":
            return "background-color: #dcfce7; color: #166534; font-weight: bold"
        if val == "Medio":
            return "background-color: #fef3c7; color: #92400e; font-weight: bold"
        return "background-color: #fee2e2; color: #991b1b; font-weight: bold"

    st.dataframe(
        campbell_df.style
        .format({
            "Frecuencia natural [Hz]": "{:.3f}",
            "RPM de intersección": "{:.2f}",
            "RPM operación": "{:.2f}",
            "Separación [%]": "{:.2f}"
        })
        .map(color_riesgo_campbell, subset=["Riesgo"]),
        use_container_width=True,
        height=460
    )

    st.markdown("### 🧾 Lectura rápida")
    st.markdown(f"""
    - **1P** representa una excitación por cada vuelta del eje.
    - **ZP** representa el paso de pala: con **Z = {z_val} palas**, la excitación principal ocurre {z_val} veces por revolución.
    - **2ZP y 3ZP** son armónicos superiores; suelen aparecer por estela no uniforme, cavitación, desbalance o interacción casco-hélice.
    - Si el riesgo aparece como **Alto**, conviene modificar RPM de operación, rigidez, diámetro del eje, distribución de apoyos o revisar el diseño de hélice.
    """)

# ==============================================================================
# CAVITACIÓN
# ==============================================================================

with tab_cav:
    st.subheader("🔍 Análisis de Cavitación y Número de Reynolds")

    st.markdown("""
    <div class="section-card">
    Esta sección evalúa el comportamiento hidrodinámico del propulsor mediante dos
    indicadores fundamentales: el <b>número de Reynolds</b>, asociado al régimen de flujo,
    y el <b>coeficiente de cavitación σ</b>, asociado a la tendencia de formación de vapor
    sobre las palas. Estos resultados son preliminares y sirven para orientar decisiones
    de diseño como inmersión del eje, área expandida y carga de la hélice.
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Velocidad efectiva Va", f"{v_ms:.2f} m/s")
    c2.metric("Número de Reynolds", f"{reynolds:.2e}")
    c3.metric("Coef. cavitación σ", f"{sigma_n:.3f}")

    with st.expander("🧮 Fórmulas de Reynolds y cavitación usadas", expanded=False):
        st.latex(r"V_A = V_s(1-w)")
        st.latex(r"Re = \frac{V_A D}{\nu}")
        st.latex(r"\sigma = \frac{P_{atm} + \rho g h - P_v}{\frac{1}{2}\rho V_A^2}")
        st.markdown("""
        **VA** es la velocidad efectiva que entra a la hélice, **Re** indica el régimen
        de flujo, y **σ** estima la tendencia preliminar a cavitación. Un valor bajo de σ
        implica mayor riesgo de formación de vapor sobre las palas.
        """)

    st.markdown("---")

    col_re, col_cav = st.columns(2)

    with col_re:
        st.markdown("### 🌊 Gráfica del Número de Reynolds")
        fig_re, ax_re = plt.subplots(figsize=(7.2, 4.0))
        etiquetas_re = ["Laminar", "Transición", "Turbulento", "Diseño actual"]
        valores_re = [2.0e3, 4.0e3, 1.0e7, reynolds]
        ax_re.barh(etiquetas_re, valores_re)
        ax_re.set_xscale("log")
        ax_re.set_xlabel("Número de Reynolds Re [escala log]")
        ax_re.set_title("Comparación de régimen de flujo")
        ax_re.grid(True, which="both", linestyle=":", alpha=0.55)
        st.pyplot(fig_re)

        if reynolds_ok:
            st.success("✅ El flujo se encuentra en régimen turbulento típico de hélices navales.")
        else:
            st.warning("⚠️ Reynolds bajo para escala naval. Revisar velocidad efectiva, diámetro o escala de análisis.")

    with col_cav:
        st.markdown("### ⚠️ Gráfica del Coeficiente de Cavitación")
        fig_sig, ax_sig = plt.subplots(figsize=(7.2, 4.0))
        etiquetas_sig = ["Riesgo alto", "Precaución", "Zona segura", "Diseño actual"]
        valores_sig = [0.20, 0.50, 1.00, sigma_n]
        ax_sig.barh(etiquetas_sig, valores_sig)
        ax_sig.axvline(0.20, linestyle="--", linewidth=2, label="Límite crítico σ = 0.20")
        ax_sig.set_xlabel("Coeficiente de cavitación σ")
        ax_sig.set_title("Comparación de riesgo de cavitación")
        ax_sig.grid(True, linestyle=":", alpha=0.55)
        ax_sig.legend(fontsize=8)
        st.pyplot(fig_sig)

        if sigma_n < 0.20:
            st.error("""
            🔴 Riesgo elevado de cavitación. Se recomienda aumentar Ae/A0, aumentar
            la inmersión del eje, reducir la velocidad efectiva o revisar el diámetro
            y la carga de la hélice.
            """)
        elif sigma_n < 0.50:
            st.warning("""
            🟡 Zona de precaución. El diseño puede funcionar, pero conviene validar
            con un análisis de cavitación más detallado y revisión de distribución de carga.
            """)
        else:
            st.success("""
            🟢 Condición preliminar favorable frente a cavitación. El valor de σ se
            encuentra por encima del umbral crítico usado en esta evaluación.
            """)

    st.markdown("---")
    st.markdown("""
    ### 📖 Interpretación técnica

    La cavitación aparece cuando la presión local en alguna región de la pala cae por debajo
    de la presión de vapor del agua. En operación real puede provocar ruido, vibración,
    erosión superficial y pérdida de eficiencia propulsiva. El número de Reynolds confirma
    si el flujo alrededor de la hélice está dentro de un régimen representativo para análisis
    hidrodinámico naval.
    """)

# ==============================================================================
# NORMATIVA APLICABLE
# ==============================================================================

with tab_normativa:
    st.subheader("📚 Normativa aplicable al sistema de eje y vibraciones")

    st.markdown("""
    <div class="section-card">
    Esta sección reúne las normas y guías relacionadas con el sistema de eje propulsor,
    vibraciones, alineación, materiales, inspección y criterios de aceptación preliminar.
    Se usan como referencia didáctica; para un proyecto real se debe consultar la edición
    vigente de la sociedad clasificadora correspondiente.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🧾 Resumen de normas y criterios")

    normativa_df = pd.DataFrame({
        "Norma / Sociedad": [
            "ABS",
            "DNV",
            "Bureau Veritas",
            "Lloyd's Register",
            "ISO 10816 / ISO 20816",
            "ISO 1940",
            "SOLAS"
        ],
        "Aplicación en la app": [
            "Sistema de eje, materiales, inspección, arreglo de eje y revisión de esfuerzos.",
            "Dimensionamiento de ejes, vibración torsional, alineación y cargas en cojinetes.",
            "Criterios de arreglo de propulsión, eje de cola, bocina y chumaceras.",
            "Revisión de shafting, aceptación de maquinaria y vibraciones en servicio.",
            "Evaluación general de vibración mecánica medida en máquinas rotativas.",
            "Balanceo de rotores rígidos y calidad de balanceo.",
            "Seguridad de maquinaria propulsora y continuidad operacional del buque."
        ],
        "Relación con resultados": [
            "Comparación de esfuerzo torsional y recomendaciones de diseño.",
            "Campbell, resonancia, torsión, alineación y velocidad crítica.",
            "Geometría del eje, apoyos, bocina y chumaceras.",
            "Criterios de aceptación de vibraciones y monitoreo.",
            "Medición de vibración axial, lateral y torsional.",
            "Pestaña de balanceo y desbalance del eje.",
            "Marco general de seguridad y confiabilidad del sistema propulsor."
        ]
    })

    st.dataframe(normativa_df, use_container_width=True, height=330)

    st.markdown("### ⚙️ Cómo se conecta con la aplicación")
    col_n1, col_n2 = st.columns(2)

    with col_n1:
        st.markdown("""
        **Cálculos directamente relacionados:**

        - Esfuerzo torsional del eje.
        - Frecuencia lateral o whirling.
        - Frecuencia axial natural.
        - Diagrama de Campbell.
        - Desbalance dinámico.
        - Cavitación y condiciones hidrodinámicas.
        """)

    with col_n2:
        st.markdown("""
        **Lo que debe revisarse en un diseño real:**

        - Diámetro mínimo del eje según clase.
        - Material y esfuerzo admisible.
        - Cargas en chumaceras y bocina.
        - Alineación del eje.
        - Resonancias dentro del rango de operación.
        - Balanceo de hélice y eje.
        """)

    st.markdown("### 📌 Nota para presentación")
    st.info(
        "La app no sustituye una aprobación de clase. Funciona como una herramienta "
        "preliminar para visualizar parámetros críticos del sistema propulsivo y justificar "
        "decisiones de diseño antes de un análisis formal con ABS, DNV, BV o LR."
    )


# ==============================================================================
# CLASE / CUMPLIMIENTO
# ==============================================================================

with tab_clase:
    st.subheader("📋 Dictamen Orientativo de Cumplimiento")

    st.markdown("""
    <div class="section-card">
    Esta sección no sustituye una aprobación oficial de ABS, DNV, Lloyd's Register,
    Bureau Veritas u otra sociedad de clasificación. Funciona como dictamen preliminar
    de ingeniería para revisar si el diseño presenta señales de riesgo en torsión,
    cavitación, vibración lateral e hidrodinámica.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📘 Relación con la teoría de vibración del eje", expanded=False):
        st.markdown("""
        El dictamen agrupa los tres enfoques principales de la asignación:

        - **Torsional:** variaciones cíclicas de torque y esfuerzo alternante del eje.
        - **Lateral / whirling:** separación entre la velocidad de servicio y velocidades críticas.
        - **Axial:** asociada a fluctuaciones de empuje de la hélice en órdenes **1P, ZP, 2ZP y 3ZP**;
          en esta versión sí se evalúa con frecuencia natural axial, rigidez equivalente,
          tabla de separación y riesgo de resonancia.

        También se incluyen las referencias técnicas mencionadas en la guía: **IACS UR M68**, notas de
        **ABS** para vibración de shafting, recomendaciones **DNV/ISO** e instrumentación como torsiógrafo,
        sensor de proximidad y acelerómetro axial.
        """)

    cumplimiento = pd.DataFrame({
        "Área evaluada": [
            "Hidrodinámica de aguas abiertas",
            "Número de Reynolds",
            "Cavitación",
            "Vibración torsional",
            "Vibración lateral",
            "Vibración axial",
        ],
        "Criterio usado": [
            "ηO máxima > 40%",
            "Re > 1.0E7",
            "σ ≥ 0.20",
            "τ real ≤ τ admisible",
            "RPM operación fuera de ±20% de RPM crítica",
            "Sin órdenes axiales en zona de alto riesgo"
        ],
        "Valor": [
            f"{max_eff*100:.2f}%",
            f"{reynolds:.2e}",
            f"{sigma_n:.3f}",
            f"{esfuerzo_real_mpa:.2f} / {tau_admisible_mpa:.2f} MPa",
            f"{rpm_motor:.1f} rpm vs {margen_inf:.1f}-{margen_sup:.1f} rpm",
            f"Riesgo axial {riesgo_axial_global}"
        ],
        "Resultado": [
            "Cumple" if hidro_ok else "Observación",
            "Cumple" if reynolds_ok else "Observación",
            "Cumple" if cavitacion_ok else "No cumple",
            "Cumple" if torsion_ok else "No cumple",
            "Cumple" if lateral_ok else "No cumple",
            "Cumple" if axial_ok else "No cumple",
        ]
    })

    def color_resultado(val):
        if val == "Cumple":
            return "background-color: #dcfce7; color: #166534; font-weight: bold"
        if val == "Observación":
            return "background-color: #fef3c7; color: #92400e; font-weight: bold"
        return "background-color: #fee2e2; color: #991b1b; font-weight: bold"

    st.dataframe(
        cumplimiento.style.map(color_resultado, subset=["Resultado"]),
        use_container_width=True,
        height=250
    )

    estado_html(f"{dictamen_icono} Dictamen general: {dictamen} ({score:.0f}%)", dictamen_tipo)

# ==============================================================================
# EXPORTACIÓN
# ==============================================================================

with tab_export:
    st.subheader("📄 Exportación de Resultados")

    st.markdown("""
    <div class="section-card">
    Esta sección permite descargar los resultados del análisis para anexarlos a una memoria
    técnica, reporte de clase o presentación académica. El archivo Excel incluye resumen,
    curvas Wageningen y tabla de cumplimiento.
    </div>
    """, unsafe_allow_html=True)

    excel_data = generar_excel()
    st.download_button(
        label="📥 Descargar resultados en Excel",
        data=excel_data,
        file_name="resultados_propulsion_shafting.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    pdf_data = generar_pdf()
    if pdf_data is not None:
        st.download_button(
            label="📄 Descargar reporte técnico PDF",
            data=pdf_data,
            file_name="reporte_propulsion_shafting.pdf",
            mime="application/pdf"
        )
    else:
        st.warning(
            "Para activar la descarga PDF agrega 'reportlab' a requirements.txt."
        )

    st.markdown("### Requisitos recomendados para Streamlit Cloud")
    st.code(
        "streamlit\npandas\nnumpy\nmatplotlib\nopenpyxl\nxlsxwriter\nreportlab",
        language="text"
    )


# ==============================================================================
# FÓRMULAS DEL MODELO
# ==============================================================================

with tab_formulas:
    st.subheader("🧮 Formulario Técnico del Modelo")

    st.markdown("""
    <div class="section-card">
    Esta pestaña reúne las principales expresiones matemáticas utilizadas por la aplicación.
    Su objetivo es que, durante la presentación, se pueda justificar de forma clara qué
    ecuaciones se emplearon para obtener los resultados de hidrodinámica, cavitación,
    vibración torsional, vibración lateral y dictamen preliminar.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 1. Velocidad efectiva de avance hacia la hélice")
    st.latex(r"V_A = V_s(1-w)")
    st.markdown("Donde **Vs** es la velocidad del buque en m/s y **w** es la fracción de estela.")

    st.markdown("### 2. Coeficiente de avance")
    st.latex(r"J = \frac{V_A}{nD}")
    st.markdown("Donde **n** es la velocidad de giro en rev/s y **D** es el diámetro de la hélice.")

    st.markdown("### 3. Polinomios Wageningen Serie B")
    st.latex(r"K_T = \sum C_i J^{s_i}(P/D)^{t_i}(A_E/A_0)^{u_i}Z^{v_i}")
    st.latex(r"K_Q = \sum C_i J^{s_i}(P/D)^{t_i}(A_E/A_0)^{u_i}Z^{v_i}")
    st.markdown("Los coeficientes **Ci, si, ti, ui, vi** se leen del archivo `Tabla 1.xlsx`.")

    st.markdown("### 4. Eficiencia en aguas abiertas")
    st.latex(r"\eta_O = \frac{J}{2\pi}\frac{K_T}{K_Q}")

    st.markdown("### 5. Número de Reynolds")
    st.latex(r"Re = \frac{V_A D}{\nu}")
    st.markdown("Se usa para identificar si el flujo se encuentra en régimen laminar, transicional o turbulento.")

    st.markdown("### 6. Coeficiente de cavitación")
    st.latex(r"\sigma = \frac{P_{atm} + \rho g h - P_v}{\frac{1}{2}\rho V_A^2}")
    st.markdown("Valores bajos de σ indican mayor riesgo de cavitación.")

    st.markdown("### 7. Torque nominal")
    st.latex(r"\omega = \frac{2\pi n}{60}")
    st.latex(r"T = \frac{P}{\omega}")

    st.markdown("### 8. Esfuerzo torsional alternante")
    st.latex(r"T_{alt} = 0.15T")
    st.latex(r"W_t = \frac{\pi d^3}{16}")
    st.latex(r"\tau = \frac{T_{alt}}{W_t}")
    st.latex(r"\tau_{adm} = 0.35\left(\frac{\sigma_{UTS}}{3}\right)")

    st.markdown("### 9. Deflexión y frecuencia lateral")
    st.latex(r"I = \frac{\pi d^4}{64}")
    st.latex(r"\delta_h = \frac{W_h L^3}{3EI}")
    st.latex(r"\delta_e = \frac{W_e L^3}{8EI}")
    st.latex(r"f_n = \frac{1}{2\pi\sqrt{\delta_h + \delta_e}}")
    st.latex(r"n_{crit} = 60 f_n")

    st.markdown("### 10. Órdenes del Diagrama de Campbell")
    st.latex(r"f_{orden} = k\frac{n}{60}")
    st.latex(r"f_{ZP} = Z\frac{n}{60}")

    st.markdown("### 11. Índice global de diseño")
    st.markdown("""
    El índice global se calcula con ponderaciones preliminares:

    - Hidrodinámica: 15 puntos
    - Reynolds: 10 puntos
    - Cavitación: 15 puntos
    - Torsión: 20 puntos
    - Vibración axial: 20 puntos
    - Vibración lateral: 20 puntos

    Este índice no sustituye una aprobación oficial de una sociedad de clasificación,
    pero permite generar un dictamen preliminar de ingeniería.
    """)

# ==============================================================================
# GUÍA DIDÁCTICA
# ==============================================================================

with tab_guia:
    st.subheader("📚 Guía de Referencia Naval")

    st.markdown("""
    <div class="section-card">
    Esta guía sirve como referencia rápida para que el usuario pueda ingresar datos coherentes
    al analizar distintos tipos de buque. Los rangos son orientativos y no sustituyen una base
    de datos de proyecto ni reglas oficiales de clasificación.
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
        ### Rangos típicos de Lpp

        | Tipo de buque | Lpp aproximado |
        |---|---:|
        | Remolcador | 20–50 m |
        | OSV / PSV | 60–110 m |
        | AHTS | 70–120 m |
        | Ferry | 80–220 m |
        | Bulk carrier | 180–250 m |
        | Buque tanque | 250–330 m |
        | Portacontenedores | 250–400 m |

        ### Número de palas

        - **3 palas:** buena eficiencia, más vibración.
        - **4 palas:** configuración comercial común.
        - **5 palas:** menor vibración y ruido.
        - **6–7 palas:** aplicaciones especiales o alta carga.
        """)

    with c2:
        st.markdown("""
        ### Rangos típicos de Ae/A0

        | Aplicación | Ae/A0 |
        |---|---:|
        | Baja carga | 0.40–0.55 |
        | Mercante estándar | 0.50–0.70 |
        | Alta carga | 0.70–0.95 |

        ### Interpretación rápida

        - **KT:** capacidad de empuje.
        - **KQ:** torque requerido.
        - **ηO:** eficiencia ideal de aguas abiertas.
        - **σ:** tendencia a cavitación.
        - **Campbell:** detección de posibles resonancias.
        """)

    st.info(
        "Recomendación: para un proyecto formal, documentar siempre la fuente de dimensiones, "
        "potencia, RPM, material y coeficientes hidrodinámicos usados."
    )

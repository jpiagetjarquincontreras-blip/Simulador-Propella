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
    st.subheader("🔩 Sistema mecánico")

    potencia_kw_base = st.number_input(
        "Potencia MCR base [kW]",
        value=22000.0,
        min_value=1.0,
        step=100.0,
        help="Potencia máxima continua instalada antes de aplicar margen de servicio."
    )

    potencia_kw = potencia_kw_base * (1 + margen_servicio / 100)

    rpm_motor = st.number_input(
        "RPM del eje / motor principal [rpm]",
        value=75.0,
        min_value=1.0,
        step=1.0
    )

    diametro_eje_mm = st.number_input(
        "Diámetro del eje [mm]",
        value=680.0,
        min_value=10.0,
        step=5.0
    )

    peso_helice_kg = st.number_input(
        "Peso de la hélice [kg]",
        value=52000.0,
        min_value=1.0,
        step=100.0
    )

    longitud_volado_m = st.number_input(
        "Longitud en voladizo del eje [m]",
        value=3.5,
        min_value=0.1,
        step=0.1
    )

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

v_ms = (velocidad * 0.5144) * (1.0 - estela)
nu = 1.188e-6
reynolds = safe_div(v_ms * diam_prop_m, nu)

sigma_n = safe_div(
    p_atm_auto + (rho_auto * g_auto * inmersion_eje_m) - p_vap_auto,
    0.5 * rho_auto * max(v_ms**2, 1e-12)
)

omega = (2.0 * math.pi * rpm_motor) / 60.0
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

# Score global ponderado
score = 0
score += 25 if torsion_ok else 0
score += 25 if lateral_ok else 0
score += 20 if cavitacion_ok else 0
score += 15 if reynolds_ok else 0
score += 15 if hidro_ok else 0

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
            score,
            dictamen
        ]
    }
    return pd.DataFrame(datos)


def generar_excel():
    output = BytesIO()
    resumen_df = construir_resumen_dataframe()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        resumen_df.to_excel(writer, sheet_name="Resumen", index=False)
        res.to_excel(writer, sheet_name="Wageningen", index=False)

        cumplimiento = pd.DataFrame({
            "Criterio": [
                "Hidrodinámica",
                "Reynolds",
                "Cavitación",
                "Vibración torsional",
                "Vibración lateral"
            ],
            "Resultado": [
                "Cumple" if hidro_ok else "Observación",
                "Cumple" if reynolds_ok else "Observación",
                "Cumple" if cavitacion_ok else "No cumple",
                "Cumple" if torsion_ok else "No cumple",
                "Cumple" if lateral_ok else "No cumple"
            ]
        })
        cumplimiento.to_excel(writer, sheet_name="Cumplimiento", index=False)

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

tab_dash, tab_resumen, tab_hidro, tab_resultados, tab_torsion, tab_lateral, tab_campbell, tab_cav, tab_clase, tab_export, tab_guia = st.tabs([
    "🏠 Dashboard",
    "📑 Resumen",
    "📈 Hidrodinámica",
    "📋 Resultados",
    "💥 Torsional",
    "📊 Lateral",
    "🗺️ Campbell",
    "🔍 Cavitación",
    "📋 Clase",
    "📄 Exportar",
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
    vibración lateral, cavitación, régimen de Reynolds y consistencia geométrica.
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

    c1, c2, c3 = st.columns(3)
    with c1:
        estado_html("✅ Torsión aceptable" if torsion_ok else "❌ Torsión fuera de límite", "good" if torsion_ok else "bad")
    with c2:
        estado_html("✅ Lateral seguro" if lateral_ok else "❌ Riesgo de velocidad crítica", "good" if lateral_ok else "bad")
    with c3:
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
# CAMPBELL
# ==============================================================================

with tab_campbell:
    st.subheader("🗺️ Diagrama de Campbell")

    st.markdown("""
    <div class="section-card">
    El diagrama de Campbell compara las frecuencias de excitación generadas por la rotación
    del eje y la hélice con las frecuencias naturales del sistema. Los cruces entre líneas
    de orden y frecuencias naturales indican posibles zonas de resonancia.
    </div>
    """, unsafe_allow_html=True)

    max_rpm_grafica = max(rpm_motor * 1.8, rpm_critica_lateral * 1.2)
    rpm_x = np.linspace(0, max_rpm_grafica, 500)

    fig_c, ax_c = plt.subplots(figsize=(11, 5.4))

    ax_c.axhline(y=f_natural_hz, linestyle="--", linewidth=2.4, label=f"Frecuencia lateral = {f_natural_hz:.2f} Hz")
    ax_c.axhline(y=f_torsional_est, linestyle="-.", linewidth=2.0, label=f"Frecuencia torsional est. = {f_torsional_est:.2f} Hz")

    for orden in range(1, 6):
        ax_c.plot(rpm_x, orden * rpm_x / 60.0, linewidth=1.6, label=f"{orden}P")

    ax_c.plot(rpm_x, z_val * rpm_x / 60.0, linewidth=3.0, label=f"{z_val}P — paso de pala")

    ax_c.axvline(x=rpm_motor, linestyle=":", linewidth=2.4, label=f"RPM operación = {rpm_motor:.0f}")
    ax_c.set_xlabel("Velocidad de giro [rpm]")
    ax_c.set_ylabel("Frecuencia [Hz]")
    ax_c.set_title("Diagrama de Campbell — órdenes de excitación y frecuencias naturales")
    ax_c.grid(True, linestyle=":", alpha=0.62)
    ax_c.legend(loc="upper left", fontsize=8)
    st.pyplot(fig_c)

# ==============================================================================
# CAVITACIÓN
# ==============================================================================

with tab_cav:with tab_cav:

    st.subheader("🔍 Análisis de Cavitación y Número de Reynolds")

    st.markdown("""
    Esta sección evalúa el comportamiento hidrodinámico del propulsor
    mediante el análisis del número de Reynolds y del coeficiente de
    cavitación.

    Estos parámetros permiten estimar:

    • Régimen de flujo alrededor de la hélice.

    • Riesgo de cavitación.

    • Condiciones de operación seguras.

    • Calidad hidrodinámica preliminar del diseño.
    """)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Número de Reynolds",
        f"{reynolds:.2e}"
    )

    col2.metric(
        "Coeficiente σ",
        f"{sigma_n:.3f}"
    )

    col3.metric(
        "Velocidad efectiva",
        f"{v_ms:.2f} m/s"
    )

    st.markdown("---")

    st.markdown("## 🌊 Evaluación del Número de Reynolds")

    fig_re, ax_re = plt.subplots(figsize=(10,4))

    referencias_re = [
        2e3,
        4e3,
        1e6,
        reynolds
    ]

    etiquetas_re = [
        "Laminar",
        "Transición",
        "Turbulento",
        "Diseño"
    ]

    ax_re.barh(
        etiquetas_re,
        referencias_re
    )

    ax_re.set_xscale("log")

    ax_re.set_title(
        "Comparación del Número de Reynolds"
    )

    ax_re.set_xlabel(
        "Número de Reynolds (escala logarítmica)"
    )

    ax_re.grid(
        True,
        linestyle=":"
    )

    st.pyplot(fig_re)

    st.info("""
    Valores superiores a 10⁷ son habituales en hélices navales
    y representan flujo completamente turbulento.
    """)

    st.markdown("---")

    st.markdown("## ⚠️ Evaluación del Riesgo de Cavitación")

    fig_sigma, ax_sigma = plt.subplots(figsize=(10,4))

    niveles_sigma = [
        0.20,
        0.50,
        1.00,
        sigma_n
    ]

    etiquetas_sigma = [
        "Riesgo Alto",
        "Precaución",
        "Seguro",
        "Diseño"
    ]

    ax_sigma.barh(
        etiquetas_sigma,
        niveles_sigma
    )

    ax_sigma.axvline(
        0.20,
        color="red",
        linestyle="--",
        label="Límite crítico"
    )

    ax_sigma.legend()

    ax_sigma.grid(
        True,
        linestyle=":"
    )

    ax_sigma.set_title(
        "Comparación del Coeficiente de Cavitación"
    )

    ax_sigma.set_xlabel(
        "σ"
    )

    st.pyplot(fig_sigma)

    if sigma_n < 0.20:

        st.error("""
        🔴 Riesgo elevado de cavitación.

        Se recomienda revisar:
        - Área expandida Ae/A0
        - Inmersión del eje
        - Velocidad efectiva
        - Diámetro de hélice
        """)

    elif sigma_n < 0.50:

        st.warning("""
        🟡 Zona de precaución.

        El diseño puede operar adecuadamente, pero se recomienda
        una evaluación más detallada.
        """)

    else:

        st.success("""
        🟢 Diseño favorable frente a cavitación.

        El coeficiente σ se encuentra dentro de rangos aceptables
        para análisis preliminar.
        """)

    st.markdown("---")

    st.markdown("""
    ## 📖 Interpretación Técnica

    La cavitación ocurre cuando la presión local en la superficie
    de las palas cae por debajo de la presión de vapor del agua.

    Este fenómeno puede provocar:

    • Pérdida de eficiencia.

    • Incremento del ruido.

    • Vibraciones.

    • Erosión superficial de las palas.

    El número de Reynolds permite verificar que el flujo se
    encuentra dentro del régimen esperado para aplicaciones navales.
    """)
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

    cumplimiento = pd.DataFrame({
        "Área evaluada": [
            "Hidrodinámica de aguas abiertas",
            "Número de Reynolds",
            "Cavitación",
            "Vibración torsional",
            "Vibración lateral",
        ],
        "Criterio usado": [
            "ηO máxima > 40%",
            "Re > 1.0E7",
            "σ ≥ 0.20",
            "τ real ≤ τ admisible",
            "RPM operación fuera de ±20% de RPM crítica"
        ],
        "Valor": [
            f"{max_eff*100:.2f}%",
            f"{reynolds:.2e}",
            f"{sigma_n:.3f}",
            f"{esfuerzo_real_mpa:.2f} / {tau_admisible_mpa:.2f} MPa",
            f"{rpm_motor:.1f} rpm vs {margen_inf:.1f}-{margen_sup:.1f} rpm"
        ],
        "Resultado": [
            "Cumple" if hidro_ok else "Observación",
            "Cumple" if reynolds_ok else "Observación",
            "Cumple" if cavitacion_ok else "No cumple",
            "Cumple" if torsion_ok else "No cumple",
            "Cumple" if lateral_ok else "No cumple",
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

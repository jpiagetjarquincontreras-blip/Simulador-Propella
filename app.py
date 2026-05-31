import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# ==============================================================================
# CONFIGURACIÓN GENERAL
# ==============================================================================

st.set_page_config(
    page_title="Universal Ship Propulsion & Shafting Analysis Suite",
    layout="wide",
    page_icon="⚓"
)

# ==============================================================================
# CSS PROFESIONAL
# ==============================================================================

st.markdown("""
<style>

.main {
    background-color:#f8fafc;
}

.main-title{
    font-size:38px;
    font-weight:800;
    color:#1e293b;
}

.main-subtitle{
    font-size:15px;
    color:#64748b;
    margin-bottom:20px;
}

.stTabs [data-baseweb="tab-list"]{
    gap:8px;
    background:#f1f5f9;
    padding:8px;
    border-radius:12px;
}

.stTabs [data-baseweb="tab"]{
    border-radius:10px;
    font-weight:600;
}

.stTabs [aria-selected="true"]{
    background-color:#4c1d95 !important;
    color:white !important;
}

.kpi-card{
    background:white;
    padding:20px;
    border-radius:12px;
    border:1px solid #e2e8f0;
}

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# TÍTULO
# ==============================================================================

st.markdown(
    """
    <div class="main-title">
    ⚓ Universal Ship Propulsion & Shafting Analysis Suite
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="main-subtitle">
    Plataforma Universal para Análisis Hidrodinámico, Vibratorio,
    Cavitación y Cumplimiento de Sistemas Propulsivos Navales
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================================================================
# CARGA DE POLINOMIOS WAGENINGEN
# ==============================================================================

@st.cache_data
def load_coefficients():

    try:

        kt_df = pd.read_excel(
            "Tabla 1.xlsx",
            sheet_name="KT"
        )

        kq_df = pd.read_excel(
            "Tabla 1.xlsx",
            sheet_name="KQ"
        )

        for df in [kt_df, kq_df]:

            df.columns = [
                c.strip().capitalize()
                for c in df.columns
            ]

        return kt_df, kq_df

    except Exception as e:

        st.error(
            f"Error al cargar Tabla 1.xlsx: {e}"
        )

        return None, None


df_kt, df_kq = load_coefficients()

# ==============================================================================
# FUNCIÓN WAGENINGEN
# ==============================================================================

def calcular_curvas(pd_v, ae_v, z_v):

    j_vals = np.linspace(
        0.001,
        1.2,
        100
    )

    kt_l = []
    kq_l = []
    no_l = []

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

            kt_f = 0.0
            kq_f = 0.0
            eff = 0.0

        else:

            kt_f = kt
            kq_f = kq

            eff = (
                (j / (2 * np.pi))
                * (kt_f / kq_f)
            )

            if eff > 0.85:
                eff = 0.0

        kt_l.append(kt_f)
        kq_l.append(kq_f)
        no_l.append(eff)

    return pd.DataFrame(
        {
            "J": j_vals,
            "KT": kt_l,
            "KQ": kq_l,
            "nO": no_l
        }
    )

# ==============================================================================
# SIDEBAR
# ==============================================================================

if df_kt is not None:

    with st.sidebar:

        st.header("⚙️ Configuración General")

        st.markdown("---")

        st.subheader("🌎 Constantes")

        p_atm_auto = st.number_input(
            "Presión Atmosférica (Pa)",
            value=101325.0
        )

        p_vap_auto = st.number_input(
            "Presión Vapor (Pa)",
            value=1704.0
        )

        rho_auto = st.number_input(
            "Densidad del Agua (kg/m³)",
            value=1026.021
        )

        g_auto = st.number_input(
            "Gravedad (m/s²)",
            value=9.80665
        )

        st.markdown("---")

        st.subheader("🚢 Geometría del Buque")

        eslora = st.number_input(
            "Lpp (m)",
            value=320.0,
            help="""
            Remolcador: 20-50 m

            OSV: 60-100 m

            Tanker: 250-330 m

            Container: 250-400 m
            """
        )

        lwl = st.number_input(
            "LWL (m)",
            value=325.5
        )

        manga = st.number_input(
            "Manga B (m)",
            value=58.0
        )

        puntal = st.number_input(
            "Puntal D (m)",
            value=30.0
        )

        calado = st.number_input(
            "Calado T (m)",
            value=20.8
        )

        velocidad = st.number_input(
            "Velocidad (kn)",
            value=15.5
        )

        st.markdown("---")

        st.subheader("🌀 Hidrodinámica")

        estela = st.number_input(
            "Fracción de Estela (w)",
            value=0.351
        )

        t_fraction = st.slider(
            "Fracción de Deducción (t)",
            0.05,
            0.35,
            0.18
        )

        eta_r = st.number_input(
            "ηR",
            value=1.015
        )

        inmersion_eje_m = st.number_input(
            "Inmersión del Eje (m)",
            value=14.1
        )

        st.markdown("---")

        st.subheader("⚙️ Hélice")

        z_val = st.slider(
            "Número de Palas",
            3,
            7,
            4
        )

        diam_prop_m = st.number_input(
            "Diámetro Hélice D (m)",
            value=9.86
        )

        pd_val = st.slider(
            "P/D",
            0.5,
            1.4,
            0.721
        )

        ae_val = st.slider(
            "Ae/A0",
            0.3,
            1.0,
            0.431
        )

        margen_servicio = st.slider(
            "Margen de Servicio (%)",
            0.0,
            30.0,
            15.0
        )

        st.markdown("---")

        st.subheader("🔩 Sistema Mecánico")

        potencia_kw = st.number_input(
            "Potencia MCR (kW)",
            value=22000.0
        )

        rpm_motor = st.number_input(
            "RPM Motor Principal",
            value=75.0
        )

        diametro_eje_mm = st.number_input(
            "Diámetro del Eje (mm)",
            value=680.0
        )

        peso_helice_kg = st.number_input(
            "Peso de Hélice (kg)",
            value=52000.0
        )

        longitud_volado_m = st.number_input(
            "Volado del Eje (m)",
            value=3.5
        )

        dict_materiales = {

            "Bronce de Níquel-Aluminio (Cu3)":590,
            "Bronce de Manganeso (Cu1)":450,
            "Bronce de Níquel-Manganeso (Cu2)":490,
            "Bronce de Manganeso-Aluminio (Cu4)":630,
            "Acero Forjado Naval Estándar":400,
            "Acero Forjado Aleado":600,
            "Acero Inoxidable Austenítico":520

        }

        material_seleccionado = st.selectbox(
            "Material",
            list(dict_materiales.keys())
        )

        sigma_uts = dict_materiales[
            material_seleccionado
        ]

# ==============================================================================
# PROCESAMIENTO
# ==============================================================================

    res = calcular_curvas(
        pd_val,
        ae_val,
        z_val
    )

    diametro_m = diametro_eje_mm / 1000

    E_acero = 2.06e11
    densidad_acero = 7850

    r_eje = diametro_m / 2

    area_eje = math.pi * r_eje**2

    I_inercia = (
        math.pi
        * diametro_m**4
    ) / 64

    peso_lineal_eje = (
        area_eje
        * densidad_acero
    )

    peso_helice_n = (
        peso_helice_kg
        * g_auto
    )

    delta_helice = (
        peso_helice_n
        * longitud_volado_m**3
    ) / (
        3
        * E_acero
        * I_inercia
    )

    peso_eje_n = (
        peso_lineal_eje
        * longitud_volado_m
        * g_auto
    )

    delta_eje = (
        peso_eje_n
        * longitud_volado_m**3
    ) / (
        8
        * E_acero
        * I_inercia
    )

    f_natural_hz = 1 / (
        2
        * math.pi
        * math.sqrt(
            delta_helice + delta_eje
        )
    )

    rpm_critica_lateral = (
        f_natural_hz * 60
    )

    margen_inf = (
        rpm_critica_lateral * 0.80
    )

    margen_sup = (
        rpm_critica_lateral * 1.20
    )

    v_ms = (
        velocidad
        * 0.5144
    ) * (
        1 - estela
    )

    nu = 1.188e-6

    reynolds = (
        v_ms
        * diam_prop_m
    ) / nu

    sigma_n = (
        p_atm_auto
        + rho_auto * g_auto * inmersion_eje_m
        - p_vap_auto
    ) / (
        0.5
        * rho_auto
        * v_ms**2
    )

# ==============================================================================
# VALIDACIONES
# ==============================================================================

    advertencias = []

    if velocidad > 35:
        advertencias.append(
            "Velocidad elevada para buques mercantes."
        )

    if calado > puntal:
        advertencias.append(
            "Calado mayor que el puntal."
        )

    if ae_val < 0.35:
        advertencias.append(
            "Ae/A0 bajo. Posible cavitación."
        )
        # ==============================================================================
# INDICE GLOBAL
# ==============================================================================

omega = (2 * math.pi * rpm_motor) / 60

torque_nominal = (
    potencia_kw * 1000
) / omega

torque_dinamico_alternante = (
    torque_nominal * 0.15
)

wt_modulo_torsional = (
    math.pi * diametro_m**3
) / 16

esfuerzo_real_mpa = (
    torque_dinamico_alternante /
    wt_modulo_torsional
) / 1e6

tau_admisible_mpa = (
    0.35 * (sigma_uts / 3)
)

score = 0

if esfuerzo_real_mpa <= tau_admisible_mpa:
    score += 35

if sigma_n >= 0.20:
    score += 35

if rpm_motor < margen_inf or rpm_motor > margen_sup:
    score += 30

# ==============================================================================
# TABS
# ==============================================================================

tab_dash, tab1, tab_res, tab2, tab3, tab4, tab_cav, tab_guide = st.tabs([

    "🏠 Dashboard",
    "📈 Hidrodinámica",
    "📋 Resultados",
    "💥 Torsional",
    "📊 Lateral",
    "🗺️ Campbell",
    "🔍 Cavitación",
    "📚 Guía"

])

# ==============================================================================
# DASHBOARD
# ==============================================================================

with tab_dash:

    st.subheader("📊 Dashboard Ejecutivo")

    c1,c2,c3,c4 = st.columns(4)

    c1.metric(
        "Velocidad",
        f"{velocidad:.1f} kn"
    )

    c2.metric(
        "Diámetro Hélice",
        f"{diam_prop_m:.2f} m"
    )

    c3.metric(
        "Palas",
        z_val
    )

    c4.metric(
        "Potencia",
        f"{potencia_kw/1000:.1f} MW"
    )

    st.markdown("---")

    st.subheader(
        "📋 Índice Global de Diseño"
    )

    st.progress(score/100)

    st.metric(
        "Cumplimiento",
        f"{score:.0f}%"
    )

    if score >= 90:

        st.success(
            "🟢 Diseño altamente recomendable"
        )

    elif score >= 70:

        st.warning(
            "🟡 Diseño aceptable"
        )

    else:

        st.error(
            "🔴 Diseño requiere revisión"
        )

    st.markdown("---")

    if len(advertencias) > 0:

        st.warning(
            "⚠️ Se detectaron observaciones"
        )

        for aviso in advertencias:
            st.write("•", aviso)

    else:

        st.success(
            "✅ Todos los parámetros son consistentes"
        )

# ==============================================================================
# HIDRODINAMICA
# ==============================================================================

with tab1:

    max_eff = res["nO"].max()

    j_opt = (
        res.loc[
            res["nO"].idxmax(),
            "J"
        ]
    )

    k1,k2,k3 = st.columns(3)

    k1.metric(
        "ηO Máxima",
        f"{max_eff*100:.2f}%"
    )

    k2.metric(
        "J Óptimo",
        f"{j_opt:.3f}"
    )

    k3.metric(
        "Material",
        material_seleccionado
    )

    fig, ax = plt.subplots(
        figsize=(10,5)
    )

    ax.plot(
        res["J"],
        res["KT"],
        linewidth=2.5,
        label="KT"
    )

    ax.plot(
        res["J"],
        res["KQ"]*10,
        linewidth=2.5,
        label="10*KQ"
    )

    ax.plot(
        res["J"],
        res["nO"],
        linewidth=3,
        linestyle="--",
        label="ηO"
    )

    ax.axvline(
        x=j_opt,
        linestyle=":"
    )

    ax.grid(True)

    ax.legend()

    ax.set_xlabel("J")

    ax.set_ylabel("Coeficientes")

    ax.set_title(
        "Curvas Wageningen Serie B"
    )

    st.pyplot(fig)

# ==============================================================================
# RESULTADOS
# ==============================================================================

with tab_res:

    st.subheader(
        "📋 Resultados Numéricos"
    )

    tabla = res.copy()

    tabla["ηO (%)"] = (
        tabla["nO"] * 100
    )

    st.dataframe(
        tabla.round(4),
        use_container_width=True
    )

# ==============================================================================
# TORSIONAL
# ==============================================================================

with tab2:

    st.subheader(
        "💥 Vibración Torsional"
    )

    c1,c2 = st.columns(2)

    c1.metric(
        "Torque",
        f"{torque_nominal/1000:.2f} kN·m"
    )

    c1.metric(
        "Esfuerzo Real",
        f"{esfuerzo_real_mpa:.2f} MPa"
    )

    c1.metric(
        "Admisible",
        f"{tau_admisible_mpa:.2f} MPa"
    )

    if esfuerzo_real_mpa <= tau_admisible_mpa:

        c1.success(
            "✅ Cumple"
        )

    else:

        c1.error(
            "❌ No cumple"
        )

    fig, ax = plt.subplots(
        figsize=(6,3)
    )

    ax.barh(
        ["Real","Admisible"],
        [
            esfuerzo_real_mpa,
            tau_admisible_mpa
        ]
    )

    c2.pyplot(fig)

# ==============================================================================
# LATERAL
# ==============================================================================

with tab3:

    st.subheader(
        "📊 Vibración Lateral"
    )

    c1,c2 = st.columns(2)

    c1.metric(
        "Frecuencia",
        f"{f_natural_hz:.2f} Hz"
    )

    c1.metric(
        "RPM Crítica",
        f"{rpm_critica_lateral:.1f}"
    )

    if rpm_motor < margen_inf or rpm_motor > margen_sup:

        c1.success(
            "✅ Seguro"
        )

    else:

        c1.error(
            "❌ Zona crítica"
        )

    fig, ax = plt.subplots(
        figsize=(7,3)
    )

    ax.axvline(
        rpm_critica_lateral,
        color="red"
    )

    ax.axvspan(
        margen_inf,
        margen_sup,
        alpha=0.2
    )

    ax.scatter(
        rpm_motor,
        1,
        s=120
    )

    st.pyplot(fig)

# ==============================================================================
# CAMPBELL
# ==============================================================================

with tab4:

    st.subheader(
        "🗺️ Diagrama de Campbell"
    )

    rpm_x = np.linspace(
        0,
        rpm_motor*1.6,
        400
    )

    fig, ax = plt.subplots(
        figsize=(10,5)
    )

    ax.axhline(
        y=f_natural_hz,
        linestyle="--",
        label="Natural"
    )

    ax.plot(
        rpm_x,
        rpm_x/60,
        label="1P"
    )

    ax.plot(
        rpm_x,
        z_val*rpm_x/60,
        label=f"{z_val}P"
    )

    ax.grid(True)

    ax.legend()

    st.pyplot(fig)

# ==============================================================================
# CAVITACION
# ==============================================================================

with tab_cav:

    st.subheader(
        "🔍 Cavitación y Reynolds"
    )

    c1,c2 = st.columns(2)

    c1.metric(
        "Reynolds",
        f"{reynolds:.2e}"
    )

    c1.metric(
        "Sigma",
        f"{sigma_n:.3f}"
    )

    if sigma_n < 0.20:

        c2.error(
            "⚠️ Riesgo de cavitación"
        )

    else:

        c2.success(
            "✅ Riesgo bajo"
        )

# ==============================================================================
# GUIA
# ==============================================================================

with tab_guide:

    st.subheader(
        "📚 Guía de Referencia Naval"
    )

    st.markdown("""

### Rangos típicos

| Tipo | Lpp |
|-------|-------|
| Remolcador | 20-50 m |
| OSV | 60-100 m |
| PSV | 70-110 m |
| Bulk Carrier | 180-250 m |
| Tanker | 250-330 m |
| Container | 250-400 m |

---

### Ae/A0

| Aplicación | Rango |
|------------|--------|
| Baja carga | 0.40-0.55 |
| Mercante | 0.50-0.70 |
| Alta carga | 0.70-0.95 |

---

### Número de palas

- 3 → máxima eficiencia
- 4 → estándar comercial
- 5 → menor vibración
- 6-7 → aplicaciones especiales

---

### Reynolds

- >10⁷ flujo plenamente turbulento.
- Valores altos son normales en hélices oceánicas.

---

### Cavitación

- σ < 0.20 → alto riesgo.
- σ > 0.20 → diseño aceptable.
""")

else:

    st.error(
        "No se encontró el archivo Tabla 1.xlsx"
    )

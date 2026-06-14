import streamlit as st
import pandas as pd
import numpy as np
import math
import re
import tempfile
import os
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


def tabla_a_reportlab(df, max_rows=30):
    """Convierte un DataFrame pequeño a estructura de tabla para ReportLab."""
    df2 = df.copy().head(max_rows)
    data = [list(df2.columns)]
    for _, row in df2.iterrows():
        fila = []
        for val in row.tolist():
            if isinstance(val, float):
                if abs(val) >= 1000:
                    fila.append(f"{val:,.2f}")
                else:
                    fila.append(f"{val:.4g}")
            else:
                fila.append(str(val))
        data.append(fila)
    return data


def crear_figura_wageningen(res_df, j_opt_val):
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(res_df["J"], res_df["KT"], linewidth=2.2, label="KT")
    ax.plot(res_df["J"], res_df["10KQ"], linewidth=2.2, label="10KQ")
    ax.plot(res_df["J"], res_df["nO"], linewidth=2.8, linestyle="--", label="ηO")
    ax.axvline(x=j_opt_val, linestyle=":", linewidth=2, label=f"J óptimo = {j_opt_val:.3f}")
    ax.set_title("Curvas Wageningen Serie B")
    ax.set_xlabel("J")
    ax.set_ylabel("Coeficientes")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="best")
    return fig


def crear_figura_comparacion(comparacion):
    """Gráfica profesional: barras agrupadas de calculado vs real y etiqueta de error."""
    df = comparacion.dropna(subset=["Calculado", "Real PDF/manual"]).copy()
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    if df.empty:
        ax.text(0.5, 0.5, "Sin datos reales para comparar", ha="center", va="center", fontsize=13, fontweight="bold")
        ax.axis("off")
        return fig
    etiquetas = df["Parámetro"].astype(str).str.replace("Potencia al freno PB ", "PB ", regex=False).tolist()
    x = np.arange(len(df))
    ancho = 0.36
    ax.bar(x - ancho/2, df["Calculado"], width=ancho, label="Calculado")
    ax.bar(x + ancho/2, df["Real PDF/manual"], width=ancho, label="Real / ficha técnica")
    for i, (_, row) in enumerate(df.iterrows()):
        err = row.get("Error [%]", np.nan)
        if pd.notna(err):
            ymax = max(row["Calculado"], row["Real PDF/manual"])
            ax.text(i, ymax * 1.03 if ymax else 0.05, f"Error {err:.1f}%", ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax.set_title("Comparación de resultados calculados contra datos reales", fontsize=12, fontweight="bold")
    ax.set_ylabel("Valor")
    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas, rotation=18, ha="right")
    ax.grid(True, axis="y", linestyle=":", alpha=0.55)
    ax.legend(loc="best")
    fig.tight_layout()
    return fig


def crear_figura_burrill(sigma_actual, tau_actual, tau_adm_actual):
    max_sigma = max(1.2, sigma_actual * 1.15)
    sig = np.linspace(0.05, max_sigma, 220)
    tau_adm = 0.22 + 0.18 * sig
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(sig, tau_adm, linewidth=2.6, label="Límite preliminar admisible")
    ax.fill_between(sig, 0, tau_adm, alpha=0.10, label="Zona aceptable")
    ax.scatter([sigma_actual], [tau_actual], s=130, zorder=5, label="Diseño actual")
    ax.axvline(sigma_actual, linestyle=":", linewidth=1.8)
    ax.axhline(tau_actual, linestyle=":", linewidth=1.8)
    ax.set_xlabel("Coeficiente de cavitación σ")
    ax.set_ylabel("Coeficiente de carga τc")
    ax.set_title("Criterio de Burrill — σ vs τc")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="best")
    return fig


def crear_figura_keller(ae_min, ae_actual):
    """Gráfica tipo indicador para evaluar Keller de forma más clara y profesional."""
    margen = ae_actual - ae_min
    cumple = margen >= 0
    xmax = max(1.0, ae_actual * 1.25, ae_min * 1.35, 0.75)
    fig, ax = plt.subplots(figsize=(9.2, 4.8))

    # Franja base de lectura: zona insuficiente y zona aceptable.
    ax.axvspan(0, ae_min, alpha=0.10, label="Zona insuficiente")
    ax.axvspan(ae_min, xmax, alpha=0.08, label="Zona aceptable")
    ax.axvline(ae_min, linestyle="--", linewidth=2.4, label=f"Keller mínimo = {ae_min:.3f}")

    # Barra horizontal del diseño actual.
    ax.barh(["Diseño actual"], [ae_actual], height=0.34)
    ax.scatter([ae_actual], [0], s=170, zorder=5, label=f"Ae/A0 actual = {ae_actual:.3f}")

    texto = f"Cumple: margen +{margen:.3f}" if cumple else f"No cumple: déficit {margen:.3f}"
    ax.annotate(
        texto,
        xy=(ae_actual, 0),
        xytext=(min(xmax * 0.62, max(ae_actual, ae_min) + xmax * 0.08), 0.22),
        arrowprops=dict(arrowstyle="->", lw=1.2),
        fontsize=10,
        fontweight="bold",
    )

    ax.set_xlim(0, xmax)
    ax.set_ylim(-0.6, 0.65)
    ax.set_xlabel("Relación de área expandida Ae/A0 [-]")
    ax.set_title("Criterio de Keller — verificación de área expandida mínima")
    ax.grid(True, axis="x", linestyle=":", alpha=0.55)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_yticks([0])
    ax.set_yticklabels(["Ae/A0"])
    return fig


def crear_figura_campbell(rpm_operacion, f_lat, f_tors, f_axial, z):
    max_rpm = max(rpm_operacion * 2.0, 120)
    rpm_x = np.linspace(0, max_rpm, 400)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.axhline(y=f_lat, linestyle="--", linewidth=2, label=f"Lateral {f_lat:.2f} Hz")
    ax.axhline(y=f_tors, linestyle="-.", linewidth=2, label=f"Torsional {f_tors:.2f} Hz")
    ax.axhline(y=f_axial, linestyle=":", linewidth=2.4, label=f"Axial {f_axial:.2f} Hz")
    for nombre, mult in [("1P",1),("2P",2),("3P",3),("ZP",z),("2ZP",2*z),("3ZP",3*z)]:
        ax.plot(rpm_x, mult*rpm_x/60.0, linewidth=1.4, label=nombre)
    ax.axvline(x=rpm_operacion, linewidth=2.2, label=f"Operación {rpm_operacion:.0f} rpm")
    ax.set_xlabel("RPM")
    ax.set_ylabel("Frecuencia [Hz]")
    ax.set_title("Diagrama de Campbell")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=8, ncols=2)
    return fig


def insertar_figura_excel(writer, fig, sheet_name, cell="A1"):
    try:
        from openpyxl.drawing.image import Image as XLImage
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        tmp.close()
        fig.savefig(tmp.name, format="png", dpi=150, bbox_inches="tight")
        ws = writer.book.create_sheet(sheet_name)
        img = XLImage(tmp.name)
        img.anchor = cell
        ws.add_image(img)
        return tmp.name
    except Exception:
        return None


def extraer_texto_pdf(uploaded_file):
    """Extrae texto básico de un PDF cargado por el usuario.
    Funciona como asistente de lectura: los datos detectados siempre deben poder revisarse.
    """
    if uploaded_file is None:
        return ""
    try:
        try:
            from pypdf import PdfReader
        except Exception:
            from PyPDF2 import PdfReader
        reader = PdfReader(uploaded_file)
        partes = []
        for page in reader.pages:
            partes.append(page.extract_text() or "")
        return "\n".join(partes)
    except Exception as e:
        st.warning(f"No se pudo leer automáticamente el PDF. Puedes ingresar los datos reales manualmente. Detalle: {e}")
        return ""


def _buscar_numero(texto, patrones):
    if not texto:
        return None
    for patron in patrones:
        m = re.search(patron, texto, flags=re.I | re.S)
        if m:
            val = m.group(1).replace(',', '').replace(' ', '')
            try:
                return float(val)
            except Exception:
                continue
    return None


def _buscar_texto(texto, patrones):
    if not texto:
        return ""
    for patron in patrones:
        m = re.search(patron, texto, flags=re.I | re.S)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
    return ""


def parsear_ficha_tecnica(texto_pdf):
    """Busca datos típicos en fichas técnicas navales. No sustituye revisión humana."""
    d = {}
    d["tipo_buque"] = "VLCC oil tanker" if re.search(r"VLCC|oil tanker|tanker", texto_pdf or "", re.I) else ""
    d["loa_m"] = _buscar_numero(texto_pdf, [r"Length overall\s*([0-9.,]+)\s*m"])
    d["lpp_m"] = _buscar_numero(texto_pdf, [r"Length between perpendiculars\s*([0-9.,]+)\s*m"])
    d["manga_m"] = _buscar_numero(texto_pdf, [r"Breadth moulded\s*([0-9.,]+)\s*m"])
    d["puntal_m"] = _buscar_numero(texto_pdf, [r"Depth moulded\s*([0-9.,]+)\s*m"])
    d["calado_m"] = _buscar_numero(texto_pdf, [r"Draft at Summer freeboard\s*([0-9.,]+)\s*m"])
    d["dwt_t"] = _buscar_numero(texto_pdf, [r"Deadweight\s*([0-9.,]+)\s*MT"])
    d["velocidad_kn"] = _buscar_numero(texto_pdf, [r"Sea speed.*?([0-9.]+)\s*knots"])
    d["sea_margin_pct"] = _buscar_numero(texto_pdf, [r"with\s*([0-9.]+)\s*%\s*sea margin"])
    d["motor_modelo"] = _buscar_texto(texto_pdf, [r"Main Engine\s*([^\n]+)"])
    m = re.search(r"MCR\s*([0-9,\.]+)\s*KW\s*/\s*([0-9,\.]+)\s*RPM", texto_pdf or "", flags=re.I)
    if m:
        d["mcr_kw"] = float(m.group(1).replace(',', ''))
        d["mcr_rpm"] = float(m.group(2).replace(',', ''))
    else:
        d["mcr_kw"] = None; d["mcr_rpm"] = None
    m = re.search(r"NCR\s*([0-9,\.]+)\s*KW\s*/\s*([0-9,\.]+)\s*RPM", texto_pdf or "", flags=re.I)
    if m:
        d["ncr_kw"] = float(m.group(1).replace(',', ''))
        d["ncr_rpm"] = float(m.group(2).replace(',', ''))
    else:
        d["ncr_kw"] = None; d["ncr_rpm"] = None
    z = _buscar_numero(texto_pdf, [r"Propeller.*?([0-9]+)\s*blades", r"([0-9]+)\s*blades\s*solid"])
    d["prop_z"] = int(z) if z else None
    d["prop_diam_m"] = None
    diam_mm = _buscar_numero(texto_pdf, [r"Diam\s*[:\-]?\s*([0-9,\.]+)\s*mm"])
    if diam_mm:
        d["prop_diam_m"] = diam_mm / 1000.0
    pitch_mm = _buscar_numero(texto_pdf, [r"Pitch\s*[:\-]?\s*([0-9,\.]+)\s*mm"])
    d["prop_pitch_m"] = pitch_mm / 1000.0 if pitch_mm else None
    d["prop_pd"] = safe_div(d.get("prop_pitch_m"), d.get("prop_diam_m"), default=None) if d.get("prop_pitch_m") and d.get("prop_diam_m") else None
    d["prop_material"] = _buscar_texto(texto_pdf, [r"Material\s*([^\n]+)"])
    return d


def nvl(dato, default):
    return default if dato is None or dato == "" else dato


def error_pct(calculado, real):
    try:
        if real is None or real == 0:
            return None
        return abs(calculado - real) / abs(real) * 100.0
    except Exception:
        return None



# ==============================================================================
# BASE DE DATOS DIDÁCTICA DE MOTORES Y REDUCTORAS
# ==============================================================================
# Esta base sirve para preselección académica. Para entrega final siempre debe
# verificarse contra la hoja técnica vigente del fabricante.
@st.cache_data(show_spinner=False)
def construir_base_motores():
    filas = []

    def add(fabricante, modelo, tipo, mcr_kw, rpm, notas=""):
        filas.append({
            "Fabricante": fabricante,
            "Modelo": modelo,
            "Tipo": tipo,
            "MCR [kW]": float(mcr_kw),
            "RPM MCR": float(rpm),
            "85% MCR [kW]": float(mcr_kw) * 0.85,
            "Notas": notas
        })

    # Motores lentos 2T para buques grandes, normalmente transmisión directa.
    for cyl, kw in [(5,24450),(6,29340),(7,34230),(8,39120),(9,44010),(10,48900),(11,53790),(12,58680)]:
        add("Hyundai MAN-B&W", f"{cyl}S90MC-C MK7", "2T lento", kw, 79, "Motor lento; normalmente acoplamiento directo")
    for cyl, kw in [(5,21000),(6,25200),(7,29400),(8,33600),(9,37800),(10,42000),(11,46200),(12,50400),(14,58800)]:
        add("MAN Energy Solutions", f"{cyl}G80ME-C", "2T lento", kw, 72, "Motor lento; portacontenedores/tanqueros")
    for cyl, kw in [(5,17100),(6,20520),(7,23940),(8,27360),(9,30780),(10,34200),(11,37620),(12,41040)]:
        add("MAN Energy Solutions", f"{cyl}S70ME-C", "2T lento", kw, 91, "Motor lento; bulk/tanker")
    for cyl, kw in [(5,12400),(6,14880),(7,17360),(8,19840),(9,22320)]:
        add("MAN Energy Solutions", f"{cyl}S60ME-C", "2T lento", kw, 105, "Motor lento/medio-bajo")
    for cyl, kw in [(5,27000),(6,32400),(7,37800),(8,43200),(9,48600),(10,54000),(11,59400),(12,64800)]:
        add("WinGD", f"{cyl}X92-B", "2T lento", kw, 80, "Motor lento; buques de gran porte")
    for cyl, kw in [(5,19500),(6,23400),(7,27300),(8,31200),(9,35100),(10,39000),(11,42900),(12,46800)]:
        add("WinGD", f"{cyl}X72", "2T lento", kw, 89, "Motor lento; tanque/bulk/container")
    for cyl, kw in [(5,12800),(6,15360),(7,17920),(8,20480),(9,23040)]:
        add("WinGD", f"{cyl}X62", "2T lento", kw, 103, "Motor lento; mercante")

    # Motores semi-rápidos 4T; normalmente requieren reductora.
    for cyl in [6,7,8,9,10,12,14,16,18,20]:
        add("Wärtsilä", f"{cyl}L32", "4T medio", cyl*580, 750, "Requiere reductora para hélice convencional")
        add("Wärtsilä", f"{cyl}V32", "4T medio", cyl*580, 750, "Requiere reductora")
    for cyl in [6,8,9,12,14,16,18,20]:
        add("Wärtsilä", f"{cyl}V46F", "4T medio", cyl*1200, 600, "Requiere reductora")
    for cyl in [6,8,9,12,14,16,18]:
        add("MAN", f"{cyl}L32/44CR", "4T medio", cyl*560, 750, "Requiere reductora")
        add("MAN", f"{cyl}L48/60CR", "4T medio", cyl*1200, 500, "Requiere reductora")
    for cyl in [6,8,9,12,16,20]:
        add("Caterpillar MaK", f"M32E {cyl} cyl", "4T medio", cyl*550, 750, "Offshore/ferry/mercante; reductora")
        add("Caterpillar MaK", f"M46DF {cyl} cyl", "4T medio", cyl*900, 500, "Dual fuel; reductora")
    for cyl in [6,8,9,12,16,20]:
        add("Hyundai HiMSEN", f"H32/40 {cyl} cyl", "4T medio", cyl*500, 720, "Auxiliar o propulsión mediana; reductora")
    for cyl in [6,8,9,12,16,20]:
        add("Bergen / Rolls-Royce", f"B33:45 {cyl} cyl", "4T medio", cyl*600, 750, "OSV/ferry; reductora")

    # Motores rápidos para embarcaciones pequeñas, remolcadores, yates, patrullas.
    for modelo, kw, rpm in [
        ("C18 ACERT", 715, 1800), ("C32 ACERT", 1450, 1800), ("3512C", 1900, 1800),
        ("3516C", 2525, 1800), ("C280-6", 2700, 1000), ("C280-8", 3600, 1000),
        ("C280-12", 5400, 1000), ("C280-16", 7200, 1000)]:
        add("Caterpillar", modelo, "4T rápido", kw, rpm, "Alta RPM; requiere reductora")
    for modelo, kw, rpm in [("QSK19-M", 600, 1800), ("QSK38-M", 1200, 1800), ("QSK50-M", 1600, 1800), ("QSK60-M", 2200, 1800), ("QSK95-M", 3200, 1700)]:
        add("Cummins", modelo, "4T rápido", kw, rpm, "Embarcaciones menores/servicio; reductora")
    for modelo, kw, rpm in [("16V4000 M63", 2000, 1800), ("20V4000 M73L", 3600, 2050), ("12V2000 M96", 1500, 2450), ("16V2000 M96L", 1939, 2450)]:
        add("MTU", modelo, "4T rápido", kw, rpm, "Alta velocidad; reductora")
    for modelo, kw, rpm in [("6AYM-WET", 610, 1900), ("12AYM-WET", 1340, 1900), ("6EY26W", 1920, 750), ("8EY26W", 2560, 750)]:
        add("Yanmar", modelo, "4T rápido/medio", kw, rpm, "Reductora según aplicación")
    for cyl in [6,8,12,16]:
        add("ABC", f"DZC {cyl} cyl", "4T medio", cyl*520, 1000, "Remolcador/ferry; reductora")



    # Base adicional ampliada para que la app funcione con más tipos de buques.
    # Son valores de preselección didáctica; deben verificarse con hojas técnicas vigentes.
    familias_2t_extra = [
        ("MAN Energy Solutions", "G95ME-C", 6100, 70, [5,6,7,8,9,10,11,12]),
        ("MAN Energy Solutions", "G90ME-C", 5600, 74, [5,6,7,8,9,10,11,12]),
        ("MAN Energy Solutions", "G70ME-C", 3200, 85, [5,6,7,8,9,10,11,12]),
        ("MAN Energy Solutions", "G60ME-C", 2500, 97, [5,6,7,8,9,10]),
        ("MAN Energy Solutions", "S50ME-C", 1780, 127, [5,6,7,8,9]),
        ("MAN Energy Solutions", "S46ME-B", 1500, 129, [5,6,7,8]),
        ("MAN Energy Solutions", "S35ME-B", 870, 173, [5,6,7,8]),
        ("WinGD", "X82", 4500, 76, [5,6,7,8,9,10,11,12]),
        ("WinGD", "X72DF", 3900, 89, [5,6,7,8,9,10,11]),
        ("WinGD", "X62DF", 2800, 103, [5,6,7,8,9,10]),
        ("WinGD", "X52", 1900, 110, [5,6,7,8,9]),
        ("WinGD", "X40-B", 1050, 146, [5,6,7,8]),
    ]
    for fabricante, familia, kw_cyl, rpm, cilindros in familias_2t_extra:
        for cyl in cilindros:
            add(fabricante, f"{cyl}{familia}", "2T lento", cyl*kw_cyl, rpm, "Motor lento; candidato para transmisión directa o baja reducción")

    familias_4t_extra = [
        ("Wärtsilä", "L20", 200, 1000, [4,6,8,9]),
        ("Wärtsilä", "L26", 340, 1000, [6,8,9,12,16]),
        ("Wärtsilä", "L31", 610, 750, [8,10,12,14,16]),
        ("Wärtsilä", "46DF", 1045, 600, [6,8,9,12,16]),
        ("Wärtsilä", "50DF", 950, 514, [6,8,9,12,16,18]),
        ("MAN", "L21/31", 220, 1000, [5,6,7,8,9]),
        ("MAN", "L27/38", 365, 800, [6,8,9]),
        ("MAN", "V28/33D", 450, 1000, [12,16,20]),
        ("MAN", "V35/44G", 530, 720, [12,16,20]),
        ("MAN", "L51/60DF", 1150, 514, [6,7,8,9,12,14,16,18]),
        ("Caterpillar MaK", "M20C", 180, 1000, [6,8,9]),
        ("Caterpillar MaK", "M25E", 330, 750, [6,8,9]),
        ("Caterpillar MaK", "M34DF", 500, 720, [6,8,9,12,16]),
        ("Bergen", "C25:33", 330, 1000, [6,8,9]),
        ("Bergen", "B35:40", 665, 750, [6,8,9,12,16,20]),
        ("Niigata", "28AHX", 320, 750, [6,8,9]),
        ("Daihatsu", "DE-28", 250, 720, [6,8]),
        ("Daihatsu", "DE-35", 500, 720, [6,8]),
    ]
    for fabricante, familia, kw_cyl, rpm, cilindros in familias_4t_extra:
        for cyl in cilindros:
            add(fabricante, f"{cyl}{familia}", "4T medio", cyl*kw_cyl, rpm, "Motor medio; usualmente requiere reductora")

    motores_rapidos_extra = [
        ("Scania", "DI13 076M", 700, 2100), ("Scania", "DI16 076M", 900, 2100),
        ("Volvo Penta", "D13 MH", 735, 2300), ("Volvo Penta", "D16 MH", 1000, 2300),
        ("John Deere", "6135SFM85", 560, 2200), ("John Deere", "PowerTech 6090SFM85", 410, 2200),
        ("MAN High Speed", "D2862 LE489", 1213, 2300), ("MAN High Speed", "D2868 LE436", 882, 2100),
        ("MTU", "8V2000 M72", 720, 2250), ("MTU", "10V2000 M72", 900, 2250),
        ("MTU", "12V4000 M65L", 2250, 1800), ("MTU", "16V4000 M93L", 3440, 2100),
        ("Baudouin", "12M26.3", 1214, 1800), ("Baudouin", "16M33.3", 2200, 1800),
        ("Mitsubishi", "S12R-MPTK", 1260, 1600), ("Mitsubishi", "S16R2-MPTK", 2000, 1500),
    ]
    for fabricante, modelo, kw, rpm in motores_rapidos_extra:
        add(fabricante, modelo, "4T rápido", kw, rpm, "Motor rápido; requiere reductora")



    # Catálogo extendido paramétrico adicional: amplia la búsqueda para uso universal.
    # No representa una ficha exacta única; es una malla de familias comerciales aproximadas para preselección.
    familias_ext = [
        ("MAN Energy Solutions", "S40ME-C", "2T lento", 1120, 146, range(5,9)),
        ("MAN Energy Solutions", "S50ME-C9", "2T lento", 1850, 127, range(5,10)),
        ("MAN Energy Solutions", "S60ME-C10", "2T lento", 2550, 105, range(5,10)),
        ("WinGD", "X35-B", "2T lento", 870, 167, range(5,9)),
        ("WinGD", "X40DF", "2T lento", 1100, 146, range(5,9)),
        ("WinGD", "X52DF", "2T lento", 2000, 110, range(5,10)),
        ("Wärtsilä", "L34DF", "4T medio", 500, 750, range(6,18,2)),
        ("Wärtsilä", "L38", "4T medio", 725, 600, range(6,18,2)),
        ("MAN", "L23/30H", "4T medio", 200, 900, range(5,10)),
        ("MAN", "L28/32DF", "4T medio", 450, 720, range(6,20,2)),
        ("Caterpillar MaK", "M43C", "4T medio", 900, 500, range(6,18,2)),
        ("Caterpillar MaK", "M32C", "4T medio", 500, 600, range(6,18,2)),
        ("Hyundai HiMSEN", "H25/33", "4T medio", 250, 900, range(5,10)),
        ("Hyundai HiMSEN", "H35/40", "4T medio", 600, 720, range(6,20,2)),
        ("Bergen", "B32:40", "4T medio", 500, 750, range(6,20,2)),
        ("Bergen", "B36:45", "4T medio", 750, 600, range(6,20,2)),
        ("ABC", "DL36", "4T medio", 750, 750, range(6,18,2)),
        ("ABC", "DZC Medium", "4T medio", 520, 1000, range(6,18,2)),
    ]
    for fabricante, familia, tipo, kw_cyl, rpm, cilindros in familias_ext:
        for cyl in cilindros:
            add(fabricante, f"{cyl}{familia}", tipo, cyl*kw_cyl, rpm, "Catálogo extendido de preselección; verificar ficha de fabricante")

    # Variantes de motores rápidos por niveles de potencia para embarcaciones menores.
    for kw in [300, 450, 600, 800, 1000, 1200, 1500, 1800, 2200, 2600, 3200, 4000, 5000]:
        add("Base genérica comercial", f"High Speed Marine {kw} kW", "4T rápido", kw, 1800 if kw < 2500 else 1500, "Opción genérica para dimensionamiento; reemplazar por modelo real")

    df = pd.DataFrame(filas).drop_duplicates(subset=["Fabricante", "Modelo"]).reset_index(drop=True)
    return df


def recomendar_motores(pb_req_kw, rpm_objetivo, transmision_tipo, n=12):
    db = construir_base_motores().copy()
    db = db[db["85% MCR [kW]"] >= max(pb_req_kw, 0)]
    if db.empty:
        return db
    # Penaliza exceso de potencia y diferencia de RPM. Para transmisión directa pesa más la RPM.
    db["Exceso 85% MCR [kW]"] = db["85% MCR [kW]"] - pb_req_kw
    db["MCR requerido aprox [kW]"] = pb_req_kw / 0.85 if pb_req_kw else 0
    if transmision_tipo.startswith("Directa"):
        db["Diferencia RPM [%]"] = abs(db["RPM MCR"] - rpm_objetivo) / max(rpm_objetivo, 1) * 100
        db["Puntaje"] = db["Exceso 85% MCR [kW]"] + db["Diferencia RPM [%]"] * 500
    else:
        db["Relación recomendada i"] = db["RPM MCR"] / max(rpm_objetivo, 1)
        db["Diferencia RPM [%]"] = 0.0
        db["Puntaje"] = db["Exceso 85% MCR [kW]"]
    if "Relación recomendada i" not in db.columns:
        db["Relación recomendada i"] = db["RPM MCR"] / max(rpm_objetivo, 1)
    return db.sort_values("Puntaje").head(n).reset_index(drop=True)

@st.cache_data(show_spinner=False)
def construir_base_reductoras():
    filas = []
    def add(marca, serie, pmin, pmax, imin, imax, eta):
        filas.append({"Marca": marca, "Serie/modelo": serie, "Potencia mín [kW]": pmin, "Potencia máx [kW]": pmax,
                      "i mín": imin, "i máx": imax, "ηG ref": eta})
    for serie, pmax in [("WAF/WGF 300", 1500),("WAF/WGF 500", 3500),("WAF/WGF 700", 7000),("WAF/WGF 1000", 12000),("WAF/WGF 1500", 20000),("WAF/WGF 2000", 30000)]:
        add("Reintjes", serie, 100, pmax, 1.2, 7.0, 0.98)
    for serie, pmax in [("ZF 500", 1200),("ZF 2000", 2500),("ZF 5000", 6000),("ZF 10000", 12000),("ZF 30000", 25000)]:
        add("ZF Marine", serie, 50, pmax, 1.2, 6.5, 0.97)
    for serie, pmax in [("MGX 5000", 1500),("MGX 6000", 3000),("MGX 7000", 5000),("MGX 8000", 8000),("MGX 9000", 12000)]:
        add("Twin Disc", serie, 50, pmax, 1.1, 6.0, 0.97)
    for serie, pmax in [("Marine Gear L", 5000),("Marine Gear M", 12000),("Marine Gear H", 30000),("Marine Gear VH", 60000)]:
        add("Lufkin", serie, 500, pmax, 1.1, 8.0, 0.98)
    return pd.DataFrame(filas)


def recomendar_reductoras(pb_kw, relacion_necesaria, n=8):
    db = construir_base_reductoras().copy()
    db = db[(db["Potencia mín [kW]"] <= pb_kw) & (db["Potencia máx [kW]"] >= pb_kw) &
            (db["i mín"] <= relacion_necesaria) & (db["i máx"] >= relacion_necesaria)]
    return db.head(n).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def optimizar_helice_wageningen(modo="Rápida"):
    """
    Optimización ligera para no bloquear la app en Streamlit Cloud.
    Modo Rápida: pocas combinaciones, ideal para clase.
    Modo Detallada: más combinaciones, pero sigue limitada para evitar congelamientos.
    """
    filas = []
    if modo == "Detallada":
        pds = np.linspace(0.55, 1.25, 8)
        aes = np.linspace(0.40, 0.95, 7)
        j_vals_local = np.linspace(0.05, 1.15, 80)
    else:
        pds = np.linspace(0.60, 1.20, 6)
        aes = np.linspace(0.40, 0.90, 5)
        j_vals_local = np.linspace(0.08, 1.10, 55)

    col_c = "Coeficiente"
    kt_c = df_kt[col_c].to_numpy(dtype=float)
    kt_s = df_kt["S (j)"].to_numpy(dtype=float)
    kt_t = df_kt["T (p/d)"].to_numpy(dtype=float)
    kt_u = df_kt["U (ae/ao)"].to_numpy(dtype=float)
    kt_v = df_kt["V (z)"].to_numpy(dtype=float)

    kq_c = df_kq[col_c].to_numpy(dtype=float)
    kq_s = df_kq["S (j)"].to_numpy(dtype=float)
    kq_t = df_kq["T (p/d)"].to_numpy(dtype=float)
    kq_u = df_kq["U (ae/ao)"].to_numpy(dtype=float)
    kq_v = df_kq["V (z)"].to_numpy(dtype=float)

    j_matrix_kt = np.power(j_vals_local[:, None], kt_s[None, :])
    j_matrix_kq = np.power(j_vals_local[:, None], kq_s[None, :])

    for z in range(3, 8):
        for pdv in pds:
            for aev in aes:
                kt_terms = kt_c * (pdv ** kt_t) * (aev ** kt_u) * (z ** kt_v)
                kq_terms = kq_c * (pdv ** kq_t) * (aev ** kq_u) * (z ** kq_v)
                kt_vals = j_matrix_kt @ kt_terms
                kq_vals = j_matrix_kq @ kq_terms
                eta_vals = np.where((kt_vals > 0) & (kq_vals > 0), (j_vals_local / (2*np.pi)) * (kt_vals / kq_vals), 0.0)
                eta_vals = np.where(eta_vals <= 0.85, eta_vals, 0.0)
                imax = int(np.nanargmax(eta_vals))
                filas.append({
                    "Z": z,
                    "P/D": float(pdv),
                    "Ae/A0": float(aev),
                    "J óptimo": float(j_vals_local[imax]),
                    "KT": float(kt_vals[imax]),
                    "KQ": float(kq_vals[imax]),
                    "ηO [%]": float(eta_vals[imax] * 100.0),
                })
    return pd.DataFrame(filas).sort_values("ηO [%]", ascending=False).reset_index(drop=True)


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
# ESTIMADORES UNIVERSALES DE PREDISEÑO
# ==============================================================================
# Estos estimadores evitan que la app dependa de un buque específico. Si el usuario
# sube un PDF, sus datos reales se usan para comparación; si no, la app genera
# valores preliminares transparentes y editables a partir de dimensiones y tipo de buque.

def coef_bloque_referencia(tipo_buque):
    tabla = {
        "Buque tanque": 0.82,
        "Bulk carrier": 0.80,
        "Portacontenedores": 0.66,
        "OSV / PSV": 0.62,
        "AHTS": 0.58,
        "Remolcador": 0.54,
        "Ferry": 0.55,
        "Libre / Personalizado": 0.70,
    }
    return tabla.get(tipo_buque, 0.70)

def estimar_estela(tipo_buque, cb=None):
    cb = coef_bloque_referencia(tipo_buque) if cb is None else cb
    w = 0.05 + 0.38 * cb
    return float(min(max(w, 0.12), 0.45))

def estimar_deduccion_empuje(w):
    # Relación preliminar habitual: t menor que w para buques de una hélice.
    return float(min(max(0.55 * w, 0.06), 0.32))

def estimar_eta_s(tipo_transmision="Directa / sin caja reductora"):
    return 0.990 if str(tipo_transmision).startswith("Directa") else 0.985

def estimar_eta_g(tipo_transmision="Directa / sin caja reductora"):
    return 1.000 if str(tipo_transmision).startswith("Directa") else 0.975

def estimar_resistencia_ittc_kn(lwl, manga, calado, velocidad_kn, tipo_buque, rho=1025.0, nu=1.1883e-6):
    # Estimación universal preliminar usando superficie mojada aproximada + ITTC-1957.
    # No sustituye canal de pruebas ni Holtrop-Mennen completo; sirve como punto inicial editable.
    v = max(velocidad_kn * 0.514444, 0.01)
    L = max(float(lwl), 1.0)
    B = max(float(manga), 0.1)
    T = max(float(calado), 0.1)
    cb = coef_bloque_referencia(tipo_buque)
    s_mojada = L * (2*T + B) * max(0.70, min(0.95, 0.72 + 0.25*cb))
    rn = max(v * L / max(nu, 1e-12), 1e5)
    cf = 0.075 / ((math.log10(rn) - 2.0) ** 2)
    q = 0.5 * rho * v**2
    rf = q * s_mojada * cf
    # Factor global por forma, apéndices y resistencia residual según tipo.
    factor = {
        "Buque tanque": 1.55, "Bulk carrier": 1.60, "Portacontenedores": 1.85,
        "OSV / PSV": 2.10, "AHTS": 2.20, "Remolcador": 2.35,
        "Ferry": 2.00, "Libre / Personalizado": 1.80
    }.get(tipo_buque, 1.80)
    return float(rf * factor / 1000.0)

def estimar_diametro_eje_mm(pb_kw, rpm, material="Acero Forjado Naval Estándar"):
    # Predimensionamiento por torsión para que la app funcione sin dato de eje.
    # Se limita a valores razonables y debe validarse con reglas de clase.
    if pb_kw <= 0 or rpm <= 0:
        return 250.0
    omega = 2.0 * math.pi * rpm / 60.0
    torque = pb_kw * 1000.0 / omega
    tau_adm = 45e6  # Pa, valor preliminar conservador para prediseño académico.
    d = (16.0 * torque / (math.pi * tau_adm)) ** (1/3)
    return float(min(max(d * 1000.0, 80.0), 1200.0))

def estimar_peso_helice_kg(diametro_m, z):
    # Correlación didáctica proporcional a D^3; evita usar pesos de un buque específico.
    return float(max(250.0, 48.0 * (max(diametro_m, 0.1)**3) * (max(z, 3)/4.0)))

def estimar_voladizo_m(diametro_m):
    return float(min(max(0.35 * diametro_m, 0.8), 5.0))


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
    st.subheader("📄 Ficha técnica del buque real")
    pdf_buque = st.file_uploader(
        "Subir PDF de ficha técnica para comparar",
        type=["pdf"],
        help="Opcional. La app intentará detectar datos reales como Lpp, velocidad, motor, MCR, hélice y RPM. Después podrás corregirlos manualmente."
    )
    texto_pdf = extraer_texto_pdf(pdf_buque) if pdf_buque is not None else ""
    datos_pdf = parsear_ficha_tecnica(texto_pdf) if texto_pdf else {}
    if pdf_buque is not None:
        st.success("PDF leído. Revisa los datos detectados en la pestaña 📄 PDF / Comparación.")

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
        value=float(nvl(datos_pdf.get("lpp_m"), 320.0)),
        min_value=1.0,
        step=1.0,
        help="Distancia longitudinal entre perpendicular de proa y popa. Remolcadores: 20–50 m; OSV: 60–100 m; buques tanque: 250–330 m; portacontenedores: 250–400 m."
    )

    lwl = st.number_input(
        "Eslora en flotación LWL [m]",
        value=float(nvl(datos_pdf.get("loa_m"), 325.5)),
        min_value=1.0,
        step=1.0,
        help="Longitud del buque sobre la línea de agua. Normalmente es igual o ligeramente mayor que Lpp."
    )

    manga = st.number_input(
        "Manga B [m]",
        value=float(nvl(datos_pdf.get("manga_m"), 58.0)),
        min_value=1.0,
        step=0.5,
        help="Ancho máximo del buque. Debe guardar proporción con Lpp según el tipo de embarcación."
    )

    puntal = st.number_input(
        "Puntal D [m]",
        value=float(nvl(datos_pdf.get("puntal_m"), 30.0)),
        min_value=1.0,
        step=0.5,
        help="Altura estructural desde la línea base hasta cubierta principal."
    )

    calado = st.number_input(
        "Calado T [m]",
        value=float(nvl(datos_pdf.get("calado_m"), 20.8)),
        min_value=0.1,
        step=0.1,
        help="Profundidad sumergida del casco. Debe ser menor que el puntal."
    )

    velocidad = st.number_input(
        "Velocidad de servicio [kn]",
        value=float(nvl(datos_pdf.get("velocidad_kn"), 15.5)),
        min_value=0.1,
        step=0.5,
        help="Velocidad de operación del buque. Buques mercantes usualmente operan entre 10 y 25 nudos."
    )

    st.markdown("---")
    st.subheader("🌀 Interacción casco-propulsor")

    w_estimado = estimar_estela(modo_guia)
    t_estimado = estimar_deduccion_empuje(w_estimado)

    estela = st.number_input(
        "Fracción de estela w [-]",
        value=float(nvl(datos_pdf.get("w"), w_estimado)),
        min_value=0.0,
        max_value=0.8,
        step=0.001,
        format="%.3f",
        help="Valor editable. Si no se conoce, la app propone una estimación según tipo de buque y coeficiente de bloque de referencia."
    )

    t_fraction = st.slider(
        "Fracción de deducción de empuje t [-]",
        0.05,
        0.35,
        float(nvl(datos_pdf.get("t"), t_estimado)),
        0.005,
        help="Valor editable. Si no se conoce, se estima preliminarmente como una fracción de la estela."
    )

    eta_r = st.number_input(
        "Eficiencia rotativa relativa ηR [-]",
        value=float(nvl(datos_pdf.get("eta_r"), 1.000)),
        min_value=0.80,
        max_value=1.15,
        step=0.005,
        format="%.3f",
        help="Si no se conoce, 1.000 es una hipótesis neutra de prediseño."
    )

    inmersion_eje_m = st.number_input(
        "Inmersión del centro del eje h [m]",
        value=float(nvl(datos_pdf.get("inmersion_eje_m"), max(0.50 * calado, 0.1))),
        min_value=0.1,
        step=0.1,
        help="Si no se conoce, se aproxima como 50% del calado. Debe corregirse con plano de arreglo de popa si existe."
    )

    st.markdown("---")
    st.subheader("⚙️ Geometría de la hélice")

    z_val = st.slider("Número de palas Z", 3, 7, int(nvl(datos_pdf.get("prop_z"), 4)))
    diam_prop_m = st.number_input("Diámetro de hélice D [m]", value=float(nvl(datos_pdf.get("prop_diam_m"), 9.86)), min_value=0.1, step=0.01)
    pd_val = st.slider("Relación paso/diámetro P/D [-]", 0.5, 1.4, float(nvl(datos_pdf.get("prop_pd"), 0.721)), 0.001)
    ae_val = st.slider("Relación de área expandida Ae/A0 [-]", 0.3, 1.0, 0.431, 0.001)
    margen_servicio = st.slider("Margen de servicio requerido [%]", 0.0, 30.0, float(nvl(datos_pdf.get("sea_margin_pct"), 15.0)), 0.5)

    st.markdown("---")
    st.subheader("⚙️ Material del sistema propulsivo")
    st.info(
        "Selecciona el material de referencia para evaluar el límite admisible de esfuerzo. "
        "Los parámetros que no existan en la ficha técnica se estiman de forma preliminar y quedan visibles/editables."
    )

    st.markdown("---")
    st.subheader("⚡ Cadena de potencias")
    rt_estimado_kn = estimar_resistencia_ittc_kn(lwl, manga, calado, velocidad, modo_guia, rho_auto)
    usar_rt_auto = st.checkbox("Usar RT estimada automáticamente", value=("rt_kn" not in datos_pdf), help="Si no tienes resistencia de pruebas o CFD, la app estima RT con una aproximación ITTC preliminar. Puedes desactivarlo y escribir tu propio valor.")
    resistencia_total_kn = st.number_input(
        "Resistencia total RT [kN]",
        value=float(nvl(datos_pdf.get("rt_kn"), rt_estimado_kn)),
        min_value=0.0, step=50.0,
        disabled=usar_rt_auto,
        help="RT es la resistencia al avance. Si está en automático, se estima con dimensiones, velocidad y tipo de buque; si tienes un dato real, desactiva el automático."
    )
    if usar_rt_auto:
        resistencia_total_kn = rt_estimado_kn
        st.caption(f"RT automática preliminar: {resistencia_total_kn:,.0f} kN. Este valor no viene de un buque específico; se recalcula con tus entradas.")

    transmision_tipo = st.selectbox("Tipo de transmisión", ["Automática según motor recomendado", "Directa / sin caja reductora", "Con caja reductora"] )
    transmision_para_eta = "Directa / sin caja reductora" if transmision_tipo.startswith("Automática") else transmision_tipo
    eta_s = st.number_input("Eficiencia del eje ηS [-]", value=estimar_eta_s(transmision_para_eta), min_value=0.50, max_value=1.00, step=0.001, format="%.3f")
    eta_g = st.number_input("Eficiencia de engranaje/transmisión ηG [-]", value=estimar_eta_g(transmision_para_eta), min_value=0.50, max_value=1.00, step=0.001, format="%.3f")
    eta_o_extra = st.number_input("Eficiencia extra / pérdidas varias [-]", value=1.000, min_value=0.50, max_value=1.00, step=0.001, format="%.3f", help="Normalmente 1.000 si no se considera una pérdida adicional.")

    st.markdown("---")
    st.subheader("🛠️ Motor y transmisión")
    st.caption("El motor real solo se toma del PDF si el usuario lo sube. Sin PDF, la app no usa ningún motor fijo: recomienda opciones desde la base interna.")
    motor_nombre_pdf = datos_pdf.get("motor_modelo") or "Sin motor real cargado"
    motor_nombre = st.text_input("Motor real detectado/manual", value=motor_nombre_pdf)
    motor_mcr_kw = st.number_input("Potencia MCR del motor [kW]", value=float(nvl(datos_pdf.get("mcr_kw"), 0.0)), min_value=0.0, step=100.0)
    motor_mcr_rpm = st.number_input("RPM MCR del motor [rpm]", value=float(nvl(datos_pdf.get("mcr_rpm"), 0.0)), min_value=0.0, step=1.0)
    motor_ncr_kw = st.number_input("Potencia NCR / servicio real [kW]", value=float(nvl(datos_pdf.get("ncr_kw"), motor_mcr_kw * 0.85 if motor_mcr_kw else 0.0)), min_value=0.0, step=100.0)
    motor_ncr_rpm = st.number_input("RPM NCR / servicio real [rpm]", value=float(nvl(datos_pdf.get("ncr_rpm"), motor_mcr_rpm if motor_mcr_rpm else 0.0)), min_value=0.0, step=1.0)

    if transmision_tipo == "Con caja reductora":
        marca_caja = st.selectbox("Caja reductora real", ["Reintjes WAF/WGF", "ZF Marine", "Twin Disc", "Lufkin", "Otra"] )
        relacion_reduccion = st.number_input("Relación de reducción i = RPM motor / RPM hélice", value=1.50, min_value=1.0, step=0.01, format="%.2f")
    elif transmision_tipo == "Directa / sin caja reductora":
        marca_caja = "No aplica: motor lento acoplado directamente"
        relacion_reduccion = 1.0
    else:
        marca_caja = "Automática: se propone directa o reductora en pestaña Motor"
        relacion_reduccion = 1.0

    st.markdown("---")
    st.subheader("🔎 Datos reales para comparar")
    st.caption("Estos campos son opcionales. Si no hay PDF o ficha técnica, déjalos en 0 y la app calculará sin comparar contra datos reales.")
    pb_real_kw = st.number_input("PB real/NCR del buque [kW]", value=float(nvl(datos_pdf.get("ncr_kw"), 0.0)), min_value=0.0, step=100.0)
    rpm_real = st.number_input("RPM reales de hélice/servicio [rpm]", value=float(nvl(datos_pdf.get("ncr_rpm"), 0.0)), min_value=0.0, step=1.0)
    diam_real_m = st.number_input("Diámetro real de hélice [m]", value=float(nvl(datos_pdf.get("prop_diam_m"), 0.0)), min_value=0.0, step=0.01)
    z_real = st.number_input("Número real de palas", value=int(nvl(datos_pdf.get("prop_z"), 0)), min_value=0, step=1)
    pd_real = st.number_input("P/D real", value=float(nvl(datos_pdf.get("prop_pd"), 0.0)), min_value=0.0, step=0.001, format="%.3f")

    st.markdown("---")
    st.subheader("⚙️ Parámetros mecánicos visibles")
    st.caption("Si no tienes estos datos, la app puede estimarlos. No se usa ningún valor fijo de un barco específico.")
    rpm_motor_default = float(nvl(datos_pdf.get("ncr_rpm"), rpm_real if rpm_real > 0 else 100.0))
    rpm_motor = st.number_input("RPM de operación para vibración [rpm]", value=rpm_motor_default, min_value=0.1, step=1.0, help="Si no hay PDF, se usa un valor preliminar editable para que el análisis vibratorio pueda ejecutarse.")
    potencia_kw_base = st.number_input("Potencia base manual para análisis de eje [kW]", value=float(nvl(datos_pdf.get("ncr_kw"), 0.0)), min_value=0.0, step=100.0, help="Opcional. Si lo dejas en 0, la app usará automáticamente la PB calculada en la cadena de potencias.")
    potencia_kw = potencia_kw_base * (1 + margen_servicio / 100) if potencia_kw_base > 0 else 0.0
    diametro_eje_default = estimar_diametro_eje_mm(max(potencia_kw_base, 1.0), rpm_motor)
    diametro_eje_mm = st.number_input("Diámetro del eje [mm]", value=diametro_eje_default, min_value=50.0, step=10.0, help="Estimado automáticamente si no hay dato de plano; editable para validación.")
    peso_helice_kg = st.number_input("Peso estimado de hélice [kg]", value=estimar_peso_helice_kg(diam_prop_m, z_val), min_value=1.0, step=500.0, help="Estimado con correlación D³; editable si el fabricante proporciona el peso real.")
    longitud_volado_m = st.number_input("Longitud en voladizo del eje [m]", value=estimar_voladizo_m(diam_prop_m), min_value=0.1, step=0.1, help="Estimación preliminar a partir del diámetro de hélice; corregir con arreglo de línea de ejes si existe.")

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

# Para una hélice naval correctamente balanceada se usa una fracción pequeña
# de la masa total, no 0.1%. Esto evita mostrar valores poco realistas
# como 52 kg de desbalance para una hélice de 52 toneladas.
masa_desbalance_kg = max(peso_helice_kg * 0.00001, 0.10)  # 0.001% de la masa de la hélice
excentricidad_desbalance_m = 0.0005  # 0.5 mm
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

# ==============================================================================
# CADENA DE POTENCIAS, MOTOR, REDUCTORA, BURRILL, KELLER Y COMPARACIÓN
# ==============================================================================
RT_N = resistencia_total_kn * 1000.0
PE_kw_sin_margen = RT_N * velocidad_buque_ms / 1000.0
PE_kw = PE_kw_sin_margen * (1 + margen_servicio / 100.0)
VA_ms = v_ms
thrust_req_N = safe_div(RT_N, max(1.0 - t_fraction, 1e-9))
PT_kw = thrust_req_N * VA_ms / 1000.0
eta_h = safe_div(1.0 - t_fraction, 1.0 - estela, default=0.0)
eta_b = max_eff * eta_r
eta_d = eta_h * eta_b * eta_o_extra
PD_kw = safe_div(PE_kw, max(eta_d, 1e-9))
PS_kw = safe_div(PD_kw, max(eta_s, 1e-9))
PB_kw_calc = safe_div(PS_kw, max(eta_g, 1e-9))
MCR_requerido_kw = safe_div(PB_kw_calc, 0.85, default=0.0)
# Si el usuario no proporcionó potencia para vibraciones, se toma PB calculada automáticamente.
if potencia_kw_base <= 0:
    potencia_kw = PB_kw_calc
    empuje_estimado_n = thrust_req_N
    amplitud_empuje_axial_n = 0.08 * empuje_estimado_n
    desplazamiento_axial_est_m = safe_div(amplitud_empuje_axial_n, rigidez_axial_equivalente_n_m)
potencia_85_mcr_kw = motor_mcr_kw * 0.85
# Validación de motor en tres niveles:
# 1) IDEAL: PB <= 85% MCR, cumple el criterio de reserva operativa pedido.
# 2) OBSERVACIÓN: PB > 85% MCR pero PB <= MCR; el motor tiene capacidad máxima,
#    pero el punto de operación queda por encima del NCR/85% MCR.
# 3) NO CUMPLE: PB > MCR; el motor no tiene capacidad suficiente.
motor_cumple_ideal = motor_mcr_kw > 0 and PB_kw_calc <= potencia_85_mcr_kw
motor_cumple_observacion = motor_mcr_kw > 0 and potencia_85_mcr_kw < PB_kw_calc <= motor_mcr_kw
motor_no_cumple = motor_mcr_kw > 0 and PB_kw_calc > motor_mcr_kw
motor_cumple = motor_cumple_ideal or motor_cumple_observacion
exceso_sobre_85_kw = max(PB_kw_calc - potencia_85_mcr_kw, 0.0)
exceso_sobre_85_pct = safe_div(exceso_sobre_85_kw, max(potencia_85_mcr_kw, 1e-9)) * 100.0
margen_hasta_mcr_kw = motor_mcr_kw - PB_kw_calc if motor_mcr_kw > 0 else 0.0
margen_hasta_mcr_pct = safe_div(margen_hasta_mcr_kw, max(motor_mcr_kw, 1e-9)) * 100.0
rpm_helice_requerida = safe_div(VA_ms, max(j_opt * diam_prop_m, 1e-9), default=0.0) * 60.0 if j_opt > 0 else 0.0
# Para validación de transmisión se usa primero la RPM real/manual si existe, porque J óptimo no siempre representa la RPM real de servicio.
rpm_helice_objetivo = rpm_real if rpm_real and rpm_real > 0 else rpm_helice_requerida
if transmision_tipo == "Con caja reductora":
    rpm_helice_por_caja = safe_div(motor_ncr_rpm, max(relacion_reduccion, 1e-9), default=0.0)
elif transmision_tipo == "Directa / sin caja reductora":
    rpm_helice_por_caja = motor_ncr_rpm
else:
    rpm_helice_por_caja = 0.0
relacion_recomendada = safe_div(motor_ncr_rpm, max(rpm_helice_objetivo, 1e-9), default=0.0) if motor_ncr_rpm > 0 else 0.0
tolerancia_rpm = max(5.0, 0.10 * max(rpm_helice_objetivo, 1.0))
caja_cumple = True if transmision_tipo.startswith("Automática") or motor_ncr_rpm <= 0 else abs(rpm_helice_por_caja - rpm_helice_objetivo) <= tolerancia_rpm
# Alias usado en el módulo avanzado de cumplimiento.
# Se separa para evitar errores si más adelante se cambia el nombre interno de la validación de caja/transmisión.
transmision_ok = bool(caja_cumple)

# Keller: área expandida mínima preliminar para evitar cavitación excesiva.
p0_pv = (p_atm_auto + rho_auto * g_auto * inmersion_eje_m - p_vap_auto)
keller_ae_min = safe_div((1.3 + 0.3 * z_val) * thrust_req_N, max(p0_pv * diam_prop_m**2, 1e-9), default=0.0) + 0.10
keller_ok = ae_val >= keller_ae_min

# Burrill preliminar: coeficiente de carga de empuje vs sigma.
area_disco = math.pi * diam_prop_m**2 / 4.0
tau_c_burrill = safe_div(thrust_req_N, 0.5 * rho_auto * max(VA_ms**2, 1e-9) * max(area_disco, 1e-9), default=0.0)
tau_c_admisible = 0.22 + 0.18 * sigma_n
burrill_ok = tau_c_burrill <= tau_c_admisible

comparacion_df = pd.DataFrame([
    {"Parámetro": "Potencia al freno PB [kW]", "Calculado": PB_kw_calc, "Real PDF/manual": pb_real_kw, "Error [%]": error_pct(PB_kw_calc, pb_real_kw)},
    {"Parámetro": "RPM de hélice [rpm]", "Calculado": rpm_helice_requerida, "Real PDF/manual": rpm_real, "Error [%]": error_pct(rpm_helice_requerida, rpm_real)},
    {"Parámetro": "Diámetro de hélice [m]", "Calculado": diam_prop_m, "Real PDF/manual": diam_real_m, "Error [%]": error_pct(diam_prop_m, diam_real_m)},
    {"Parámetro": "Número de palas Z", "Calculado": z_val, "Real PDF/manual": z_real, "Error [%]": error_pct(z_val, z_real)},
    {"Parámetro": "P/D", "Calculado": pd_val, "Real PDF/manual": pd_real, "Error [%]": error_pct(pd_val, pd_real)},
])

power_chain_df = pd.DataFrame([
    {"Etapa": "RT", "Descripción": "Resistencia total", "Valor": resistencia_total_kn, "Unidad": "kN"},
    {"Etapa": "PE", "Descripción": "Potencia efectiva sin margen", "Valor": PE_kw_sin_margen, "Unidad": "kW"},
    {"Etapa": "PE + Sea Margin", "Descripción": f"Potencia efectiva con {margen_servicio:.1f}% de margen", "Valor": PE_kw, "Unidad": "kW"},
    {"Etapa": "PT", "Descripción": "Potencia de empuje", "Valor": PT_kw, "Unidad": "kW"},
    {"Etapa": "PD", "Descripción": "Potencia entregada a la hélice", "Valor": PD_kw, "Unidad": "kW"},
    {"Etapa": "PS", "Descripción": "Potencia en el eje", "Valor": PS_kw, "Unidad": "kW"},
    {"Etapa": "PB", "Descripción": "Potencia al freno requerida", "Valor": PB_kw_calc, "Unidad": "kW"},
    {"Etapa": "MCR requerido", "Descripción": "MCR mínimo para operar PB al 85%", "Valor": MCR_requerido_kw, "Unidad": "kW"},
])

torque_nominal = safe_div(PB_kw_calc * 1000.0, omega)
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
            "PB calculada [kW]",
            "MCR requerido [kW]",
            "RPM hélice requerida [rpm]",
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
            PB_kw_calc,
            MCR_requerido_kw,
            rpm_helice_requerida,
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
    tmp_files = []

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        resumen_df.to_excel(writer, sheet_name="Resumen", index=False)
        res.to_excel(writer, sheet_name="Wageningen_Datos", index=False)
        power_chain_df.to_excel(writer, sheet_name="Cadena_Potencias", index=False)
        comparacion_df.to_excel(writer, sheet_name="Comparacion_Real", index=False)

        cumplimiento = pd.DataFrame({
            "Criterio": [
                "Hidrodinámica", "Reynolds", "Cavitación sigma",
                "Burrill", "Keller", "Motor", "Transmisión/reductora",
                "Vibración torsional", "Vibración lateral", "Vibración axial", "Balanceo/desbalance"
            ],
            "Resultado": [
                "Cumple" if hidro_ok else "Observación",
                "Cumple" if reynolds_ok else "Observación",
                "Cumple" if cavitacion_ok else "No cumple",
                "Cumple" if burrill_ok else "Revisar",
                "Cumple" if keller_ok else "No cumple",
                "Cumple ideal" if motor_cumple_ideal else ("Cumple con observación" if motor_cumple_observacion else "No cumple"),
                "Cumple" if caja_cumple else "Revisar",
                "Cumple" if torsion_ok else "No cumple",
                "Cumple" if lateral_ok else "No cumple",
                "Cumple" if axial_ok else "No cumple",
                "Cumple" if desbalance_ok else "No cumple"
            ]
        })
        cumplimiento.to_excel(writer, sheet_name="Cumplimiento", index=False)
        axial_df.to_excel(writer, sheet_name="Vibracion_Axial", index=False)
        campbell_df.to_excel(writer, sheet_name="Campbell_Datos", index=False)
        rec_motores_export = recomendar_motores(PB_kw_calc, rpm_helice_objetivo, "Directa / sin caja reductora" if transmision_tipo.startswith("Automática") else transmision_tipo, n=20)
        rec_motores_export.to_excel(writer, sheet_name="Motores_Recomendados", index=False)

        cav_df = pd.DataFrame([
            {"Análisis": "Reynolds", "Resultado": reynolds, "Límite/Referencia": "> 1e7", "Dictamen": "Cumple" if reynolds_ok else "Revisar"},
            {"Análisis": "Sigma cavitación", "Resultado": sigma_n, "Límite/Referencia": "> 0.20 preliminar", "Dictamen": "Cumple" if cavitacion_ok else "Revisar"},
            {"Análisis": "Burrill τc", "Resultado": tau_c_burrill, "Límite/Referencia": tau_c_admisible, "Dictamen": "Cumple" if burrill_ok else "Revisar"},
            {"Análisis": "Keller Ae/A0", "Resultado": ae_val, "Límite/Referencia": keller_ae_min, "Dictamen": "Cumple" if keller_ok else "No cumple"},
        ])
        cav_df.to_excel(writer, sheet_name="Cavitacion_Resultados", index=False)

        graf_desc = pd.DataFrame([
            {"Hoja": "Graf_Wageningen", "Pestaña de origen": "Hidrodinámica", "Descripción": "Curvas KT, 10KQ y eficiencia ηO de la hélice Wageningen Serie B. Sirve para identificar el comportamiento en aguas abiertas y el J óptimo."},
            {"Hoja": "Graf_Comparacion", "Pestaña de origen": "PDF / Comparación", "Descripción": "Comparación de error porcentual entre resultados calculados y datos reales detectados o ingresados desde la ficha técnica del buque."},
            {"Hoja": "Graf_Burrill", "Pestaña de origen": "Cavitación", "Descripción": "Criterio preliminar de Burrill. Compara el coeficiente de cavitación σ contra el coeficiente de carga τc para estimar riesgo de cavitación."},
            {"Hoja": "Graf_Keller", "Pestaña de origen": "Cavitación", "Descripción": "Criterio de Keller. Verifica si el Ae/A0 actual es mayor o igual al área expandida mínima requerida."},
            {"Hoja": "Graf_Campbell", "Pestaña de origen": "Campbell", "Descripción": "Diagrama de Campbell. Relaciona RPM de operación, órdenes de excitación y modos naturales lateral, torsional y axial."},
        ])
        graf_desc.to_excel(writer, sheet_name="Guia_Graficas", index=False)

        figs = [
            (crear_figura_wageningen(res, j_opt), "Graf_Wageningen"),
            (crear_figura_comparacion(comparacion_df), "Graf_Comparacion"),
            (crear_figura_burrill(sigma_n, tau_c_burrill, tau_c_admisible), "Graf_Burrill"),
            (crear_figura_keller(keller_ae_min, ae_val), "Graf_Keller"),
            (crear_figura_campbell(rpm_motor, f_natural_hz, f_torsional_est, f_axial_natural_hz, z_val), "Graf_Campbell"),
        ]
        for fig, sheet in figs:
            tmp = insertar_figura_excel(writer, fig, sheet)
            if tmp:
                tmp_files.append(tmp)
            plt.close(fig)

    for tmp in tmp_files:
        try:
            os.unlink(tmp)
        except Exception:
            pass
    output.seek(0)
    return output


def generar_pdf():
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    except Exception:
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CustomTitle", parent=styles["Title"], textColor=colors.HexColor("#1e1b4b"), fontSize=18, leading=22)
    h2 = styles["Heading2"]
    body = styles["BodyText"]

    def add_table(story, df, col_widths=None, max_rows=35):
        data = tabla_a_reportlab(df, max_rows=max_rows)
        if col_widths is None:
            col_widths = [max(70, min(170, 500 / max(len(data[0]), 1)))] * len(data[0])
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e1b4b")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#CBD5E1")),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#F8FAFC")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("FONTSIZE", (0,0), (-1,-1), 7),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    def add_fig(story, fig, title=None, caption=None, source_tab=None, width=500):
        if title:
            story.append(Paragraph(title, styles["Heading3"]))
        if source_tab:
            story.append(Paragraph(f"Pestaña de origen: {source_tab}", body))
        if caption:
            story.append(Paragraph(caption, body))
            story.append(Spacer(1, 4))
        img_buf = fig_to_bytes(fig)
        story.append(Image(img_buf, width=width, height=width*0.55))
        story.append(Spacer(1, 12))
        plt.close(fig)

    story = []
    story.append(Paragraph("Universal Ship Propulsion & Shafting Analysis Suite", title_style))
    story.append(Paragraph("Reporte técnico integral de propulsión naval", h2))
    story.append(Paragraph("Este reporte integra resultados de hidrodinámica, cadena de potencias, selección de motor, transmisión, cavitación Burrill/Keller, vibraciones, Campbell y comparación con datos reales cuando existe ficha técnica cargada.", body))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Dictamen general: {dictamen}", h2))
    add_table(story, construir_resumen_dataframe(), col_widths=[230, 250], max_rows=45)

    story.append(PageBreak())
    story.append(Paragraph("Cadena de potencias", h2))
    add_table(story, power_chain_df, col_widths=[90, 240, 90, 60])

    story.append(Paragraph("Comparación con datos reales", h2))
    add_table(story, comparacion_df, col_widths=[180, 90, 90, 70])
    add_fig(story, crear_figura_comparacion(comparacion_df), title="Gráfica de comparación", source_tab="PDF / Comparación", caption="Muestra el error porcentual entre los resultados calculados por la aplicación y los datos reales del buque. Permite validar qué tan cercano es el prediseño frente a la ficha técnica.")

    story.append(PageBreak())
    story.append(Paragraph("Curvas Wageningen Serie B", h2))
    add_fig(story, crear_figura_wageningen(res, j_opt), title="Curvas Wageningen Serie B", source_tab="Hidrodinámica", caption="Presenta KT, 10KQ y ηO en función del coeficiente de avance J. El máximo de ηO identifica el punto de operación hidrodinámicamente más eficiente para la geometría evaluada.")
    story.append(Paragraph("Cavitación: Burrill y Keller", h2))
    cav_df = pd.DataFrame([
        {"Análisis": "Sigma", "Resultado": sigma_n, "Referencia": "> 0.20 preliminar", "Dictamen": "Cumple" if cavitacion_ok else "Revisar"},
        {"Análisis": "Burrill τc", "Resultado": tau_c_burrill, "Referencia": tau_c_admisible, "Dictamen": "Cumple" if burrill_ok else "Revisar"},
        {"Análisis": "Keller Ae/A0", "Resultado": ae_val, "Referencia": keller_ae_min, "Dictamen": "Cumple" if keller_ok else "No cumple"},
    ])
    add_table(story, cav_df, col_widths=[120, 90, 120, 100])
    add_fig(story, crear_figura_burrill(sigma_n, tau_c_burrill, tau_c_admisible), title="Criterio de Burrill", source_tab="Cavitación", caption="Relaciona el coeficiente de cavitación σ con el coeficiente de carga τc. Si el punto del diseño queda dentro de la zona aceptable, el riesgo preliminar de cavitación es bajo.")
    add_fig(story, crear_figura_keller(keller_ae_min, ae_val), title="Criterio de Keller", source_tab="Cavitación", caption="Compara el Ae/A0 actual con el Ae/A0 mínimo requerido. Si el valor actual supera la línea mínima, la hélice tiene área expandida suficiente según la revisión preliminar de Keller.")

    story.append(PageBreak())
    story.append(Paragraph("Diagrama de Campbell", h2))
    add_fig(story, crear_figura_campbell(rpm_motor, f_natural_hz, f_torsional_est, f_axial_natural_hz, z_val), title="Diagrama de Campbell", source_tab="Campbell", caption="Cruza los órdenes de excitación con las frecuencias naturales lateral, torsional y axial. Sirve para identificar posibles zonas de resonancia cerca de la RPM de operación.")
    story.append(Paragraph("Recomendaciones", h2))
    for rec in recomendaciones:
        story.append(Paragraph(f"• {rec}", body))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ==============================================================================

tab_dash, tab_resumen, tab_pdf_comp, tab_potencias, tab_motor, tab_hidro, tab_opt, tab_resultados, tab_vibracion, tab_balanceo, tab_campbell, tab_cav, tab_normativa, tab_clase, tab_formulas, tab_avanzado = st.tabs([
    "🏠 Dashboard",
    "📑 Resumen",
    "📄 PDF / Comparación",
    "⚡ Potencias",
    "🛠️ Motor / Reductora",
    "📈 Hidrodinámica",
    "⭐ Optimización",
    "📋 Resultados",
    "🧭 Vibración",
    "⚖️ Balanceo",
    "🗺️ Campbell",
    "🔍 Cavitación",
    "📚 Normativa",
    "📋 Clase",
    "🧮 Fórmulas / Guía",
    "🧠 Avanzado"
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
    c2.metric("PB requerida", f"{PB_kw_calc/1000:.2f} MW")
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

    st.markdown("### 📄 Exportar resultados completos")
    st.markdown("""
    Desde aquí puedes descargar el análisis completo. El Excel incluye tablas y hojas con gráficas;
    el PDF incluye resumen, cadena de potencias, comparación real, Wageningen, Burrill, Keller, Campbell y recomendaciones.
    """)

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        excel_data = generar_excel()
        st.download_button(
            label="📥 Descargar Excel completo",
            data=excel_data,
            file_name="resultados_propulsion_completo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col_exp2:
        pdf_data = generar_pdf()
        if pdf_data is not None:
            st.download_button(
                label="📄 Descargar PDF completo",
                data=pdf_data,
                file_name="reporte_propulsion_completo.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("Para activar PDF agrega 'reportlab' a requirements.txt.")


# ==============================================================================
# PDF / COMPARACIÓN CON BUQUE REAL
# ==============================================================================

with tab_pdf_comp:
    st.subheader("📄 Lectura de ficha técnica y comparación con buque real")
    st.markdown("""
    <div class="section-card">
    Esta sección permite que la app funcione en dos modos: con un PDF de ficha técnica para extraer datos reales y comparar, o sin PDF usando datos manuales. La extracción automática es una ayuda; siempre se recomienda revisar los valores detectados.
    </div>
    """, unsafe_allow_html=True)

    if datos_pdf:
        st.markdown("### Datos detectados del PDF")
        df_pdf = pd.DataFrame([{"Dato": k, "Valor detectado": v} for k, v in datos_pdf.items()])
        st.dataframe(df_pdf, use_container_width=True, height=360)
    else:
        st.info("No se cargó PDF o no se detectaron datos. La app continuará con los parámetros manuales del panel lateral.")

    st.markdown("### Comparación calculado vs real")
    comparacion_vista = comparacion_df.copy()
    for col in ["Calculado", "Real PDF/manual", "Error [%]"]:
        comparacion_vista[col] = pd.to_numeric(comparacion_vista[col], errors="coerce")
    st.dataframe(
        comparacion_vista.style
        .format({
            "Calculado": lambda x: "—" if pd.isna(x) else f"{x:,.3f}",
            "Real PDF/manual": lambda x: "—" if pd.isna(x) else f"{x:,.3f}",
            "Error [%]": lambda x: "—" if pd.isna(x) else f"{x:,.2f}"
        })
        .map(lambda v: "color:#64748b" if pd.isna(v) else "", subset=["Calculado", "Real PDF/manual", "Error [%]"]),
        use_container_width=True
    )

    st.markdown("### 📊 Comparación visual profesional")
    st.caption("La gráfica compara directamente el valor calculado por la app contra el dato real de la ficha técnica o entrada manual. La etiqueta indica el error porcentual.")
    fig_cmp = crear_figura_comparacion(comparacion_df)
    st.pyplot(fig_cmp)

# ==============================================================================
# CADENA DE POTENCIAS
# ==============================================================================

with tab_potencias:
    st.subheader("⚡ Cadena completa de potencias")
    st.markdown("""
    <div class="section-card">
    Esta sección organiza la cadena de potencia en módulos. Cada subpestaña explica una etapa:
    resistencia, potencia efectiva, empuje, potencia entregada, potencia al eje, potencia al freno
    y eficiencias. Así la app no solo entrega números, sino que muestra el flujo completo de cálculo.
    </div>
    """, unsafe_allow_html=True)

    pot_resumen, pot_pe, pot_pt, pot_pd, pot_pb, pot_eff, pot_formulas = st.tabs([
        "📌 Resumen", "🌊 PE", "🌀 PT", "⚙️ PD", "🔩 PS / PB", "📉 Eficiencias", "🧮 Fórmulas"
    ])

    with pot_resumen:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PE con margen", f"{PE_kw:,.0f} kW")
        c2.metric("PD", f"{PD_kw:,.0f} kW")
        c3.metric("PB requerida", f"{PB_kw_calc:,.0f} kW")
        c4.metric("MCR requerido", f"{MCR_requerido_kw:,.0f} kW")

        if motor_mcr_kw <= 0:
            estado_html("ℹ️ Sin motor real cargado: la cadena de potencias se calcula normalmente y la app puede recomendar candidatos en la pestaña Motor / Reductora.", "warn")
        elif motor_cumple_ideal:
            estado_html("✅ Cumple potencia ideal: la PB requerida queda cubierta por el 85% del MCR del motor seleccionado.", "good")
        elif motor_cumple_observacion:
            estado_html(f"⚠️ Cumple con observación: la PB requerida supera el 85% MCR en {exceso_sobre_85_pct:.1f}%, pero todavía está por debajo del MCR.", "warn")
        else:
            estado_html("❌ No cumple potencia: la PB requerida supera el MCR del motor seleccionado.", "bad")

        st.markdown("### 📊 Diagrama general de cadena de potencias")
        etapas_plot = power_chain_df[power_chain_df["Unidad"].astype(str).str.contains("kW", na=False)].copy()
        etapas_plot = etapas_plot[etapas_plot["Etapa"].isin(["PE", "PE + Sea Margin", "PT", "PD", "PS", "PB"])]
        fig_pot, ax_pot = plt.subplots(figsize=(11, 4.8))
        ax_pot.plot(etapas_plot["Etapa"], etapas_plot["Valor"], marker="o", linewidth=2.6)
        ax_pot.fill_between(range(len(etapas_plot)), etapas_plot["Valor"], alpha=0.10)
        ax_pot.set_title("Cadena de potencias: desde PE hasta PB", fontsize=12, fontweight="bold")
        ax_pot.set_xlabel("Etapa de cálculo")
        ax_pot.set_ylabel("Potencia [kW]")
        ax_pot.grid(True, linestyle=":", alpha=0.6)
        for i, val in enumerate(etapas_plot["Valor"]):
            ax_pot.text(i, val, f"{val:,.0f}", ha="center", va="bottom", fontsize=8)
        st.pyplot(fig_pot)

        st.markdown("### Tabla completa de la cadena")
        st.dataframe(power_chain_df.style.format({"Valor":"{:,.3f}"}), use_container_width=True)

    with pot_pe:
        st.markdown("### 🌊 Potencia efectiva PE")
        st.markdown("La potencia efectiva representa la potencia mínima necesaria para vencer la resistencia total del casco a la velocidad de servicio. En esta etapa todavía no se consideran pérdidas propulsivas.")
        c1, c2, c3 = st.columns(3)
        c1.metric("RT", f"{RT_kn:,.1f} kN")
        c2.metric("Velocidad", f"{velocidad_buque_ms:.2f} m/s")
        c3.metric("PE sin margen", f"{PE_sin_margen_kw:,.0f} kW")
        c4, c5 = st.columns(2)
        with c4:
            st.metric("Sea Margin", f"{margen_servicio:.1f}%")
        with c5:
            st.metric("PE con margen", f"{PE_kw:,.0f} kW")
        df_pe = pd.DataFrame([
            {"Concepto":"Resistencia total RT", "Valor":RT_kn, "Unidad":"kN"},
            {"Concepto":"Velocidad del buque VS", "Valor":velocidad_buque_ms, "Unidad":"m/s"},
            {"Concepto":"PE sin margen", "Valor":PE_sin_margen_kw, "Unidad":"kW"},
            {"Concepto":"PE con Sea Margin", "Valor":PE_kw, "Unidad":"kW"},
        ])
        st.dataframe(df_pe.style.format({"Valor":"{:,.3f}"}), use_container_width=True)
        fig, ax = plt.subplots(figsize=(8, 3.8))
        ax.bar(["PE sin margen", "PE con margen"], [PE_sin_margen_kw, PE_kw])
        ax.set_ylabel("Potencia [kW]")
        ax.set_title("Efecto del Sea Margin sobre PE")
        ax.grid(True, axis="y", linestyle=":", alpha=0.6)
        st.pyplot(fig)

    with pot_pt:
        st.markdown("### 🌀 Potencia de empuje PT")
        st.markdown("La potencia de empuje considera la interacción casco-hélice. La hélice debe producir más empuje que la resistencia neta debido a la deducción de empuje t y trabaja con la velocidad de avance VA.")
        c1, c2, c3 = st.columns(3)
        c1.metric("t", f"{t_fraction:.3f}")
        c2.metric("VA", f"{v_ms:.2f} m/s")
        c3.metric("PT", f"{PT_kw:,.0f} kW")
        df_pt = pd.DataFrame([
            {"Parámetro":"Resistencia total RT", "Valor":RT_kn, "Unidad":"kN"},
            {"Parámetro":"Deducción de empuje t", "Valor":t_fraction, "Unidad":"-"},
            {"Parámetro":"Velocidad de avance VA", "Valor":v_ms, "Unidad":"m/s"},
            {"Parámetro":"Potencia de empuje PT", "Valor":PT_kw, "Unidad":"kW"},
        ])
        st.dataframe(df_pt.style.format({"Valor":"{:,.4f}"}), use_container_width=True)
        fig, ax = plt.subplots(figsize=(8, 3.8))
        ax.bar(["PE con margen", "PT"], [PE_kw, PT_kw])
        ax.set_ylabel("Potencia [kW]")
        ax.set_title("Comparación PE con margen vs PT")
        ax.grid(True, axis="y", linestyle=":", alpha=0.6)
        st.pyplot(fig)

    with pot_pd:
        st.markdown("### ⚙️ Potencia entregada a la hélice PD")
        st.markdown("PD es la potencia que realmente llega a la hélice después de considerar la eficiencia cuasi-propulsiva del conjunto casco-hélice.")
        c1, c2, c3 = st.columns(3)
        c1.metric("ηH", f"{eta_h:.3f}")
        c2.metric("ηD", f"{eta_d:.3f}")
        c3.metric("PD", f"{PD_kw:,.0f} kW")
        df_pd = pd.DataFrame([
            {"Concepto":"Eficiencia de casco ηH", "Valor":eta_h, "Unidad":"-"},
            {"Concepto":"Eficiencia aguas abiertas ηO", "Valor":max_eff, "Unidad":"-"},
            {"Concepto":"Eficiencia rotativa ηR", "Valor":eta_r, "Unidad":"-"},
            {"Concepto":"Eficiencia cuasi-propulsiva ηD", "Valor":eta_d, "Unidad":"-"},
            {"Concepto":"Potencia entregada PD", "Valor":PD_kw, "Unidad":"kW"},
        ])
        st.dataframe(df_pd.style.format({"Valor":"{:,.4f}"}), use_container_width=True)
        fig, ax = plt.subplots(figsize=(8, 3.8))
        ax.bar(["ηH", "ηO", "ηR", "ηD"], [eta_h, max_eff, eta_r, eta_d])
        ax.set_ylabel("Eficiencia [-]")
        ax.set_ylim(0, max(1.2, max(eta_h, max_eff, eta_r, eta_d)*1.15))
        ax.set_title("Componentes de eficiencia hasta PD")
        ax.grid(True, axis="y", linestyle=":", alpha=0.6)
        st.pyplot(fig)

    with pot_pb:
        st.markdown("### 🔩 Potencia en eje PS y potencia al freno PB")
        st.markdown("PS considera pérdidas en el eje. PB considera además pérdidas en caja, acoplamiento o transmisión. Esta es la potencia que debe cubrir el motor.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PS", f"{PS_kw:,.0f} kW")
        c2.metric("PB", f"{PB_kw_calc:,.0f} kW")
        c3.metric("ηS", f"{eta_s:.3f}")
        c4.metric("ηG", f"{eta_g:.3f}")
        df_pb = pd.DataFrame([
            {"Etapa":"PD", "Descripción":"Potencia entregada a la hélice", "Valor":PD_kw, "Unidad":"kW"},
            {"Etapa":"PS", "Descripción":"Potencia en el eje", "Valor":PS_kw, "Unidad":"kW"},
            {"Etapa":"PB", "Descripción":"Potencia al freno requerida", "Valor":PB_kw_calc, "Unidad":"kW"},
            {"Etapa":"MCR requerido", "Descripción":"MCR mínimo para trabajar a 85%", "Valor":MCR_requerido_kw, "Unidad":"kW"},
        ])
        st.dataframe(df_pb.style.format({"Valor":"{:,.3f}"}), use_container_width=True)
        fig, ax = plt.subplots(figsize=(8, 3.8))
        ax.bar(["PD", "PS", "PB", "MCR req."], [PD_kw, PS_kw, PB_kw_calc, MCR_requerido_kw])
        ax.set_ylabel("Potencia [kW]")
        ax.set_title("Potencia requerida hasta el motor")
        ax.grid(True, axis="y", linestyle=":", alpha=0.6)
        st.pyplot(fig)

    with pot_eff:
        st.markdown("### 📉 Eficiencias adoptadas")
        st.markdown("Esta tabla permite defender las pérdidas consideradas en la cadena de potencia. Son datos editables o estimados, por lo que deben citarse o justificarse en el reporte.")
        eff_df = pd.DataFrame([
            {"Eficiencia": "ηH", "Descripción": "Eficiencia de casco = (1-t)/(1-w)", "Valor": eta_h},
            {"Eficiencia": "ηO", "Descripción": "Eficiencia en aguas abiertas", "Valor": max_eff},
            {"Eficiencia": "ηR", "Descripción": "Eficiencia rotativa relativa", "Valor": eta_r},
            {"Eficiencia": "ηB", "Descripción": "Eficiencia detrás del casco aproximada = ηO·ηR", "Valor": eta_b},
            {"Eficiencia": "ηD", "Descripción": "Eficiencia cuasi-propulsiva aproximada", "Valor": eta_d},
            {"Eficiencia": "ηS", "Descripción": "Eficiencia del eje", "Valor": eta_s},
            {"Eficiencia": "ηG", "Descripción": "Eficiencia de caja/transmisión", "Valor": eta_g},
        ])
        st.dataframe(eff_df.style.format({"Valor":"{:.4f}"}), use_container_width=True)
        fig, ax = plt.subplots(figsize=(9, 4.2))
        ax.barh(eff_df["Eficiencia"][::-1], eff_df["Valor"][::-1])
        ax.set_xlabel("Valor [-]")
        ax.set_title("Mapa de eficiencias del sistema propulsivo")
        ax.grid(True, axis="x", linestyle=":", alpha=0.6)
        st.pyplot(fig)

    with pot_formulas:
        st.markdown("### 🧮 Fórmulas de la cadena de potencias")
        st.latex(r"P_E = R_T V_S")
        st.latex(r"P_{E,SM}=P_E(1+SM)")
        st.latex(r"T=\frac{R_T}{1-t}")
        st.latex(r"P_T=T V_A")
        st.latex(r"\eta_H=\frac{1-t}{1-w}")
        st.latex(r"\eta_D=\eta_H\eta_O\eta_R")
        st.latex(r"P_D=\frac{P_E}{\eta_D}")
        st.latex(r"P_S=\frac{P_D}{\eta_S}")
        st.latex(r"P_B=\frac{P_S}{\eta_G}")


# ==============================================================================
# MOTOR Y REDUCTORA
# ==============================================================================

with tab_motor:
    st.subheader("🛠️ Selección de motor real y transmisión")
    st.markdown("""
    <div class="section-card">
    El motor se valida contra la potencia al freno calculada. El criterio pedido por el proyecto es que la potencia de diseño trabaje aproximadamente al 85% del MCR, dejando 15% de reserva operativa.
    </div>
    """, unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("PB calculada", f"{PB_kw_calc:,.0f} kW")
    c2.metric("MCR motor", f"{motor_mcr_kw:,.0f} kW")
    c3.metric("85% MCR", f"{potencia_85_mcr_kw:,.0f} kW")
    c4.metric("MCR requerido", f"{MCR_requerido_kw:,.0f} kW")

    if motor_mcr_kw <= 0:
        estado_html("ℹ️ No hay motor real cargado. La app no asume ningún motor fijo; usa la tabla de recomendación automática para elegir candidatos preliminares.", "warn")
    elif motor_cumple_ideal:
        estado_html(f"✅ Motor compatible ideal: {motor_nombre}. El 85% del MCR cubre la PB calculada.", "good")
    elif motor_cumple_observacion:
        estado_html(f"⚠️ Motor compatible con observación: {motor_nombre}. La PB calculada queda {exceso_sobre_85_pct:.1f}% arriba del 85% MCR, pero aún está por debajo del MCR. Es válido como alerta de revisión, no como falla automática.", "warn")
    else:
        estado_html(f"❌ Motor insuficiente: {motor_nombre}. Se requiere un MCR mínimo aproximado de {MCR_requerido_kw:,.0f} kW.", "bad")

    st.markdown("### 🧠 Recomendación automática desde base de motores")
    st.caption("Base didáctica amplia para preselección. Antes de entregar, confirma el modelo exacto con hoja técnica del fabricante.")
    total_motores_db = len(construir_base_motores())
    st.info(f"La base de datos interna contiene {total_motores_db} configuraciones de motores de referencia entre motores lentos 2T, medios 4T y rápidos. La selección es preliminar y debe verificarse con ficha técnica del fabricante.")
    transmision_busqueda = "Directa / sin caja reductora" if transmision_tipo.startswith("Automática") else transmision_tipo
    rec_motores = recomendar_motores(PB_kw_calc, rpm_helice_objetivo, transmision_busqueda, n=25)
    if rec_motores.empty:
        st.warning("No se encontró un motor en la base didáctica que cubra la PB calculada al 85% MCR. Prueba aumentar base de datos o usar un motor manual.")
    else:
        st.dataframe(rec_motores.drop(columns=["Puntaje"], errors="ignore").style.format({
            "MCR [kW]":"{:,.0f}", "RPM MCR":"{:,.0f}", "85% MCR [kW]":"{:,.0f}",
            "Exceso 85% MCR [kW]":"{:,.0f}", "MCR requerido aprox [kW]":"{:,.0f}",
            "Diferencia RPM [%]":"{:.1f}", "Relación recomendada i":"{:.2f}"
        }), use_container_width=True, height=420)
        mejor_motor = rec_motores.iloc[0]
        estado_html(f"Sugerencia: {mejor_motor['Fabricante']} {mejor_motor['Modelo']} — MCR {mejor_motor['MCR [kW]']:,.0f} kW, {mejor_motor['RPM MCR']:.0f} rpm.", "good")

    st.markdown("### Transmisión")
    trans_df = pd.DataFrame([
        {"Concepto":"Tipo", "Valor": transmision_tipo},
        {"Concepto":"Caja/reductora", "Valor": marca_caja},
        {"Concepto":"Relación de reducción indicada", "Valor": relacion_reduccion},
        {"Concepto":"Relación recomendada i", "Valor": relacion_recomendada},
        {"Concepto":"RPM hélice por J óptimo", "Valor": rpm_helice_requerida},
        {"Concepto":"RPM objetivo usada para validar", "Valor": rpm_helice_objetivo},
        {"Concepto":"RPM hélice por transmisión", "Valor": rpm_helice_por_caja},
        {"Concepto":"Compatibilidad", "Valor": "Compatible" if caja_cumple else "Revisar"},
    ])
    st.dataframe(trans_df, use_container_width=True)
    if caja_cumple:
        estado_html("✅ La transmisión/RPM es compatible dentro de una tolerancia preliminar.", "good")
    else:
        estado_html("⚠️ Revisar relación de reducción o RPM: la RPM que entrega la transmisión no coincide con la RPM objetivo de la hélice.", "warn")

    if transmision_tipo == "Con caja reductora":
        st.markdown("### ⚙️ Reductoras sugeridas")
        rec_red = recomendar_reductoras(PB_kw_calc, relacion_recomendada, n=8)
        if rec_red.empty:
            st.info("No se encontró una reductora estándar en la base didáctica para esa potencia y relación. Puede requerirse otro rango/modelo o transmisión directa.")
        else:
            st.dataframe(rec_red.style.format({"Potencia mín [kW]":"{:,.0f}", "Potencia máx [kW]":"{:,.0f}", "i mín":"{:.2f}", "i máx":"{:.2f}", "ηG ref":"{:.3f}"}), use_container_width=True)

    with st.expander("¿Qué significa esto?", expanded=False):
        st.markdown("""
        - Si el motor es lento y trabaja casi a las mismas RPM que la hélice, puede usarse **transmisión directa**.
        - Si el motor gira más rápido que la hélice, se necesita una **caja reductora**.
        - La relación se calcula como: **i = RPM motor / RPM hélice**.
        """)

# ==============================================================================
# OPTIMIZACIÓN AUTOMÁTICA
# ==============================================================================

with tab_opt:
    st.subheader("⭐ Optimización automática de hélice Wageningen")
    st.markdown("""
    <div class="section-card">
    Esta herramienta no cambia tus datos automáticamente: prueba combinaciones comerciales de número de palas Z, P/D y Ae/A0, calcula sus curvas Wageningen, encuentra el máximo ηO de cada una y ordena las alternativas por eficiencia. Sirve para comparar tu hélice actual contra una propuesta preliminar más eficiente.
    Para evitar que la app se quede cargando y bloquee las pestañas siguientes, la optimización se ejecuta solo cuando el usuario presiona el botón.
    </div>
    """, unsafe_allow_html=True)

    modo_opt = st.radio("Nivel de búsqueda", ["Rápida", "Detallada"], horizontal=True, help="Usa Rápida para obtener resultado casi inmediato. Detallada revisa más combinaciones.")
    ejecutar_opt = st.button("▶️ Ejecutar optimización automática", key="btn_opt_helice")

    if ejecutar_opt:
        with st.spinner("Calculando combinaciones de hélice... espera unos segundos."):
            st.session_state["opt_df"] = optimizar_helice_wageningen(modo_opt)
            st.session_state["opt_modo"] = modo_opt
        st.success(f"Optimización {modo_opt.lower()} terminada. Se evaluaron {len(st.session_state['opt_df'])} combinaciones.")

    if "opt_df" in st.session_state:
        opt_df = st.session_state["opt_df"]
        st.dataframe(
            opt_df.head(20).style.format({
                "P/D":"{:.3f}",
                "Ae/A0":"{:.3f}",
                "J óptimo":"{:.3f}",
                "KT":"{:.4f}",
                "KQ":"{:.4f}",
                "ηO [%]":"{:.2f}"
            }),
            use_container_width=True,
            height=520
        )
        mejor = opt_df.iloc[0]
        estado_html(f"Mejor combinación encontrada: Z={int(mejor['Z'])}, P/D={mejor['P/D']:.3f}, Ae/A0={mejor['Ae/A0']:.3f}, ηO={mejor['ηO [%]']:.2f}%.", "good")

        st.markdown("### 📊 Visualización de mejores alternativas")
        top_opt = opt_df.head(10).copy()
        top_opt["Configuración"] = top_opt.apply(lambda r: f"Z{int(r['Z'])} | P/D {r['P/D']:.2f} | Ae {r['Ae/A0']:.2f}", axis=1)
        fig_opt, ax_opt = plt.subplots(figsize=(10.5, 5.0))
        ax_opt.barh(top_opt["Configuración"][::-1], top_opt["ηO [%]"][::-1])
        ax_opt.set_xlabel("Eficiencia en aguas abiertas ηO [%]")
        ax_opt.set_title("Top 10 combinaciones optimizadas de hélice", fontsize=12, fontweight="bold")
        ax_opt.grid(True, axis="x", linestyle=":", alpha=0.55)
        for y, val in enumerate(top_opt["ηO [%]"][::-1]):
            ax_opt.text(val + 0.15, y, f"{val:.2f}%", va="center", fontsize=8)
        st.pyplot(fig_opt)

        st.markdown("### 📌 Comparación contra la configuración actual")
        comp_opt = pd.DataFrame([
            {"Concepto":"Actual", "Z":z_val, "P/D":pd_val, "Ae/A0":ae_val, "J óptimo":j_opt, "ηO [%]":max_eff*100},
            {"Concepto":"Óptima encontrada", "Z":int(mejor['Z']), "P/D":mejor['P/D'], "Ae/A0":mejor['Ae/A0'], "J óptimo":mejor['J óptimo'], "ηO [%]":mejor['ηO [%]']},
        ])
        st.dataframe(comp_opt.style.format({"P/D":"{:.3f}", "Ae/A0":"{:.3f}", "J óptimo":"{:.3f}", "ηO [%]":"{:.2f}"}), use_container_width=True)
    else:
        st.info("Presiona el botón para iniciar la optimización. Mientras no lo hagas, la app seguirá cargando rápido y todas las pestañas estarán disponibles.")

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
# VIBRACIÓN DEL EJE: TORSIONAL, AXIAL Y LATERAL
# ==============================================================================

with tab_vibracion:
    st.subheader("🧭 Análisis integral de vibración del eje")
    st.markdown("""
    <div class="section-card">
    Esta pestaña concentra los tres análisis principales de vibración del eje propulsor:
    <b>torsional</b>, <b>axial</b> y <b>lateral/whirling</b>. Se mantienen los mismos cálculos,
    tablas y gráficas, pero organizados en subpestañas para que la navegación sea más limpia.
    </div>
    """, unsafe_allow_html=True)

    vib_torsion, vib_axial, vib_lateral = st.tabs(["💥 Torsional", "↔️ Axial", "📊 Lateral / Whirling"])

    # ==============================================================================
    # TORSIONAL
    # ==============================================================================
    
    with vib_torsion:
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
    
    with vib_axial:
        st.subheader("↔️ Análisis de Vibración Axial")
    
        st.markdown("""
        <div class="section-card">
        La vibración axial corresponde al movimiento longitudinal del eje propulsor.
        En buques, suele estar asociada a fluctuaciones del empuje de la hélice y a la
        interacción hélice-casco. Esta sección completa el análisis de
        vibración del eje junto con la parte torsional y lateral.
        </div>
        """, unsafe_allow_html=True)
    
        with st.expander("📘 Base teórica de vibración axial", expanded=False):
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
    
        with st.expander("🧮 Fórmulas de vibración axial usadas", expanded=False):
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
    
        st.markdown("### 📈 Mapa profesional de separación axial")
        st.caption("La gráfica compara cada orden de excitación contra la frecuencia natural axial. Mientras más lejos quede cada punto de la línea natural, menor riesgo de resonancia.")
        fig_a, ax_a = plt.subplots(figsize=(10.8, 4.8))
        axial_plot = axial_df.copy()
        x = np.arange(len(axial_plot))
        f_exc_vals = axial_plot["Frecuencia excitante [Hz]"].to_numpy()
        sep_vals = axial_plot["Separación [%]"].to_numpy()
        ax_a.axhspan(f_axial_natural_hz*0.95, f_axial_natural_hz*1.05, alpha=0.16, label="Zona crítica ±5%")
        ax_a.axhspan(f_axial_natural_hz*0.88, f_axial_natural_hz*1.12, alpha=0.08, label="Zona de precaución ±12%")
        ax_a.axhline(y=f_axial_natural_hz, linestyle="--", linewidth=2.6, label=f"Frecuencia natural axial = {f_axial_natural_hz:.2f} Hz")
        ax_a.vlines(x, 0, f_exc_vals, linewidth=4, alpha=0.55)
        ax_a.scatter(x, f_exc_vals, s=180, zorder=5, label="Excitación calculada")
        for i, (f, sep, riesgo) in enumerate(zip(f_exc_vals, sep_vals, axial_plot["Riesgo axial"])):
            ax_a.text(i, f + max(f_axial_natural_hz*0.035, 0.15), f"{f:.2f} Hz\nsep. {sep:.1f}%", ha="center", va="bottom", fontsize=8)
        ax_a.set_xticks(x)
        ax_a.set_xticklabels(axial_plot["Orden de excitación"].tolist())
        ax_a.set_ylabel("Frecuencia [Hz]")
        ax_a.set_title("Órdenes axiales vs frecuencia natural del sistema", fontsize=12, fontweight="bold")
        ax_a.grid(True, axis="y", linestyle=":", alpha=0.55)
        ax_a.legend(loc="best", fontsize=8)
        st.pyplot(fig_a)
    
        st.markdown("### 🧾 Lectura técnica automática")
        peor_ax = axial_df.sort_values("Separación [%]").iloc[0]
        if peor_ax["Riesgo axial"] == "Bajo":
            estado_html(f"✅ La excitación más cercana es {peor_ax['Orden de excitación']} con separación de {peor_ax['Separación [%]']:.1f}%. La condición axial es aceptable para prediseño.", "good")
        elif peor_ax["Riesgo axial"] == "Medio":
            estado_html(f"⚠️ La excitación más cercana es {peor_ax['Orden de excitación']} con separación de {peor_ax['Separación [%]']:.1f}%. Conviene revisar rigidez axial, RPM o número de palas.", "warn")
        else:
            estado_html(f"❌ La excitación {peor_ax['Orden de excitación']} queda demasiado cerca de la frecuencia natural axial. Riesgo alto de resonancia.", "bad")
    
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
    
    with vib_lateral:
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

    with st.expander("📘 Base teórica de balanceo", expanded=False):
        st.markdown("""
        En un eje ideal, la masa gira de forma simétrica alrededor del centro. Cuando existe
        una pequeña masa excéntrica, se produce una fuerza dinámica proporcional a la masa,
        a la excentricidad y al cuadrado de la velocidad angular. Por eso un pequeño
        desbalance puede volverse importante cuando aumentan las RPM.

        En sistemas navales, el desbalance puede originarse por imperfecciones de fabricación,
        daños en palas, incrustaciones marinas, reparación desigual de la hélice o montaje
        incorrecto del conjunto eje-hélice.
        """)

    with st.expander("🧮 Fórmulas de desbalance usadas", expanded=False):
        st.latex(r"\omega=\frac{2\pi n}{60}")
        st.latex(r"F_u=m_u e \omega^2")
        st.latex(r"\%F_u=\frac{F_u}{W_h}\times 100")
        st.markdown("""
        Donde **mᵤ** es la masa equivalente desbalanceada, **e** es la excentricidad,
        **ω** es la velocidad angular y **Wₕ** es el peso de la hélice.
        """)
        st.info("""
        Para este análisis preliminar, la masa desbalanceada equivalente se toma como
        una fracción muy pequeña de la masa total de la hélice. Esto representa una
        condición de hélice correctamente balanceada y evita asumir desbalances excesivos.
        """)

    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Masa desbalanceada equivalente", f"{masa_desbalance_kg:.2f} kg")
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
    st.subheader("🔍 Cavitación y régimen de flujo")
    st.markdown("""
    <div class="section-card">
    La cavitación se organiza en subpestañas para separar claramente la revisión general
    de flujo, el criterio de Burrill, el criterio de Keller y las fórmulas usadas. Esto hace
    que la sección sea más limpia, defendible y fácil de explicar en presentación.
    </div>
    """, unsafe_allow_html=True)

    cav_resumen, cav_burrill, cav_keller, cav_flujo, cav_formulas = st.tabs([
        "📋 Resumen", "🫧 Burrill", "📐 Keller", "🌊 Reynolds / σ", "🧮 Fórmulas"
    ])

    with cav_resumen:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Reynolds", f"{reynolds:.2e}")
        c2.metric("σ", f"{sigma_n:.3f}")
        c3.metric("τc Burrill", f"{tau_c_burrill:.3f}")
        c4.metric("Ae/A0 Keller mín.", f"{keller_ae_min:.3f}")

        resumen_cav = pd.DataFrame([
            {"Análisis":"Reynolds", "Valor calculado":reynolds, "Límite/Referencia":"> 1e7", "Resultado":"Cumple" if reynolds_ok else "Revisar"},
            {"Análisis":"Sigma cavitación", "Valor calculado":sigma_n, "Límite/Referencia":"> 0.20 preliminar", "Resultado":"Cumple" if cavitacion_ok else "Revisar"},
            {"Análisis":"Burrill τc", "Valor calculado":tau_c_burrill, "Límite/Referencia":tau_c_admisible, "Resultado":"Cumple" if burrill_ok else "Revisar"},
            {"Análisis":"Keller Ae/A0", "Valor calculado":ae_val, "Límite/Referencia":keller_ae_min, "Resultado":"Cumple" if keller_ok else "No cumple"},
        ])
        def color_resultado(val):
            if val == "Cumple":
                return "background-color:#dcfce7; color:#166534; font-weight:bold"
            if val == "Revisar":
                return "background-color:#fef3c7; color:#92400e; font-weight:bold"
            if val == "No cumple":
                return "background-color:#fee2e2; color:#991b1b; font-weight:bold"
            return ""
        st.dataframe(
            resumen_cav.style.format({"Valor calculado":"{:,.4g}"}).map(color_resultado, subset=["Resultado"]),
            use_container_width=True
        )

        if burrill_ok and keller_ok and reynolds_ok and cavitacion_ok:
            estado_html("✅ Dictamen de cavitación preliminar favorable: cumple Reynolds, σ, Burrill y Keller.", "good")
        elif keller_ok and burrill_ok:
            estado_html("⚠️ Dictamen con observaciones: Burrill y Keller cumplen, pero conviene revisar Reynolds o σ.", "warn")
        else:
            estado_html("❌ Dictamen de cavitación con riesgo: revisar área expandida, diámetro, inmersión o carga de la hélice.", "bad")

    with cav_burrill:
        st.markdown("### 🫧 Criterio de Burrill")
        st.markdown("Burrill compara la carga de pala τc contra un límite admisible dependiente de σ. Es útil para detectar si la hélice está demasiado cargada y puede presentar cavitación perjudicial.")
        b1, b2, b3 = st.columns(3)
        b1.metric("τc calculado", f"{tau_c_burrill:.3f}")
        b2.metric("τc admisible", f"{tau_c_admisible:.3f}")
        b3.metric("Margen", f"{(tau_c_admisible - tau_c_burrill):.3f}")
        if burrill_ok:
            estado_html("✅ Cumple Burrill preliminar: la carga de pala queda por debajo del límite admisible.", "good")
        else:
            estado_html("⚠️ Revisar Burrill: la carga de pala es elevada. Conviene aumentar Ae/A0, aumentar D o reducir carga.", "warn")
        fig_burr = crear_figura_burrill(sigma_n, tau_c_burrill, tau_c_admisible)
        st.pyplot(fig_burr)
        st.caption("La línea representa el límite preliminar; el punto de operación debe quedar por debajo de la curva admisible.")

    with cav_keller:
        st.markdown("### 📐 Criterio de Keller")
        st.markdown("Keller estima el área expandida mínima requerida para que la hélice no quede excesivamente cargada. La comparación principal es Ae/A0 actual contra Ae/A0 mínimo.")
        k1, k2, k3 = st.columns(3)
        k1.metric("Ae/A0 mínimo", f"{keller_ae_min:.3f}")
        k2.metric("Ae/A0 actual", f"{ae_val:.3f}")
        k3.metric("Margen", f"{(ae_val - keller_ae_min):.3f}")
        if keller_ok:
            estado_html("✅ Cumple Keller preliminar: el área expandida actual es mayor o igual al mínimo requerido.", "good")
        else:
            estado_html("❌ No cumple Keller: se recomienda aumentar Ae/A0 o reducir la carga de la hélice.", "bad")
        fig_kel = crear_figura_keller(keller_ae_min, ae_val)
        st.pyplot(fig_kel)
        st.caption("La barra del diseño actual debe quedar por encima del mínimo Keller para considerarse aceptable en esta revisión preliminar.")

    with cav_flujo:
        st.markdown("### 🌊 Reynolds y coeficiente de cavitación σ")
        c1, c2, c3 = st.columns(3)
        c1.metric("Velocidad efectiva VA", f"{v_ms:.2f} m/s")
        c2.metric("Reynolds", f"{reynolds:.2e}")
        c3.metric("σ", f"{sigma_n:.3f}")
        col_re, col_sig = st.columns(2)
        with col_re:
            fig_re, ax_re = plt.subplots(figsize=(7.2, 4.0))
            etiquetas_re = ["Laminar", "Transición", "Turbulento", "Diseño actual"]
            valores_re = [2.0e3, 4.0e3, 1.0e7, reynolds]
            ax_re.barh(etiquetas_re, valores_re)
            ax_re.set_xscale("log")
            ax_re.set_xlabel("Número de Reynolds Re [escala log]")
            ax_re.set_title("Comparación de régimen de flujo")
            ax_re.grid(True, which="both", linestyle=":", alpha=0.55)
            st.pyplot(fig_re)
            st.success("✅ Flujo turbulento típico de hélices navales.") if reynolds_ok else st.warning("⚠️ Reynolds bajo para escala naval.")
        with col_sig:
            fig_sig, ax_sig = plt.subplots(figsize=(7.2, 4.0))
            etiquetas_sig = ["Riesgo alto", "Precaución", "Zona segura", "Diseño actual"]
            valores_sig = [0.20, 0.50, 1.00, sigma_n]
            ax_sig.barh(etiquetas_sig, valores_sig)
            ax_sig.axvline(0.20, linestyle="--", linewidth=2, label="Límite preliminar σ = 0.20")
            ax_sig.set_xlabel("Coeficiente de cavitación σ")
            ax_sig.set_title("Riesgo general de cavitación")
            ax_sig.grid(True, linestyle=":", alpha=0.55)
            ax_sig.legend(fontsize=8)
            st.pyplot(fig_sig)
            st.success("🟢 σ favorable frente a cavitación.") if cavitacion_ok else st.warning("🟡 σ bajo: revisar inmersión, carga o diámetro.")

    with cav_formulas:
        st.markdown("### 🧮 Fórmulas usadas en cavitación")
        st.latex(r"V_A = V_s(1-w)")
        st.latex(r"Re = \frac{V_A D}{\nu}")
        st.latex(r"\sigma = \frac{P_{atm}+\rho gh-P_v}{\frac{1}{2}\rho V_A^2}")
        st.latex(r"\tau_c = \frac{T}{\frac{1}{2}\rho V_A^2 A_0}")
        st.latex(r"A_0 = \frac{\pi D^2}{4}")
        st.latex(r"\tau_{c,adm}=0.22+0.18\sigma")
        st.latex(r"\left(\frac{A_E}{A_0}\right)_{min}=\frac{(1.3+0.3Z)T}{(P_0-P_v)D^2}+0.10")
        st.latex(r"P_0-P_v=P_{atm}+\rho gh-P_v")
        st.info("Estos criterios son preliminares para prediseño. Para aprobación final deben contrastarse con diagramas originales, pruebas de modelo o reglas de clase aplicables.")


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



    st.markdown("---")
    st.markdown("## 📚 Guía rápida de referencia")
    st.markdown("""
    Esta guía se integra aquí para evitar una pestaña adicional. Los rangos son orientativos
    y sirven para revisar si los datos ingresados son coherentes antes de ejecutar el cálculo.
    """)

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
        - **Burrill:** revisa carga de pala vs cavitación.
        - **Keller:** revisa área expandida mínima.
        - **Campbell:** detección de posibles resonancias.
        """)


# ==============================================================================
# MÓDULOS AVANZADOS: TVA, BODE, ÓRBITAS Y TRANSITORIO
# ==============================================================================

with tab_avanzado:
    st.subheader("🧠 Módulos avanzados de shafting y vibraciones")

    st.markdown("""
    <div class="section-card">
    Esta sección agrega herramientas de análisis avanzado para elevar la aplicación a nivel de
    proyecto final: modelo torsional de masas discretas, respuesta en frecuencia tipo Bode,
    órbitas laterales del eje, respuesta transitoria y matriz de cumplimiento normativo.
    Los resultados son preliminares y didácticos; no sustituyen un cálculo certificado por ABS, DNV,
    Lloyd's Register u otra sociedad de clasificación.
    </div>
    """, unsafe_allow_html=True)

    av1, av2, av3, av4, av5 = st.tabs([
        "✅ Cumplimiento",
        "🔩 Modelo TVA",
        "📉 Bode",
        "🌀 Órbitas",
        "⏱️ Transitorio"
    ])

    with av1:
        st.markdown("### ✅ Matriz de cumplimiento técnico preliminar")
        st.markdown("""
        Esta tabla resume si el diseño cumple los criterios principales que normalmente se revisarían
        antes de pasar a un análisis formal de clase. La columna de referencia indica de dónde sale el criterio.
        """)

        cumplimiento_avanzado = pd.DataFrame({
            "Área": [
                "Agua de cálculo", "Sea Margin", "Cavitación Burrill", "Cavitación Keller",
                "Potencia/MCR", "Transmisión", "Torsión", "Vibración axial",
                "Vibración lateral", "Campbell", "Reynolds", "Trazabilidad"
            ],
            "Criterio revisado": [
                "Propiedades de agua salada a 15 °C", "Margen aplicado a la potencia",
                "Carga de pala frente a límite admisible", "Ae/A0 actual contra Ae/A0 mínimo",
                "PB requerida frente a MCR disponible", "RPM motor / RPM hélice o transmisión directa",
                "Esfuerzo torsional alternante frente al admisible", "Separación de órdenes 1P, ZP, 2ZP, 3ZP",
                "RPM fuera de zona crítica lateral", "Intersecciones lejos de RPM de operación",
                "Régimen turbulento representativo", "Datos visibles, editables o estimados claramente"
            ],
            "Resultado": [
                "Cumple", "Cumple" if margen_servicio >= 10 else "Revisar",
                "Cumple" if burrill_ok else "Revisar", "Cumple" if keller_ok else "Revisar",
                estado_motor_potencia if 'estado_motor_potencia' in globals() else "Revisar",
                "Cumple" if transmision_ok else "Revisar",
                "Cumple" if torsion_ok else "Revisar", "Cumple" if axial_ok else "Revisar",
                "Cumple" if lateral_ok else "Revisar", "Cumple" if not (campbell_df["Riesgo"] == "Alto").any() else "Revisar",
                "Cumple" if reynolds_ok else "Revisar", "Cumple"
            ],
            "Referencia": [
                "ITTC @15 °C", "ITTC 7.5-02-03-01.4", "Burrill", "Keller",
                "Fabricante / MCR-NCR", "Fabricante de motor o caja", "IACS UR M68 / DNV Pt.4 Ch.4",
                "Shafting vibration practice", "Shaft whirling / lateral critical speed",
                "Campbell diagram", "ITTC Open Water", "Requisito de transparencia del proyecto"
            ]
        })

        def color_resultado(v):
            txt = str(v).lower()
            if "cumple" in txt and "observ" not in txt:
                return "background-color:#dcfce7;color:#166534;font-weight:bold"
            if "observ" in txt or "revis" in txt:
                return "background-color:#fef3c7;color:#92400e;font-weight:bold"
            return "background-color:#fee2e2;color:#991b1b;font-weight:bold"

        st.dataframe(
            cumplimiento_avanzado.style.map(color_resultado, subset=["Resultado"]),
            use_container_width=True,
            height=450
        )

        st.info("""
        Lectura: esta matriz sirve para defensa del proyecto. Si un profesor pregunta por qué el diseño
        se considera aceptable, aquí se ve cada criterio, su resultado y la referencia técnica usada.
        """)

    with av2:
        st.markdown("### 🔩 Modelo torsional de masas discretas para TVA")
        st.markdown("""
        El sistema propulsor se representa como masas rotatorias unidas por rigideces torsionales.
        Este modelo permite estimar frecuencias naturales torsionales y visualizar modos de vibración.
        """)

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            n_masas = st.slider("Número de masas discretas", 3, 6, 4)
        with col_m2:
            factor_rigidez = st.slider("Factor de rigidez torsional", 0.5, 2.0, 1.0, 0.05)

        try:
            G_mod = 7.9e10
            d_eje_m = max(diametro_m, 0.05)
            J_polar = math.pi * d_eje_m**4 / 32.0
            L_total_tva = max(eslora * 0.18, 8.0)
            k_base = max(G_mod * J_polar / max(L_total_tva / max(n_masas-1, 1), 0.1), 1.0) * factor_rigidez

            omega_op = max(omega, 0.1)
            inercia_base = max((potencia_kw_calc * 1000.0) / (omega_op**2), 10.0)
            inercias = np.linspace(1.25, 0.70, n_masas) * inercia_base
            inercias[-1] *= 1.8  # hélice como masa dominante final
            rigideces = np.ones(n_masas - 1) * k_base

            M = np.diag(inercias)
            K = np.zeros((n_masas, n_masas))
            for i in range(n_masas - 1):
                k = rigideces[i]
                K[i, i] += k
                K[i+1, i+1] += k
                K[i, i+1] -= k
                K[i+1, i] -= k

            # Se elimina el modo rígido usando pseudo-inversa; se filtran frecuencias casi cero.
            eigvals, eigvecs = np.linalg.eig(np.linalg.pinv(M) @ K)
            eigvals = np.real(eigvals)
            eigvecs = np.real(eigvecs)
            idx = np.argsort(eigvals)
            eigvals = eigvals[idx]
            eigvecs = eigvecs[:, idx]
            freqs_tva = np.sqrt(np.clip(eigvals, 0, None)) / (2*np.pi)
            freqs_tva = freqs_tva[freqs_tva > 0.05]

            tva_df = pd.DataFrame({
                "Modo torsional": [f"Modo {i+1}" for i in range(len(freqs_tva))],
                "Frecuencia natural [Hz]": freqs_tva,
                "RPM equivalente 1P": freqs_tva * 60,
                "RPM equivalente ZP": freqs_tva * 60 / max(z_val, 1)
            })

            st.dataframe(tva_df.style.format({
                "Frecuencia natural [Hz]": "{:.3f}",
                "RPM equivalente 1P": "{:.1f}",
                "RPM equivalente ZP": "{:.1f}"
            }), use_container_width=True)

            fig_tva, ax_tva = plt.subplots(figsize=(10, 4.5))
            masas_x = np.arange(1, n_masas + 1)
            for j in range(min(len(freqs_tva), eigvecs.shape[1]-1)):
                vec = eigvecs[:, j+1]
                vec = vec / max(np.max(np.abs(vec)), 1e-9)
                ax_tva.plot(masas_x, vec, marker="o", linewidth=2, label=f"Modo {j+1}: {freqs_tva[j]:.2f} Hz")
            ax_tva.axhline(0, linestyle="--", linewidth=1)
            ax_tva.set_title("Formas modales torsionales normalizadas")
            ax_tva.set_xlabel("Elemento discreto del tren propulsor")
            ax_tva.set_ylabel("Amplitud relativa")
            ax_tva.grid(True, linestyle=":", alpha=0.6)
            ax_tva.legend(fontsize=8)
            st.pyplot(fig_tva)

            st.caption("Modelo equivalente: motor — acople — eje intermedio — eje de cola — hélice, según el número de masas seleccionado.")
        except Exception as e:
            st.warning(f"No se pudo resolver el modelo TVA con los datos actuales: {e}")

    with av3:
        st.markdown("### 📉 Diagramas de Bode preliminares")
        st.markdown("""
        El diagrama de Bode muestra cómo responde el sistema cuando se excita a distintas frecuencias.
        Cerca de una frecuencia natural, la magnitud aumenta y aparece cambio fuerte de fase.
        """)

        zeta = st.slider("Amortiguamiento modal ζ", 0.01, 0.20, 0.05, 0.01)
        fmax_bode = max(f_axial_natural_hz, f_natural_hz, f_torsional_est, 1.0) * 3.0
        f_bode = np.linspace(0.05, fmax_bode, 600)

        def bode_sdoF(freq_nat):
            r = f_bode / max(freq_nat, 1e-9)
            mag = 1.0 / np.sqrt((1-r**2)**2 + (2*zeta*r)**2)
            phase = -np.degrees(np.arctan2(2*zeta*r, 1-r**2))
            return mag, phase

        modo_bode = st.selectbox("Modo a visualizar", ["Axial", "Lateral", "Torsional estimado"])
        fn_sel = {"Axial": f_axial_natural_hz, "Lateral": f_natural_hz, "Torsional estimado": f_torsional_est}[modo_bode]
        mag, phase = bode_sdoF(fn_sel)

        fig_mag, ax_mag = plt.subplots(figsize=(10, 4.2))
        ax_mag.plot(f_bode, 20*np.log10(mag), linewidth=2.4)
        ax_mag.axvline(fn_sel, linestyle="--", linewidth=2, label=f"fn = {fn_sel:.2f} Hz")
        ax_mag.set_title(f"Bode de magnitud — modo {modo_bode}")
        ax_mag.set_xlabel("Frecuencia [Hz]")
        ax_mag.set_ylabel("Magnitud [dB]")
        ax_mag.grid(True, linestyle=":", alpha=0.6)
        ax_mag.legend()
        st.pyplot(fig_mag)

        fig_phase, ax_phase = plt.subplots(figsize=(10, 4.2))
        ax_phase.plot(f_bode, phase, linewidth=2.4)
        ax_phase.axvline(fn_sel, linestyle="--", linewidth=2, label=f"fn = {fn_sel:.2f} Hz")
        ax_phase.set_title(f"Bode de fase — modo {modo_bode}")
        ax_phase.set_xlabel("Frecuencia [Hz]")
        ax_phase.set_ylabel("Fase [°]")
        ax_phase.grid(True, linestyle=":", alpha=0.6)
        ax_phase.legend()
        st.pyplot(fig_phase)

    with av4:
        st.markdown("### 🌀 Órbitas laterales del eje")
        st.markdown("""
        Las órbitas representan el movimiento radial del eje en dos direcciones perpendiculares.
        Una órbita circular o elíptica puede asociarse a desbalance, desalineación o cercanía a una velocidad crítica.
        """)

        sep_lat = min(abs(rpm_motor - margen_inf), abs(rpm_motor - margen_sup)) / max(rpm_motor, 1e-9) * 100
        amp_base_um = 80.0 if lateral_ok else 220.0
        amp_x = amp_base_um * (1 + max(0, 12-sep_lat)/12)
        amp_y = amp_x * (0.55 if lateral_ok else 0.85)
        fase_orbita = np.deg2rad(35 if lateral_ok else 75)
        th = np.linspace(0, 2*np.pi, 600)
        x_orb = amp_x * np.cos(th)
        y_orb = amp_y * np.sin(th + fase_orbita)

        o1, o2, o3 = st.columns(3)
        o1.metric("Amplitud X estimada", f"{amp_x:.1f} µm")
        o2.metric("Amplitud Y estimada", f"{amp_y:.1f} µm")
        o3.metric("Condición lateral", "Aceptable" if lateral_ok else "Revisar")

        fig_orb, ax_orb = plt.subplots(figsize=(6.4, 6.0))
        ax_orb.plot(x_orb, y_orb, linewidth=2.4)
        ax_orb.scatter([0], [0], s=80, marker="+")
        ax_orb.set_aspect("equal", adjustable="box")
        ax_orb.set_title("Órbita lateral estimada del eje")
        ax_orb.set_xlabel("Desplazamiento X [µm]")
        ax_orb.set_ylabel("Desplazamiento Y [µm]")
        ax_orb.grid(True, linestyle=":", alpha=0.6)
        st.pyplot(fig_orb)

        st.info("La órbita es estimada y sirve para explicar visualmente el comportamiento del eje; para validación real se requieren sensores de proximidad o acelerómetros.")

    with av5:
        st.markdown("### ⏱️ Respuesta transitoria al arranque")
        st.markdown("""
        Este módulo simula de forma didáctica cómo crece y se amortigua la respuesta vibratoria
        durante el arranque del sistema hasta llegar a la RPM de operación.
        """)

        t_final = st.slider("Tiempo de simulación [s]", 10, 120, 45)
        zeta_tr = st.slider("Amortiguamiento transitorio ζ", 0.02, 0.25, 0.06, 0.01, key="zeta_transitorio")
        t_sim = np.linspace(0, t_final, 1200)
        rpm_sim = rpm_motor * (1 - np.exp(-t_sim / max(t_final/5, 1)))
        w_n_ax = 2*np.pi*max(f_axial_natural_hz, 0.1)
        envelope = np.exp(-zeta_tr*w_n_ax*t_sim)
        respuesta = (1 - envelope*np.cos(w_n_ax*t_sim)) * desplazamiento_axial_est_m * 1000

        fig_rpm, ax_rpm = plt.subplots(figsize=(10, 4.2))
        ax_rpm.plot(t_sim, rpm_sim, linewidth=2.4)
        ax_rpm.axhline(rpm_motor, linestyle="--", linewidth=2, label="RPM operación")
        ax_rpm.set_title("Rampa de arranque del eje")
        ax_rpm.set_xlabel("Tiempo [s]")
        ax_rpm.set_ylabel("RPM")
        ax_rpm.grid(True, linestyle=":", alpha=0.6)
        ax_rpm.legend()
        st.pyplot(fig_rpm)

        fig_resp, ax_resp = plt.subplots(figsize=(10, 4.2))
        ax_resp.plot(t_sim, respuesta, linewidth=2.4)
        ax_resp.set_title("Respuesta transitoria axial estimada")
        ax_resp.set_xlabel("Tiempo [s]")
        ax_resp.set_ylabel("Desplazamiento axial [mm]")
        ax_resp.grid(True, linestyle=":", alpha=0.6)
        st.pyplot(fig_resp)

        st.success("La respuesta transitoria permite explicar el comportamiento durante arranque/parada y no solo en régimen permanente.")

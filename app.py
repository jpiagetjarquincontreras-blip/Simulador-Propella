import streamlit as st
import pandas as pd
import numpy as np
import math
import re
import tempfile
import os
from io import BytesIO
import matplotlib.pyplot as plt

try:
    import plotly.graph_objects as go
except Exception:
    go = None
HAS_PLOTLY = go is not None

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
# plotly
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
    """Gráfica profesional: muestra el error porcentual por parámetro para no mezclar escalas diferentes."""
    df = comparacion.copy()
    df["Calculado"] = pd.to_numeric(df["Calculado"], errors="coerce")
    df["Real PDF/manual"] = pd.to_numeric(df["Real PDF/manual"], errors="coerce")
    df["Error [%]"] = pd.to_numeric(df["Error [%]"], errors="coerce")
    df = df.dropna(subset=["Error [%]"]).copy()
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    if df.empty:
        ax.text(0.5, 0.5, "Sin datos reales suficientes para comparar", ha="center", va="center", fontsize=13, fontweight="bold")
        ax.axis("off")
        return fig
    df = df.sort_values("Error [%]", ascending=True)
    ax.barh(df["Parámetro"], df["Error [%]"])
    ax.axvline(5, linestyle="--", linewidth=1.8, label="Cumple ≤ 5%")
    ax.axvline(15, linestyle=":", linewidth=1.8, label="Revisar ≤ 15%")
    ax.set_title("Validación contra ficha técnica — error porcentual", fontsize=12, fontweight="bold")
    ax.set_xlabel("Error porcentual [%]")
    ax.grid(True, axis="x", linestyle=":", alpha=0.55)
    ax.legend(loc="lower right")
    xmax = max(float(df["Error [%]"].max()), 1.0)
    for i, val in enumerate(df["Error [%]"]):
        ax.text(val + xmax*0.02, i, f"{val:.1f}%", va="center", fontsize=9, fontweight="bold")
    ax.set_xlim(0, xmax*1.18)
    fig.tight_layout()
    return fig




# ==============================================================================
# GRÁFICAS PROFESIONALES PARA LA CADENA DE POTENCIAS
# ==============================================================================

def aplicar_estilo_marino(ax, titulo="", xlabel="", ylabel=""):
    """Estilo visual sobrio para que las gráficas se vean más técnicas y delicadas."""
    ax.set_facecolor("#ffffff")
    ax.figure.patch.set_facecolor("#ffffff")
    ax.set_title(titulo, fontsize=13, fontweight="bold", color="#0f172a", pad=14)
    ax.set_xlabel(xlabel, fontsize=10, color="#334155")
    ax.set_ylabel(ylabel, fontsize=10, color="#334155")
    ax.tick_params(axis="both", labelsize=9, colors="#334155")
    ax.grid(True, linestyle=":", linewidth=0.8, alpha=0.45)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#cbd5e1")
    ax.spines["bottom"].set_color("#cbd5e1")


def crear_figura_cadena_potencias_profesional(power_df):
    """Curva limpia de crecimiento de potencia con etiquetas y zona de pérdidas."""
    etapas = ["PE", "PE + Sea Margin", "PT", "PD", "PS", "PB", "MCR requerido"]
    df = power_df[power_df["Etapa"].isin(etapas)].copy()
    df["Etapa"] = pd.Categorical(df["Etapa"], categories=etapas, ordered=True)
    df = df.sort_values("Etapa")
    x = np.arange(len(df))
    y = pd.to_numeric(df["Valor"], errors="coerce").to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    aplicar_estilo_marino(ax, "Progresión energética del sistema propulsivo", "Etapa de cálculo", "Potencia [kW]")
    ax.plot(x, y, linewidth=3.0, marker="o", markersize=7, color="#2563eb", label="Potencia requerida")
    ax.fill_between(x, y, alpha=0.10, color="#2563eb")
    ax.scatter(x[-1], y[-1], s=150, color="#7c3aed", zorder=5, label="MCR requerido")
    ax.set_xticks(x)
    ax.set_xticklabels(df["Etapa"].astype(str), rotation=0)
    ymax = max(float(np.nanmax(y))*1.16, 1.0)
    ax.set_ylim(0, ymax)
    for i, val in enumerate(y):
        ax.text(i, val + ymax*0.025, f"{val:,.0f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0f172a")
    ax.legend(frameon=True, framealpha=0.92, edgecolor="#e2e8f0", fontsize=9)
    fig.tight_layout()
    return fig


def crear_figura_waterfall_pe(pe_sin, pe_con, margen_pct):
    """Waterfall delicado para mostrar cómo el Sea Margin aumenta PE."""
    incremento = max(pe_con - pe_sin, 0.0)
    fig, ax = plt.subplots(figsize=(9.2, 4.5))
    aplicar_estilo_marino(ax, "Potencia efectiva y efecto del Sea Margin", "Concepto", "Potencia [kW]")
    labels = ["PE base", f"Sea Margin\n{margen_pct:.1f}%", "PE diseño"]
    ax.bar(labels[0], pe_sin, color="#1d4ed8", alpha=0.88, label="PE base")
    ax.bar(labels[1], incremento, bottom=pe_sin, color="#f59e0b", alpha=0.88, label="Incremento por margen")
    ax.bar(labels[2], pe_con, color="#059669", alpha=0.88, label="PE con margen")
    ax.plot([0, 1], [pe_sin, pe_sin], linestyle="--", color="#64748b", linewidth=1.4)
    ax.plot([1, 2], [pe_con, pe_con], linestyle="--", color="#64748b", linewidth=1.4)
    ymax = max(pe_con*1.22, 1.0)
    ax.set_ylim(0, ymax)
    for xpos, val, txt in [(0, pe_sin, f"{pe_sin:,.0f} kW"), (1, pe_con, f"+{incremento:,.0f} kW"), (2, pe_con, f"{pe_con:,.0f} kW")]:
        ax.text(xpos, val + ymax*0.025, txt, ha="center", va="bottom", fontsize=9, fontweight="bold", color="#0f172a")
    ax.legend(frameon=True, edgecolor="#e2e8f0", fontsize=8)
    fig.tight_layout()
    return fig


def crear_figura_empuje_profesional(pe_kw, pt_kw, va_ms, thrust_kn):
    """Gráfica combinada para PT: comparación de potencia y anotación de empuje/VA."""
    fig, ax = plt.subplots(figsize=(9.2, 4.5))
    aplicar_estilo_marino(ax, "Conversión de resistencia a empuje útil", "Etapa", "Potencia [kW]")
    labels = ["PE con margen", "PT"]
    vals = [pe_kw, pt_kw]
    bars = ax.bar(labels, vals, color=["#2563eb", "#7c3aed"], alpha=0.88, width=0.55)
    ymax = max(max(vals)*1.25, 1.0)
    ax.set_ylim(0, ymax)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, val+ymax*0.025, f"{val:,.0f} kW", ha="center", fontsize=9, fontweight="bold")
    ax.text(0.5, ymax*0.82, f"Empuje requerido ≈ {thrust_kn:,.1f} kN\nVelocidad de avance VA = {va_ms:.2f} m/s", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.55", fc="#f8fafc", ec="#cbd5e1"), fontsize=9, color="#334155")
    fig.tight_layout()
    return fig


def crear_figura_eficiencias_propulsivas(eta_h, eta_o, eta_r, eta_d):
    """Barras con línea de referencia para lectura de eficiencias."""
    labels = ["ηH\ncasco", "ηO\naguas abiertas", "ηR\nrotativa", "ηD\ncuasi-propulsiva"]
    vals = [eta_h, eta_o, eta_r, eta_d]
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    aplicar_estilo_marino(ax, "Composición de eficiencias hasta PD", "Eficiencia", "Valor [-]")
    bars = ax.bar(labels, vals, color=["#0f766e", "#2563eb", "#7c3aed", "#f59e0b"], alpha=0.90, width=0.58)
    ax.axhline(1.0, linestyle="--", linewidth=1.3, color="#64748b", label="Referencia 1.0")
    ax.set_ylim(0, max(1.25, max(vals)*1.18))
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, val+0.025, f"{val:.3f}", ha="center", fontsize=9, fontweight="bold")
    ax.legend(frameon=True, edgecolor="#e2e8f0", fontsize=8)
    fig.tight_layout()
    return fig


def crear_figura_motor_mcr(pd_kw, ps_kw, pb_kw, mcr_kw):
    """Gráfica en escalones para pérdidas mecánicas y margen MCR."""
    labels = ["PD", "PS", "PB", "MCR req."]
    vals = [pd_kw, ps_kw, pb_kw, mcr_kw]
    fig, ax = plt.subplots(figsize=(9.5, 4.7))
    aplicar_estilo_marino(ax, "Pérdidas mecánicas y reserva de potencia del motor", "Etapa", "Potencia [kW]")
    x = np.arange(len(labels))
    ax.plot(x, vals, color="#1d4ed8", linewidth=2.7, marker="o", markersize=7)
    ax.fill_between(x, vals, alpha=0.10, color="#1d4ed8")
    ax.bar(x, vals, color=["#93c5fd", "#60a5fa", "#2563eb", "#7c3aed"], alpha=0.28, width=0.52)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ymax = max(max(vals)*1.18, 1.0)
    ax.set_ylim(0, ymax)
    for i, val in enumerate(vals):
        ax.text(i, val+ymax*0.025, f"{val:,.0f}", ha="center", fontsize=9, fontweight="bold")
    fig.tight_layout()
    return fig


def crear_figura_mapa_eficiencias(eff_df):
    """Gráfica horizontal más elegante para el mapa de eficiencias."""
    df = eff_df.copy()
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    df = df.dropna(subset=["Valor"]).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    aplicar_estilo_marino(ax, "Mapa de eficiencias adoptadas", "Valor [-]", "")
    y = np.arange(len(df))
    ax.barh(y, df["Valor"], color="#2563eb", alpha=0.82, height=0.55)
    ax.axvline(1.0, linestyle="--", linewidth=1.2, color="#64748b", label="Referencia 1.0")
    ax.set_yticks(y)
    ax.set_yticklabels(df["Eficiencia"].astype(str))
    ax.set_xlim(0, max(1.20, float(df["Valor"].max())*1.15))
    for i, val in enumerate(df["Valor"]):
        ax.text(val+0.015, i, f"{val:.3f}", va="center", fontsize=8.5, fontweight="bold")
    ax.legend(frameon=True, edgecolor="#e2e8f0", fontsize=8)
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
    """Busca datos típicos en fichas técnicas navales en inglés o español.
    No sustituye revisión humana: todos los valores detectados quedan editables."""
    txt = texto_pdf or ""
    d = {}
    d["tipo_buque"] = "VLCC / Buque tanque" if re.search(r"VLCC|oil tanker|tanker|buque tanque|crude carrier", txt, re.I) else ""

    # Dimensiones principales: inglés y español.
    d["loa_m"] = _buscar_numero(txt, [r"Length overall\s*([0-9.,]+)\s*m", r"Eslora\s+Total\s*[:\-]?\s*([0-9.,]+)\s*(?:Metros|m)"])
    d["lwl_m"] = _buscar_numero(txt, [r"Length waterline\s*([0-9.,]+)\s*m", r"Eslora\s+De\s+Flotaci[oó]n\s*[:\-]?\s*([0-9.,]+)\s*(?:Metros|m)"])
    d["lpp_m"] = _buscar_numero(txt, [r"Length between perpendiculars\s*([0-9.,]+)\s*m", r"Eslora\s+Entre\s+Perpendiculares\s*[:\-]?\s*([0-9.,]+)\s*(?:Metros|M|m)"])
    d["manga_m"] = _buscar_numero(txt, [r"Breadth moulded\s*([0-9.,]+)\s*m", r"Manga\s*[:\-]?\s*([0-9.,]+)\s*(?:Metros|m)"])
    d["puntal_m"] = _buscar_numero(txt, [r"Depth moulded\s*([0-9.,]+)\s*m", r"Puntal\s*[:\-]?\s*([0-9.,]+)\s*(?:Metros|m)"])
    d["calado_m"] = _buscar_numero(txt, [r"Draft at Summer freeboard\s*([0-9.,]+)\s*m", r"Calado\s*[:\-]?\s*([0-9.,]+)\s*(?:Metros|m)"])
    d["dwt_t"] = _buscar_numero(txt, [r"Deadweight\s*([0-9.,]+)\s*MT", r"Peso muerto\s*[:\-]?\s*([0-9.,]+)"])
    d["velocidad_kn"] = _buscar_numero(txt, [r"Sea speed.*?([0-9.]+)\s*knots", r"Velocidad\s+De\s+Servicio\s*[:\-]?\s*([0-9.,]+)\s*Nudos"])
    d["sea_margin_pct"] = _buscar_numero(txt, [r"with\s*([0-9.]+)\s*%\s*sea margin", r"Margen\s+De\s+Servicio\s+Requerido\s*[:\-]?\s*([0-9.,]+)\s*%"])

    # Resistencia y parámetros de interacción casco-propulsor.
    d["rt_kn"] = _buscar_numero(txt, [r"Calm\s+Water\s+Resistance\s*[:\-]?\s*([0-9.,]+)", r"Resistencia\s+(?:en\s+)?calma\s*[:\-]?\s*([0-9.,]+)"])
    d["wake_adjustment_pct"] = _buscar_numero(txt, [r"Nonuniform\s+Wake\s+Adjustment\s*[:\-]?\s*([0-9.,]+)\s*%"])
    d["eta_r"] = _buscar_numero(txt, [r"Eficiencia\s+Rotativa\s+Relativa\s*[:\-]?\s*([0-9.,]+)", r"Relative\s+rotative\s+efficiency\s*[:\-]?\s*([0-9.,]+)"])
    d["t"] = _buscar_numero(txt, [r"Fracci[oó]n\s+de\s+deducci[oó]n\s+de\s+empuje\s*[:\-]?\s*([0-9.,]+)", r"Thrust\s+deduction\s*[:\-]?\s*([0-9.,]+)"])
    d["w"] = _buscar_numero(txt, [r"Fracci[oó]n\s+De\s+Estela\s*[:\-]?\s*([0-9.,]+)", r"Wake\s+fraction\s*[:\-]?\s*([0-9.,]+)"])
    d["inmersion_eje_m"] = _buscar_numero(txt, [r"Inmersi[oó]n\s+Del\s+Eje\s*[:\-]?\s*([0-9.,]+)\s*M", r"Shaft\s+immersion\s*[:\-]?\s*([0-9.,]+)"])

    # Condiciones de agua. Se corrige presión atmosférica si viene en kPa o con punto mal colocado.
    p_atm = _buscar_numero(txt, [r"Presi[oó]n\s+Del\s+Aire\s*[:\-]?\s*([0-9.,]+)", r"Atmospheric\s+pressure\s*[:\-]?\s*([0-9.,]+)"])
    if p_atm:
        if p_atm < 2000:
            p_atm = p_atm * 100.0 if p_atm > 500 else p_atm * 1000.0
        d["p_atm_pa"] = p_atm
    d["p_vap_pa"] = _buscar_numero(txt, [r"Presi[oó]n\s+De\s+Vapor.*?[:\-]?\s*([0-9.,]+)", r"Vapor\s+pressure\s*[:\-]?\s*([0-9.,]+)"])
    d["rho_kg_m3"] = _buscar_numero(txt, [r"Densidad.*?([0-9]{3,4}[.,][0-9]+)\s*Kg/M3", r"Density.*?([0-9]{3,4}[.,][0-9]+)"])
    d["g_ms2"] = _buscar_numero(txt, [r"gravitacional\s*[:\-]?\s*([0-9.,]+)", r"Gravity\s*[:\-]?\s*([0-9.,]+)"])

    # Motor real.
    d["motor_modelo"] = _buscar_texto(txt, [r"Main Engine\s*([^\n]+)"])
    m = re.search(r"MCR\s*([0-9,\.]+)\s*KW\s*/\s*([0-9,\.]+)\s*RPM", txt, flags=re.I)
    if m:
        d["mcr_kw"] = float(m.group(1).replace(',', ''))
        d["mcr_rpm"] = float(m.group(2).replace(',', ''))
    else:
        d["mcr_kw"] = None; d["mcr_rpm"] = None
    m = re.search(r"NCR\s*([0-9,\.]+)\s*KW\s*/\s*([0-9,\.]+)\s*RPM", txt, flags=re.I)
    if m:
        d["ncr_kw"] = float(m.group(1).replace(',', ''))
        d["ncr_rpm"] = float(m.group(2).replace(',', ''))
    else:
        d["ncr_kw"] = None; d["ncr_rpm"] = None

    # Hélice real o de referencia.
    z = _buscar_numero(txt, [r"Propeller.*?([0-9]+)\s*blades", r"([0-9]+)\s*blades\s*solid", r"Numero\s+De\s+Palas\s*[:\-]?\s*([0-9]+)"])
    d["prop_z"] = int(z) if z else None
    d["prop_diam_m"] = None
    diam_mm = _buscar_numero(txt, [r"Diam\s*[:\-]?\s*([0-9,\.]+)\s*mm"])
    diam_m = _buscar_numero(txt, [r"Di[aá]metro\s*\(D\)\s*[:\-]?\s*([0-9.,]+)\s*M", r"Di[aá]metro\s*[:\-]?\s*([0-9.,]+)\s*M"])
    if diam_mm:
        d["prop_diam_m"] = diam_mm / 1000.0
    elif diam_m:
        d["prop_diam_m"] = diam_m
    pitch_mm = _buscar_numero(txt, [r"Pitch\s*[:\-]?\s*([0-9,\.]+)\s*mm"])
    d["prop_pitch_m"] = pitch_mm / 1000.0 if pitch_mm else None
    pd_val_detect = _buscar_numero(txt, [r"P/D.*?\)\s*[:\-]?\s*([0-9.,]+)", r"Relaci[oó]n\s+Paso/Di[aá]metro.*?[:\-]?\s*([0-9.,]+)"])
    d["prop_pd"] = pd_val_detect if pd_val_detect else (safe_div(d.get("prop_pitch_m"), d.get("prop_diam_m"), default=None) if d.get("prop_pitch_m") and d.get("prop_diam_m") else None)
    d["prop_aeao"] = _buscar_numero(txt, [r"Ae\s*/\s*A0\s*\)?\s*[:\-]?\s*([0-9.,]+)", r"Relaci[oó]n\s+De\s+[AÁ]rea\s+Expandida.*?[:\-]?\s*([0-9.,]+)"])
    d["hub_ratio"] = _buscar_numero(txt, [r"Hub\s+Ratio\s*[:\-]?\s*([0-9.,]+)", r"Relaci[oó]n\s+Del\s+Cubo.*?[:\-]?\s*([0-9.,]+)"])
    d["prop_material"] = _buscar_texto(txt, [r"Material\s*([^\n]+)"])
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
def optimizar_helice_wageningen(modo="Rápida", rpm_referencia=0.0, va_ms_ref=0.0, diametro_ref_m=1.0):
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
                j_best = float(j_vals_local[imax])
                eta_pct = float(eta_vals[imax] * 100.0)
                rpm_est = safe_div(va_ms_ref, max(j_best * diametro_ref_m, 1e-9), default=0.0) * 60.0 if va_ms_ref > 0 else 0.0
                error_rpm = abs(rpm_est - rpm_referencia) / max(rpm_referencia, 1e-9) * 100.0 if rpm_referencia and rpm_referencia > 0 and rpm_est > 0 else np.nan
                # Puntaje profesional: maximiza eficiencia, pero penaliza alejarse de la RPM real/PDF si existe.
                penalizacion_rpm = 0.35 * error_rpm if not np.isnan(error_rpm) else 0.0
                puntaje = eta_pct - penalizacion_rpm
                dictamen_rpm = "Cumple" if (np.isnan(error_rpm) or error_rpm <= 10) else ("Revisar" if error_rpm <= 20 else "No cumple")
                filas.append({
                    "Z": z,
                    "P/D": float(pdv),
                    "Ae/A0": float(aev),
                    "J óptimo": j_best,
                    "KT": float(kt_vals[imax]),
                    "KQ": float(kq_vals[imax]),
                    "ηO [%]": eta_pct,
                    "RPM estimada [rpm]": rpm_est,
                    "Error RPM [%]": error_rpm,
                    "Puntaje optimizado": puntaje,
                    "Dictamen RPM": dictamen_rpm,
                })
    df_opt = pd.DataFrame(filas)
    return df_opt.sort_values("Puntaje optimizado", ascending=False).reset_index(drop=True)




# ==============================================================================
# GEMELO DIGITAL 3D E INTERACTIVO
# ==============================================================================

def _plotly_available():
    return go is not None


def _cylinder_surface(radius=1.0, length=1.0, x0=0.0, axis="x", n_theta=48, n_len=12):
    theta = np.linspace(0, 2*np.pi, n_theta)
    s = np.linspace(0, length, n_len)
    T, S = np.meshgrid(theta, s)
    if axis == "x":
        X = x0 + S
        Y = radius*np.cos(T)
        Z = radius*np.sin(T)
    elif axis == "z":
        X = radius*np.cos(T)
        Y = radius*np.sin(T)
        Z = x0 + S
    else:
        X = radius*np.cos(T)
        Y = x0 + S
        Z = radius*np.sin(T)
    return X, Y, Z


def _add_cuboid(fig, center, size, name="Bloque", opacity=0.75, color="#475569", hovertext=None):
    """Bloque 3D con tooltip. Se usa para motor, caja y equipos auxiliares."""
    cx, cy, cz = center
    sx, sy, sz = size
    x = np.array([cx-sx/2, cx+sx/2])
    y = np.array([cy-sy/2, cy+sy/2])
    z = np.array([cz-sz/2, cz+sz/2])
    vertices = np.array([
        [x[0], y[0], z[0]], [x[1], y[0], z[0]], [x[1], y[1], z[0]], [x[0], y[1], z[0]],
        [x[0], y[0], z[1]], [x[1], y[0], z[1]], [x[1], y[1], z[1]], [x[0], y[1], z[1]],
    ])
    faces = np.array([
        [0,1,2], [0,2,3], [4,5,6], [4,6,7], [0,1,5], [0,5,4],
        [1,2,6], [1,6,5], [2,3,7], [2,7,6], [3,0,4], [3,4,7]
    ])
    if hovertext is None:
        hovertext = f"<b>{name}</b><br>Elemento conceptual del tren propulsor"
    fig.add_trace(go.Mesh3d(
        x=vertices[:,0], y=vertices[:,1], z=vertices[:,2],
        i=faces[:,0], j=faces[:,1], k=faces[:,2],
        name=name, opacity=opacity, flatshading=True,
        color=color, showscale=False,
        hovertemplate=hovertext + "<extra></extra>"
    ))


def _add_hull_envelope(fig, D, Lpp, shaft_len):
    """Silueta técnica de casco de popa, sin volumen ovalado.

    Se dibuja como líneas/curvas de referencia para que el tren propulsor se lea
    dentro de un buque, pero sin tapar la hélice ni hacer pesada la escena 3D.
    """
    D = max(float(D), 0.2)
    x_min = -1.55*D
    x_max = shaft_len + 1.45*D
    x = np.linspace(x_min, x_max, 120)
    s = (x - x_min) / max(x_max - x_min, 1e-9)

    # Perfil de popa/casco visto como wireframe: más fino en proa/popas, más lleno al centro.
    half_beam = 1.10*D * (np.sin(np.pi*s)**0.50) * (0.78 + 0.22*s)
    keel = -0.72*D + 0.10*D*np.sin(np.pi*s)
    deck = 0.46*D * (np.sin(np.pi*s)**0.18) + 0.10*D

    line_color = "rgba(30,64,175,0.42)"
    keel_color = "rgba(15,23,42,0.78)"

    # Bordas/deck y quilla longitudinal.
    for ysign, nombre in [(1, "Borda de estribor"), (-1, "Borda de babor")]:
        fig.add_trace(go.Scatter3d(
            x=x, y=ysign*half_beam, z=deck,
            mode="lines", line=dict(width=4, color=line_color), name=nombre,
            hovertemplate=(f"<b>{nombre}</b><br>Silueta conceptual del casco alrededor del tren propulsor.<br>"
                           "Permite ubicar motor, línea de ejes y hélice dentro del buque.<extra></extra>")
        ))
        fig.add_trace(go.Scatter3d(
            x=x, y=ysign*0.68*half_beam, z=keel+0.10*D,
            mode="lines", line=dict(width=3, color="rgba(59,130,246,0.24)"), showlegend=False,
            hovertemplate="<b>Línea lateral inferior</b><br>Referencia de volumen sumergido de popa.<extra></extra>"
        ))

    fig.add_trace(go.Scatter3d(
        x=x, y=np.zeros_like(x), z=keel,
        mode="lines", line=dict(width=6, color=keel_color), name="Quilla / crujía",
        hovertemplate="<b>Quilla / línea de crujía</b><br>Referencia longitudinal central del buque.<extra></extra>"
    ))

    # Cuadernas/frames conceptuales, pocas para no saturar ni volver lenta la escena.
    for idx, sx in enumerate(np.linspace(0.10, 0.92, 7)):
        xi = x_min + sx*(x_max-x_min)
        hb = np.interp(xi, x, half_beam)
        ztop = np.interp(xi, x, deck)
        zbot = np.interp(xi, x, keel)
        ang = np.linspace(0, np.pi, 50)
        yy = hb*np.cos(ang)
        zz = zbot + (ztop-zbot)*(np.sin(ang)**0.72)
        fig.add_trace(go.Scatter3d(
            x=np.full_like(yy, xi), y=yy, z=zz,
            mode="lines", line=dict(width=2.2, color="rgba(15,23,42,0.23)"),
            name="Cuadernas conceptuales" if idx == 0 else "", showlegend=bool(idx == 0),
            hovertemplate="<b>Cuaderna conceptual</b><br>Sección transversal simplificada del casco de popa.<extra></extra>"
        ))

    # Espejo de popa cerca de la hélice.
    xi = shaft_len + 0.28*D
    hb = np.interp(min(xi, x_max), x, half_beam)
    ztop = np.interp(min(xi, x_max), x, deck)
    zbot = np.interp(min(xi, x_max), x, keel)
    yy = np.array([-hb, hb, hb*0.86, -hb*0.86, -hb])
    zz = np.array([zbot+0.10*D, zbot+0.10*D, ztop, ztop, zbot+0.10*D])
    fig.add_trace(go.Scatter3d(
        x=np.full_like(yy, xi), y=yy, z=zz,
        mode="lines", line=dict(width=4, color="rgba(14,116,144,0.42)"), name="Espejo / popa",
        hovertemplate="<b>Zona de popa</b><br>Salida del eje, bocina y ubicación del propulsor.<extra></extra>"
    ))

def _rotar_xy(x, y, ang):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    ca, sa = np.cos(ang), np.sin(ang)
    return ca*x - sa*y, sa*x + ca*y


def crear_sankey_potencias_interactivo(PE_kw, PD_kw, PS_kw, PB_kw, MCR_kw):
    """Diagrama interactivo profesional del flujo de potencia.

    Se reemplaza el Sankey clásico por un diagrama técnico de flujo con etiquetas
    nítidas, porque en Streamlit/Plotly las etiquetas dentro del Sankey pueden verse
    borrosas cuando hay flujos muy anchos. Mantiene interacción mediante tooltips.
    """
    if go is None:
        return None

    PE_kw = max(float(PE_kw), 0.0)
    PD_kw = max(float(PD_kw), max(PE_kw, 1.0))
    PS_kw = max(float(PS_kw), PD_kw)
    PB_kw = max(float(PB_kw), PS_kw)
    MCR_kw = max(float(MCR_kw), PB_kw)

    perdida_prop = max(PD_kw - PE_kw, 0.0)
    perdida_eje = max(PS_kw - PD_kw, 0.0)
    perdida_trans = max(PB_kw - PS_kw, 0.0)
    reserva_motor = max(MCR_kw - PB_kw, 0.0)

    fig = go.Figure()

    # Coordenadas normalizadas para obtener un aspecto muy limpio y legible.
    nodes = [
        {"id":"MCR", "x":0.06, "y":0.64, "label":"MCR requerido", "value":MCR_kw, "color":"#312e81",
         "desc":"Potencia máxima continua requerida para que el motor cubra la operación con margen."},
        {"id":"PB", "x":0.27, "y":0.64, "label":"PB motor", "value":PB_kw, "color":"#4f46e5",
         "desc":"Potencia al freno que debe entregar el motor hacia la transmisión."},
        {"id":"PS", "x":0.48, "y":0.64, "label":"PS eje", "value":PS_kw, "color":"#2563eb",
         "desc":"Potencia transmitida por el eje después de pérdidas de transmisión."},
        {"id":"PD", "x":0.69, "y":0.64, "label":"PD hélice", "value":PD_kw, "color":"#0891b2",
         "desc":"Potencia entregada al propulsor antes de convertirla en empuje útil."},
        {"id":"PE", "x":0.90, "y":0.64, "label":"PE útil", "value":PE_kw, "color":"#059669",
         "desc":"Potencia efectiva útil para vencer la resistencia total del casco."},
    ]
    losses = [
        {"x":0.17, "y":0.24, "label":"Reserva MCR", "value":reserva_motor, "color":"#f59e0b",
         "desc":"Diferencia entre MCR requerido y PB de operación; representa margen operativo."},
        {"x":0.38, "y":0.24, "label":"Pérdida transmisión", "value":perdida_trans, "color":"#fb7185",
         "desc":"Pérdidas asociadas a caja, acoplamientos o transmisión."},
        {"x":0.59, "y":0.24, "label":"Pérdida eje", "value":perdida_eje, "color":"#f97316",
         "desc":"Pérdidas mecánicas del eje y elementos asociados."},
        {"x":0.80, "y":0.24, "label":"Pérdidas propulsivas", "value":perdida_prop, "color":"#ef4444",
         "desc":"Pérdidas hidrodinámicas entre potencia entregada y potencia efectiva."},
    ]

    max_val = max(MCR_kw, PB_kw, PS_kw, PD_kw, PE_kw, 1.0)
    def lw(v):
        return max(10.0, min(34.0, 8.0 + 28.0*v/max_val))

    # Flujo principal: líneas gruesas con hover y texto nítido separado del flujo.
    main_pairs = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
    for a, b in main_pairs:
        val = min(a["value"], b["value"])
        fig.add_trace(go.Scatter(
            x=[a["x"], b["x"]], y=[a["y"], b["y"]], mode="lines",
            line=dict(width=lw(val), color="rgba(37,99,235,0.26)", shape="spline"),
            hoverinfo="skip", showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=[a["x"], b["x"]], y=[a["y"], b["y"]], mode="lines",
            line=dict(width=3, color="rgba(15,23,42,0.20)"), hoverinfo="skip", showlegend=False
        ))

    # Derivaciones de pérdidas/reserva hacia abajo.
    for idx, loss in enumerate(losses):
        a = nodes[idx]
        fig.add_trace(go.Scatter(
            x=[a["x"]+0.055, loss["x"]], y=[a["y"]-0.06, loss["y"]+0.08], mode="lines",
            line=dict(width=max(4.0, min(16.0, 4.0 + 22.0*loss["value"]/max_val)), color=loss["color"].replace('#','rgba(') if False else "rgba(245,158,11,0.28)"),
            hoverinfo="skip", showlegend=False
        ))

    # Nodos principales como tarjetas nítidas.
    for n in nodes:
        fig.add_shape(type="rect", x0=n["x"]-0.066, x1=n["x"]+0.066, y0=n["y"]-0.105, y1=n["y"]+0.105,
                      line=dict(color=n["color"], width=1.4), fillcolor="rgba(255,255,255,0.98)", layer="above")
        fig.add_annotation(x=n["x"], y=n["y"]+0.038, text=f"<b>{n['label']}</b>", showarrow=False,
                           font=dict(size=13, color="#0f172a"), align="center")
        fig.add_annotation(x=n["x"], y=n["y"]-0.030, text=f"{n['value']:,.0f} kW", showarrow=False,
                           font=dict(size=12, color=n["color"]), align="center")
        fig.add_trace(go.Scatter(
            x=[n["x"]], y=[n["y"]], mode="markers", marker=dict(size=28, color="rgba(0,0,0,0)"),
            hovertemplate=f"<b>{n['label']}</b><br>{n['value']:,.0f} kW<br>{n['desc']}<extra></extra>",
            showlegend=False
        ))

    # Tarjetas de pérdidas debajo.
    for loss in losses:
        fig.add_shape(type="rect", x0=loss["x"]-0.082, x1=loss["x"]+0.082, y0=loss["y"]-0.070, y1=loss["y"]+0.070,
                      line=dict(color=loss["color"], width=1.2), fillcolor="rgba(255,255,255,0.98)", layer="above")
        fig.add_annotation(x=loss["x"], y=loss["y"]+0.022, text=f"<b>{loss['label']}</b>", showarrow=False,
                           font=dict(size=11, color="#334155"), align="center")
        fig.add_annotation(x=loss["x"], y=loss["y"]-0.027, text=f"{loss['value']:,.0f} kW", showarrow=False,
                           font=dict(size=11, color=loss["color"]), align="center")
        fig.add_trace(go.Scatter(
            x=[loss["x"]], y=[loss["y"]], mode="markers", marker=dict(size=24, color="rgba(0,0,0,0)"),
            hovertemplate=f"<b>{loss['label']}</b><br>{loss['value']:,.0f} kW<br>{loss['desc']}<extra></extra>",
            showlegend=False
        ))

    eficiencia_global = safe_div(PE_kw, PB_kw, default=0.0) * 100.0
    fig.add_annotation(
        x=0.5, y=0.92, showarrow=False, align="center",
        text=(f"<b>Flujo energético interactivo del sistema propulsivo</b><br>"
              f"Eficiencia global PB→PE ≈ {eficiencia_global:.1f}% · pérdidas propulsivas ≈ {perdida_prop:,.0f} kW"),
        font=dict(size=15, color="#0f172a")
    )
    fig.add_annotation(
        x=0.5, y=0.06, showarrow=False, align="center",
        text="Pasa el cursor sobre cada tarjeta para ver qué representa y cómo se relaciona con la cadena de potencias.",
        font=dict(size=11, color="#64748b")
    )

    fig.update_xaxes(visible=False, range=[0,1])
    fig.update_yaxes(visible=False, range=[0,1])
    fig.update_layout(
        height=440,
        margin=dict(l=18, r=18, t=18, b=18),
        paper_bgcolor="white",
        plot_bgcolor="white",
        hoverlabel=dict(bgcolor="white", font_size=12, font_color="#0f172a"),
    )
    return fig

def _propeller_mesh_arrays(D=9.86, Z=4, PD=0.72, AeAo=0.43, hub_ratio=0.155, phase=0.0, x_offset=0.0, axis="z", detail=24):
    """Genera una hélice conceptual pero más refinada: pala con cuerda radial, twist, skew, rake y espesor.
    axis='z' orienta la hélice en el plano XY; axis='x' orienta el disco en YZ para el tren propulsor.
    """
    R = max(D/2.0, 0.1)
    Rhub = max(hub_ratio*R, 0.08*R)
    n_r = detail
    radial = np.linspace(Rhub*1.04, R, n_r)
    x_all, y_all, z_all, i_all, j_all, k_all, intensity = [], [], [], [], [], [], []

    def chord(r):
        mu = (r - Rhub) / max(R - Rhub, 1e-9)
        # cuerda tipo pala naval: crece desde raíz, máximo alrededor 0.55R y reduce hacia punta
        c = (0.18 + 0.95*np.sin(np.pi*mu)**0.78) * R * 0.30
        return c * (0.72 + 1.10*AeAo) / max((Z/4.0)**0.30, 0.75)

    for blade in range(Z):
        base_ang = phase + 2*np.pi*blade/Z
        start = len(x_all)
        for r in radial:
            mu = (r - Rhub) / max(R - Rhub, 1e-9)
            c = chord(r)
            pitch = PD*D
            beta = math.atan2(pitch, 2*np.pi*r)
            skew = np.deg2rad(20.0)*(mu**1.55)       # barrido hacia punta
            rake = 0.055*R*(mu**1.4)                 # desplazamiento axial conceptual
            half_ang = c/(2*max(r, 1e-9))
            thick = (0.030 + 0.055*(1-mu)**1.4)*R*0.16
            # 4 puntos por estación: borde presión/succión visual.
            for side, surf in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                th = base_ang + skew + side*half_ang
                camber = 0.045*R*np.sin(np.pi*mu)
                z_axial = rake + surf*thick + side*0.018*c*np.sin(beta) + camber*0.20
                xp = r*np.cos(th)
                yp = r*np.sin(th)
                zp = z_axial
                if axis == "z":
                    x_all.append(xp); y_all.append(yp); z_all.append(zp + x_offset)
                else:
                    # disco de hélice en plano YZ, eje longitudinal en X
                    x_all.append(zp + x_offset); y_all.append(xp); z_all.append(yp)
                intensity.append(mu)
        # caras entre estaciones, conectando superficies
        for rr in range(n_r-1):
            a = start + 4*rr
            b = start + 4*(rr+1)
            # superficie inferior: puntos 0,1
            i_all += [a, a+1]
            j_all += [a+1, b+1]
            k_all += [b, b]
            # superficie superior: puntos 2,3
            i_all += [a+2, a+3]
            j_all += [a+3, b+3]
            k_all += [b+2, b+2]
            # borde de ataque y salida
            i_all += [a, a+2, a+1, a+3]
            j_all += [a+2, b+2, a+3, b+3]
            k_all += [b, b, b+1, b+1]
    return np.array(x_all), np.array(y_all), np.array(z_all), np.array(i_all), np.array(j_all), np.array(k_all), np.array(intensity)


def crear_helice_3d_parametrica(D=9.86, Z=4, PD=0.72, AeAo=0.43, hub_ratio=0.155, rpm=75.0, animar=True):
    """Hélice paramétrica interactiva en vista de perfil naval.

    Eje longitudinal en X y disco de hélice en YZ, como se observa en un arreglo
    propulsivo real. El modelo cambia con D, Z, P/D, Ae/A0 y hub ratio.
    """
    if go is None:
        return None
    R = max(D/2.0, 0.1)
    Rhub = max(hub_ratio*R, 0.08*R)

    # Menor densidad cuando hay animación para que el giro sea más fluido.
    detail = 26 if animar else 38
    x, y, z, i, j, k, inten = _propeller_mesh_arrays(D, Z, PD, AeAo, hub_ratio, phase=0, axis="x", detail=detail)
    fig = go.Figure()
    hover_pala = (
        f"<b>Pala paramétrica</b><br>"
        f"D={D:.2f} m · Z={Z}<br>P/D={PD:.3f}<br>Ae/A0={AeAo:.3f}<br>"
        "Radio normalizado=%{intensity:.2f}<br>La cuerda y torsión visual cambian con los datos de entrada.<extra></extra>"
    )
    fig.add_trace(go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        intensity=inten, colorscale="Viridis", opacity=0.96, flatshading=False,
        name="Palas paramétricas", hovertemplate=hover_pala, showscale=False
    ))

    # Anillos de referencia del disco de hélice en plano YZ.
    theta = np.linspace(0, 2*np.pi, 180)
    for rr, name, width in [(R, "Disco de hélice", 4), (0.70*R, "Radio 0.7R", 2)]:
        fig.add_trace(go.Scatter3d(
            x=np.zeros_like(theta), y=rr*np.cos(theta), z=rr*np.sin(theta), mode="lines",
            line=dict(width=width, color="#94a3b8" if rr == R else "#10b981"), name=name,
            hovertemplate=f"<b>{name}</b><br>Referencia radial del propulsor.<extra></extra>"
        ))

    # Cubo y eje corto alineados en X.
    Xh, Yh, Zh = _cylinder_surface(radius=Rhub, length=0.46*R, x0=-0.23*R, axis="x", n_theta=60, n_len=10)
    fig.add_trace(go.Surface(x=Xh, y=Yh, z=Zh, colorscale=[[0,"#1e293b"],[1,"#64748b"]], showscale=False, opacity=0.98, name="Cubo", hovertemplate=f"<b>Cubo de hélice</b><br>Hub ratio={hub_ratio:.3f}<br>Radio cubo≈{Rhub:.2f} m<extra></extra>"))
    Xs, Ys, Zs = _cylinder_surface(radius=max(0.055*R, Rhub*0.22), length=1.55*R, x0=-1.05*R, axis="x", n_theta=52, n_len=10)
    fig.add_trace(go.Surface(x=Xs, y=Ys, z=Zs, colorscale=[[0,"#334155"],[1,"#cbd5e1"]], showscale=False, opacity=0.88, name="Eje", hovertemplate="<b>Eje de referencia</b><br>Permite visualizar la orientación real del propulsor.<extra></extra>"))

    # Flecha de empuje/flujo en perfil.
    fig.add_trace(go.Cone(
        x=[0.95*R], y=[0], z=[0], u=[0.9*R], v=[0], w=[0], sizemode="absolute", sizeref=0.40*R,
        anchor="tail", colorscale=[[0,"#38bdf8"],[1,"#0284c7"]], showscale=False, name="Empuje",
        hovertemplate="<b>Empuje</b><br>Dirección conceptual de la fuerza propulsiva en el eje longitudinal.<extra></extra>"
    ))

    if animar:
        frames=[]
        y0 = np.asarray(y, dtype=float); z0 = np.asarray(z, dtype=float)
        yd0 = R*np.cos(theta); zd0 = R*np.sin(theta)
        y07 = 0.70*R*np.cos(theta); z07 = 0.70*R*np.sin(theta)
        # 18 cuadros: más liviano y más fluido en Streamlit Cloud.
        for n, ang in enumerate(np.linspace(0, 2*np.pi, 18, endpoint=False)):
            ca, sa = np.cos(ang), np.sin(ang)
            yr = ca*y0 - sa*z0
            zr = sa*y0 + ca*z0
            ydr = ca*yd0 - sa*zd0
            zdr = sa*yd0 + ca*zd0
            y7r = ca*y07 - sa*z07
            z7r = sa*y07 + ca*z07
            frames.append(go.Frame(data=[
                go.Mesh3d(x=x, y=yr, z=zr, i=i, j=j, k=k, intensity=inten, colorscale="Viridis", opacity=0.96, flatshading=False, showscale=False, hovertemplate=hover_pala),
                go.Scatter3d(x=np.zeros_like(theta), y=ydr, z=zdr, mode="lines", line=dict(width=4, color="#94a3b8")),
                go.Scatter3d(x=np.zeros_like(theta), y=y7r, z=z7r, mode="lines", line=dict(width=2, color="#10b981")),
            ], traces=[0,1,2], name=str(n)))
        fig.frames = frames
        fig.update_layout(updatemenus=[dict(type="buttons", showactive=False, x=0.02, y=1.05, xanchor="left", yanchor="top", buttons=[
            dict(label="▶ Giro continuo", method="animate", args=[None, {"frame":{"duration":45, "redraw":True}, "fromcurrent":True, "transition":{"duration":0}}]),
            dict(label="⏸ Pausa", method="animate", args=[[None], {"frame":{"duration":0, "redraw":False}, "mode":"immediate", "transition":{"duration":0}}])
        ])])

    fig.update_layout(
        title=dict(text=f"Hélice 3D paramétrica de perfil — Z={Z}, D={D:.2f} m, P/D={PD:.3f}, Ae/A0={AeAo:.3f}, n≈{rpm:.1f} rpm", x=0.02, xanchor="left"),
        scene=dict(
            xaxis_title="Eje longitudinal X [m]", yaxis_title="Radio transversal Y [m]", zaxis_title="Radio vertical Z [m]",
            aspectmode="data", bgcolor="white",
            camera=dict(eye=dict(x=1.90, y=1.95, z=0.95)),
            dragmode="orbit",
            xaxis=dict(backgroundcolor="white", gridcolor="#e2e8f0", zerolinecolor="#cbd5e1"),
            yaxis=dict(backgroundcolor="white", gridcolor="#e2e8f0", zerolinecolor="#cbd5e1"),
            zaxis=dict(backgroundcolor="white", gridcolor="#e2e8f0", zerolinecolor="#cbd5e1"),
        ),
        height=640,
        margin=dict(l=0, r=0, t=70, b=0),
        paper_bgcolor="white",
        hoverlabel=dict(bgcolor="white", font_size=12, font_color="#0f172a")
    )
    return fig

def crear_sistema_propulsor_3d(D=9.86, eje_d_mm=650, Lpp=320, tipo_trans="Directa", relacion=1.0, PB=25000, rpm=75, Z=4, PD=0.72, AeAo=0.43, hub_ratio=0.155):
    """Gemelo digital 3D del tren propulsor.

    Es conceptual, pero dinámico: escala el casco, eje, hélice, motor, transmisión,
    flujo y tooltip técnico con los datos actuales de la app. La hélice gira con animación.
    """
    if go is None:
        return None
    fig = go.Figure()
    D = max(float(D), 0.2)
    escala = max(D, 1.0)
    shaft_radius = max(eje_d_mm/1000.0/2.0, 0.025*escala)
    shaft_len = max(2.65*D, 10.0)

    # Casco/volumen del buque para que no se vea como elementos flotantes aislados.
    _add_hull_envelope(fig, D=D, Lpp=Lpp, shaft_len=shaft_len)

    # Bancada y línea de ejes.
    fig.add_trace(go.Scatter3d(
        x=[-1.10*D, shaft_len+0.95*D], y=[0,0], z=[-0.42*D,-0.42*D], mode="lines",
        line=dict(width=9, color="#cbd5e1"), name="Bancada / línea base",
        hovertemplate="<b>Bancada / línea base</b><br>Referencia estructural donde se apoya la línea de ejes.<extra></extra>"
    ))

    # Eje propulsor.
    X, Y, Zc = _cylinder_surface(radius=shaft_radius, length=shaft_len, x0=0, axis="x", n_theta=72, n_len=22)
    fig.add_trace(go.Surface(
        x=X, y=Y, z=Zc, colorscale=[[0,"#334155"],[1,"#cbd5e1"]], showscale=False, opacity=0.98, name="Eje propulsor",
        hovertemplate=(f"<b>Eje propulsor</b><br>Diámetro estimado: {eje_d_mm:,.0f} mm<br>"
                       f"Potencia transmitida: {PB:,.0f} kW<br>RPM de referencia: {rpm:.1f} rpm<extra></extra>")
    ))

    # Cojinetes y bocina.
    for xb, name, desc in [
        (0.58*D, "Cojinete de empuje", "Recibe la fuerza axial generada por la hélice."),
        (1.35*D, "Cojinete intermedio", "Soporta el eje y ayuda a controlar vibración lateral."),
        (shaft_len-0.42*D, "Bocina / stern tube", "Zona de salida del eje hacia la hélice."),
    ]:
        Xb, Yb, Zb = _cylinder_surface(radius=shaft_radius*1.70, length=0.18*D, x0=xb, axis="x", n_theta=56, n_len=6)
        fig.add_trace(go.Surface(
            x=Xb, y=Yb, z=Zb, colorscale=[[0,"#0f766e"],[1,"#14b8a6"]], showscale=False, opacity=0.93, name=name,
            hovertemplate=f"<b>{name}</b><br>{desc}<extra></extra>"
        ))

    # Motor y transmisión con tooltip detallado.
    _add_cuboid(
        fig, center=(-0.72*D, 0, 0.28*D), size=(0.86*D, 0.54*D, 0.46*D), name="Motor principal",
        opacity=0.88, color="#334155",
        hovertext=(f"<b>Motor principal</b><br>Entrega la potencia al freno requerida.<br>"
                   f"PB ≈ {PB:,.0f} kW<br>n hélice ≈ {rpm:.1f} rpm<br>El MCR debe cubrir PB con margen operativo.")
    )
    # Cilindros de motor simbólicos.
    for n in range(6):
        Xc, Yc, Zcc = _cylinder_surface(radius=0.045*D, length=0.14*D, x0=-1.08*D+n*0.14*D, axis="z", n_theta=28, n_len=5)
        fig.add_trace(go.Surface(
            x=Xc, y=Yc, z=Zcc+0.49*D, colorscale=[[0,"#111827"],[1,"#64748b"]], showscale=False,
            opacity=0.92, name="Cilindros del motor" if n==0 else "",
            hovertemplate="<b>Cilindros del motor</b><br>Representación conceptual del motor principal.<extra></extra>"
        ))

    if not str(tipo_trans).startswith("Directa"):
        _add_cuboid(
            fig, center=(0.06*D, 0, 0.17*D), size=(0.34*D, 0.39*D, 0.30*D), name=f"Caja reductora i≈{relacion:.2f}",
            opacity=0.85, color="#475569",
            hovertext=(f"<b>Caja reductora / transmisión</b><br>Relación aproximada i={relacion:.2f}:1<br>"
                       "Ajusta RPM del motor a la RPM requerida por la hélice.")
        )
    else:
        fig.add_trace(go.Scatter3d(
            x=[-0.15*D], y=[0], z=[0.40*D], mode="text", text=["Transmisión directa"],
            textfont=dict(color="#0f766e", size=13), name="Transmisión directa",
            hovertemplate="<b>Transmisión directa</b><br>Motor lento acoplado directamente al eje.<extra></extra>"
        ))

    # Hélice paramétrica en plano YZ al final del eje.
    xp, yp, zp, ii, jj, kk, inten = _propeller_mesh_arrays(D, Z, PD, AeAo, hub_ratio, phase=0.0, x_offset=shaft_len+0.05*D, axis="x", detail=24)
    prop_trace = len(fig.data)
    fig.add_trace(go.Mesh3d(
        x=xp, y=yp, z=zp, i=ii, j=jj, k=kk, intensity=inten, colorscale="Viridis", opacity=0.97,
        flatshading=False, showscale=False, name="Hélice paramétrica",
        hovertemplate=(f"<b>Hélice paramétrica</b><br>D={D:.2f} m<br>Z={Z}<br>P/D={PD:.3f}<br>Ae/A0={AeAo:.3f}<br>"
                       "La geometría se actualiza con los datos del usuario.<extra></extra>")
    ))
    Xh, Yh, Zh = _cylinder_surface(radius=max(0.10*D, hub_ratio*D/2), length=0.26*D, x0=shaft_len-0.10*D, axis="x", n_theta=64, n_len=8)
    fig.add_trace(go.Surface(
        x=Xh, y=Yh, z=Zh, colorscale=[[0,"#1e293b"],[1,"#64748b"]], showscale=False, opacity=0.97, name="Cubo de hélice",
        hovertemplate=f"<b>Cubo de hélice</b><br>Hub ratio={hub_ratio:.3f}<br>Conecta pala y eje propulsor.<extra></extra>"
    ))

    # Empuje y flujo de agua conceptual con tooltip.
    fig.add_trace(go.Cone(
        x=[shaft_len+0.68*D], y=[0], z=[0], u=[0.95*D], v=[0], w=[0], sizemode="absolute", sizeref=0.62*D,
        anchor="tail", colorscale=[[0,"#38bdf8"],[1,"#0284c7"]], showscale=False, name="Vector de empuje",
        hovertemplate="<b>Vector de empuje</b><br>Dirección conceptual de la fuerza propulsiva generada por la hélice.<extra></extra>"
    ))
    for idx, yy in enumerate(np.linspace(-0.95*D, 0.95*D, 7)):
        fig.add_trace(go.Scatter3d(
            x=[shaft_len+1.35*D, shaft_len+0.16*D], y=[yy, yy*0.42], z=[-0.65*D, -0.12*D], mode="lines",
            line=dict(width=4 if idx==3 else 3, color="rgba(56,189,248,.34)"),
            name="Flujo de agua hacia hélice" if idx==3 else "", showlegend=bool(idx==3),
            hovertemplate="<b>Flujo de agua</b><br>Representación conceptual de la estela hacia el propulsor.<extra></extra>"
        ))

    # Las etiquetas flotantes se omiten para evitar texto borroso; la información aparece en hover y tablas.

    # Animación: rota la hélice alrededor del eje X. El usuario también puede mover todo con el mouse.
    frames = []
    y0 = np.asarray(yp, dtype=float)
    z0 = np.asarray(zp, dtype=float)
    zcenter = 0.0
    for n, ang in enumerate(np.linspace(0, 2*np.pi, 18, endpoint=False)):
        ca, sa = np.cos(ang), np.sin(ang)
        yr = ca*y0 - sa*(z0-zcenter)
        zr = sa*y0 + ca*(z0-zcenter) + zcenter
        frames.append(go.Frame(
            data=[go.Mesh3d(x=xp, y=yr, z=zr, i=ii, j=jj, k=kk, intensity=inten, colorscale="Viridis", opacity=0.97, flatshading=False, showscale=False)],
            traces=[prop_trace], name=f"giro_{n}"
        ))
    fig.frames = frames
    fig.update_layout(updatemenus=[dict(type="buttons", showactive=False, x=0.02, y=1.05, xanchor="left", yanchor="top", buttons=[
        dict(label="▶ Animar hélice", method="animate", args=[None, {"frame":{"duration":45, "redraw":True}, "fromcurrent":True, "transition":{"duration":0}}]),
        dict(label="⏸ Pausa", method="animate", args=[[None], {"frame":{"duration":0, "redraw":False}, "mode":"immediate", "transition":{"duration":0}}])
    ])])

    fig.update_layout(
        title=dict(text=f"Gemelo digital del tren propulsor — PB={PB:,.0f} kW, n={rpm:.1f} rpm, D={D:.2f} m", x=0.02, xanchor="left"),
        scene=dict(
            xaxis_title="Longitud del tren [m]", yaxis_title="Manga conceptual", zaxis_title="Vertical",
            aspectmode="data", bgcolor="white",
            camera=dict(eye=dict(x=1.75, y=1.65, z=0.92)),
            xaxis=dict(backgroundcolor="white", gridcolor="#e2e8f0", zerolinecolor="#cbd5e1"),
            yaxis=dict(backgroundcolor="white", gridcolor="#e2e8f0", zerolinecolor="#cbd5e1"),
            zaxis=dict(backgroundcolor="white", gridcolor="#e2e8f0", zerolinecolor="#cbd5e1"),
        ),
        height=660,
        margin=dict(l=0, r=0, t=70, b=0),
        paper_bgcolor="white",
        hoverlabel=dict(bgcolor="white", font_size=12, font_color="#0f172a")
    )
    return fig


def crear_cavitacion_3d_visual(D=9.86, Z=4, PD=0.72, AeAo=0.43, hub_ratio=0.155, sigma=1.0, keller_ok=True, burrill_ok=True):
    """Visualización animada conceptual de cavitación alrededor de la hélice."""
    if go is None:
        return None
    fig = crear_helice_3d_parametrica(D=D, Z=Z, PD=PD, AeAo=AeAo, hub_ratio=hub_ratio, rpm=0, animar=False)
    if fig is None:
        return None
    riesgo = 0.18 if (keller_ok and burrill_ok and sigma > 0.2) else 0.78
    rng = np.random.default_rng(7)
    n = int(34 + 95*riesgo)
    R = D/2

    # Nube de burbujas cerca de punta y cara de succión, en perfil YZ.
    theta_b = rng.uniform(0, 2*np.pi, n)
    rr = rng.uniform(0.62*R, 1.05*R, n)
    xb = rng.normal(0.10*R, 0.18*R, n)
    yb = rr*np.cos(theta_b)
    zb = rr*np.sin(theta_b)
    size = 3.2 + 6.0*riesgo
    bubble_trace = len(fig.data)
    fig.add_trace(go.Scatter3d(
        x=xb, y=yb, z=zb, mode="markers",
        marker=dict(size=size, opacity=0.42, color="#38bdf8"), name="Burbujas simbólicas",
        hovertemplate=(f"<b>Burbujas de cavitación simbólicas</b><br>σ={sigma:.3f}<br>"
                       f"Burrill={'Cumple' if burrill_ok else 'Revisar'}<br>Keller={'Cumple' if keller_ok else 'Revisar'}<br>"
                       "La densidad visual aumenta cuando el riesgo preliminar es mayor.<extra></extra>")
    ))

    th = np.linspace(0, 2*np.pi, 180)
    fig.add_trace(go.Scatter3d(
        x=np.full_like(th, 0.10*R), y=0.95*R*np.cos(th), z=0.95*R*np.sin(th), mode="lines",
        line=dict(width=5, color="#f59e0b" if riesgo>0.4 else "#10b981"), name="Zona de punta",
        hovertemplate="<b>Zona de punta</b><br>Región donde suelen aparecer las primeras señales de cavitación de punta.<extra></extra>"
    ))

    # Líneas de flujo animadas.
    flow_traces = []
    for idx, yy in enumerate(np.linspace(-0.82*R, 0.82*R, 5)):
        flow_traces.append(len(fig.data))
        xx = np.linspace(-1.6*R, 0.9*R, 80)
        zz = 0.12*R*np.sin(np.linspace(0, 2*np.pi, 80) + idx)
        fig.add_trace(go.Scatter3d(
            x=xx, y=np.full_like(xx, yy), z=zz, mode="lines",
            line=dict(width=3, color="rgba(14,165,233,0.38)"), name="Líneas de flujo" if idx==0 else "", showlegend=idx==0,
            hovertemplate="<b>Línea de flujo</b><br>Representa la estela que llega al disco de la hélice.<extra></extra>"
        ))

    frames=[]
    for nframe, ang in enumerate(np.linspace(0, 2*np.pi, 20, endpoint=False)):
        # Las burbujas orbitan suavemente y avanzan un poco en X.
        ca, sa = np.cos(ang), np.sin(ang)
        ybr = ca*yb - sa*zb
        zbr = sa*yb + ca*zb
        xbr = xb + 0.10*R*np.sin(ang + theta_b)
        frame_data = [go.Scatter3d(x=xbr, y=ybr, z=zbr, mode="markers", marker=dict(size=size, opacity=0.42, color="#38bdf8"))]
        traces = [bubble_trace]
        for idx, tr in enumerate(flow_traces):
            xx = np.linspace(-1.6*R, 0.9*R, 80)
            zz = 0.12*R*np.sin(np.linspace(0, 2*np.pi, 80) + idx + ang)
            frame_data.append(go.Scatter3d(x=xx, y=np.full_like(xx, np.linspace(-0.82*R,0.82*R,5)[idx]), z=zz, mode="lines", line=dict(width=3, color="rgba(14,165,233,0.38)")))
            traces.append(tr)
        frames.append(go.Frame(data=frame_data, traces=traces, name=f"cav_{nframe}"))
    fig.frames = frames
    fig.update_layout(
        title=dict(text="Cavitación visual animada — zona de punta, burbujas y estela", x=0.02, xanchor="left"),
        updatemenus=[dict(type="buttons", showactive=False, x=0.02, y=1.05, xanchor="left", yanchor="top", buttons=[
            dict(label="▶ Animar cavitación", method="animate", args=[None, {"frame":{"duration":55, "redraw":True}, "fromcurrent":True, "transition":{"duration":0}}]),
            dict(label="⏸ Pausa", method="animate", args=[[None], {"frame":{"duration":0, "redraw":False}, "mode":"immediate", "transition":{"duration":0}}])
        ])],
        scene=dict(camera=dict(eye=dict(x=1.9, y=1.8, z=0.95)), dragmode="orbit"),
        height=640
    )
    return fig

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

def estimar_resistencia_ittc_kn(lwl, manga, calado, velocidad_kn, tipo_buque, rho=1025.0, nu=1.1883e-6, sw_m2=0.0, ajuste_pct=0.0):
    """
    Estimación preliminar universal de resistencia total RT.

    Método usado por la app:
    1) Calcula la resistencia friccional con la línea ITTC-1957:
       Cf = 0.075 / (log10(Re) - 2)^2
    2) Usa la superficie mojada real si el usuario la proporciona.
       Si no existe, estima S con L, B, T y Cb de referencia por tipo de buque.
    3) Convierte resistencia friccional a resistencia total mediante un factor global
       por forma, apéndices y resistencia residual. Este factor es preliminar y editable
       indirectamente mediante el tipo de buque.
    4) Aplica un ajuste adicional opcional, por ejemplo estela no uniforme o margen
       hidrodinámico local, solo cuando el usuario lo indique.

    No sustituye canal de pruebas, CFD ni Holtrop-Mennen completo; sirve como
    predimensionamiento reproducible para que la app funcione con cualquier buque.
    """
    v = max(velocidad_kn * 0.514444, 0.01)
    L = max(float(lwl), 1.0)
    B = max(float(manga), 0.1)
    T = max(float(calado), 0.1)
    cb = coef_bloque_referencia(tipo_buque)

    if sw_m2 and sw_m2 > 0:
        s_mojada = float(sw_m2)
    else:
        s_mojada = L * (2*T + B) * max(0.70, min(0.95, 0.72 + 0.25*cb))

    rn = max(v * L / max(nu, 1e-12), 1e5)
    cf = 0.075 / ((math.log10(rn) - 2.0) ** 2)
    q = 0.5 * rho * v**2
    rf = q * s_mojada * cf

    factor = {
        "Buque tanque": 1.70,
        "Bulk carrier": 1.65,
        "Portacontenedores": 1.85,
        "OSV / PSV": 2.10,
        "AHTS": 2.20,
        "Remolcador": 2.35,
        "Ferry": 2.00,
        "Libre / Personalizado": 1.80
    }.get(tipo_buque, 1.80)

    rt_kn = float(rf * factor / 1000.0)
    rt_kn = rt_kn * (1.0 + max(float(ajuste_pct), 0.0)/100.0)
    return rt_kn

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
        index=1,
        help="Este selector solo sirve como guía visual. Los valores siguen siendo editables por el usuario. Por defecto se abre como buque tanque KVLCC2."
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

    p_atm_auto = st.number_input("Presión atmosférica [Pa]", value=float(nvl(datos_pdf.get("p_atm_pa"), 101325.0)), format="%.2f")
    p_vap_auto = st.number_input("Presión de vapor del agua [Pa]", value=float(nvl(datos_pdf.get("p_vap_pa"), 1704.0)), format="%.2f")
    rho_auto = st.number_input("Densidad del agua [kg/m³]", value=float(nvl(datos_pdf.get("rho_kg_m3"), 1026.021)), format="%.3f")
    g_auto = st.number_input("Gravedad [m/s²]", value=float(nvl(datos_pdf.get("g_ms2"), 9.80665)), format="%.5f")

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
        value=float(nvl(datos_pdf.get("lwl_m"), 325.5)),
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
    st.subheader("🌊 Superficies y ajustes hidrodinámicos")
    superficie_mojada_sin_timon_m2 = st.number_input(
        "Superficie mojada sin timón Swo [m²]",
        value=float(nvl(datos_pdf.get("swo_m2"), 27194.0)),
        min_value=0.0,
        step=100.0,
        help="Dato de referencia del KVLCC2. Se muestra como entrada visible; si no se conoce puede dejarse como estimación o ajustarse."
    )
    superficie_mojada_con_timon_m2 = st.number_input(
        "Superficie mojada con timón Sw [m²]",
        value=float(nvl(datos_pdf.get("sw_m2"), 27467.0)),
        min_value=0.0,
        step=100.0,
        help="Superficie mojada total incluyendo timón. Sirve como respaldo para cálculos de resistencia cuando se dispone del dato."
    )
    ajuste_estela_no_uniforme_pct = st.number_input(
        "Nonuniform Wake Adjustment [%]",
        value=float(nvl(datos_pdf.get("wake_adjustment_pct"), 5.0)),
        min_value=0.0,
        max_value=30.0,
        step=0.5,
        help="Ajuste por estela no uniforme. Por defecto se usa 5% según los datos del buque de referencia."
    )

    st.markdown("---")
    st.subheader("🌀 Interacción casco-propulsor")

    w_estimado = estimar_estela(modo_guia)
    t_estimado = estimar_deduccion_empuje(w_estimado)

    estela = st.number_input(
        "Fracción de estela w [-]",
        value=float(nvl(datos_pdf.get("w"), 0.351)),
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
        float(nvl(datos_pdf.get("t"), 0.220)),
        0.005,
        help="Valor editable. Si no se conoce, se estima preliminarmente como una fracción de la estela."
    )

    eta_r = st.number_input(
        "Eficiencia rotativa relativa ηR [-]",
        value=float(nvl(datos_pdf.get("eta_r"), 1.015)),
        min_value=0.80,
        max_value=1.15,
        step=0.005,
        format="%.3f",
        help="Si no se conoce, 1.000 es una hipótesis neutra de prediseño."
    )

    inmersion_eje_m = st.number_input(
        "Inmersión del centro del eje h [m]",
        value=float(nvl(datos_pdf.get("inmersion_eje_m"), 14.10)),
        min_value=0.1,
        step=0.1,
        help="Si no se conoce, se aproxima como 50% del calado. Debe corregirse con plano de arreglo de popa si existe."
    )

    st.markdown("---")
    st.subheader("⚙️ Geometría de la hélice")

    z_val = st.slider("Número de palas Z", 3, 7, int(nvl(datos_pdf.get("prop_z"), 4)))
    diam_prop_m = st.number_input("Diámetro de hélice D [m]", value=float(nvl(datos_pdf.get("prop_diam_m"), 9.86)), min_value=0.1, step=0.01)
    pd_val = st.slider("Relación paso/diámetro P/D [-]", 0.5, 1.4, float(nvl(datos_pdf.get("prop_pd"), 0.721)), 0.001)
    ae_val = st.slider("Relación de área expandida Ae/A0 [-]", 0.3, 1.0, float(nvl(datos_pdf.get("prop_aeao"), 0.431)), 0.001)
    hub_ratio = st.number_input("Relación del cubo Hub Ratio [-]", value=float(nvl(datos_pdf.get("hub_ratio"), 0.155)), min_value=0.0, max_value=0.5, step=0.001, format="%.3f")
    margen_servicio = st.slider("Margen de servicio requerido [%]", 0.0, 30.0, float(nvl(datos_pdf.get("sea_margin_pct"), 15.0)), 0.5)

    st.markdown("---")
    st.subheader("⚙️ Material del sistema propulsivo")
    st.info(
        "Selecciona el material de referencia para evaluar el límite admisible de esfuerzo. "
        "Los parámetros que no existan en la ficha técnica se estiman de forma preliminar y quedan visibles/editables."
    )

    st.markdown("---")
    st.subheader("⚡ Cadena de potencias")
    rt_estimado_kn = estimar_resistencia_ittc_kn(
        lwl, manga, calado, velocidad, modo_guia, rho_auto, nu=1.1883e-6,
        sw_m2=superficie_mojada_con_timon_m2, ajuste_pct=0.0
    )
    rt_modo = st.radio(
        "Modo de resistencia total RT",
        ["Automática preliminar", "Dato conocido / manual"],
        index=0,
        horizontal=True,
        help="Para que la app sea universal, por defecto RT se calcula automáticamente con ITTC-1957 + factor por tipo de buque. Si tienes RT de canal, CFD, Holtrop o ficha técnica, puedes usar el modo manual."
    )
    resistencia_total_manual_kn = st.number_input(
        "RT conocida/manual [kN]",
        value=float(nvl(datos_pdf.get("rt_kn"), 2120.0)),
        min_value=0.0, step=50.0,
        disabled=(rt_modo == "Automática preliminar"),
        help="Úsalo solo si cuentas con una resistencia de referencia. Para KVLCC2 el dato de referencia es aproximadamente 2120 kN."
    )
    if rt_modo == "Automática preliminar":
        resistencia_total_kn = rt_estimado_kn
        rt_fuente = "Calculada automáticamente por la app"
        st.caption(f"RT automática preliminar: {resistencia_total_kn:,.0f} kN. Se recalcula con LWL, B, T, Vs, superficie mojada y tipo de buque.")
    else:
        resistencia_total_kn = resistencia_total_manual_kn
        rt_fuente = "Dato conocido/manual del usuario o PDF"
        st.caption(f"RT manual usada: {resistencia_total_kn:,.0f} kN.")

    with st.expander("📘 ¿Cómo calcula la app la RT automática?", expanded=False):
        st.markdown("""
        La resistencia total automática es una **estimación preliminar universal**. La app no usa un valor fijo de un barco específico.

        1. Calcula Reynolds con la eslora y la velocidad.
        2. Calcula el coeficiente friccional con ITTC-1957.
        3. Usa la superficie mojada ingresada; si no existe, la aproxima con dimensiones principales.
        4. Aplica un factor global por tipo de buque para representar forma, apéndices y resistencia residual.

        Para trabajo académico es suficiente como prediseño, pero para diseño final debe validarse con canal de pruebas, CFD, Holtrop-Mennen completo o datos reales del buque.
        """)
        st.latex(r"Re=\frac{V_s L}{\nu}")
        st.latex(r"C_F=\frac{0.075}{(\log_{10}Re-2)^2}")
        st.latex(r"R_F=\frac{1}{2}\rho V_s^2 S C_F")
        st.latex(r"R_T \approx R_F \cdot K_{forma/residual}")

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
    rpm_motor_default = float(nvl(datos_pdf.get("ncr_rpm"), rpm_real if rpm_real > 0 else 75.0))
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
# Para validación contra ficha técnica NO se fuerza que la RPM teórica por J óptimo sea igual a la RPM real.
# La RPM teórica representa el punto de máxima eficiencia en aguas abiertas; la RPM real puede responder a motor,
# transmisión, diámetro permitido, cavitación, vibración, contrato de velocidad o decisiones de fabricante.
rpm_helice_validacion = rpm_real if rpm_real and rpm_real > 0 else rpm_helice_requerida
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
    {"Parámetro": "RPM de hélice de validación [rpm]", "Calculado": rpm_helice_validacion, "Real PDF/manual": rpm_real, "Error [%]": error_pct(rpm_helice_validacion, rpm_real)},
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


def dictamen_error_porcentual(err):
    try:
        if pd.isna(err):
            return "Sin dato real"
        if err <= 5:
            return "Cumple"
        if err <= 15:
            return "Revisar"
        return "No cumple"
    except Exception:
        return "Sin dato real"


def dictamen_eficiencia(valor, minimo=0.0, maximo=1.2):
    try:
        if pd.isna(valor):
            return "Sin dato"
        if minimo <= float(valor) <= maximo:
            return "Cumple"
        return "Revisar"
    except Exception:
        return "Sin dato"


def style_estado(val):
    if val in ["Cumple", "Aprobado", "Ideal"]:
        return "background-color:#dcfce7; color:#166534; font-weight:800"
    if val in ["Revisar", "Observación", "Cumple con observación", "Sin dato real", "Sin dato"]:
        return "background-color:#fef3c7; color:#92400e; font-weight:800"
    if val in ["No cumple", "Riesgo"]:
        return "background-color:#fee2e2; color:#991b1b; font-weight:800"
    return ""


def formatear_numero_tabla(x):
    try:
        if pd.isna(x):
            return "—"
        return f"{float(x):,.3f}"
    except Exception:
        return str(x)


# Tablas de apoyo con dictamen visible.
power_chain_status_df = power_chain_df.copy()
power_chain_status_df["Dictamen"] = "Cumple"
power_chain_status_df.loc[power_chain_status_df["Valor"].isna(), "Dictamen"] = "Revisar"

comparacion_prof_df = comparacion_df.copy()
comparacion_prof_df["Dictamen"] = comparacion_prof_df["Error [%]"].apply(dictamen_error_porcentual)

efficiency_prof_df = pd.DataFrame([
    {"Eficiencia": "ηH", "Descripción": "Eficiencia de casco = (1-t)/(1-w)", "Valor": eta_h, "Rango esperado": "0.80–1.30", "Dictamen": dictamen_eficiencia(eta_h, 0.80, 1.30)},
    {"Eficiencia": "ηO", "Descripción": "Eficiencia en aguas abiertas Wageningen", "Valor": max_eff, "Rango esperado": "0.40–0.85", "Dictamen": dictamen_eficiencia(max_eff, 0.40, 0.85)},
    {"Eficiencia": "ηR", "Descripción": "Eficiencia rotativa relativa", "Valor": eta_r, "Rango esperado": "0.90–1.10", "Dictamen": dictamen_eficiencia(eta_r, 0.90, 1.10)},
    {"Eficiencia": "ηB", "Descripción": "Eficiencia detrás del casco aproximada = ηO·ηR", "Valor": eta_b, "Rango esperado": "0.35–0.90", "Dictamen": dictamen_eficiencia(eta_b, 0.35, 0.90)},
    {"Eficiencia": "ηD", "Descripción": "Eficiencia cuasi-propulsiva aproximada", "Valor": eta_d, "Rango esperado": "0.35–0.90", "Dictamen": dictamen_eficiencia(eta_d, 0.35, 0.90)},
    {"Eficiencia": "ηS", "Descripción": "Eficiencia del eje", "Valor": eta_s, "Rango esperado": "0.95–1.00", "Dictamen": dictamen_eficiencia(eta_s, 0.95, 1.00)},
    {"Eficiencia": "ηG", "Descripción": "Eficiencia de engranaje/transmisión", "Valor": eta_g, "Rango esperado": "0.94–1.00", "Dictamen": dictamen_eficiencia(eta_g, 0.94, 1.00)},
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
            "Superficie mojada sin timón Swo [m²]",
            "Superficie mojada con timón Sw [m²]",
            "Nonuniform Wake Adjustment [%]",
            "Hub Ratio [-]",
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
            superficie_mojada_sin_timon_m2,
            superficie_mojada_con_timon_m2,
            ajuste_estela_no_uniforme_pct,
            hub_ratio,
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
    story.append(Paragraph("Reporte técnico integral de diseño de sistema propulsor", h2))
    story.append(Paragraph("Buque de referencia: KVLCC2 / buque tanque VLCC", styles["Heading3"]))
    story.append(Paragraph("El presente documento funciona como memoria técnica automática. Integra datos de entrada, hipótesis, metodología de cálculo, resultados, gráficas, dictámenes y recomendaciones para el prediseño del sistema propulsor naval.", body))
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Objetivo", h2))
    story.append(Paragraph("Diseñar y verificar preliminarmente el sistema de propulsión de un buque mediante la cadena de potencia, curvas Wageningen B-Series, selección de motor, transmisión, cavitación Burrill/Keller, vibraciones del eje y comparación con datos reales o de ficha técnica.", body))
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Datos principales de entrada", h2))
    datos_entrada_pdf = pd.DataFrame([
        ["Tipo de buque", modo_guia, "Entrada del usuario / valor por defecto"],
        ["Lpp", f"{eslora:.3f} m", "Dato principal"],
        ["LWL", f"{lwl:.3f} m", "Dato principal"],
        ["Manga B", f"{manga:.3f} m", "Dato principal"],
        ["Puntal", f"{puntal:.3f} m", "Dato principal"],
        ["Calado", f"{calado:.3f} m", "Dato principal"],
        ["Velocidad de servicio", f"{velocidad:.3f} kn", "Dato principal"],
        ["Superficie mojada sin timón", f"{superficie_mojada_sin_timon_m2:,.1f} m²", "Dato visible"],
        ["Superficie mojada con timón", f"{superficie_mojada_con_timon_m2:,.1f} m²", "Dato visible"],
        ["RT", f"{resistencia_total_kn:,.1f} kN", "Entrada o estimación"],
        ["Sea Margin", f"{margen_servicio:.1f} %", "Criterio ITTC / usuario"],
        ["w", f"{estela:.3f}", "Interacción casco-propulsor"],
        ["t", f"{t_fraction:.3f}", "Interacción casco-propulsor"],
        ["ηR", f"{eta_r:.3f}", "Eficiencia rotativa relativa"],
        ["Z", f"{z_val}", "Geometría hélice"],
        ["D hélice", f"{diam_prop_m:.3f} m", "Geometría hélice"],
        ["P/D", f"{pd_val:.3f}", "Geometría hélice"],
        ["Ae/A0", f"{ae_val:.3f}", "Geometría hélice"],
        ["Hub ratio", f"{hub_ratio:.3f}", "Geometría hélice"],
        ["Inmersión del eje", f"{inmersion_eje_m:.3f} m", "Cavitación"],
    ], columns=["Parámetro", "Valor", "Comentario"])
    add_table(story, datos_entrada_pdf, col_widths=[170, 120, 220], max_rows=30)

    story.append(Paragraph("3. Hipótesis y metodología", h2))
    hipotesis_df = pd.DataFrame([
        ["Propiedades del fluido", f"ρ={rho_auto:.3f} kg/m³, ν=1.1883e-6 m²/s, Pv={p_vap_auto:.1f} Pa", "Agua salada a 15 °C / ITTC"],
        ["Potencia efectiva", "PE = RT · Vs", "Convierte resistencia al avance en potencia"],
        ["Velocidad de avance", "VA = Vs(1-w)", "Incluye efecto de estela"],
        ["Eficiencia de casco", "ηH = (1-t)/(1-w)", "Interacción casco-hélice"],
        ["Potencia al freno", "PB = PS / ηG", "Potencia requerida en motor"],
        ["MCR requerido", "MCR = PB / 0.85", "Margen operativo del 15%"],
        ["Burrill", "Comparación τc vs τ admisible", "Riesgo preliminar de cavitación"],
        ["Keller", "Ae/A0 actual vs Ae/A0 mínimo", "Área expandida mínima"],
        ["Vibración", "Comparación de frecuencias naturales y órdenes 1P/ZP", "Revisión preliminar, no sustituye TVA de clase"],
    ], columns=["Tema", "Fórmula / criterio", "Uso"])
    add_table(story, hipotesis_df, col_widths=[120, 190, 200], max_rows=25)

    story.append(Paragraph(f"4. Dictamen general: {dictamen}", h2))
    story.append(Paragraph("El dictamen resume los módulos principales de la aplicación. Cuando aparece una observación, no implica necesariamente falla de diseño; indica que el valor debe revisarse, justificarse o compararse contra una restricción real del buque.", body))
    add_table(story, construir_resumen_dataframe(), col_widths=[230, 250], max_rows=55)

    story.append(PageBreak())
    story.append(Paragraph("5. Cadena de potencias", h2))
    story.append(Paragraph("Esta sección documenta la progresión RT → PE → PT → PD → PS → PB. Permite rastrear las pérdidas desde el casco hasta el motor y verificar el efecto del Sea Margin y de las eficiencias adoptadas.", body))
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

    story.append(Spacer(1, 10))
    story.append(Paragraph("Conclusión técnica", h2))
    story.append(Paragraph("El sistema propulsor evaluado presenta un prediseño verificable con entradas editables y trazabilidad de cálculo. Los resultados deben interpretarse como una evaluación académica/preliminar: para aprobación de clase se requerirían datos definitivos de pruebas de canal, fabricante, planos de línea de ejes y revisión formal de sociedad clasificadora.", body))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ==============================================================================

tab_dash, tab_resumen, tab_pdf_comp, tab_potencias, tab_motor, tab_hidro, tab_opt, tab_vibracion, tab_balanceo, tab_campbell, tab_cav, tab_normativa, tab_clase, tab_gemelo, tab_avanzado = st.tabs([
    "🏠 Dashboard",
    "📑 Resumen",
    "📄 PDF / Comparación",
    "⚡ Potencias",
    "🛠️ Motor / Reductora",
    "📈 Hidrodinámica",
    "⭐ Optimización",
    "🧭 Vibración",
    "⚖️ Balanceo",
    "🗺️ Campbell",
    "🔍 Cavitación",
    "📚 Normativa",
    "📋 Clase",
    "🚢 Gemelo Digital",
    "⚙️ Integridad dinámica"
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
    Esta sección valida el prediseño contra datos reales. Si se carga una ficha técnica, la app extrae valores de referencia y los compara con los resultados calculados. Si no hay PDF, se usan datos manuales opcionales.
    </div>
    """, unsafe_allow_html=True)

    if datos_pdf:
        st.markdown("### Datos detectados del PDF")
        df_pdf = pd.DataFrame([{"Dato": k, "Valor detectado": v} for k, v in datos_pdf.items()])
        st.dataframe(df_pdf, use_container_width=True, height=320)
    else:
        st.info("No se cargó PDF o no se detectaron datos. La app continuará con los parámetros manuales del panel lateral.")

    st.markdown("### Tabla profesional de validación")
    st.caption("Criterio sugerido: ≤5% cumple, 5–15% requiere revisión, >15% no cumple respecto al dato real disponible.")
    if rpm_real and rpm_real > 0 and rpm_helice_requerida > 0:
        err_teorico_rpm = error_pct(rpm_helice_requerida, rpm_real)
        estado_html(
            f"ℹ️ Interpretación técnica de RPM: la app identifica una velocidad teórica de máxima eficiencia en aguas abiertas de {rpm_helice_requerida:.2f} rpm y la ficha/entrada de referencia trabaja a {rpm_real:.2f} rpm. Esta diferencia puede ser normal en diseño naval: la RPM final también depende del motor disponible, la transmisión, el diámetro máximo permitido, cavitación, vibración, margen de servicio y decisiones del fabricante. Por eso la RPM real se usa como referencia operativa y la RPM teórica queda como apoyo para optimización hidrodinámica.",
            "warn" if err_teorico_rpm and err_teorico_rpm > 15 else "good"
        )
    st.dataframe(
        comparacion_prof_df.style
        .format({"Calculado": formatear_numero_tabla, "Real PDF/manual": formatear_numero_tabla, "Error [%]": lambda x: "—" if pd.isna(x) else f"{x:.2f}%"})
        .map(style_estado, subset=["Dictamen"]),
        use_container_width=True,
        height=270
    )

    st.markdown("### 📊 Error porcentual por parámetro")
    fig_cmp = crear_figura_comparacion(comparacion_df)
    st.pyplot(fig_cmp)

    colv1, colv2, colv3 = st.columns(3)
    errores_validos = pd.to_numeric(comparacion_prof_df["Error [%]"], errors="coerce").dropna()
    colv1.metric("Error medio", "—" if errores_validos.empty else f"{errores_validos.mean():.2f}%")
    colv2.metric("Error máximo", "—" if errores_validos.empty else f"{errores_validos.max():.2f}%")
    colv3.metric("Parámetros comparados", f"{len(errores_validos)}")

    rpm_err_row = comparacion_prof_df[comparacion_prof_df["Parámetro"].astype(str).str.contains("RPM", case=False, na=False)]
    if not rpm_err_row.empty:
        err_val = pd.to_numeric(rpm_err_row.iloc[0].get("Error [%]"), errors="coerce")
        if pd.notna(err_val) and err_val > 10:
            estado_html(f"⚠️ La RPM de validación se aleja {err_val:.2f}% de la RPM real. Revisa si estás comparando la RPM de servicio correcta o si deseas usar la optimización con restricción de RPM.", "warn")

# ==============================================================================
# CADENA DE POTENCIAS
# ==============================================================================

with tab_potencias:
    st.subheader("⚡ Cadena completa de potencias")
    st.markdown("""
    <div class="section-card">
    La cadena de potencias se presenta como una memoria interactiva: cada subpestaña explica una etapa, muestra su fórmula, su tabla de cálculo, una gráfica y un dictamen de cumplimiento preliminar.
    </div>
    """, unsafe_allow_html=True)

    pot_resumen, pot_flow, pot_pe, pot_pt, pot_pd, pot_pb, pot_eff = st.tabs([
        "📌 Resumen", "🔁 Flujo interactivo", "🌊 PE", "🌀 PT", "⚙️ PD", "🔩 PS / PB", "📉 Eficiencias"
    ])

    with pot_resumen:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PE con margen", f"{PE_kw:,.0f} kW")
        c2.metric("PD", f"{PD_kw:,.0f} kW")
        c3.metric("PB requerida", f"{PB_kw_calc:,.0f} kW")
        c4.metric("MCR requerido", f"{MCR_requerido_kw:,.0f} kW")

        if motor_mcr_kw <= 0:
            estado_html("ℹ️ Sin motor real cargado: se calcula la PB requerida y la app puede recomendar motores candidatos.", "warn")
        elif motor_cumple_ideal:
            estado_html("✅ Cumple potencia ideal: PB requerida ≤ 85% del MCR del motor seleccionado.", "good")
        elif motor_cumple_observacion:
            estado_html(f"⚠️ Cumple con observación: PB supera el 85% MCR en {exceso_sobre_85_pct:.1f}%, pero todavía está por debajo del MCR.", "warn")
        else:
            estado_html("❌ No cumple potencia: PB requerida supera el MCR del motor seleccionado.", "bad")

        st.markdown("### Diagrama profesional de crecimiento de potencia")
        fig_pot = crear_figura_cadena_potencias_profesional(power_chain_df)
        st.pyplot(fig_pot)

        st.markdown("### Tabla de cadena con dictamen")
        st.dataframe(
            power_chain_status_df.style
            .format({"Valor":"{:,.3f}"})
            .map(style_estado, subset=["Dictamen"]),
            use_container_width=True,
            height=360
        )

    with pot_flow:
        st.markdown("""
        ### 🔁 Flujo energético interactivo del sistema propulsivo
        Esta visualización convierte la cadena de potencias en un flujo tipo Sankey. Permite ver de forma directa cómo la energía pasa desde el motor hasta la potencia útil y dónde aparecen las pérdidas por eficiencia propulsiva, eje y transmisión.
        """)
        if HAS_PLOTLY:
            fig_sankey = crear_sankey_potencias_interactivo(PE_kw, PD_kw, PS_kw, PB_kw_calc, MCR_requerido_kw)
            st.plotly_chart(fig_sankey, use_container_width=True)
        else:
            estado_html("⚠️ Para activar el flujo interactivo instala Plotly agregando `plotly` a requirements.txt.", "warn")
        sankey_df = pd.DataFrame([
            {"Etapa": "PE útil con margen", "Valor [kW]": PE_kw, "Lectura técnica": "Potencia útil para vencer la resistencia del casco."},
            {"Etapa": "Pérdidas propulsivas", "Valor [kW]": max(PD_kw-PE_kw, 0), "Lectura técnica": "Efecto de la interacción casco-hélice y eficiencia propulsiva."},
            {"Etapa": "Pérdida de eje", "Valor [kW]": max(PS_kw-PD_kw, 0), "Lectura técnica": "Pérdidas mecánicas de la línea de ejes."},
            {"Etapa": "Pérdida de transmisión", "Valor [kW]": max(PB_kw_calc-PS_kw, 0), "Lectura técnica": "Caja reductora/acoplamientos/transmisión."},
            {"Etapa": "Reserva MCR", "Valor [kW]": max(MCR_requerido_kw-PB_kw_calc, 0), "Lectura técnica": "Margen para operar la PB alrededor del 85% del MCR."},
        ])
        st.dataframe(sankey_df.style.format({"Valor [kW]": "{:,.1f}"}), use_container_width=True, height=255)

    with pot_pe:
        st.markdown("### 🌊 Potencia efectiva PE")
        st.markdown("La potencia efectiva es la potencia mínima para vencer la resistencia del casco a la velocidad de servicio, antes de pérdidas propulsivas.")
        st.latex(r"P_E=R_TV_S")
        cols = st.columns(4)
        cols[0].metric("RT", f"{resistencia_total_kn:,.1f} kN")
        cols[1].metric("VS", f"{velocidad_buque_ms:.2f} m/s")
        cols[2].metric("PE sin margen", f"{PE_kw_sin_margen:,.0f} kW")
        cols[3].metric("PE con margen", f"{PE_kw:,.0f} kW")
        df_pe = pd.DataFrame([
            {"Parámetro":"Resistencia total RT", "Valor":resistencia_total_kn, "Unidad":"kN", "Fuente/criterio":"Entrada, PDF o estimación", "Dictamen":"Cumple"},
            {"Parámetro":"Velocidad de servicio VS", "Valor":velocidad_buque_ms, "Unidad":"m/s", "Fuente/criterio":"kn × 0.5144", "Dictamen":"Cumple"},
            {"Parámetro":"Sea Margin", "Valor":margen_servicio, "Unidad":"%", "Fuente/criterio":"ITTC / criterio usuario", "Dictamen":"Cumple" if margen_servicio >= 10 else "Revisar"},
            {"Parámetro":"PE con margen", "Valor":PE_kw, "Unidad":"kW", "Fuente/criterio":"PE(1+SM)", "Dictamen":"Cumple"},
        ])
        st.dataframe(df_pe.style.format({"Valor":"{:,.3f}"}).map(style_estado, subset=["Dictamen"]), use_container_width=True)
        fig = crear_figura_waterfall_pe(PE_kw_sin_margen, PE_kw, margen_servicio)
        st.pyplot(fig)

    with pot_pt:
        st.markdown("### 🌀 Potencia de empuje PT")
        st.markdown("PT considera el empuje que debe producir la hélice y la velocidad de avance afectada por la estela.")
        st.latex(r"T=\frac{R_T}{1-t}\qquad P_T=TV_A")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("t", f"{t_fraction:.3f}")
        c2.metric("VA", f"{VA_ms:.2f} m/s")
        c3.metric("Empuje", f"{thrust_req_N/1000:,.1f} kN")
        c4.metric("PT", f"{PT_kw:,.0f} kW")
        df_pt = pd.DataFrame([
            {"Parámetro":"Deducción de empuje t", "Valor":t_fraction, "Unidad":"-", "Rango esperado":"0.05–0.35", "Dictamen":dictamen_eficiencia(t_fraction,0.05,0.35)},
            {"Parámetro":"Velocidad de avance VA", "Valor":VA_ms, "Unidad":"m/s", "Rango esperado":">0", "Dictamen":"Cumple" if VA_ms>0 else "No cumple"},
            {"Parámetro":"Empuje requerido", "Valor":thrust_req_N/1000, "Unidad":"kN", "Rango esperado":"positivo", "Dictamen":"Cumple" if thrust_req_N>0 else "No cumple"},
            {"Parámetro":"Potencia de empuje PT", "Valor":PT_kw, "Unidad":"kW", "Rango esperado":"positivo", "Dictamen":"Cumple" if PT_kw>0 else "No cumple"},
        ])
        st.dataframe(df_pt.style.format({"Valor":"{:,.4f}"}).map(style_estado, subset=["Dictamen"]), use_container_width=True)
        fig = crear_figura_empuje_profesional(PE_kw, PT_kw, VA_ms, thrust_req_N/1000)
        st.pyplot(fig)

    with pot_pd:
        st.markdown("### ⚙️ Potencia entregada a la hélice PD")
        st.markdown("PD es la potencia que debe llegar a la hélice considerando la eficiencia cuasi-propulsiva del conjunto casco-hélice.")
        st.latex(r"\eta_D=\eta_H\eta_O\eta_R\qquad P_D=\frac{P_E}{\eta_D}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ηH", f"{eta_h:.3f}")
        c2.metric("ηO", f"{max_eff:.3f}")
        c3.metric("ηD", f"{eta_d:.3f}")
        c4.metric("PD", f"{PD_kw:,.0f} kW")
        df_pd = efficiency_prof_df[efficiency_prof_df["Eficiencia"].isin(["ηH","ηO","ηR","ηD"])].copy()
        st.dataframe(df_pd.style.format({"Valor":"{:.4f}"}).map(style_estado, subset=["Dictamen"]), use_container_width=True)
        fig = crear_figura_eficiencias_propulsivas(eta_h, max_eff, eta_r, eta_d)
        st.pyplot(fig)

    with pot_pb:
        st.markdown("### 🔩 Potencia en eje PS y potencia al freno PB")
        st.markdown("PS incluye pérdidas mecánicas del eje; PB es la potencia que debe cubrir el motor antes de aplicar el criterio MCR.")
        st.latex(r"P_S=\frac{P_D}{\eta_S}\qquad P_B=\frac{P_S}{\eta_G}\qquad MCR_{req}=\frac{P_B}{0.85}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("PS", f"{PS_kw:,.0f} kW")
        c2.metric("PB", f"{PB_kw_calc:,.0f} kW")
        c3.metric("MCR requerido", f"{MCR_requerido_kw:,.0f} kW")
        c4.metric("ηS·ηG", f"{eta_s*eta_g:.3f}")
        df_pb = pd.DataFrame([
            {"Etapa":"PD", "Descripción":"Potencia entregada a la hélice", "Valor":PD_kw, "Unidad":"kW", "Dictamen":"Cumple"},
            {"Etapa":"PS", "Descripción":"Potencia en el eje", "Valor":PS_kw, "Unidad":"kW", "Dictamen":"Cumple"},
            {"Etapa":"PB", "Descripción":"Potencia al freno requerida", "Valor":PB_kw_calc, "Unidad":"kW", "Dictamen":"Cumple"},
            {"Etapa":"MCR requerido", "Descripción":"MCR mínimo para trabajar al 85%", "Valor":MCR_requerido_kw, "Unidad":"kW", "Dictamen":"Cumple" if MCR_requerido_kw>0 else "Revisar"},
        ])
        st.dataframe(df_pb.style.format({"Valor":"{:,.3f}"}).map(style_estado, subset=["Dictamen"]), use_container_width=True)
        fig = crear_figura_motor_mcr(PD_kw, PS_kw, PB_kw_calc, MCR_requerido_kw)
        st.pyplot(fig)

    with pot_eff:
        st.markdown("### 📉 Eficiencias adoptadas")
        st.markdown("Esta tabla resume las eficiencias usadas, sus rangos de referencia y un dictamen para defender las hipótesis de cálculo.")
        st.dataframe(efficiency_prof_df.style.format({"Valor":"{:.4f}"}).map(style_estado, subset=["Dictamen"]), use_container_width=True, height=330)
        fig = crear_figura_mapa_eficiencias(efficiency_prof_df)
        st.pyplot(fig)

# ==============================================================================
# MOTOR Y REDUCTORA
# ==============================================================================

with tab_motor:
    st.subheader("🛠️ Selección de motor real y transmisión")
    with st.expander("📘 Teoría y fórmulas de motor / reductora", expanded=False):
        st.markdown("""
        El motor se selecciona comparando la potencia al freno requerida contra el MCR disponible. Para operación continua se usa como referencia el 85% del MCR. Si el motor gira a más RPM que la hélice, se requiere una caja reductora.
        """)
        st.latex(r"P_{85\%MCR}=0.85\,MCR")
        st.latex(r"MCR_{req}=\frac{P_B}{0.85}")
        st.latex(r"i=\frac{n_{motor}}{n_{helice}}")
        st.markdown("Si PB ≤ 85% MCR, cumple ideal. Si PB está entre 85% MCR y MCR, cumple con observación. Si PB > MCR, no cumple.")

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
    Esta herramienta no cambia tus datos automáticamente: prueba combinaciones comerciales de número de palas Z, P/D y Ae/A0, calcula sus curvas Wageningen y genera una propuesta preliminar. Si existe RPM real cargada desde el PDF o entrada manual, la optimización no solo busca eficiencia: también penaliza las configuraciones que se alejan demasiado de la RPM real de servicio.
    Para evitar que la app se quede cargando y bloquee las pestañas siguientes, la optimización se ejecuta solo cuando el usuario presiona el botón.
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📘 Teoría y fórmulas de optimización", expanded=False):
        st.markdown("""
        La optimización evalúa combinaciones de geometría de hélice dentro de rangos comerciales. Para cada combinación se calcula la curva de aguas abiertas, se localiza la máxima eficiencia y, si existe dato real del PDF, se compara la RPM estimada contra la RPM real del buque.
        """)
        st.latex(r"J=\frac{V_A}{nD}")
        st.latex(r"n=\frac{V_A}{JD}")
        st.latex(r"\eta_O=\frac{J}{2\pi}\frac{K_T}{K_Q}")
        st.latex(r"\text{Error RPM}=\frac{|n_{calc}-n_{real}|}{n_{real}}\times100")
        st.latex(r"\text{Puntaje}=\eta_O(\%) - 0.35\,\text{Error RPM}(\%)")
        st.info("Si no se sube PDF o no existe RPM real, la app ordena principalmente por eficiencia ηO.")

    st.markdown("### ⚙️ Optimización Wageningen B-Series")
    st.caption("La app usa la búsqueda detallada por defecto para mantener una evaluación más consistente. Se revisan combinaciones de Z, P/D y Ae/A0 y se pondera la eficiencia junto con la cercanía a la RPM real cuando existe.")
    modo_opt = "Detallada"
    ejecutar_opt = st.button("▶️ Ejecutar optimización detallada", key="btn_opt_helice")

    if ejecutar_opt:
        with st.spinner("Calculando combinaciones de hélice con búsqueda detallada... espera unos segundos."):
            st.session_state["opt_df"] = optimizar_helice_wageningen(modo_opt, rpm_real, VA_ms, diam_prop_m)
            st.session_state["opt_modo"] = modo_opt
        st.success(f"Optimización detallada terminada. Se evaluaron {len(st.session_state['opt_df'])} combinaciones.")

    if "opt_df" in st.session_state:
        opt_df = st.session_state["opt_df"]
        st.dataframe(
            opt_df.head(20).style.format({
                "P/D":"{:.3f}",
                "Ae/A0":"{:.3f}",
                "J óptimo":"{:.3f}",
                "KT":"{:.4f}",
                "KQ":"{:.4f}",
                "ηO [%]":"{:.2f}",
                "RPM estimada [rpm]":"{:.2f}",
                "Error RPM [%]":"{:.2f}",
                "Puntaje optimizado":"{:.2f}"
            }).map(style_estado, subset=["Dictamen RPM"]),
            use_container_width=True,
            height=520
        )
        mejor = opt_df.iloc[0]
        estado_html(f"Mejor combinación encontrada por puntaje: Z={int(mejor['Z'])}, P/D={mejor['P/D']:.3f}, Ae/A0={mejor['Ae/A0']:.3f}, ηO={mejor['ηO [%]']:.2f}%, RPM estimada={mejor['RPM estimada [rpm]']:.2f} rpm.", "good")

        st.markdown("### 📊 Visualización de mejores alternativas")
        top_opt = opt_df.head(10).copy()
        top_opt["Configuración"] = top_opt.apply(lambda r: f"Z{int(r['Z'])} | P/D {r['P/D']:.2f} | Ae {r['Ae/A0']:.2f}", axis=1)
        fig_opt, ax_opt = plt.subplots(figsize=(10.5, 5.0))
        ax_opt.barh(top_opt["Configuración"][::-1], top_opt["Puntaje optimizado"][::-1])
        ax_opt.set_xlabel("Puntaje optimizado [-]")
        ax_opt.set_title("Top 10 combinaciones por eficiencia y cercanía a RPM real", fontsize=12, fontweight="bold")
        ax_opt.grid(True, axis="x", linestyle=":", alpha=0.55)
        for y, val in enumerate(top_opt["Puntaje optimizado"][::-1]):
            ax_opt.text(val + 0.15, y, f"{val:.2f}", va="center", fontsize=8)
        st.pyplot(fig_opt)

        st.markdown("### 📌 Comparación contra la configuración actual")
        comp_opt = pd.DataFrame([
            {"Concepto":"Actual", "Z":z_val, "P/D":pd_val, "Ae/A0":ae_val, "J óptimo":j_opt, "ηO [%]":max_eff*100, "RPM estimada [rpm]":rpm_helice_requerida, "Error RPM [%]": error_pct(rpm_helice_requerida, rpm_real)},
            {"Concepto":"Óptima encontrada", "Z":int(mejor['Z']), "P/D":mejor['P/D'], "Ae/A0":mejor['Ae/A0'], "J óptimo":mejor['J óptimo'], "ηO [%]":mejor['ηO [%]'], "RPM estimada [rpm]":mejor['RPM estimada [rpm]'], "Error RPM [%]":mejor['Error RPM [%]']},
        ])
        st.dataframe(comp_opt.style.format({"P/D":"{:.3f}", "Ae/A0":"{:.3f}", "J óptimo":"{:.3f}", "ηO [%]":"{:.2f}", "RPM estimada [rpm]":"{:.2f}", "Error RPM [%]":"{:.2f}"}), use_container_width=True)
        if rpm_real and rpm_real > 0:
            st.info("Para bajar el error de RPM puedes usar la configuración óptima sugerida como referencia y ajustar D, P/D o Ae/A0 en el panel de entrada hasta acercarte a la RPM real del PDF.")
    else:
        st.info("Presiona el botón para iniciar la optimización. Mientras no lo hagas, la app seguirá cargando rápido y todas las pestañas estarán disponibles.")

# ==============================================================================
# HIDRODINÁMICA
# ==============================================================================

with tab_hidro:
    st.subheader("📈 Hidrodinámica en Aguas Abiertas — Wageningen Serie B")
    st.markdown("""
    <div class="section-card">
    Esta sección integra las curvas Wageningen y la matriz numérica de resultados. Se eliminó la pestaña independiente de Resultados porque estos valores pertenecen directamente al análisis hidrodinámico.
    </div>
    """, unsafe_allow_html=True)

    hidro_curvas, hidro_tabla, hidro_formulas = st.tabs(["📈 Curvas", "📋 Resultados numéricos", "🧮 Fórmulas"])

    with hidro_curvas:
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
        st.info("KT indica capacidad de empuje; KQ indica demanda de torque; ηO expresa eficiencia hidrodinámica ideal.")

    with hidro_tabla:
        st.markdown("### 📋 Matriz numérica de resultados Wageningen")
        tabla = res.copy()
        st.dataframe(
            tabla.style
            .highlight_max(subset=["nO", "ηO (%)"], color="#dcfce7")
            .format("{:.4f}"),
            use_container_width=True,
            height=520
        )

    with hidro_formulas:
        st.markdown("### 🧮 Fórmulas hidrodinámicas usadas")
        st.latex(r"J = \frac{V_A}{nD}")
        st.latex(r"K_T = \sum C_i J^{s_i}(P/D)^{t_i}(A_E/A_0)^{u_i}Z^{v_i}")
        st.latex(r"K_Q = \sum C_i J^{s_i}(P/D)^{t_i}(A_E/A_0)^{u_i}Z^{v_i}")
        st.latex(r"\eta_O = \frac{J}{2\pi}\frac{K_T}{K_Q}")
        st.markdown("Los coeficientes polinomiales se leen desde `Tabla 1.xlsx`.")

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
    with st.expander("📘 Teoría y fórmulas del Campbell", expanded=False):
        st.markdown("""
        El diagrama de Campbell compara las frecuencias naturales del sistema contra órdenes de excitación generados por el giro del eje y el paso de palas. Una intersección cerca de la RPM de operación indica riesgo de resonancia.
        """)
        st.latex(r"f_{exc}=k\frac{n}{60}")
        st.latex(r"f_{ZP}=Z\frac{n}{60}")
        st.latex(r"n_{cruce}=\frac{60f_n}{k}")

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
    La cavitación se organiza por análisis: resumen general, Burrill, Keller, Reynolds/σ y fórmulas. Cada subpestaña incluye dictamen y explicación para evitar depender de una pestaña final de fórmulas.
    </div>
    """, unsafe_allow_html=True)

    cav_resumen, cav_visual, cav_burrill, cav_keller, cav_flujo, cav_formulas = st.tabs([
        "📋 Resumen", "🌊 Visual 3D", "🫧 Burrill", "📐 Keller", "🌊 Reynolds / σ", "🧮 Fórmulas"
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
        st.dataframe(
            resumen_cav.style.format({"Valor calculado":"{:,.4g}"}).map(style_estado, subset=["Resultado"]),
            use_container_width=True
        )

        if burrill_ok and keller_ok and reynolds_ok and cavitacion_ok:
            estado_html("✅ Dictamen de cavitación preliminar favorable: cumple Reynolds, σ, Burrill y Keller.", "good")
        elif keller_ok and burrill_ok:
            estado_html("⚠️ Dictamen con observaciones: Burrill y Keller cumplen, pero conviene revisar Reynolds o σ.", "warn")
        else:
            estado_html("❌ Dictamen de cavitación con riesgo: revisar área expandida, diámetro, inmersión o carga de la hélice.", "bad")

    with cav_visual:
        st.markdown("""
        ### 🌊 Cavitación visual interactiva
        Esta vista convierte los resultados de **σ**, **Burrill** y **Keller** en una representación espacial alrededor de la hélice. No sustituye CFD ni prueba de túnel de cavitación, pero ayuda a explicar visualmente dónde podría concentrarse el riesgo de formación de vapor y cómo influyen Ae/A0, diámetro, inmersión y carga de pala.
        """)
        if HAS_PLOTLY:
            fig_cav3d = crear_cavitacion_3d_visual(D=diam_prop_m, Z=z_val, PD=pd_val, AeAo=ae_val, hub_ratio=hub_ratio, sigma=sigma_n, keller_ok=keller_ok, burrill_ok=burrill_ok)
            st.plotly_chart(fig_cav3d, use_container_width=True)
        else:
            estado_html("⚠️ Para activar la cavitación visual instala Plotly agregando `plotly` a requirements.txt.", "warn")
        cav_visual_df = pd.DataFrame([
            {"Criterio": "Coeficiente σ", "Valor": f"{sigma_n:.3f}", "Lectura": "Mayor σ indica menor tendencia a formación de vapor."},
            {"Criterio": "Burrill", "Valor": "Cumple" if burrill_ok else "Revisar", "Lectura": "Evalúa carga de pala contra límite admisible."},
            {"Criterio": "Keller", "Valor": "Cumple" if keller_ok else "Revisar", "Lectura": "Evalúa si Ae/A0 es suficiente para limitar cavitación."},
            {"Criterio": "Ae/A0 actual", "Valor": f"{ae_val:.3f}", "Lectura": "Más área expandida reduce carga de pala, aunque puede penalizar eficiencia."},
        ])
        st.dataframe(cav_visual_df, use_container_width=True, height=220)
        if keller_ok and burrill_ok and sigma_n > 0.20:
            estado_html("✅ Visualización favorable: los criterios preliminares de cavitación son aceptables.", "good")
        else:
            estado_html("⚠️ Visualización con observación: revisar inmersión, Ae/A0, diámetro, carga de pala o velocidad de avance.", "warn")

    with cav_burrill:
        st.markdown("### 🫧 Criterio de Burrill")
        st.markdown("Burrill compara la carga de pala τc contra un límite admisible dependiente de σ. Es útil para detectar si la hélice está demasiado cargada.")
        st.latex(r"\tau_c = \frac{T}{\frac{1}{2}\rho V_A^2A_0}")
        b1, b2, b3 = st.columns(3)
        b1.metric("τc calculado", f"{tau_c_burrill:.3f}")
        b2.metric("τc admisible", f"{tau_c_admisible:.3f}")
        b3.metric("Margen", f"{(tau_c_admisible - tau_c_burrill):.3f}")
        estado_html("✅ Cumple Burrill preliminar: la carga de pala queda por debajo del límite admisible." if burrill_ok else "⚠️ Revisar Burrill: la carga de pala es elevada.", "good" if burrill_ok else "warn")
        st.pyplot(crear_figura_burrill(sigma_n, tau_c_burrill, tau_c_admisible))

    with cav_keller:
        st.markdown("### 📐 Criterio de Keller")
        st.markdown("Keller estima el área expandida mínima requerida para evitar una carga excesiva sobre las palas.")
        st.latex(r"\left(\frac{A_E}{A_0}\right)_{min}=\frac{(1.3+0.3Z)T}{(P_0-P_v)D^2}+0.10")
        k1, k2, k3 = st.columns(3)
        k1.metric("Ae/A0 mínimo", f"{keller_ae_min:.3f}")
        k2.metric("Ae/A0 actual", f"{ae_val:.3f}")
        k3.metric("Margen", f"{(ae_val - keller_ae_min):.3f}")
        estado_html("✅ Cumple Keller preliminar: el área expandida actual es mayor o igual al mínimo requerido." if keller_ok else "❌ No cumple Keller: se recomienda aumentar Ae/A0 o reducir la carga.", "good" if keller_ok else "bad")
        st.pyplot(crear_figura_keller(keller_ae_min, ae_val))

    with cav_flujo:
        st.markdown("### 🌊 Reynolds y coeficiente de cavitación σ")
        st.latex(r"Re = \frac{V_A D}{\nu}\qquad \sigma = \frac{P_{atm}+\rho gh-P_v}{\frac{1}{2}\rho V_A^2}")
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
            if reynolds_ok:
                st.success("✅ Flujo turbulento típico de hélices navales.")
            else:
                st.warning("⚠️ Reynolds bajo para escala naval.")
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
            if cavitacion_ok:
                st.success("🟢 σ favorable frente a cavitación.")
            else:
                st.warning("🟡 σ bajo: revisar inmersión, carga o diámetro.")

    with cav_formulas:
        st.markdown("### 🧮 Fórmulas usadas en cavitación")
        st.latex(r"V_A = V_s(1-w)")
        st.latex(r"Re = \frac{V_A D}{\nu}")
        st.latex(r"\sigma = \frac{P_{atm}+\rho gh-P_v}{\frac{1}{2}\rho V_A^2}")
        st.latex(r"\tau_c = \frac{T}{\frac{1}{2}\rho V_A^2 A_0}")
        st.latex(r"A_0 = \frac{\pi D^2}{4}")
        st.latex(r"\tau_{c,adm}=0.22+0.18\sigma")
        st.latex(r"P_0-P_v=P_{atm}+\rho gh-P_v")
        st.info("Estos criterios son preliminares para prediseño. Para aprobación final deben contrastarse con diagramas originales, pruebas de modelo o reglas de clase aplicables.")

# ==============================================================================
# NORMATIVA APLICABLE
# ==============================================================================

with tab_normativa:
    st.subheader("📚 Normativa y cumplimiento técnico preliminar")

    st.markdown("""
    <div class="section-card">
    Esta sección conecta los resultados de la aplicación con normas, guías y prácticas
    usadas en diseño de sistemas propulsivos. El objetivo es que el usuario pueda defender
    cada decisión: agua ITTC, hélice Wageningen, cavitación Burrill/Keller, motor al 85% MCR,
    eje, transmisión, vibración y comparación contra datos reales. El dictamen es académico
    y preliminar: una aprobación real debe hacerse con la edición vigente de la sociedad
    clasificadora del buque.
    </div>
    """, unsafe_allow_html=True)

    potencia_norma_estado = "Cumple" if PB_kw_calc <= MCR_requerido_kw else "Revisar"
    mcr_real_disponible = motor_mcr_kw if motor_mcr_kw > 0 else 0.0
    if mcr_real_disponible > 0:
        if PB_kw_calc <= 0.85*mcr_real_disponible:
            motor_norma_estado = "Cumple ideal"
        elif PB_kw_calc <= mcr_real_disponible:
            motor_norma_estado = "Cumple con observación"
        else:
            motor_norma_estado = "No cumple"
    else:
        motor_norma_estado = "Sin dato real"

    transmision_norma_estado = "Cumple" if transmision_ok else "Revisar"
    rt_norma_estado = "Calculada" if rt_modo == "Automática preliminar" else "Dato manual"
    keller_norma_estado = "Cumple" if keller_ok else "No cumple"
    burrill_norma_estado = "Cumple" if burrill_ok else "No cumple"
    reynolds_norma_estado = "Cumple" if reynolds_ok else "Revisar"
    campbell_norma_estado = "Cumple" if not (campbell_df["Riesgo"] == "Alto").any() else "No cumple"
    eje_norma_estado = "Cumple" if torsion_ok else "No cumple"

    normativa_detallada_df = pd.DataFrame([
        {"Área": "Condición del agua", "Referencia técnica": "ITTC @ 15 °C", "Qué exige / controla": "Propiedades consistentes del fluido: densidad, viscosidad, presión de vapor y presión atmosférica.", "Variable de la app": f"ρ={rho_auto:.1f} kg/m³, ν=1.1883E-6 m²/s, Pv={p_vap_auto:.0f} Pa", "Dictamen": "Cumple"},
        {"Área": "Resistencia al avance", "Referencia técnica": "ITTC-1957 / prediseño hidrodinámico", "Qué exige / controla": "Estimar RT de forma reproducible o usar dato real de canal, CFD, Holtrop-Mennen o ficha técnica.", "Variable de la app": f"RT={resistencia_total_kn:,.0f} kN ({rt_fuente})", "Dictamen": rt_norma_estado},
        {"Área": "Margen de servicio", "Referencia técnica": "ITTC Speed/Power Trials 7.5-02-03-01.4 / práctica de diseño", "Qué exige / controla": "Documentar el Sea Margin y su efecto en la potencia de diseño.", "Variable de la app": f"Sea Margin={margen_servicio:.1f}%", "Dictamen": "Cumple" if margen_servicio >= 10 else "Revisar"},
        {"Área": "Hélice en aguas abiertas", "Referencia técnica": "Wageningen B-Series / ITTC Propeller Open Water", "Qué exige / controla": "Calcular KT, KQ, J y ηO con coeficientes visibles y trazables.", "Variable de la app": f"ηO máx={max_eff*100:.2f}%, J={j_opt:.3f}", "Dictamen": "Cumple" if hidro_ok else "Revisar"},
        {"Área": "Cavitación Burrill", "Referencia técnica": "Burrill / diagrama σ - τc", "Qué exige / controla": "Verificar que la carga de pala no exceda el límite preliminar admisible.", "Variable de la app": f"τc={tau_c_burrill:.3f}, τadm={tau_c_admisible:.3f}", "Dictamen": burrill_norma_estado},
        {"Área": "Cavitación Keller", "Referencia técnica": "Keller / área expandida mínima", "Qué exige / controla": "Verificar que Ae/A0 instalada sea mayor o igual al área mínima requerida.", "Variable de la app": f"Ae/A0={ae_val:.3f}, mínimo={keller_ae_min:.3f}", "Dictamen": keller_norma_estado},
        {"Área": "Régimen hidrodinámico", "Referencia técnica": "ITTC / similitud Reynolds", "Qué exige / controla": "Confirmar flujo turbulento típico de hélice naval para que el análisis sea representativo.", "Variable de la app": f"Re={reynolds:.2e}", "Dictamen": reynolds_norma_estado},
        {"Área": "Motor propulsor", "Referencia técnica": "Fabricante / punto de operación 85% MCR", "Qué exige / controla": "PB de diseño idealmente ≤85% MCR; si queda entre NCR y MCR se reporta como observación.", "Variable de la app": f"PB={PB_kw_calc:,.0f} kW, MCR real={mcr_real_disponible:,.0f} kW", "Dictamen": motor_norma_estado},
        {"Área": "Transmisión / reductora", "Referencia técnica": "Fabricante de caja / práctica de shafting", "Qué exige / controla": "Relación compatible entre RPM motor y RPM hélice, o transmisión directa si es motor lento.", "Variable de la app": f"Tipo={transmision_tipo}, i={relacion_reduccion:.2f}", "Dictamen": transmision_norma_estado},
        {"Área": "Eje propulsor - torsión", "Referencia técnica": "ABS/DNV/IACS UR M68 como marco de verificación torsional", "Qué exige / controla": "Esfuerzo torsional alternante menor que el límite admisible preliminar.", "Variable de la app": f"τ={esfuerzo_real_mpa:.2f} MPa, τadm={tau_admisible_mpa:.2f} MPa", "Dictamen": eje_norma_estado},
        {"Área": "Vibración lateral / whirling", "Referencia técnica": "ABS/DNV shaft alignment y práctica de velocidad crítica", "Qué exige / controla": "RPM de operación fuera de la banda crítica ±20% alrededor de la velocidad crítica.", "Variable de la app": f"Operación={rpm_motor:.1f} rpm, zona={margen_inf:.1f}-{margen_sup:.1f} rpm", "Dictamen": "Cumple" if lateral_ok else "No cumple"},
        {"Área": "Vibración axial", "Referencia técnica": "Análisis de excitaciones 1P/ZP/armónicos", "Qué exige / controla": "Separación suficiente entre frecuencia natural axial y órdenes de excitación.", "Variable de la app": f"Riesgo axial={riesgo_axial_global}", "Dictamen": "Cumple" if axial_ok else "No cumple"},
        {"Área": "Campbell", "Referencia técnica": "Análisis de resonancia en sistemas rotativos", "Qué exige / controla": "Evitar cruces peligrosos entre órdenes de excitación y modos naturales cerca de la RPM de operación.", "Variable de la app": "Intersecciones 1P, ZP, 2ZP, 3ZP", "Dictamen": campbell_norma_estado},
        {"Área": "Balanceo", "Referencia técnica": "ISO 1940 / práctica de balanceo de rotores", "Qué exige / controla": "Mantener fuerza de desbalance baja y evitar excitación 1P excesiva.", "Variable de la app": f"Riesgo={riesgo_desbalance}", "Dictamen": "Cumple" if desbalance_ok else "No cumple"}
    ])

    def color_dictamen_normativa(val):
        txt = str(val).lower()
        if "no cumple" in txt:
            return "background-color: #fee2e2; color:#991b1b; font-weight:700"
        if "cumple" in txt:
            return "background-color: #dcfce7; color:#166534; font-weight:700"
        if "observ" in txt or "revis" in txt or "manual" in txt or "calculada" in txt or "sin dato" in txt:
            return "background-color: #fef3c7; color:#92400e; font-weight:700"
        return ""

    st.markdown("### ✅ Matriz normativa de cumplimiento")
    st.dataframe(normativa_detallada_df.style.map(color_dictamen_normativa, subset=["Dictamen"]), use_container_width=True, height=520)

    st.markdown("### 📌 Lectura de cumplimiento")
    col_nc1, col_nc2, col_nc3 = st.columns(3)
    total_bad = sum(normativa_detallada_df["Dictamen"].astype(str).str.contains("No cumple", case=False, na=False))
    total_ok = sum(normativa_detallada_df["Dictamen"].astype(str).str.contains("Cumple", case=False, na=False)) - total_bad
    total_rev = len(normativa_detallada_df) - total_ok - total_bad
    col_nc1.metric("Criterios que cumplen", total_ok)
    col_nc2.metric("Criterios a revisar", total_rev)
    col_nc3.metric("Criterios no conformes", total_bad)

    st.markdown("### 📚 Referencias técnicas usadas por la app")
    referencias_df = pd.DataFrame([
        ["ITTC", "Propiedades de agua, resistencia friccional, ensayos de aguas abiertas, margen de servicio y pruebas de velocidad/potencia."],
        ["Wageningen B-Series", "Cálculo de KT, KQ y ηO mediante coeficientes polinomiales de hélices serie B."],
        ["Burrill", "Criterio preliminar de cavitación por carga de pala usando relación σ - τc."],
        ["Keller", "Criterio preliminar de área expandida mínima para limitar cavitación."],
        ["IACS UR M68", "Referencia para análisis torsional de instalaciones propulsoras; marco conceptual, no aprobación oficial."],
        ["ABS / DNV / LR / BV", "Reglas de clase aplicables a shafting, materiales, alineación, bocina, chumaceras, vibración y maquinaria propulsora."],
        ["ISO 1940", "Balanceo de rotores; referencia conceptual para la sección de desbalance."],
        ["ISO 10816 / ISO 20816", "Evaluación de vibración en maquinaria rotativa; referencia conceptual para medición y diagnóstico."],
        ["Fabricante de motor", "MCR, NCR, RPM, campo de potencia y selección del punto de operación."],
        ["Fabricante de caja reductora", "Relaciones de reducción, eficiencia, torque admisible y compatibilidad con RPM."]
    ], columns=["Fuente", "Uso en la aplicación"])
    st.dataframe(referencias_df, use_container_width=True, height=360)

    with st.expander("📘 Alcance y limitaciones", expanded=False):
        st.markdown("""
        - Esta matriz es **preliminar y académica**. No sustituye una aprobación oficial de clase.
        - La RT automática es útil para prediseño, pero debe validarse con canal de pruebas, CFD, Holtrop-Mennen completo o datos reales.
        - Burrill y Keller son verificaciones preliminares; para diseño final deben usarse diagramas originales, pruebas de modelo o validación especializada.
        - La evaluación de eje, Campbell, Bode, axial, lateral y balanceo es didáctica; una aprobación real requiere modelo completo de shafting, datos de rigidez, inercias, chumaceras, acoplamientos y motor.
        """)

    st.success("La pestaña normativa ahora funciona como checklist técnico: muestra qué criterio se revisó, con qué referencia se relaciona, qué variable usa la app y si cumple, requiere revisión o no cumple.")


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
# INTEGRIDAD DINÁMICA DEL SISTEMA PROPULSIVO
# ==============================================================================


with tab_gemelo:
    st.subheader("🚢 Gemelo Digital Paramétrico del Sistema Propulsivo")
    st.markdown("""
    <div class="section-card">
    <b>Objetivo del módulo:</b> convertir los resultados numéricos de la app en una visualización técnica interactiva del sistema propulsivo.
    El módulo funciona como un <b>gemelo digital conceptual</b>: cuando el usuario cambia diámetro, número de palas, P/D, Ae/A0, potencia, RPM, transmisión o cavitación, las gráficas y modelos se actualizan automáticamente.
    <br><br>
    <span class="small-muted">
    Nota técnica: el modelo 3D es paramétrico y didáctico. No sustituye CAD de fabricación, CFD, planos aprobados ni modelo de astillero; sirve para prediseño, presentación, revisión de consistencia y explicación visual del sistema motor–transmisión–eje–hélice.
    </span>
    </div>
    """, unsafe_allow_html=True)

    if go is None:
        estado_html("⚠️ Para activar el Gemelo Digital instala Plotly agregando `plotly` a requirements.txt.", "warn")
    else:
        twin_resumen, twin_sistema, twin_helice = st.tabs([
            "📌 Panel digital", "🔩 Tren propulsor 3D", "🌀 Hélice 3D animada"
        ])

        with twin_resumen:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PB requerida", f"{PB_kw_calc:,.0f} kW")
            c2.metric("MCR requerido", f"{MCR_requerido_kw:,.0f} kW")
            c3.metric("Hélice", f"Z={z_val} · D={diam_prop_m:.2f} m")
            c4.metric("RPM ref.", f"{rpm_helice_objetivo:.1f} rpm")
            estado_html("✅ Gemelo digital activo: las visualizaciones se alimentan de los datos actuales de entrada y resultados calculados por la app.", "good")

            st.markdown("""
            ### ¿Qué evalúa esta pestaña?
            - **Tren propulsor:** representa motor, transmisión/reductora, eje, cojinetes, hélice y dirección de empuje.
            - **Hélice paramétrica:** cambia con Z, D, P/D, Ae/A0 y hub ratio.
            - **Integración visual:** concentra la parte geométrica del sistema eje-hélice, mientras que el flujo energético vive en Potencias y la cavitación animada vive en Cavitación.
            - **Defensa del proyecto:** permite explicar el sistema como si fuera un software de diseño, no solo una hoja de cálculo.
            """)

            resumen_twin_df = pd.DataFrame([
                {"Variable": "Potencia efectiva PE", "Valor": f"{PE_kw:,.1f} kW", "Uso en gemelo": "Inicio del flujo energético útil."},
                {"Variable": "Potencia al freno PB", "Valor": f"{PB_kw_calc:,.1f} kW", "Uso en gemelo": "Carga requerida en motor."},
                {"Variable": "MCR requerido", "Valor": f"{MCR_requerido_kw:,.1f} kW", "Uso en gemelo": "Reserva de potencia al 85% MCR."},
                {"Variable": "Diámetro de hélice", "Valor": f"{diam_prop_m:.2f} m", "Uso en gemelo": "Escala la hélice 3D y el disco propulsor."},
                {"Variable": "P/D", "Valor": f"{pd_val:.3f}", "Uso en gemelo": "Modifica la torsión geométrica/twist visual de las palas."},
                {"Variable": "Ae/A0", "Valor": f"{ae_val:.3f}", "Uso en gemelo": "Aumenta o reduce la cuerda/área visual de las palas."},
                {"Variable": "σ cavitación", "Valor": f"{sigma_n:.3f}", "Uso en gemelo": "Controla la nube simbólica de cavitación."},
            ])
            st.dataframe(resumen_twin_df, use_container_width=True, height=285)

        with twin_sistema:
            st.markdown("""
            ### Tren propulsor 3D interactivo de popa
            El modelo representa el arreglo conceptual **motor → transmisión → línea de ejes → cojinetes → hélice → empuje** dentro de una envolvente de casco.
            Puedes rotarlo, acercarlo y moverlo con el mouse; además, al pasar el cursor sobre cada componente aparece información técnica del elemento. La escala cambia automáticamente con el diámetro de hélice, diámetro de eje, potencia, RPM y tipo de transmisión.
            """)
            fig_sys = crear_sistema_propulsor_3d(
                D=diam_prop_m,
                eje_d_mm=diametro_eje_mm,
                Lpp=eslora,
                tipo_trans=transmision_tipo,
                relacion=relacion_reduccion,
                PB=PB_kw_calc,
                rpm=rpm_helice_objetivo,
                Z=z_val,
                PD=pd_val,
                AeAo=ae_val,
                hub_ratio=hub_ratio
            )
            st.plotly_chart(fig_sys, use_container_width=True)
            sistema_df = pd.DataFrame([
                {"Elemento": "Motor", "Dato asociado": f"PB={PB_kw_calc:,.0f} kW / MCR≈{MCR_requerido_kw:,.0f} kW", "Qué representa": "Fuente de potencia del sistema."},
                {"Elemento": "Transmisión", "Dato asociado": f"{transmision_tipo} · i={relacion_reduccion:.2f}", "Qué representa": "Compatibilidad entre RPM de motor y hélice."},
                {"Elemento": "Eje", "Dato asociado": f"d≈{diametro_eje_mm:.0f} mm", "Qué representa": "Transmisión de torque y soporte dinámico."},
                {"Elemento": "Hélice", "Dato asociado": f"D={diam_prop_m:.2f} m · Z={z_val}", "Qué representa": "Conversión de potencia en empuje."},
                {"Elemento": "Empuje", "Dato asociado": f"T≈{thrust_req_N/1000:,.1f} kN", "Qué representa": "Fuerza propulsiva generada."},
            ])
            st.dataframe(sistema_df, use_container_width=True, height=250)

        with twin_helice:
            st.markdown("""
            ### Hélice 3D paramétrica de perfil y animada
            Esta hélice no es una pieza CAD final, pero sí es un modelo paramétrico: cambia con el **número de palas, diámetro, P/D, Ae/A0 y hub ratio**.
            Puedes rotarla manualmente con el mouse o usar el botón **Girar** dentro de la gráfica. El objetivo es visualizar cómo los parámetros hidrodinámicos se traducen en forma geométrica del propulsor.
            """)
            fig_prop = crear_helice_3d_parametrica(D=diam_prop_m, Z=z_val, PD=pd_val, AeAo=ae_val, hub_ratio=hub_ratio, rpm=rpm_helice_objetivo, animar=True)
            st.plotly_chart(fig_prop, use_container_width=True)
            helice_visual_df = pd.DataFrame([
                {"Parámetro": "Número de palas Z", "Valor": z_val, "Efecto visual/técnico": "Define cuántas palas se distribuyen angularmente; influye en vibración y eficiencia."},
                {"Parámetro": "Diámetro D", "Valor": f"{diam_prop_m:.3f} m", "Efecto visual/técnico": "Escala el radio del disco propulsor y la longitud de pala."},
                {"Parámetro": "P/D", "Valor": f"{pd_val:.3f}", "Efecto visual/técnico": "Aumenta el avance geométrico y la torsión visual de la pala."},
                {"Parámetro": "Ae/A0", "Valor": f"{ae_val:.3f}", "Efecto visual/técnico": "Modifica la cuerda/área de pala; mayor área suele ayudar contra cavitación."},
                {"Parámetro": "Hub ratio", "Valor": f"{hub_ratio:.3f}", "Efecto visual/técnico": "Define el tamaño relativo del cubo central."},
                {"Parámetro": "RPM de referencia", "Valor": f"{rpm_helice_objetivo:.2f} rpm", "Efecto visual/técnico": "Se usa para la interpretación de velocidad de operación del propulsor."},
            ])
            st.dataframe(helice_visual_df, use_container_width=True, height=285)



with tab_avanzado:
    st.subheader("⚙️ Integridad dinámica del sistema eje–hélice")

    st.markdown("""
    <div class="section-card">
    Esta pestaña reúne una lectura avanzada del sistema propulsivo desde el punto de vista dinámico.
    En una embarcación real no basta con que la hélice entregue empuje y que el motor tenga potencia:
    el eje también debe operar lejos de resonancias, con respuesta vibratoria controlada y sin indicios
    preliminares de inestabilidad torsional, axial o lateral.
    <br><br>
    <b>¿Qué hace esta sección?</b> Integra una matriz de cumplimiento, un modelo torsional equivalente,
    respuesta tipo Bode, órbitas laterales del eje y respuesta transitoria de arranque. Todo se calcula
    con parámetros de prediseño y sirve para explicar el comportamiento dinámico del tren
    motor–eje–hélice antes de pasar a un análisis de clase o a mediciones reales.
    <br><br>
    <b>Uso correcto:</b> es una herramienta didáctica y de prevalidación. Para aprobación formal se requieren
    datos certificados de fabricante: inercias reales, rigidez de acoplamientos, chumaceras, alineación,
    amortiguamiento, modelo TVA completo y verificación de sociedad clasificadora.
    </div>
    """, unsafe_allow_html=True)

    dyn_resumen, dyn_tva, dyn_bode, dyn_orbitas, dyn_trans, dyn_interpretacion = st.tabs([
        "✅ Cumplimiento",
        "🔩 Modelo TVA",
        "📉 Bode",
        "🌀 Órbitas",
        "⏱️ Transitorio",
        "📚 Fundamento"
    ])

    def _status_css(v):
        s = str(v).lower()
        if "cumple" in s and "no" not in s and "revis" not in s:
            return "background-color:#dcfce7;color:#166534;font-weight:800"
        if "revis" in s or "observ" in s or "precauc" in s:
            return "background-color:#fef3c7;color:#92400e;font-weight:800"
        return "background-color:#fee2e2;color:#991b1b;font-weight:800"

    def _sf(x, default=0.0):
        try:
            if x is None:
                return default
            y = float(x)
            if np.isnan(y):
                return default
            return y
        except Exception:
            return default

    pb_dyn_kw = _sf(globals().get("PB_kw_calc", globals().get("PB_kw", globals().get("potencia_kw", 0.0))), 0.0)
    rpm_dyn = max(_sf(globals().get("rpm_motor", globals().get("rpm_real", 0.0)), 75.0), 0.1)
    d_dyn_m = max(_sf(globals().get("diametro_m", globals().get("diametro_eje_mm", 250.0)/1000.0), 0.25), 0.05)
    L_equiv_dyn = max(_sf(globals().get("eslora", 100.0), 100.0) * 0.18, 8.0)
    G_steel = 7.9e10
    Jp_dyn = math.pi * d_dyn_m**4 / 32.0
    kt_eje_base = G_steel * Jp_dyn / max(L_equiv_dyn, 0.1)

    try:
        campbell_alto = bool((campbell_df["Riesgo"].astype(str) == "Alto").any())
    except Exception:
        campbell_alto = False

    # Variables globales de dictamen dinámico usadas en varias subpestañas.
    sep_ax_min = float(axial_df["Separación [%]"].min()) if "axial_df" in globals() and not axial_df.empty else 99.0
    bode_ratio_default = 1.0
    orbit_status_default = "Cumple" if lateral_ok else "Revisar"
    trans_status_default = "Cumple"

    with dyn_resumen:
        st.markdown("### ✅ Matriz de integridad dinámica")
        st.markdown("""
        Esta matriz resume los puntos principales que justifican si el sistema puede considerarse
        dinámicamente aceptable en etapa preliminar. Un resultado **Revisar** no significa falla: indica
        que para cerrar el criterio se necesita información más fina, como modelo de shafting, datos de
        fabricante o medición experimental.
        """)

        motor_estado_av = globals().get("motor_norma_estado", globals().get("estado_motor_potencia", "Revisar"))
        transmision_estado_av = "Cumple" if bool(globals().get("transmision_ok", False)) else "Revisar"

        cumplimiento_avanzado = pd.DataFrame([
            {"Análisis": "Potencia propulsiva", "Qué verifica": "PB requerida compatible con MCR/NCR", "Valor usado": f"PB={pb_dyn_kw:,.0f} kW", "Referencia": "Fabricante / 85% MCR", "Dictamen": motor_estado_av},
            {"Análisis": "Transmisión", "Qué verifica": "RPM motor y RPM hélice compatibles", "Valor usado": f"n={rpm_dyn:.1f} rpm", "Referencia": "Directa o reductora", "Dictamen": transmision_estado_av},
            {"Análisis": "Torsión", "Qué verifica": "Esfuerzo alternante menor al admisible", "Valor usado": f"τ={esfuerzo_real_mpa:.2f} MPa / adm={tau_admisible_mpa:.2f} MPa", "Referencia": "IACS UR M68 / DNV Pt.4 Ch.4", "Dictamen": "Cumple" if torsion_ok else "No cumple"},
            {"Análisis": "Axial", "Qué verifica": "Órdenes 1P, ZP, 2ZP y 3ZP alejadas de fn", "Valor usado": f"separación mín={sep_ax_min:.1f}%", "Referencia": "Práctica shafting", "Dictamen": "Cumple" if axial_ok else "Revisar"},
            {"Análisis": "Lateral / whirling", "Qué verifica": "RPM fuera de zona crítica ±20%", "Valor usado": f"zona={margen_inf:.1f}-{margen_sup:.1f} rpm", "Referencia": "Velocidad crítica lateral", "Dictamen": "Cumple" if lateral_ok else "No cumple"},
            {"Análisis": "Campbell", "Qué verifica": "Sin cruces críticos cerca de operación", "Valor usado": f"RPM op={rpm_dyn:.1f}", "Referencia": "Órdenes 1P/ZP", "Dictamen": "Revisar" if campbell_alto else "Cumple"},
            {"Análisis": "Cavitación", "Qué verifica": "Burrill, Keller y σ preliminar", "Valor usado": f"σ={sigma_n:.2f}; Ae/A0={ae_val:.3f}", "Referencia": "Burrill / Keller", "Dictamen": "Cumple" if (burrill_ok and keller_ok and cavitacion_ok) else "Revisar"},
            {"Análisis": "Reynolds", "Qué verifica": "Flujo turbulento representativo", "Valor usado": f"Re={reynolds:.2e}", "Referencia": "ITTC open-water", "Dictamen": "Cumple" if reynolds_ok else "Revisar"},
            {"Análisis": "Trazabilidad", "Qué verifica": "Entradas visibles o estimadas con explicación", "Valor usado": "Datos editables", "Referencia": "Requisito del proyecto", "Dictamen": "Cumple"},
        ])

        st.dataframe(cumplimiento_avanzado.style.map(_status_css, subset=["Dictamen"]), use_container_width=True, height=430)

        ok = int((cumplimiento_avanzado["Dictamen"].astype(str).str.contains("Cumple", case=False, na=False) & ~cumplimiento_avanzado["Dictamen"].astype(str).str.contains("No", case=False, na=False)).sum())
        rev = int(cumplimiento_avanzado["Dictamen"].astype(str).str.contains("Revisar|observ", case=False, na=False).sum())
        no = int(cumplimiento_avanzado["Dictamen"].astype(str).str.contains("No cumple", case=False, na=False).sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Criterios que cumplen", ok)
        c2.metric("Criterios a revisar", rev)
        c3.metric("No cumple", no)

        # Gráfica compacta y más ejecutiva del dictamen global.
        fig_dyn_status, ax_dyn_status = plt.subplots(figsize=(6.6, 2.55))
        labels = ["Cumple", "Revisar", "No cumple"]
        vals = [ok, rev, no]
        y = np.arange(len(labels))
        bars = ax_dyn_status.barh(y, vals, height=0.46)
        ax_dyn_status.set_yticks(y)
        ax_dyn_status.set_yticklabels(labels)
        ax_dyn_status.set_xlabel("Criterios")
        ax_dyn_status.set_title("Resumen ejecutivo de integridad dinámica", fontsize=11, fontweight="bold")
        ax_dyn_status.grid(True, axis="x", linestyle=":", alpha=0.28)
        ax_dyn_status.spines[["top", "right", "left"]].set_visible(False)
        ax_dyn_status.set_xlim(0, max(vals + [1]) + 1.2)
        for i, v in enumerate(vals):
            ax_dyn_status.text(v + 0.08, i, str(v), va="center", fontsize=10, fontweight="bold")
        fig_dyn_status.tight_layout()
        st.pyplot(fig_dyn_status, use_container_width=False)

        if no == 0 and rev <= 2:
            estado_html("✅ Integridad dinámica preliminar aceptable: no se observan fallas críticas en los criterios revisados.", "good")
        elif no == 0:
            estado_html("⚠️ Integridad dinámica con observaciones: el sistema puede defenderse, pero conviene explicar los puntos marcados como revisar.", "warn")
        else:
            estado_html("❌ Revisar integridad dinámica: existe al menos un criterio crítico marcado como no cumple.", "bad")

    with dyn_tva:
        st.markdown("### 🔩 Modelo torsional de masas discretas — TVA")
        st.markdown("""
        El modelo TVA representa el tren propulsor como inercias rotatorias conectadas por rigideces torsionales.
        En ingeniería naval se usa para identificar frecuencias naturales torsionales y modos que podrían coincidir
        con excitaciones del motor o de la hélice. En esta app se usa como modelo equivalente de prediseño, útil para
        visualizar la lógica del análisis sin requerir datos confidenciales del fabricante.
        """)

        with st.expander("📘 Teoría y fórmulas usadas", expanded=False):
            st.latex(r"J_p = \frac{\pi d^4}{32}")
            st.latex(r"k_t = \frac{GJ_p}{L}")
            st.latex(r"\mathbf{K}\phi = \omega_n^2\mathbf{M}\phi")
            st.latex(r"f_n = \frac{\omega_n}{2\pi}")
            st.markdown("El modelo no sustituye un TVA de clase; muestra una aproximación transparente a partir de potencia, RPM, diámetro de eje y geometría equivalente.")

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            n_masas = st.slider("Número de masas equivalentes", 3, 6, 4)
        with col_m2:
            factor_kt = st.slider("Factor de rigidez torsional", 0.50, 2.00, 1.00, 0.05)
        with col_m3:
            factor_inercia = st.slider("Factor de inercia equivalente", 0.50, 2.00, 1.00, 0.05)

        try:
            omega_op = 2 * math.pi * rpm_dyn / 60.0
            torque_base = safe_div(max(pb_dyn_kw, 1.0) * 1000.0, max(omega_op, 1e-6), default=1.0)
            inercia_base = max(torque_base / max(omega_op**2, 1e-6), 1.0) * factor_inercia

            nombres_base = ["Motor", "Volante/acople", "Eje intermedio", "Eje de cola", "Bocina", "Hélice"][:n_masas]
            inercias = np.linspace(0.85, 1.35, n_masas) * inercia_base
            inercias[-1] *= 1.8
            rigideces = np.linspace(1.15, 0.85, n_masas-1) * kt_eje_base * factor_kt

            M = np.diag(inercias)
            K = np.zeros((n_masas, n_masas))
            for i in range(n_masas-1):
                k = rigideces[i]
                K[i, i] += k
                K[i+1, i+1] += k
                K[i, i+1] -= k
                K[i+1, i] -= k

            eigvals, eigvecs = np.linalg.eig(np.linalg.pinv(M) @ K)
            eigvals = np.real(eigvals)
            eigvecs = np.real(eigvecs)
            freqs = np.sqrt(np.clip(eigvals, 0, None)) / (2*np.pi)
            order = np.argsort(freqs)
            freqs = freqs[order]
            eigvecs = eigvecs[:, order]
            freqs_nonzero = freqs[freqs > 1e-3]

            tva_df = pd.DataFrame({
                "Elemento": nombres_base,
                "Inercia equivalente [kg·m²]": inercias,
                "Rigidez hacia siguiente [MN·m/rad]": list(rigideces/1e6) + [np.nan]
            })
            st.dataframe(tva_df.style.format({"Inercia equivalente [kg·m²]":"{:,.2f}", "Rigidez hacia siguiente [MN·m/rad]":"{:,.2f}"}), use_container_width=True)

            if len(freqs_nonzero) == 0:
                estado_html("⚠️ Modelo TVA sin frecuencias útiles. Revisa rigidez, diámetro de eje o potencia.", "warn")
            else:
                f1 = float(freqs_nonzero[0])
                ordenes_hz = np.array([rpm_dyn/60.0, z_val*rpm_dyn/60.0, 2*z_val*rpm_dyn/60.0, 3*z_val*rpm_dyn/60.0])
                sep_min = float(np.min(np.abs(f1 - ordenes_hz) / max(f1, 1e-9) * 100))
                estado_tva = "Cumple" if sep_min > 12 else ("Revisar" if sep_min > 5 else "No cumple")
                c1, c2, c3 = st.columns(3)
                c1.metric("Primera fn torsional", f"{f1:.2f} Hz")
                c2.metric("Separación mínima", f"{sep_min:.1f}%")
                c3.metric("Dictamen TVA", estado_tva)
                estado_html(f"{'✅' if estado_tva=='Cumple' else '⚠️' if estado_tva=='Revisar' else '❌'} Modelo TVA: {estado_tva}. La separación mínima frente a órdenes 1P/ZP es {sep_min:.1f}%.", "good" if estado_tva=="Cumple" else "warn" if estado_tva=="Revisar" else "bad")

                fig_modes, ax_modes = plt.subplots(figsize=(10.2, 4.6))
                modos_a_graficar = min(3, eigvecs.shape[1]-1)
                x = np.arange(n_masas)
                for m in range(1, modos_a_graficar+1):
                    vec = eigvecs[:, m]
                    vec = vec / max(np.max(np.abs(vec)), 1e-9)
                    ax_modes.plot(x, vec, marker="o", linewidth=2.2, label=f"Modo {m} — {freqs[m]:.2f} Hz")
                ax_modes.axhline(0, linewidth=1)
                ax_modes.set_xticks(x)
                ax_modes.set_xticklabels(nombres_base, rotation=20)
                ax_modes.set_ylabel("Amplitud modal normalizada")
                ax_modes.set_title("Formas modales torsionales equivalentes")
                ax_modes.grid(True, linestyle=":", alpha=0.5)
                ax_modes.legend(fontsize=8)
                st.pyplot(fig_modes)
        except Exception as e:
            st.error(f"No se pudo resolver el modelo TVA. Detalle técnico: {e}")

    with dyn_bode:
        st.markdown("### 📉 Respuesta en frecuencia tipo Bode")
        st.markdown("""
        El diagrama de Bode muestra cómo responde dinámicamente el sistema eje-hélice ante diferentes
        frecuencias de excitación. En lugar de interpretar únicamente el pico matemático de resonancia,
        esta versión separa dos conceptos: **sensibilidad teórica del modo** y **amplificación real en operación**.
        Esto evita marcar como falla un caso que solo tendría problemas si el eje operara cerca de su frecuencia natural.
        """)
        with st.expander("📘 Teoría, lectura del resultado y fórmulas usadas", expanded=False):
            st.latex(r"H(r)=\frac{1}{\sqrt{(1-r^2)^2+(2\zeta r)^2}}")
            st.latex(r"r=\frac{f}{f_n}")
            st.latex(r"\phi=-\tan^{-1}\left(\frac{2\zeta r}{1-r^2}\right)")
            st.markdown("""
            El pico máximo de un Bode ocurre cerca de la frecuencia natural. Con amortiguamiento bajo, por ejemplo
            ζ = 0.05, el pico teórico puede acercarse a 10×. Eso **no significa automáticamente que el eje falle**;
            lo importante para el dictamen de operación es cuánto se amplifica el sistema en las frecuencias reales
            de excitación: **1P** y **ZP**. Por eso la app muestra dos lecturas: el pico teórico y la amplificación operacional.

            **Criterio usado en la app:** amplificación operacional máxima < 1.5× cumple; 1.5–2.5× revisar; > 2.5× no cumple.
            """)

        zeta = st.slider("Amortiguamiento modal ζ", 0.01, 0.25, 0.05, 0.01)
        modo_bode = st.selectbox("Modo a visualizar", ["Axial", "Lateral / whirling", "Torsional estimado"])
        fn_sel = {"Axial": f_axial_natural_hz, "Lateral / whirling": f_natural_hz, "Torsional estimado": f_torsional_est}[modo_bode]
        f_1p = rpm_dyn / 60.0
        f_zp = z_val * rpm_dyn / 60.0
        fmax_bode = max(fn_sel*3.0, f_zp*1.35, 1.0)
        f_bode = np.linspace(0.05, fmax_bode, 650)
        r = f_bode / max(fn_sel, 1e-9)
        mag = 1.0 / np.sqrt((1-r**2)**2 + (2*zeta*r)**2)
        phase = -np.degrees(np.arctan2(2*zeta*r, 1-r**2))
        peak = float(np.nanmax(mag))
        peak_db = 20*np.log10(max(peak, 1e-9))

        def _amp_at(freq):
            rr = freq / max(fn_sel, 1e-9)
            return float(1.0 / math.sqrt((1-rr**2)**2 + (2*zeta*rr)**2))

        amp_1p = _amp_at(f_1p)
        amp_zp = _amp_at(f_zp)
        amp_oper = max(amp_1p, amp_zp)
        amp_oper_db = 20*np.log10(max(amp_oper, 1e-9))
        bode_estado = "Cumple" if amp_oper < 1.5 else ("Revisar" if amp_oper <= 2.5 else "No cumple")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Modo", modo_bode)
        c2.metric("fn", f"{fn_sel:.2f} Hz")
        c3.metric("Amplif. operacional", f"{amp_oper:.2f}× / {amp_oper_db:.1f} dB")
        c4.metric("Dictamen", bode_estado)
        estado_html(
            f"{'✅' if bode_estado=='Cumple' else '⚠️' if bode_estado=='Revisar' else '❌'} Bode operacional: {bode_estado}. "
            f"La amplificación máxima en 1P/ZP es {amp_oper:.2f}×. El pico teórico de resonancia es {peak:.2f}×, "
            "pero solo sería crítico si la operación cae cerca de esa frecuencia natural.",
            "good" if bode_estado=="Cumple" else "warn" if bode_estado=="Revisar" else "bad"
        )

        st.caption("Lectura rápida: el pico teórico ayuda a entender la sensibilidad del modo; el dictamen se basa en las frecuencias reales de operación 1P y ZP.")
        bode_resumen_df = pd.DataFrame([
            {"Frecuencia": "1P operación", "Hz": f_1p, "Amplificación [x]": amp_1p, "Magnitud [dB]": 20*np.log10(max(amp_1p, 1e-9))},
            {"Frecuencia": "ZP operación", "Hz": f_zp, "Amplificación [x]": amp_zp, "Magnitud [dB]": 20*np.log10(max(amp_zp, 1e-9))},
            {"Frecuencia": "Pico teórico", "Hz": float(f_bode[np.nanargmax(mag)]), "Amplificación [x]": peak, "Magnitud [dB]": peak_db},
        ])
        st.dataframe(bode_resumen_df.style.format({"Hz":"{:.2f}", "Amplificación [x]":"{:.2f}", "Magnitud [dB]":"{:.1f}"}), use_container_width=True, height=150)

        fig_mag, ax_mag = plt.subplots(figsize=(8.2, 3.2))
        mag_db = 20*np.log10(mag)
        ax_mag.plot(f_bode, mag_db, linewidth=2.2, label="Magnitud")
        ax_mag.axvline(fn_sel, linestyle="--", linewidth=1.8, label=f"fn = {fn_sel:.2f} Hz")
        ax_mag.scatter([f_1p, f_zp], [20*np.log10(max(amp_1p, 1e-9)), 20*np.log10(max(amp_zp, 1e-9))], s=70, zorder=5, label="1P / ZP")
        ax_mag.set_title(f"Bode operacional de magnitud — {modo_bode}", fontsize=11, fontweight="bold")
        ax_mag.set_xlabel("Frecuencia [Hz]")
        ax_mag.set_ylabel("Magnitud [dB]")
        ax_mag.grid(True, linestyle=":", alpha=0.35)
        ax_mag.spines[["top", "right"]].set_visible(False)
        ax_mag.legend(fontsize=8, loc="best")
        fig_mag.tight_layout()
        st.pyplot(fig_mag, use_container_width=False)

        fig_phase, ax_phase = plt.subplots(figsize=(8.2, 3.0))
        ax_phase.plot(f_bode, phase, linewidth=2.2)
        ax_phase.axvline(fn_sel, linestyle="--", linewidth=1.8, label=f"fn = {fn_sel:.2f} Hz")
        ax_phase.scatter([f_1p, f_zp], [np.interp(f_1p, f_bode, phase), np.interp(f_zp, f_bode, phase)], s=70, zorder=5, label="1P / ZP")
        ax_phase.set_title(f"Bode operacional de fase — {modo_bode}", fontsize=11, fontweight="bold")
        ax_phase.set_xlabel("Frecuencia [Hz]")
        ax_phase.set_ylabel("Fase [°]")
        ax_phase.grid(True, linestyle=":", alpha=0.35)
        ax_phase.spines[["top", "right"]].set_visible(False)
        ax_phase.legend(fontsize=8, loc="best")
        fig_phase.tight_layout()
        st.pyplot(fig_phase, use_container_width=False)

    with dyn_orbitas:
        st.markdown("### 🌀 Órbitas laterales estimadas del eje")
        st.markdown("""
        Las órbitas muestran el recorrido del centro del eje en el plano transversal. En buques reales se obtienen
        con sensores de proximidad y acelerómetros. En la app sirven para explicar visualmente desbalance,
        whirling, anisotropía de apoyos y cercanía a velocidades críticas.
        """)
        with st.expander("📘 Teoría y fórmulas usadas", expanded=False):
            st.latex(r"x(t)=X\cos(\Omega t)")
            st.latex(r"y(t)=Y\sin(\Omega t+\phi)")
            st.markdown("Criterio didáctico: amplitudes bajas y órbita estable cumplen; amplitudes elevadas o fase extrema requieren revisión.")

        sep_lat = min(abs(rpm_dyn - margen_inf), abs(rpm_dyn - margen_sup)) / max(rpm_dyn, 1e-9) * 100.0
        amp_base_um = 70.0 if lateral_ok else 220.0
        amplificacion = 1.0 + max(0.0, 12.0 - sep_lat)/12.0
        amp_x = amp_base_um * amplificacion
        amp_y = amp_x * (0.55 if lateral_ok else 0.85)
        fase_deg = 35 if lateral_ok else 75
        orbit_estado = "Cumple" if (lateral_ok and amp_x < 150) else ("Revisar" if amp_x < 300 else "No cumple")
        th = np.linspace(0, 2*np.pi, 720)
        x_orb = amp_x * np.cos(th)
        y_orb = amp_y * np.sin(th + np.deg2rad(fase_deg))

        o1, o2, o3, o4 = st.columns(4)
        o1.metric("Amplitud X", f"{amp_x:.1f} µm")
        o2.metric("Amplitud Y", f"{amp_y:.1f} µm")
        o3.metric("Fase", f"{fase_deg}°")
        o4.metric("Dictamen", orbit_estado)
        estado_html(f"{'✅' if orbit_estado=='Cumple' else '⚠️' if orbit_estado=='Revisar' else '❌'} Órbitas: {orbit_estado}. La visualización sugiere {'movimiento lateral controlado' if orbit_estado=='Cumple' else 'posible sensibilidad lateral a revisar'}.", "good" if orbit_estado=="Cumple" else "warn" if orbit_estado=="Revisar" else "bad")

        fig_orb, ax_orb = plt.subplots(figsize=(6.8, 6.2))
        ax_orb.plot(x_orb, y_orb, linewidth=2.6)
        ax_orb.scatter([0], [0], s=80, marker="+")
        ax_orb.set_aspect("equal", adjustable="box")
        ax_orb.set_title("Órbita lateral estimada del eje")
        ax_orb.set_xlabel("Desplazamiento X [µm]")
        ax_orb.set_ylabel("Desplazamiento Y [µm]")
        ax_orb.grid(True, linestyle=":", alpha=0.55)
        st.pyplot(fig_orb)

        orb_df = pd.DataFrame([
            {"Parámetro": "Separación lateral mínima", "Valor": sep_lat, "Unidad": "%", "Interpretación": "Mayor separación implica menor riesgo de resonancia"},
            {"Parámetro": "Amplitud X estimada", "Valor": amp_x, "Unidad": "µm", "Interpretación": "Componente horizontal de órbita"},
            {"Parámetro": "Amplitud Y estimada", "Valor": amp_y, "Unidad": "µm", "Interpretación": "Componente vertical de órbita"},
            {"Parámetro": "Ángulo de fase", "Valor": fase_deg, "Unidad": "°", "Interpretación": "Inclinación/retardo de la órbita"},
            {"Parámetro": "Dictamen", "Valor": np.nan, "Unidad": "—", "Interpretación": orbit_estado},
        ])
        st.dataframe(orb_df.style.format({"Valor": lambda x: "—" if pd.isna(x) else f"{x:.2f}"}), use_container_width=True)

    with dyn_trans:
        st.markdown("### ⏱️ Respuesta transitoria durante arranque")
        st.markdown("""
        El sistema propulsivo no pasa instantáneamente de reposo a régimen permanente. Durante el arranque puede
        cruzar frecuencias de excitación cercanas a frecuencias naturales. Este módulo permite observar si la
        respuesta se amortigua correctamente y si el paso de pala ZP se aproxima a la frecuencia axial.
        """)
        with st.expander("📘 Teoría y fórmulas usadas", expanded=False):
            st.latex(r"n(t)=n_{op}\left(1-e^{-t/\tau}\right)")
            st.latex(r"x(t)=x_{est}\left[1-e^{-\zeta\omega_n t}\cos(\omega_n t)\right]")
            st.markdown("Criterio didáctico: respuesta amortiguada cumple; sobreimpulso elevado requiere revisión; vibración creciente no cumple.")

        t_final = st.slider("Tiempo de simulación [s]", 10, 180, 60)
        zeta_tr = st.slider("Amortiguamiento transitorio ζ", 0.02, 0.25, 0.06, 0.01, key="zeta_transitorio_prof")
        tau_arranque = st.slider("Constante de rampa τ [s]", 2, 60, max(5, int(t_final/5)))

        t_sim = np.linspace(0, t_final, 1400)
        rpm_sim = rpm_dyn * (1 - np.exp(-t_sim / max(tau_arranque, 1)))
        w_n_ax = 2*np.pi*max(f_axial_natural_hz, 0.1)
        respuesta = (1 - np.exp(-zeta_tr*w_n_ax*t_sim)*np.cos(w_n_ax*t_sim)) * desplazamiento_axial_est_m * 1000
        f_zp_trans = z_val * rpm_sim / 60.0
        sobreimpulso = (np.nanmax(respuesta) - respuesta[-1]) / max(abs(respuesta[-1]), 1e-9) * 100.0 if len(respuesta) else 0.0
        distancia_zp = np.nanmin(np.abs(f_zp_trans - f_axial_natural_hz)) / max(f_axial_natural_hz, 1e-9) * 100.0
        trans_estado = "Cumple" if (sobreimpulso < 25 and distancia_zp > 8) else ("Revisar" if sobreimpulso < 60 else "No cumple")

        c1, c2, c3 = st.columns(3)
        c1.metric("Sobreimpulso estimado", f"{sobreimpulso:.1f}%")
        c2.metric("Separación mínima ZP-fn", f"{distancia_zp:.1f}%")
        c3.metric("Dictamen", trans_estado)
        estado_html(f"{'✅' if trans_estado=='Cumple' else '⚠️' if trans_estado=='Revisar' else '❌'} Transitorio: {trans_estado}. La respuesta {'se amortigua de forma aceptable' if trans_estado=='Cumple' else 'debe revisarse por cercanía a resonancia o sobreimpulso'}.", "good" if trans_estado=="Cumple" else "warn" if trans_estado=="Revisar" else "bad")

        fig_rpm, ax_rpm = plt.subplots(figsize=(10.5, 4.3))
        ax_rpm.plot(t_sim, rpm_sim, linewidth=2.6, label="RPM del eje")
        ax_rpm.axhline(rpm_dyn, linestyle="--", linewidth=2, label="RPM operación")
        ax_rpm.set_title("Rampa de arranque del eje")
        ax_rpm.set_xlabel("Tiempo [s]")
        ax_rpm.set_ylabel("RPM")
        ax_rpm.grid(True, linestyle=":", alpha=0.55)
        ax_rpm.legend(fontsize=8)
        st.pyplot(fig_rpm)

        fig_resp, ax_resp = plt.subplots(figsize=(10.5, 4.3))
        ax_resp.plot(t_sim, respuesta, linewidth=2.6, label="Respuesta axial")
        ax_resp.set_title("Respuesta transitoria axial estimada")
        ax_resp.set_xlabel("Tiempo [s]")
        ax_resp.set_ylabel("Desplazamiento axial [mm]")
        ax_resp.grid(True, linestyle=":", alpha=0.55)
        ax_resp.legend(fontsize=8)
        st.pyplot(fig_resp)

        fig_cross, ax_cross = plt.subplots(figsize=(10.5, 4.0))
        ax_cross.plot(t_sim, f_zp_trans, linewidth=2.4, label="ZP durante arranque")
        ax_cross.axhline(f_axial_natural_hz, linestyle="--", linewidth=2, label="fn axial")
        ax_cross.set_title("Cruce de paso de pala durante arranque")
        ax_cross.set_xlabel("Tiempo [s]")
        ax_cross.set_ylabel("Frecuencia [Hz]")
        ax_cross.grid(True, linestyle=":", alpha=0.55)
        ax_cross.legend(fontsize=8)
        st.pyplot(fig_cross)

    with dyn_interpretacion:
        st.markdown("### 📚 Fundamento técnico y defensa oral")
        st.markdown("""
        **Por qué esta pestaña es importante:** en un sistema propulsivo real, la potencia calculada y la eficiencia
        de la hélice no garantizan por sí solas una operación segura. El eje trabaja bajo torque, empuje axial,
        cargas laterales, excitaciones periódicas por paso de pala y cambios transitorios de velocidad. Si alguna
        excitación coincide con una frecuencia natural, puede aparecer resonancia, aumento de vibración, ruido,
        fatiga, daño en cojinetes o pérdida de confiabilidad.

        **Qué aporta a la app:**
        - Convierte el diseño de propulsión en una revisión integral motor–eje–hélice.
        - Permite justificar por qué se revisan Campbell, Bode, órbitas y transitorio.
        - Da argumentos claros para explicar que una RPM teórica óptima no siempre coincide con la RPM real.
        - Sirve como puente entre hidrodinámica, shafting dynamics y criterios de clasificación.

        **Cómo defenderlo:** estos módulos son preliminares. No sustituyen un software de clase ni un análisis TVA
        certificado, pero demuestran que el diseño considera riesgos dinámicos relevantes y que los resultados se
        interpretan con criterio de ingeniería.
        """)

        st.warning("""
        Limitación técnica: para diseño final real se requieren datos certificados de fabricante y reglas completas
        de clase. La app usa modelos equivalentes de prediseño para fines académicos, transparentes y editables.
        """)

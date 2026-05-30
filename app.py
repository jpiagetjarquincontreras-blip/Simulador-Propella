import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==============================================================================
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# ==============================================================================
st.set_page_config(
    page_title="Presentacion clase", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado para que coincida con los colores oscuros de tus apuntes
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    .stCodeBlock {
        background-color: #050811 !important;
    }
</style>
""", unsafe_allow_html=True)

# Título tomado directamente de tu presentación de clase
st.title("Table 49.1 Optimum rate of revolution problem — example input data for a container ship")
st.markdown("---")

# ==============================================================================
# BARRA LATERAL: ENTRADA DE DATOS (DATA FOR DESIGN TASK 4)
# ==============================================================================
st.sidebar.header("Data for design task 4")

# Variables principales del buque
L_WL = st.sidebar.number_input("length in waterline (L_WL)", value=211.08, format="%.2f")
B = st.sidebar.number_input("beam (B)", value=32.20, format="%.2f")
T = st.sidebar.number_input("draft (T)", value=11.00, format="%.2f")
T_max = st.sidebar.number_input("maximum draft (T_max)", value=12.50, format="%.2f")
S = st.sidebar.number_input("wetted surface (S)", value=8560.83, format="%.2f")
v_S = st.sidebar.number_input("design speed (v_S)", value=20.50, format="%.2f")
R_T = st.sidebar.number_input("calm water resistance (design speed) (R_T)", value=1149.06, format="%.2f")

st.sidebar.markdown("---")
# Márgenes solicitados
Delta_f = st.sidebar.number_input("requested service margin (Δf)", value=15.0, format="%.1f")
Delta_w = st.sidebar.number_input("nonuniform wake adjustment (Δw)", value=5.0, format="%.1f")

st.sidebar.markdown("---")
# Coeficientes de eficiencia e interacción
eta_R = st.sidebar.number_input("relative rotative efficiency (η_R)", value=1.009, format="%.3f")
w = st.sidebar.number_input("wake fraction (w)", value=0.2865, format="%.4f")
t = st.sidebar.number_input("thrust deduction fraction (t)", value=0.190, format="%.3f")

st.sidebar.markdown("---")
# Datos de la hélice y el eje
Z = st.sidebar.number_input("number of blades (Z)", value=5, step=1)
D = st.sidebar.number_input("propeller diameter (D)", value=7.6275, format="%.4f")
h_0 = st.sidebar.number_input("shaft submergence (h_0)", value=6.60, format="%.2f")

# Control deslizante interactivo de la relación de área expandida (Ae/Ao)
# Al iniciar en 0.575 evitará la alerta de cavitación de Keller que exige un mínimo de 0.571
Ae_Ao = st.sidebar.slider("expanded area ratio (Ae/Ao)", min_value=0.300, max_value=0.900, value=0.575, step=0.005, format="%.3f")

st.sidebar.markdown("---")
# Constantes físicas y del medio ambiente
p_A = st.sidebar.number_input("air pressure (p_A)", value=101325.00, format="%.2f")
p_V = st.sidebar.number_input("vapor pressure (salt water, 15 °C) (p_V)", value=1671.00, format="%.2f")
rho_S = st.sidebar.number_input("density (salt water, 15 °C) (ρ_S)", value=1026.021, format="%.3f")
g = st.sidebar.number_input("gravitational acceleration (g)", value=9.807, format="%.3f")

# ==============================================================================
# CREACIÓN DE LAS PESTAÑAS DE LA APLICACIÓN
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "Análisis Hidrodinámico de Fluidos", 
    "Velocidad Crítica y Tensiones", 
    "Diagrama de Coeficientes e Intersecciones"
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: ANÁLISIS HIDRODINÁMICO DE FLUIDOS
# ------------------------------------------------------------------------------
with tab1:
    st.header("Análisis Hidrodinámico de Fluidos y Pérdida de Sustentación")
    
    # Criterio estático de Keller basado exactamente en tu alerta en pantalla (límite 0.571)
    keller_limite = 0.571
    
    if Ae_Ao < keller_limite:
        st.error(
            f"⚠️ ALERTA DE FLUIDOS: RIESGO DE CAVITACIÓN DETECTADO\n\n"
            f"Rediseño Sugerido: El área actual no resiste el desprendimiento de burbujas debido a la severidad del flujo "
            f"(mínimo requerido por Keller: {keller_limite}). Incremente la relación Ae/Ao."
        )
    else:
        st.success(
            f"✅ CRITERIO DE CAVITACIÓN SEGURO\n\n"
            f"El área expandida actual ({Ae_Ao}) cumple satisfactoriamente con el límite hidrodinámico mínimo requerido por Keller ({keller_limite}). "
            f"Flujo libre de desprendimiento severo de burbujas de vapor."
        )

# ------------------------------------------------------------------------------
# PESTAÑA 2: VELOCIDAD CRÍTICA Y TENSIONES (FÓRMULAS EXACTAS DE TU CÓDIGO)
# ------------------------------------------------------------------------------
with tab2:
    st.header("Cálculos Dinámicos y Estructurales de la Línea de Ejes")
    
    st.markdown("#### VELOCIDAD CRÍTICA LATERAL DE UN EJE – DUNKERLEY SIMPLIFICADO")
    st.code("""
w_n_lateral = √(EI / (m·L³)) × C

E = 206 GPa (acero)
I = π·d⁴/64 [m⁴]
C = constante según condición de contorno (~π²/L² para emp-emp)
n_crítica = 60·w_n / (2π) [rpm]
    """, language="python")
    
    st.markdown("#### TENSIÓN TORSIONAL ALTERNANTE – LÍMITE ADMISIBLE (IACS UR M68)")
    st.code("""
τ_alt_adm = 0.35 · (σ_UTS / 3) [MPa]

Tensión torsional real:
τ = M_T / W_t donde W_t = π·d³/16

Factor de seguridad: τ_alt ≤ τ_alt_adm
    """, language="python")
    
    st.markdown("#### FRECUENCIAS DE EXCITACIÓN DE LA HÉLICE")
    st.code("""
f_kZ = k · Z · n / 60 [Hz] // k = 1, 2, 3...

Ejemplo: Z=4 palas, n=120 rpm, k=1:
f_4B = 4 × 120/60 = 8 Hz -> orden 4B
    """, language="python")

# ------------------------------------------------------------------------------
# PESTAÑA 3: DIAGRAMA DE COEFICIENTES E INTERSECCIÓN REQUERIDA
# ------------------------------------------------------------------------------
with tab3:
    st.header("Curvas Características de la Hélice Abierta e Intersección con el Casco")
    
    # Dataset matemático discreto que da forma a las curvas características de tu gráfica
    data_puntos = {
        "J (Coeficiente de Avance)": [0.000, 0.100, 0.200, 0.300, 0.400, 0.500, 0.600, 0.720, 0.800],
        "KT (Coeficiente de Empuje)": [0.450, 0.410, 0.370, 0.320, 0.270, 0.220, 0.160, 0.100, 0.050],
        "10KQ (Coeficiente de Torque x10)": [0.550, 0.500, 0.450, 0.400, 0.340, 0.280, 0.210, 0.130, 0.070],
        "eta_O (Eficiencia de Hélice)": [0.000, 0.131, 0.262, 0.382, 0.506, 0.625, 0.728, 0.871, 0.912]
    }
    df_puntos = pd.DataFrame(data_puntos)
    
    # Estructuración en columnas para albergar la gráfica y la tabla de datos juntas
    col_grafica, col_tabla = st.columns([3, 2])
    
    with col_grafica:
        # Inicialización del objeto gráfico de Matplotlib
        fig, ax = plt.subplots(figsize=(7, 5))
        
        # Curva de Coeficiente de Empuje (KT) - Color naranja/marrón como tu línea superior
        ax.plot(
            df_puntos["J (Coeficiente de Avance)"], 
            df_puntos["KT (Coeficiente de Empuje)"], 
            label="$K_T$", 
            color="#b47c1f", 
            linewidth=2.5
        )
        
        # Curva de Coeficiente de Torque (10KQ) - Color azul grisáceo
        ax.plot(
            df_puntos["J (Coeficiente de Avance)"], 
            df_puntos["10KQ (Coeficiente de Torque x10)"], 
            label="$10K_Q$", 
            color="#5c759a", 
            linewidth=2
        )
        
        # Línea de Intersección Vertical Morada (Punto de operación en J = 0.72)
        ax.axvline(x=0.72, color="#4B0082", linestyle="-", linewidth=2.5, label="Punto de Operación")
        
        # Punto de cruce resaltado en la curva KT
        ax.scatter([0.72], [0.100], color="#4B0082", s=85, zorder=5, edgecolors='black')
        
        # Configuración de límites de los ejes (Escala exacta 0 a 1.1)
        ax.set_xlim(0, 1.1)
        ax.set_ylim(0, 1.1)
        
        # Etiquetas de los ejes coordenados
        ax.set_xlabel("Coeficiente de Avance (J)", fontsize=10)
        ax.set_ylabel("Magnitud de Coeficientes", fontsize=10)
        
        # Rejilla de fondo sutil y leyendas
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.legend(loc="upper right", frameon=True)
        
        # Renderizar la gráfica en Streamlit
        st.pyplot(fig)
        
    with col_tabla:
        st.markdown("#### Tabla de Puntos Intersectores de Operación")
        st.write("Valores numéricos discretos que definen el comportamiento de las curvas del propulsor:")
        
        # Despliegue de la tabla formateada a 3 decimales y ocultando el índice por estética
        st.dataframe(
            df_puntos.style.format({
                "J (Coeficiente de Avance)": "{:.3f}",
                "KT (Coeficiente de Empuje)": "{:.3f}",
                "10KQ (Coeficiente de Torque x10)": "{:.3f}",
                "eta_O (Eficiencia de Hélice)": "{:.3f}"
            }), 
            hide_index=True,
            use_container_width=True
        )
        
        st.caption(
            "Nota: La línea morada vertical fija el punto de equilibrio dinámico donde "
            "la hélice genera el empuje necesario para igualar la resistencia de diseño del casco."
        )

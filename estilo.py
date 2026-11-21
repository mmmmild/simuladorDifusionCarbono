# Simulador Difusión Carbono. Colores, límites y nombres de páginas que usan varios módulos.
# UNAM, Facultad de Ingeniería. Ingeniería de Materiales.
#
# Aquí SOLO hay constantes (nada de Streamlit ni de cálculos). Así cualquier módulo
# puede importar de aquí sin que se enreden los imports entre ellos.
# Si cambia un límite o un color, se cambia en este archivo y ya.

# ---------- Datos de la portada ----------
NOMBRE_PROYECTO = "Simulador Difusión Carbono"
SUBTITULO_PROYECTO = "Simulador interactivo para analizar y diseñar condiciones de difusión de carbono en aceros"
UNIVERSIDAD = "Universidad Nacional Autónoma de México"
FACULTAD = "Facultad de Ingeniería"
CARRERA = "Ingeniería de Materiales"
PROFESORA = "Artemisa Mazón Martínez"
INTEGRANTES = (
    "Meza Prieto Adriel",
    "Uriostegui Rodriguez Adolfo Saúl",
    "Vega Hurtado Mildred Dessire",
)

# ---------- Límites de la interfaz ----------
T_MIN = 900.0             # [°C] intervalo de demostración del proyecto (900–1050 °C)
T_MAX = 1050.0            # [°C]
SOLUBILIDAD_MAX = 2.11    # [wt %] máxima solubilidad del C en austenita según el diagrama de clase (a 1147 °C)
FACTOR_SEMIINFINITO = 4.0 # el sólido se considera semiinfinito si el espesor es mayor o igual que 4*L (L = raíz(D*t))
                          # (a esa profundidad erfc(2) ≈ 0.005, o sea casi no llega carbono)

# ---------- Nombres de las páginas (los usa la barra lateral y el botón del Módulo 2) ----------
# La primera página trae la portada, el resumen teórico y, debajo, el simulador directo
PAGINA_SIMULADOR = "1. Inicio y simulación directa"
PAGINA_INVERSO = "2. Diseño inverso"
PAGINA_COMPARACION = "3. Comparación de tratamientos"
PAGINA_TEORIA = "4. Fundamento teórico"
PAGINA_VALIDACION = "5. Validación y limitaciones"

# ---------- Llaves de st.session_state ----------
ESTADO_PAGINA = "pagina"            # página que está seleccionada en la barra lateral
ESTADO_PRECARGA = "precarga_m1"     # tratamiento que el Módulo 2 le manda al Módulo 1

# ---------- Colores de las gráficas (pensados para fondo blanco) ----------
COLOR_PERFIL = "#E8590C"  # naranja "metal al rojo"
COLOR_C0 = "#5C6B80"      # gris azulado (acero frío)
COLOR_CS = "#C92A2A"      # rojo
COLOR_COBJ = "#1C7ED6"    # azul
COLOR_X = "#2F9E44"       # verde
COLOR_TEXTO = "#1B2430"   # azul muy oscuro, para texto y líneas sobre fondo blanco
COLORES_TRATAMIENTOS = ["#E8590C", "#1C7ED6", "#2F9E44"]  # tratamientos A, B y C (Módulo 3)

# ---------- Formato común de todas las gráficas de Plotly ----------
# Se usa así:  fig.update_layout(**LAYOUT_BASE, xaxis_title="...", height=480)
LAYOUT_BASE = dict(
    template="plotly_white",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(l=10, r=10, t=40, b=10),
)

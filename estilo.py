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

# ---------- Rangos de los controles (el porqué de cada uno se explica en la página de Simulación) ----------
T_MIN, T_MAX = 900.0, 1050.0      # [°C]  temperatura de cementación
T_H_MIN, T_H_MAX = 0.5, 50.0      # [h]   tiempo de tratamiento
C0_MIN, C0_MAX = 0.05, 0.30       # [wt %] carbono inicial del acero (aceros de bajo carbono)
CS_MIN, CS_MAX = 0.50, 1.15       # [wt %] carbono en la superficie
COBJ_MIN, COBJ_MAX = 0.10, 1.10   # [wt %] concentración objetivo (además debe quedar entre C0 y Cs)
X_OBJ_MIN, X_OBJ_MAX = 0.10, 2.0  # [mm]  profundidad objetivo del diseño inverso
SOLUBILIDAD_MAX = 2.11    # [wt %] máxima solubilidad del C en austenita según el diagrama de clase (a 1147 °C)
FACTOR_SEMIINFINITO = 4.0 # el sólido se considera semiinfinito si el espesor es mayor o igual que 4*L (L = raíz(D*t))
                          # (a esa profundidad erfc(2) ≈ 0.005, o sea casi no llega carbono)

# Valores de demostración (no son estándares industriales)
T_DEMO, T_H_DEMO = 927.0, 10.0
C0_DEMO, CS_DEMO, COBJ_DEMO = 0.20, 1.00, 0.40
X_OBJ_DEMO = 0.80

# ---------- Nombres de las páginas (los usa la barra lateral y el botón del diseño inverso) ----------
PAGINA_TEORIA = "1. Fundamento teórico"
PAGINA_SIMULADOR = "2. Simulación"
PAGINA_INVERSO = "3. Diseño inverso"
PAGINA_COMPARACION = "4. Comparación de tratamientos"
PAGINA_INDUSTRIA = "5. Importancia en la industria"

# ---------- Llaves de st.session_state ----------
ESTADO_PAGINA = "pagina"            # página que está seleccionada en la barra lateral
ESTADO_PRECARGA = "precarga_m1"     # tratamiento que el diseño inverso le manda a la simulación

# ---------- Colores de las gráficas (pensados para fondo blanco) ----------
COLOR_PERFIL = "#E8590C"  # naranja "metal al rojo"
COLOR_C0 = "#5C6B80"      # gris azulado (acero frío)
COLOR_CS = "#C92A2A"      # rojo
COLOR_COBJ = "#1C7ED6"    # azul
COLOR_X = "#2F9E44"       # verde
COLOR_TEXTO = "#1B2430"   # azul muy oscuro, para texto y líneas sobre fondo blanco
COLOR_REFERENCIA = "#ADB5BD"  # gris claro para curvas de referencia
COLORES_TRATAMIENTOS = ["#E8590C", "#1C7ED6", "#2F9E44"]  # tratamientos A, B y C
# Escala de color del "corte de la pieza": acero con poco carbono (gris) -> mucho carbono (rojo oscuro)
ESCALA_CARBONO = [[0.0, "#E9ECEF"], [0.35, "#FFD8A8"], [0.65, "#F76707"], [1.0, "#7B1E1E"]]

# ---------- Formato común de todas las gráficas de Plotly ----------
# Se usa así:  fig.update_layout(**LAYOUT_BASE)  y luego  fig.update_layout(lo propio de cada gráfica)
LAYOUT_BASE = dict(
    template="plotly_white",
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    margin=dict(l=10, r=10, t=40, b=10),
)

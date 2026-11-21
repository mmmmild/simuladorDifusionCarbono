# Simulador Difusión Carbono. Módulo 4: fundamento teórico.
#
# Todos los valores numéricos salen de modelo.py (no están escritos a mano), así que si cambia una constante, cambia aquí también.
# app.py solo llama a mostrar().
#
# Se usa austenita por estabilidad de fase, solubilidad y porque se transforma en martensita al templar.

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from estilo import COLOR_PERFIL, COLOR_X, LAYOUT_BASE, SOLUBILIDAD_MAX, T_MAX, T_MIN
from modelo import CERO_CELSIUS_K, D0, Q, R, calcular_difusividad


# ---------- Cálculos que alimentan el texto ----------
TEMPERATURAS_TABLA = (900, 950, 1000, 1050)  # [°C] las del intervalo de demostración del proyecto


def tabla_difusividad():
    """Filas (T [°C], T [K], D [m²/s], D/D(900 °C)) para ilustrar el efecto de la temperatura.
    Regresa una lista de diccionarios. Todo sale de modelo.calcular_difusividad."""
    D_ref = float(calcular_difusividad(TEMPERATURAS_TABLA[0]))
    filas = []
    for T_C in TEMPERATURAS_TABLA:
        D = float(calcular_difusividad(T_C))
        filas.append({"T_C": T_C, "T_K": T_C + CERO_CELSIUS_K, "D": D, "razon": D / D_ref})
    return filas


def construir_figura_arrhenius():
    """Gráfica de Arrhenius: ln D contra 1000/T. Es una recta cuya pendiente es -Q/R.
    El eje x va en 1000/T [1/K]; los puntos marcados son las temperaturas de la tabla."""
    T_C = np.linspace(T_MIN - 100.0, T_MAX + 50.0, 200)          # [°C] un poco más amplio que el intervalo del proyecto
    T_K = T_C + CERO_CELSIUS_K                                    # [K]
    D = calcular_difusividad(T_C)                                 # [m²/s]
    puntos_C = np.array(TEMPERATURAS_TABLA, dtype=float)          # [°C]
    puntos_D = calcular_difusividad(puntos_C)                     # [m²/s]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=1000.0 / T_K, y=np.log(D), mode="lines", name="ln D (Arrhenius)",
        line=dict(color=COLOR_PERFIL, width=3),
        hovertemplate="1000/T = %{x:.3f} [1/K]<br>ln D = %{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=1000.0 / (puntos_C + CERO_CELSIUS_K), y=np.log(puntos_D), mode="markers+text", name="Temperaturas de la tabla",
        text=[f"{int(t)} °C" for t in puntos_C], textposition="top right",
        marker=dict(color=COLOR_X, size=10),
        hovertemplate="%{text}<br>D = %{customdata:.3e} [m²/s]<extra></extra>", customdata=puntos_D,
    ))
    fig.update_layout(
        **LAYOUT_BASE, height=380,
        xaxis_title="1000 / T [1/K]  (la temperatura sube hacia la izquierda)",
        yaxis_title="ln D  (D en [m²/s])",
    )
    return fig


# ---------- Pantalla ----------
def mostrar():
    st.header("Módulo 4. Fundamento teórico")
    st.write(
        "Esta sección explica la física detrás del simulador: qué es la cementación, qué ecuaciones "
        "se usan y por qué se modela el carbono en austenita. Los números salen del mismo código "
        "que usan los demás módulos."
    )

    # ===== Bloque 1: qué es la cementación y qué es la difusión =====
    st.subheader("De la cementación a la difusión")

    with st.expander("1. ¿Qué es la cementación?", expanded=True):
        st.markdown(
            """
La **cementación** es un tratamiento termoquímico. Una pieza de acero de bajo carbono se calienta
hasta que su estructura es **austenita** y se mantiene en un medio que cede carbono (atmósfera,
polvo, sales). El carbono entra por la superficie y **difunde hacia el interior**: la superficie
termina con más carbono que el núcleo.

Después de cementar normalmente se templa. Con más carbono, la austenita de la superficie puede
transformarse en una martensita más dura que la del núcleo. **Eso último queda fuera de este
proyecto**: el simulador solo calcula cómo se reparte el carbono (el perfil de concentración).
No calcula dureza ni profundidad efectiva de endurecimiento.
            """
        )

    with st.expander("2. ¿Qué es la difusión?"):
        st.markdown(
            """
La **difusión** es el transporte de materia por el movimiento de átomos que saltan de una posición
a otra. Es un proceso **activado térmicamente**: a mayor temperatura, los átomos saltan con más
frecuencia. Cuando hay una diferencia de concentración, el resultado neto es un flujo de átomos
de las zonas de **mayor** concentración a las de **menor** concentración, hasta igualarse.

En la cementación, la superficie tiene mucho carbono (Cs) y el núcleo poco (C₀), por eso el carbono
avanza hacia dentro.
            """
        )

    with st.expander("3. Autodifusión e interdifusión"):
        st.markdown(
            """
| | Autodifusión | Interdifusión |
|---|---|---|
| Qué se mueve | Átomos del **mismo** elemento que el material (por ejemplo, Fe en Fe) | Átomos **distintos** (por ejemplo, C en Fe) |
| Gradiente de concentración | No lo necesita (se sigue con trazadores) | Sí, es la fuerza que lo impulsa |
| Ejemplo aquí | — | **Cementación: carbono en hierro** |

La cementación es **interdifusión** de carbono en hierro.
            """
        )

    with st.expander("4. Difusión intersticial y difusión por vacancias"):
        st.markdown(
            """
No hay que confundir el **tipo** de difusión (auto o inter) con el **mecanismo** (cómo saltan los átomos):

- **Por vacancias (sustitucional):** un átomo salta a un sitio de la red que está vacío. Así se mueven
  los átomos grandes, como el Fe. Necesita que existan vacancias, por eso es lento.
- **Intersticial:** un átomo pequeño salta entre los huecos (intersticios) de la red, sin necesitar
  vacancias. Así se mueve el **carbono** en el hierro. Es mucho más rápido que la difusión del Fe.

Resumen: la cementación es **interdifusión de carbono en hierro por mecanismo intersticial**.
            """
        )

    # ===== Bloque 2: leyes de Fick =====
    st.subheader("Las leyes de Fick")

    with st.expander("5. Primera ley de Fick"):
        st.latex(r"J = -D\,\frac{\partial C}{\partial x}")
        st.markdown(
            """
- **J**: flujo de átomos que atraviesa una unidad de área por unidad de tiempo
  (por ejemplo, [átomos/(m²·s)] o [kg/(m²·s)], según las unidades de C).
- **D**: coeficiente de difusión [m²/s].
- **∂C/∂x**: gradiente de concentración. El signo negativo indica que el flujo va de mayor a menor concentración.

Esta ley describe **cuánto** flujo hay en un instante dado, pero no dice cómo cambia el perfil con el
tiempo. Para eso se necesita la segunda ley.
            """
        )

    with st.expander("6. Segunda ley de Fick y la solución que usa el simulador"):
        st.markdown("Combinando la primera ley con la conservación de la materia, y con **D constante**:")
        st.latex(r"\frac{\partial C}{\partial t} = D\,\frac{\partial^2 C}{\partial x^2}")
        st.markdown("Se resuelve para un **sólido semiinfinito** con estas condiciones:")
        st.latex(r"C(x,0) = C_0 \quad (x>0), \qquad C(0,t) = C_s \quad (t>0), \qquad C(\infty,t) = C_0")
        st.markdown("La solución es:")
        st.latex(r"C(x,t) = C_0 + (C_s - C_0)\,\mathrm{erfc}\!\left(\frac{x}{2\sqrt{Dt}}\right)")
        st.markdown(
            """
donde erfc = 1 − erf es la función error complementaria. El perfil solo depende de la combinación
**x / (2√(Dt))**: por eso, al duplicar la profundidad hace falta **cuadruplicar** el tiempo.

**Para el diseño inverso** se invierte la ecuación. Con z = erfc⁻¹[(Cobj − C₀)/(Cs − C₀)]:
            """
        )
        st.latex(r"x = 2z\sqrt{Dt}, \qquad t = \frac{1}{D}\left(\frac{x}{2z}\right)^{2}, \qquad D\,t = \left(\frac{x}{2z}\right)^{2} = K")
        st.markdown(
            "Para una profundidad **x** y una concentración **Cobj** dadas, el producto **D·t = K** es constante: "
            "cualquier pareja (T, t) con ese producto da el mismo resultado. Esa es la curva que muestra el Módulo 2."
        )

    with st.expander("7. Estado estacionario y estado transitorio"):
        st.markdown(
            """
- **Estado estacionario:** la concentración en cada punto **no cambia con el tiempo** (∂C/∂t = 0) y el
  flujo es constante. Se usa la primera ley directamente.
- **Estado transitorio (no estacionario):** la concentración **sí cambia** con el tiempo. Se necesita la
  segunda ley.

La cementación es un proceso **transitorio**: el perfil de carbono se va "metiendo" cada vez más hacia
el interior mientras pasa el tiempo. Por eso se usa la segunda ley y la solución con erfc.
            """
        )

    # ===== Bloque 3: temperatura y Arrhenius =====
    st.subheader("Efecto de la temperatura")

    with st.expander("8. Influencia de la temperatura"):
        filas = tabla_difusividad()
        texto = "| T [°C] | T [K] | D [m²/s] | D / D(900 °C) |\n|---|---|---|---|\n"
        for f in filas:
            texto += f"| {f['T_C']} | {f['T_K']:.2f} | {f['D']:.3e} | {f['razon']:.2f} |\n"
        st.markdown(
            "Con los parámetros del modelo (carbono en Fe-γ), el coeficiente de difusión crece muy rápido con la temperatura:\n\n"
            + texto
        )
        st.markdown(
            f"Entre {filas[0]['T_C']} y {filas[-1]['T_C']} °C, D se multiplica por **{filas[-1]['razon']:.1f}**. "
            "Como para una misma profundidad y concentración D·t es constante, **el tiempo necesario baja en la "
            "misma proporción** (t ∝ 1/D). Esa es la idea del diseño inverso: subir la temperatura acorta el tratamiento."
        )
        st.caption(
            "Subir la temperatura tiene costos que este modelo no calcula (por ejemplo, el crecimiento de grano de la austenita)."
        )

    with st.expander("9. Ecuación de Arrhenius"):
        st.latex(r"D = D_0\,\exp\!\left(-\frac{Q}{R\,T}\right) \qquad\Longleftrightarrow\qquad \ln D = \ln D_0 - \frac{Q}{R}\cdot\frac{1}{T}")
        st.markdown(
            f"""
- **D₀ = {D0:.1e} [m²/s]**: factor de frecuencia (valor de las diapositivas de clase para C en Fe-γ).
- **Q = {Q:.0f} [J/mol]**: energía de activación (valor de las diapositivas de clase para C en Fe-γ).
  Es la "barrera" que debe vencer un salto atómico.
- **R = {R} [J/(mol·K)]**: constante de los gases.
- **T**: temperatura **absoluta** [K] = T[°C] + {CERO_CELSIUS_K}.

Si se grafica ln D contra 1/T sale una **línea recta** de pendiente −Q/R = −{Q / R:.0f} [K]. Esa es la forma de
obtener D₀ y Q a partir de mediciones.

Para el diseño inverso de temperatura (dado un D requerido):
            """
        )
        st.latex(r"T = -\frac{Q}{R\,\ln\!\left(D_{req}/D_0\right)}")
        st.plotly_chart(construir_figura_arrhenius(), width="stretch")

    # ===== Bloque 4: austenita =====
    st.subheader("¿Por qué austenita?")

    with st.expander("10. Por qué se modela en austenita (Fe-γ)"):
        st.markdown(
            f"""
A la temperatura de cementación (900–1050 °C en este proyecto) el hierro de bajo carbono está en forma de
**austenita (Fe-γ, estructura FCC)**. Se modela el carbono en austenita por estas razones:

1. **Es la fase estable** a la temperatura de cementación. Un acero de bajo carbono a 900–1050 °C está
   en el campo austenítico del diagrama Fe–Fe₃C.
2. **Disuelve mucho más carbono.** Según el diagrama de clase, la austenita llega a {SOLUBILIDAD_MAX} wt % de C
   (a 1147 °C) y la ferrita (BCC) solo a 0.02 wt %. Sin esa solubilidad no se podría enriquecer la superficie.
3. **Al templar**, la austenita rica en carbono se transforma en martensita, que es lo que da el endurecimiento
   superficial (eso no se calcula aquí).
            """
        )
        st.warning(
            "Aclaración importante: el carbono difunde **más rápido en ferrita (BCC) que en austenita (FCC)**. "
            "La estructura FCC **no** es la razón de una difusión más fácil. Se usa austenita por estabilidad de fase, "
            "solubilidad y transformación a martensita, no por velocidad de difusión."
        )

    # ===== Resumen =====
    st.subheader("Resumen de ecuaciones del simulador")
    st.markdown(
        """
| Qué se calcula | Ecuación |
|---|---|
| Coeficiente de difusión | D = D₀·exp(−Q/RT) |
| Perfil de carbono | C(x,t) = C₀ + (Cs − C₀)·erfc[x / (2√(Dt))] |
| Profundidad donde C = Cobj | x = 2z√(Dt),  z = erfc⁻¹[(Cobj − C₀)/(Cs − C₀)] |
| Tiempo para llegar a x | t = [x/(2z)]² / D |
| Temperatura para llegar a x en un tiempo dado | T = −Q / [R·ln(D_req/D₀)],  D_req = [x/(2z)]²/t |
| Longitud característica | L = √(Dt) |
| Sólido semiinfinito | espesor ≥ 4L (a esa profundidad erfc(2) ≈ 0.005) |
        """
    )
    st.caption(
        "La profundidad que calcula el simulador es donde la concentración de carbono llega a Cobj. "
        "No es la profundidad efectiva de endurecimiento: esa se define con un criterio de dureza después del temple."
    )

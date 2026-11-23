# Simulador Difusión Carbono. Página 1: portada y fundamento teórico.
# Primero se cuenta qué pasa en realidad (con dibujos de la pieza) y luego la teoría con sus ecuaciones.
# Todos los números salen de modelo.py (no están escritos a mano). app.py solo llama a mostrar().
#
# CUIDADO con el tema de la austenita: el carbono difunde MÁS RÁPIDO en ferrita (BCC) que en austenita (FCC).
# Se usa austenita por estabilidad de fase, solubilidad y porque se transforma en martensita al templar.

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from estilo import (
    C0_DEMO, COLOR_PERFIL, COLOR_X, CS_DEMO, LAYOUT_BASE, SOLUBILIDAD_MAX, T_DEMO, T_MAX, T_MIN,
)
from modelo import CERO_CELSIUS_K, D0, Q, R, calcular_difusividad
from modulos.inicio import mostrar_portada
from modulos.visual import construir_cortes_estaticos

TEMPERATURAS_TABLA = (900, 950, 1000, 1050)  # [°C]
TIEMPOS_DIBUJO = (0.0, 1.0, 4.0, 10.0)       # [h] para los cortes de la pieza


def tabla_difusividad():
    """Filas (T [°C], T [K], D [m²/s], D/D(900 °C)) para ilustrar el efecto de la temperatura."""
    D_ref = float(calcular_difusividad(TEMPERATURAS_TABLA[0]))
    return [{"T_C": T, "T_K": T + CERO_CELSIUS_K, "D": float(calcular_difusividad(T)),
             "razon": float(calcular_difusividad(T)) / D_ref} for T in TEMPERATURAS_TABLA]


def construir_figura_arrhenius():
    """D contra temperatura (eje vertical logarítmico): muestra lo rápido que crece D."""
    T_C = np.linspace(T_MIN - 50.0, T_MAX + 50.0, 200)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=T_C, y=calcular_difusividad(T_C), mode="lines", name="D(T)",
                             line=dict(color=COLOR_PERFIL, width=3),
                             hovertemplate="T = %{x:.0f} °C<br>D = %{y:.3e} m²/s<extra></extra>"))
    puntos = np.array(TEMPERATURAS_TABLA, dtype=float)
    fig.add_trace(go.Scatter(x=puntos, y=calcular_difusividad(puntos), mode="markers", name="Tabla",
                             marker=dict(color=COLOR_X, size=10),
                             hovertemplate="T = %{x:.0f} °C<br>D = %{y:.3e} m²/s<extra></extra>"))
    fig.update_layout(**LAYOUT_BASE)
    fig.update_layout(height=340, xaxis_title="Temperatura [°C]", yaxis_title="D [m²/s] (escala logarítmica)",
                      yaxis_type="log", showlegend=False)
    return fig


def mostrar():
    mostrar_portada()
    st.write("")

    # ===== 1. Qué pasa en realidad =====
    st.header("¿Qué pasa en realidad durante la cementación?")
    st.write(
        "La cementación es un tratamiento que le agrega carbono a la **superficie** de una pieza de acero de "
        "bajo carbono. Así, después del temple, la superficie queda dura y el interior sigue siendo tenaz. "
        "Esto es lo que pasa dentro del horno:"
    )
    c1, c2, c3, c4 = st.columns(4)
    pasos = [
        ("🔥 1. Se calienta", f"La pieza entra al horno y se calienta a {T_MIN:.0f}–{T_MAX:.0f} °C. A esa "
         "temperatura el acero es **austenita**, que puede disolver mucho carbono."),
        ("💨 2. La atmósfera da carbono", "Un gas rico en carbono rodea la pieza y mantiene la superficie con "
         "una concentración alta, **Cs**. El interior todavía tiene la concentración original, **C₀**."),
        ("➡️ 3. El carbono se mete", "Los átomos de carbono saltan entre los huecos de la red del hierro, de "
         "donde hay más hacia donde hay menos: eso es la **difusión**. Con más tiempo y más temperatura, llegan "
         "más profundo."),
        ("❄️ 4. Se templa", "Al final la pieza se enfría rápido. La superficie rica en carbono queda dura y el "
         "núcleo, tenaz. **Este paso ya no lo calcula el simulador.**"),
    ]
    for col, (titulo, texto) in zip((c1, c2, c3, c4), pasos):
        with col:
            with st.container(border=True):
                st.markdown(f"**{titulo}**")
                st.write(texto)

    st.markdown(
        f"**Así se vería un corte de la pieza** a {T_DEMO:.0f} °C con C₀ = {C0_DEMO:.2f} wt % y "
        f"Cs = {CS_DEMO:.2f} wt %. La superficie está arriba; el color oscuro es más carbono:"
    )
    st.plotly_chart(construir_cortes_estaticos(T_DEMO, TIEMPOS_DIBUJO, C0_DEMO, CS_DEMO), width="stretch")
    st.caption("Fíjate que pasar de 4 h a 10 h (2.5 veces más tiempo) no mete el carbono 2.5 veces más profundo: "
               "la profundidad crece con la raíz del tiempo. Eso lo explica la segunda ley de Fick (abajo).")

    st.divider()

    # ===== 2. Difusión =====
    st.header("La teoría detrás")
    st.subheader("1. ¿Qué es la difusión?")
    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(
            "La **difusión** es el transporte de materia por el movimiento de átomos que saltan de una posición "
            "a otra. Es un proceso **activado térmicamente**: a mayor temperatura, los átomos saltan más seguido. "
            "Si hay diferencia de concentración, el flujo neto va de donde hay **más** a donde hay **menos**."
        )
        st.markdown(
            "- **Autodifusión:** se mueven átomos del mismo elemento (Fe en Fe), sin gradiente de concentración.\n"
            "- **Interdifusión:** se mueven átomos distintos (C en Fe) por un gradiente de concentración. "
            "**La cementación es interdifusión.**"
        )
    with der:
        st.markdown(
            "**Mecanismos (cómo saltan los átomos):**\n\n"
            "- **Por vacancias:** un átomo grande (como el Fe) salta a un sitio vacío de la red. Es lento.\n"
            "- **Intersticial:** un átomo pequeño (como el **C**) salta entre los huecos de la red, sin necesitar "
            "vacancias. Es mucho más rápido.\n\n"
            "La cementación es **interdifusión de carbono en hierro por mecanismo intersticial**."
        )

    # ===== 3. Fick =====
    st.subheader("2. Leyes de Fick")
    izq, der = st.columns(2)
    with izq:
        st.markdown("**Primera ley:** el flujo de átomos es proporcional al gradiente de concentración.")
        st.latex(r"J = -D\,\frac{\partial C}{\partial x}")
        st.markdown(
            "Sirve para el **estado estacionario**, cuando la concentración en cada punto no cambia con el "
            "tiempo. El signo negativo indica que el flujo va de mayor a menor concentración."
        )
    with der:
        st.markdown("**Segunda ley:** cómo cambia la concentración con el tiempo (con D constante).")
        st.latex(r"\frac{\partial C}{\partial t} = D\,\frac{\partial^2 C}{\partial x^2}")
        st.markdown(
            "Sirve para el **estado transitorio**, cuando el perfil cambia con el tiempo. La cementación es "
            "transitoria: el carbono se va metiendo cada vez más."
        )

    st.markdown(
        "**La solución que usa el simulador.** Para una pieza gruesa (sólido semiinfinito), con la superficie "
        "en Cs desde el inicio y el interior en C₀:"
    )
    st.latex(r"C(x,t) = C_0 + (C_s - C_0)\,\mathrm{erfc}\!\left(\frac{x}{2\sqrt{Dt}}\right)")
    st.markdown(
        "- **erfc** es la función error complementaria: vale 1 en la superficie (x = 0) y baja a 0 muy adentro.\n"
        "- Todo depende de **x / (2√(Dt))**. Por eso, para meter el carbono **al doble de profundidad** hace "
        "falta **cuatro veces** el tiempo.\n"
        "- La distancia típica que recorre el carbono es **L = √(Dt)**."
    )

    # ===== 4. Temperatura =====
    st.subheader("3. ¿Por qué importa tanto la temperatura? Ecuación de Arrhenius")
    izq, der = st.columns([2, 3])
    filas = tabla_difusividad()
    with izq:
        st.latex(r"D = D_0\,\exp\!\left(-\frac{Q}{R\,T}\right)")
        st.markdown(
            f"- D₀ = {D0:.1e} [m²/s] y Q = {Q:.0f} [J/mol]: carbono en Fe-γ (diapositivas de clase).\n"
            f"- R = {R} [J/(mol·K)] y T en kelvin.\n"
            "- Q es la barrera de energía que debe vencer cada salto atómico."
        )
        texto = "| T [°C] | D [m²/s] | Veces D(900 °C) |\n|---|---|---|\n"
        for f in filas:
            texto += f"| {f['T_C']} | {f['D']:.2e} | {f['razon']:.1f} |\n"
        st.markdown(texto)
    with der:
        st.plotly_chart(construir_figura_arrhenius(), width="stretch")
        st.markdown(
            f"Entre {filas[0]['T_C']} y {filas[-1]['T_C']} °C, D se multiplica por **{filas[-1]['razon']:.1f}**. "
            "Para llegar a la misma profundidad, el tiempo baja en la misma proporción: **subir la temperatura "
            "acorta el tratamiento**."
        )

    # ===== 5. Austenita =====
    st.subheader("4. ¿Por qué se modela en austenita (Fe-γ)?")
    st.markdown(
        f"1. **Es la fase estable** a la temperatura de cementación en un acero de bajo carbono.\n"
        f"2. **Disuelve mucho más carbono:** hasta {SOLUBILIDAD_MAX} wt % (a 1147 °C) contra 0.02 wt % de la "
        "ferrita, según el diagrama de clase.\n"
        "3. **Al templar**, la austenita rica en carbono se transforma en martensita."
    )
    st.warning(
        "Ojo: el carbono difunde **más rápido en ferrita (BCC) que en austenita (FCC)**. No se usa austenita por "
        "velocidad de difusión, sino por estabilidad, solubilidad y transformación a martensita."
    )

    # ===== 6. Resumen =====
    st.subheader("5. Lo que calcula el simulador (y lo que no)")
    st.markdown(
        """
| Qué se calcula | Ecuación |
|---|---|
| Coeficiente de difusión | D = D₀·exp(−Q/RT) |
| Perfil de carbono | C(x,t) = C₀ + (Cs − C₀)·erfc[x / (2√(Dt))] |
| Profundidad donde C = Cobj | x = 2z√(Dt),  z = erfc⁻¹[(Cobj − C₀)/(Cs − C₀)] |
| Tiempo para llegar a x | t = [x/(2z)]² / D |
| Temperatura para llegar a x en un tiempo dado | T = −Q / [R·ln(D_req/D₀)] |
        """
    )
    st.info(
        "La profundidad que calcula el simulador es donde el carbono llega a una concentración objetivo. "
        "**No** calcula dureza, temple ni profundidad efectiva de endurecimiento."
    )

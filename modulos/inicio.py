# Simulador Difusión Carbono. 
# Los números salen de modelo.py.

import streamlit as st

from estilo import (
    CARRERA, COLOR_PERFIL, COLOR_TEXTO, FACULTAD, INTEGRANTES, NOMBRE_PROYECTO,
    PROFESORA, SUBTITULO_PROYECTO, T_MAX, T_MIN, UNIVERSIDAD,
)
from modelo import D0, Q, R, calcular_difusividad


def mostrar_portada():
    """Portada con los datos de la universidad, la profesora y el equipo."""
    equipo = "<br>".join(INTEGRANTES)
    # Ojo: el HTML va pegado a la izquierda y sin líneas en blanco, si no Streamlit lo toma como texto
    st.markdown(
        f"""
<div style="text-align:center; padding:2rem 1rem; background:#FFFFFF; color:{COLOR_TEXTO}; border-top:8px solid {COLOR_PERFIL}; border-bottom:1px solid #D0D7DE;">
<div style="font-size:1.15rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase;">{UNIVERSIDAD}</div>
<div style="font-size:1.05rem; margin-top:0.2rem;">{FACULTAD}</div>
<div style="font-size:1.05rem;">{CARRERA}</div>
<div style="font-size:2.6rem; font-weight:800; margin:1.6rem 0 0.4rem 0; color:{COLOR_PERFIL};">{NOMBRE_PROYECTO}</div>
<div style="font-size:1.1rem; margin-bottom:1.6rem;">{SUBTITULO_PROYECTO}</div>
<div style="font-size:1rem;"><b>Profesora:</b> {PROFESORA}</div>
<div style="font-size:1rem; margin-top:0.8rem;"><b>Equipo:</b><br>{equipo}</div>
</div>
        """,
        unsafe_allow_html=True,
    )

def mostrar_resumen_teorico():
    """Resumen corto de la teoría. La versión completa está en el Módulo 4."""
    st.header("Resumen teórico")
    st.write(
        "Antes de usar el simulador, estas son las ideas que lo sustentan. "
        "Son seis pasos cortos; la versión completa está en el Módulo 4."
    )

    D_inf = float(calcular_difusividad(T_MIN))
    D_sup = float(calcular_difusividad(T_MAX))

    # ----- 1 -----
    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(
            "**1. ¿Qué es la cementación?** Es un tratamiento termoquímico: una pieza de acero de bajo carbono se "
            "calienta hasta que es **austenita** y se deja en un medio que cede carbono. El carbono entra por la "
            "superficie y se va metiendo hacia el interior, así que la superficie queda con más carbono que el núcleo."
        )
    with der:
        st.info("Lo que calcula esta app es **cómo se reparte el carbono**. La dureza después del temple queda fuera.")

    # ----- 2 -----
    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(
            "**2. ¿Qué mueve al carbono? La difusión.** Los átomos de carbono saltan entre los huecos de la red del "
            "hierro (difusión *intersticial*) y, como hay más carbono afuera que adentro, el flujo neto va hacia el "
            "interior. La **primera ley de Fick** dice que el flujo es proporcional al gradiente de concentración."
        )
    with der:
        st.latex(r"J = -D\,\frac{\partial C}{\partial x}")

    # ----- 3 -----
    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(
            "**3. ¿Cómo cambia el perfil con el tiempo? Segunda ley de Fick.** El perfil de carbono cambia mientras "
            "pasa el tiempo (estado transitorio). Para una pieza gruesa (sólido semiinfinito), con la superficie en Cs "
            "y el interior en C₀, la solución usa la función error complementaria (erfc)."
        )
    with der:
        st.latex(r"\frac{\partial C}{\partial t} = D\,\frac{\partial^2 C}{\partial x^2}")
        st.latex(r"C(x,t) = C_0 + (C_s - C_0)\,\mathrm{erfc}\!\left(\frac{x}{2\sqrt{Dt}}\right)")

    # ----- 4 -----
    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(
            f"**4. ¿Y la temperatura? Arrhenius.** El coeficiente de difusión D crece muy rápido con la temperatura. "
            f"Aquí se usan D₀ = {D0:.1e} [m²/s] y Q = {Q:.0f} [J/mol] (carbono en Fe-γ, de las diapositivas de clase) "
            f"y R = {R} [J/(mol·K)]. Entre {T_MIN:.0f} y {T_MAX:.0f} °C, D pasa de {D_inf:.2e} a {D_sup:.2e} [m²/s], "
            f"o sea que se multiplica por {D_sup / D_inf:.1f}."
        )
    with der:
        st.latex(r"D = D_0\,\exp\!\left(-\frac{Q}{R\,T}\right)")

    # ----- 5 -----
    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(
            "**5. ¿Cómo se usa para diseñar?** Se invierte la solución: con "
            "z = erfc⁻¹[(Cobj − C₀)/(Cs − C₀)] se obtiene la profundidad x donde el carbono llega a la concentración "
            "objetivo Cobj, el tiempo necesario o la temperatura necesaria. Para una x y una Cobj dadas, el producto "
            "**D·t** es constante: se puede cambiar temperatura por tiempo."
        )
    with der:
        st.latex(r"x = 2z\sqrt{Dt} \qquad\Longrightarrow\qquad D\,t = \left(\frac{x}{2z}\right)^{2}")

    # ----- 6 -----
    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(
            "**6. ¿Por qué austenita?** A la temperatura de cementación el acero está en fase austenítica (Fe-γ, FCC), "
            "que es la fase estable y la que disuelve mucho carbono (hasta 2.11 wt %, contra 0.02 wt % de la ferrita). "
            "Además, al templar se transforma en martensita."
        )
    with der:
        st.info("Los resultados son soluciones matemáticas con supuestos. No son propiedades de un acero industrial.")

    st.divider()


def mostrar():
    """Portada y resumen juntos."""
    mostrar_portada()
    mostrar_resumen_teorico()

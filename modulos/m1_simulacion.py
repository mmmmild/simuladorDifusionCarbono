# Simulador Difusión Carbono. Página 2: simulación.
# Mueves temperatura, tiempo y concentraciones; la app dibuja cómo entra el carbono en la pieza
# (con animación), explica lo que pasa y por qué cada control tiene ese rango.
# Los cálculos salen de modelo.py. app.py solo llama a mostrar().

import numpy as np
import streamlit as st

from estilo import (
    C0_DEMO, C0_MAX, C0_MIN, COBJ_DEMO, COBJ_MAX, COBJ_MIN, CS_DEMO, CS_MAX, CS_MIN, ESTADO_PRECARGA,
    FACTOR_SEMIINFINITO, T_DEMO, T_H_DEMO, T_H_MAX, T_H_MIN, T_MAX, T_MIN,
)
from modelo import (
    CERO_CELSIUS_K, MARGEN_ACM, calcular_difusividad, calcular_longitud_difusion, calcular_profundidad,
    calcular_solubilidad_acm, calcular_temperatura_austenita_minima, calcular_z, verificar_austenita,
)
from modulos.visual import construir_animacion


# ---------- Lógica (sin Streamlit, para poder probarla aparte) ----------
def calcular_modulo1(T_C, t_h, C0, Cs, Cobj):
    """Junta lo que necesita la pantalla. Regresa un diccionario con:
      'errores' (no se puede calcular nada), 'avisos' (se calcula pero con cuidado) y los resultados."""
    r = {"errores": [], "avisos": [], "D": None, "L": None, "z": None, "x_obj": None, "espesor_minimo": None}
    if Cs <= C0:
        r["errores"].append("Cs debe ser mayor que C₀: en cementación la superficie tiene más carbono que el núcleo.")
        return r
    r["D"] = float(calcular_difusividad(T_C))             # [m²/s]
    r["L"] = float(calcular_longitud_difusion(t_h, T_C))  # [mm]
    r["espesor_minimo"] = FACTOR_SEMIINFINITO * r["L"]    # [mm]
    if C0 < Cobj < Cs:
        r["z"] = float(calcular_z(C0, Cs, Cobj))
        r["x_obj"] = float(calcular_profundidad(t_h, C0, Cs, Cobj, T_C))  # [mm]
    else:
        r["avisos"].append("La concentración objetivo debe quedar entre C₀ y Cs; con ese valor no hay profundidad.")
    r["avisos"].extend(verificar_austenita(T_C, C0, Cs))
    return r


def explicar_simulacion(T_C, t_h, C0, Cs, Cobj, r):
    """Texto (markdown) que cuenta, paso a paso y con los números de la simulación, lo que sucede."""
    T_K = T_C + CERO_CELSIUS_K  # [K]
    L = r["L"]                  # [mm]
    texto = (
        f"1. **La pieza está a {T_C:.0f} °C ({T_K:.2f} [K]).** A esa temperatura el carbono se mueve con un "
        f"coeficiente de difusión D = {r['D']:.3e} [m²/s].\n"
        f"2. **La superficie se mantiene en Cs = {Cs:.2f} wt % y el interior empezó con C₀ = {C0:.2f} wt %.** "
        f"Esa diferencia empuja al carbono hacia adentro: en el corte, la parte de arriba es la más oscura.\n"
        f"3. **Pasan {t_h:g} h.** El carbono recorre una distancia típica L = √(D·t) = {L:.3f} [mm]. "
        f"La concentración baja rápido en los primeros 2·L = {2 * L:.2f} [mm] y a 4·L = {4 * L:.2f} [mm] "
        f"ya casi es C₀.\n"
    )
    if r["x_obj"] is None:
        return texto + "4. **Elige una concentración objetivo entre C₀ y Cs** para ver hasta dónde llega.\n"
    x_obj = r["x_obj"]
    texto += (
        f"4. **Cobj = {Cobj:.2f} wt % llega hasta {x_obj:.3f} [mm]** (la línea azul punteada). "
        f"Se calcula con x = 2·z·L = 2 × {r['z']:.4f} × {L:.3f}.\n"
        f"5. **Para que el modelo valga**, la pieza debe medir al menos 4·L = {r['espesor_minimo']:.2f} [mm] de "
        f"espesor (sólido semiinfinito).\n"
    )
    t2 = min(2.0 * t_h, T_H_MAX)                              # [h]
    x_t2 = float(calcular_profundidad(t2, C0, Cs, Cobj, T_C))  # [mm]
    T2 = T_C + 50.0 if T_C + 50.0 <= T_MAX else T_C - 50.0    # [°C]
    x_T2 = float(calcular_profundidad(t_h, C0, Cs, Cobj, T2))  # [mm]
    texto += (
        f"\n**Pruébalo:**\n\n"
        f"- Con {t2:g} h en lugar de {t_h:g} h, la profundidad pasa de {x_obj:.3f} a {x_t2:.3f} [mm] "
        f"(× {x_t2 / x_obj:.2f}): crece con √t, no al mismo ritmo que el tiempo.\n"
        f"- Con {T2:.0f} °C y el mismo tiempo, pasa de {x_obj:.3f} a {x_T2:.3f} [mm] "
        f"(× {x_T2 / x_obj:.2f}): la temperatura cambia D de forma exponencial."
    )
    return texto


def tabla_rangos():
    """Tabla (markdown) con el porqué de cada rango. Los números salen de modelo.py y estilo.py."""
    A3_c0min = calcular_temperatura_austenita_minima(C0_MIN)      # [°C]
    A3_demo = calcular_temperatura_austenita_minima(C0_DEMO)      # [°C]
    acm_tmin = float(calcular_solubilidad_acm(T_MIN))              # [wt %]
    L_min = float(calcular_longitud_difusion(T_H_MIN, T_MIN))      # [mm]
    L_max = float(calcular_longitud_difusion(T_H_MAX, T_MAX))      # [mm]
    return f"""
| Control | Rango | ¿Por qué? |
|---|---|---|
| Temperatura | {T_MIN:.0f}–{T_MAX:.0f} °C | **Abajo:** todo el acero debe ser austenita. Con la línea A3 aproximada del diagrama de clase, un acero de {C0_MIN:.2f} wt % ya es austenita a {A3_c0min:.0f} °C y uno de {C0_DEMO:.2f} wt % a {A3_demo:.0f} °C. **Arriba:** la austenita es estable hasta la línea de 1147 °C; el máximo deja margen y evita efectos que el modelo no calcula, como el crecimiento de grano. |
| Tiempo | {T_H_MIN:g}–{T_H_MAX:g} h | **Abajo:** con {T_H_MIN:g} h a {T_MIN:.0f} °C el carbono apenas recorre L = {L_min:.2f} mm. **Arriba:** {T_H_MAX:g} h son más de dos días de horno; a {T_MAX:.0f} °C, L = {L_max:.2f} mm y la pieza tendría que medir al menos 4·L = {4 * L_max:.1f} mm para que el modelo valga. |
| C₀ (carbono del acero) | {C0_MIN:.2f}–{C0_MAX:.2f} wt % | La cementación se hace en **aceros de bajo carbono**: el núcleo debe quedar con poco carbono para ser tenaz. Con menos de {C0_MIN:.2f} wt % el acero no sería todo austenita a {T_MIN:.0f} °C (para hierro puro, A3 ≈ 912 °C). |
| Cs (carbono en la superficie) | {CS_MIN:.2f}–{CS_MAX:.2f} wt % | Debe ser mayor que C₀ para que entre carbono; con menos de {CS_MIN:.2f} wt % la superficie casi no se distinguiría del núcleo. El máximo queda debajo de lo que disuelve la austenita a {T_MIN:.0f} °C (≈ {acm_tmin:.2f} wt %, línea Acm aproximada, con {MARGEN_ACM} wt % de margen): así **no se forman carburos** en ningún punto del rango. |
| Cobj (concentración objetivo) | {COBJ_MIN:.2f}–{COBJ_MAX:.2f} wt % | Es la concentración cuya profundidad quieres conocer. Solo tiene sentido si queda **entre C₀ y Cs**. |
"""


# ---------- Pantalla ----------
def mostrar():
    st.header("Simulación")
    st.write(
        "Mueve los controles y observa cómo entra el carbono en la pieza. En la gráfica, presiona "
        "**▶ Ver la difusión** para ver el proceso desde el inicio hasta el tiempo que elegiste."
    )

    # Si venimos del diseño inverso, los valores del tratamiento elegido llegan en 'precarga'
    precarga = st.session_state.get(ESTADO_PRECARGA, {})
    if precarga:
        st.info(f"Valores cargados desde el diseño inverso: el objetivo era {precarga['Cobj']:.2f} wt % "
                f"a {precarga['x_obj_mm']:.2f} [mm]. Puedes moverlos.")

    col_controles, col_grafica = st.columns([1, 2.3])
    with col_controles:
        st.subheader("Condiciones")
        T_C = st.slider("Temperatura [°C]", T_MIN, T_MAX, float(precarga.get("T_C", T_DEMO)), 1.0,
                        help="Más temperatura → D más grande → el carbono entra más rápido.")
        t_h = st.slider("Tiempo [h]", T_H_MIN, T_H_MAX, float(precarga.get("t_h", T_H_DEMO)), 0.01,
                        help="Más tiempo → más profundidad, pero crece con la raíz del tiempo.")
        C0 = st.slider("C₀: carbono inicial del acero [wt %]", C0_MIN, C0_MAX, float(precarga.get("C0", C0_DEMO)),
                       0.01, help="El carbono que ya tenía el acero en todo su volumen.")
        Cs = st.slider("Cs: carbono en la superficie [wt %]", CS_MIN, CS_MAX, float(precarga.get("Cs", CS_DEMO)),
                       0.01, help="Lo fija la atmósfera del horno. Es el máximo que puede tener la pieza.")
        Cobj = st.slider("Cobj: concentración objetivo [wt %]", COBJ_MIN, COBJ_MAX,
                         float(precarga.get("Cobj", COBJ_DEMO)), 0.01,
                         help="¿Hasta qué profundidad llega esta concentración? Debe quedar entre C₀ y Cs.")

    r = calcular_modulo1(T_C, t_h, C0, Cs, Cobj)
    with col_grafica:
        if r["errores"]:
            for mensaje in r["errores"]:
                st.error(mensaje)
            return
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("D [m²/s]", f"{r['D']:.2e}", help="Coeficiente de difusión a esa temperatura (Arrhenius).")
        m2.metric("L = √(Dt) [mm]", f"{r['L']:.3f}", help="Distancia típica que recorre el carbono.")
        m3.metric("Profundidad para Cobj [mm]", f"{r['x_obj']:.3f}" if r["x_obj"] is not None else "—")
        m4.metric("Espesor mínimo de pieza [mm]", f"{r['espesor_minimo']:.2f}",
                  help="4·L: con menos espesor, el modelo de sólido semiinfinito deja de valer.")
        for aviso in r["avisos"]:
            st.warning(aviso)
        st.plotly_chart(construir_animacion(T_C, t_h, C0, Cs, Cobj), width="stretch")

    st.subheader("¿Qué está pasando?")
    st.markdown(explicar_simulacion(T_C, t_h, C0, Cs, Cobj, r))
    st.caption("La profundidad calculada es donde el carbono llega a Cobj. No es la profundidad efectiva de "
               "endurecimiento: esa depende del temple y de la dureza, que esta app no calcula.")

    st.subheader("¿Por qué estos rangos?")
    st.markdown(tabla_rangos())
    st.caption("Los rangos los eligió el equipo con el diagrama Fe–Fe₃C de clase y el propio modelo. "
               "No son estándares industriales.")

    with st.expander("¿Cómo se calculó? (ecuaciones con tus números)"):
        st.latex(r"D = D_0 \exp\!\left(-\frac{Q}{RT}\right)")
        st.latex(r"C(x,t) = C_0 + (C_s - C_0)\,\mathrm{erfc}\!\left(\frac{x}{2\sqrt{Dt}}\right)")
        st.latex(r"x_C = 2\,z\,\sqrt{Dt}, \qquad z = \mathrm{erfc}^{-1}\!\left(\frac{C_{obj}-C_0}{C_s-C_0}\right)")
        texto = (
            f"- T = {T_C:.0f} + {CERO_CELSIUS_K} = {T_C + CERO_CELSIUS_K:.2f} [K]\n"
            f"- D = {r['D']:.3e} [m²/s]\n"
            f"- L = √(Dt) = {r['L']:.3f} [mm]\n"
        )
        if r["z"] is not None:
            texto += f"- z = {r['z']:.4f} (sin unidades) y x = 2·z·L = {r['x_obj']:.3f} [mm]\n"
        st.markdown(texto)

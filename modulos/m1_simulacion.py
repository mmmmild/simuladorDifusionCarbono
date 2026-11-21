# Simulador Difusión Carbono. Módulo 1: simulación directa (persona A).
# Aquí va la pantalla y la lógica que la alimenta. Los cálculos de física salen de modelo.py.
# app.py solo llama a mostrar().

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from estilo import (
    COLOR_C0, COLOR_COBJ, COLOR_CS, COLOR_PERFIL, COLOR_X,
    ESTADO_PRECARGA, FACTOR_SEMIINFINITO, LAYOUT_BASE, SOLUBILIDAD_MAX, T_MAX, T_MIN,
)
from modulos.inicio import mostrar_portada, mostrar_resumen_teorico
from modelo import (
    CERO_CELSIUS_K, D0, Q, R,
    calcular_difusividad, calcular_longitud_difusion, calcular_perfil,
    calcular_profundidad, calcular_z, verificar_austenita,
)


# ---------- Lógica (sin Streamlit, para poder probarla aparte) ----------
def calcular_modulo1(T_C, t_h, C0, Cs, Cobj, x_max_mm, espesor_mm=None):
    """Junta todo lo que necesita la pantalla del Módulo 1.
    Regresa un diccionario. Si algo no tiene sentido físico:
      - 'errores': no se puede calcular nada.
      - 'avisos': se calcula, pero hay que tener cuidado."""
    r = {
        "errores": [], "avisos": [],
        "D": None, "L": None, "z": None, "x_obj": None,
        "x": None, "C": None, "espesor_minimo": None,
    }

    if Cs <= C0:
        r["errores"].append("Cs debe ser mayor que C₀: en cementación la superficie tiene más carbono que el núcleo.")
        return r

    r["D"] = float(calcular_difusividad(T_C))            # [m²/s]
    r["L"] = float(calcular_longitud_difusion(t_h, T_C))  # [mm]
    r["x"] = np.linspace(0.0, x_max_mm, 400)              # [mm]
    r["C"] = calcular_perfil(r["x"], t_h, C0, Cs, T_C)    # [wt %]

    if C0 < Cobj < Cs:
        r["z"] = float(calcular_z(C0, Cs, Cobj))
        r["x_obj"] = float(calcular_profundidad(t_h, C0, Cs, Cobj, T_C))  # [mm]
        if r["x_obj"] > x_max_mm:
            r["avisos"].append(
                f"La profundidad calculada ({r['x_obj']:.2f} [mm]) queda fuera de la gráfica. "
                "Aumenta la profundidad máxima a visualizar."
            )
    else:
        r["avisos"].append(
            "La concentración objetivo debe cumplir C₀ < Cobj < Cs. Con ese valor no existe una profundidad."
        )

    # Chequeo aproximado de fases (A3 y Acm del diagrama de clase): solo avisa, no frena nada
    r["avisos"].extend(verificar_austenita(T_C, C0, Cs))

    if espesor_mm is not None:
        r["espesor_minimo"] = FACTOR_SEMIINFINITO * r["L"]  # [mm]
        if espesor_mm < r["espesor_minimo"]:
            r["avisos"].append(
                f"El espesor ({espesor_mm:.2f} [mm]) es menor que 4·L = {r['espesor_minimo']:.2f} [mm]. "
                "El supuesto de sólido semiinfinito deja de ser razonable y el resultado pierde validez."
            )
    return r


def explicar_simulacion(T_C, t_h, C0, Cs, Cobj, r):
    """Texto (markdown) que cuenta, paso a paso y con los números de la simulación, lo que sucede.
    'r' es lo que regresa calcular_modulo1. Los números salen de modelo.py, no están escritos a mano."""
    T_K = T_C + CERO_CELSIUS_K  # [K]
    L = r["L"]                  # [mm]
    texto = (
        f"1. **Se calienta la pieza a {T_C:.0f} °C ({T_K:.2f} [K]).** A esa temperatura el carbono se mueve "
        f"con un coeficiente de difusión D = {r['D']:.3e} [m²/s]. Con más temperatura, D sube muy rápido (Arrhenius).\n"
        f"2. **La superficie se mantiene en Cs = {Cs:.2f} wt % y el interior parte de C₀ = {C0:.2f} wt %.** "
        f"Esa diferencia empuja al carbono hacia adentro: en la gráfica, la curva empieza en Cs (en x = 0) "
        f"y baja hacia C₀ (lejos de la superficie).\n"
        f"3. **Pasan {t_h:g} h.** En ese tiempo el carbono recorre una distancia característica "
        f"L = √(D·t) = {L:.3f} [mm]. La concentración cae rápido entre 0 y 2·L = {2 * L:.3f} [mm], "
        f"y a partir de 4·L = {4 * L:.3f} [mm] ya casi es igual a C₀ (erfc(2) ≈ 0.005).\n"
    )
    if r["x_obj"] is None:
        texto += (
            "4. **Falta elegir una concentración objetivo válida.** Para ver la profundidad, Cobj debe estar "
            "entre C₀ y Cs.\n"
        )
        return texto

    x_obj = r["x_obj"]  # [mm]
    texto += (
        f"4. **¿Hasta dónde llega Cobj = {Cobj:.2f} wt %?** Se busca el punto donde la curva baja hasta Cobj. "
        f"Eso ocurre en x = 2·z·L = 2 × {r['z']:.4f} × {L:.3f} = **{x_obj:.3f} [mm]** "
        f"(el punto marcado en la gráfica).\n"
        f"5. **Qué significa y qué no.** Es la profundidad a la que el carbono alcanza la concentración que elegiste. "
        f"No es la profundidad efectiva de endurecimiento: esa depende del temple y de la dureza.\n"
    )

    # Dos preguntas "¿y si...?" con números del propio modelo
    t2 = 2.0 * t_h                                          # [h]
    x_t2 = float(calcular_profundidad(t2, C0, Cs, Cobj, T_C))  # [mm]
    T2 = T_C + 25.0 if T_C + 25.0 <= T_MAX else T_C - 25.0  # [°C] otra temperatura dentro del intervalo
    x_T2 = float(calcular_profundidad(t_h, C0, Cs, Cobj, T2))  # [mm]
    texto += (
        f"\n**Pruébalo:**\n\n"
        f"- Si duplicas el tiempo ({t2:g} h), la profundidad **no** se duplica: crece con √t y pasa de "
        f"{x_obj:.3f} a {x_t2:.3f} [mm] (× {x_t2 / x_obj:.2f}).\n"
        f"- Con {T2:.0f} °C y el mismo tiempo, la profundidad pasa de {x_obj:.3f} a {x_T2:.3f} [mm]."
    )
    return texto


def construir_figura(x, C, C0, Cs, Cobj, x_obj):
    """Gráfica de concentración de carbono [wt %] contra profundidad [mm]."""
    fig = go.Figure()

    # Perfil de concentración
    fig.add_trace(go.Scatter(
        x=x, y=C, mode="lines", name="C(x, t)",
        line=dict(color=COLOR_PERFIL, width=3),
        hovertemplate="x = %{x:.3f} mm<br>C = %{y:.3f} wt %<extra></extra>",
    ))

    # Líneas horizontales de referencia
    fig.add_hline(y=Cs, line_dash="dash", line_color=COLOR_CS,
                  annotation_text=f"Cs = {Cs:.2f} wt %", annotation_position="top right")
    fig.add_hline(y=C0, line_dash="dash", line_color=COLOR_C0,
                  annotation_text=f"C₀ = {C0:.2f} wt %", annotation_position="bottom right")

    # Concentración objetivo y la profundidad a la que se alcanza
    if C0 < Cobj < Cs:
        fig.add_hline(y=Cobj, line_dash="dot", line_color=COLOR_COBJ,
                      annotation_text=f"Cobj = {Cobj:.2f} wt %", annotation_position="top right")
        if x_obj is not None and x_obj <= x[-1]:
            fig.add_vline(x=x_obj, line_dash="dot", line_color=COLOR_X)
            fig.add_trace(go.Scatter(
                x=[x_obj], y=[Cobj], mode="markers", name=f"x = {x_obj:.3f} mm para Cobj",
                marker=dict(size=12, color=COLOR_X, line=dict(width=2, color="white")),
                hovertemplate="x = %{x:.3f} mm<br>C = %{y:.3f} wt %<extra></extra>",
            ))

    fig.update_layout(
        **LAYOUT_BASE,
        xaxis_title="Profundidad [mm]",
        yaxis_title="Concentración de carbono [wt %]",
        xaxis_range=[0, float(x[-1])],
        yaxis_range=[0, Cs * 1.12],
        hovermode="x unified",
        height=480,
    )
    return fig


# ---------- Pantalla ----------
def mostrar():
    # Si venimos del Módulo 2, los valores del tratamiento elegido llegan en 'precarga'
    precarga = st.session_state.get(ESTADO_PRECARGA, {})
    if precarga:
        st.success("Cargaste un tratamiento desde el Módulo 2. [Baja al simulador ↓](#simulador) para verlo.")

    # Arriba: portada y resumen teórico. Abajo: el simulador.
    mostrar_portada()
    mostrar_resumen_teorico()

    st.header("Simulador (Módulo 1: simulación directa)", anchor="simulador")
    st.write(
        "Aquí pruebas la teoría de arriba con números. La app calcula el coeficiente de difusión, "
        "el perfil de carbono y la profundidad a la que se alcanza la concentración objetivo."
    )
    st.markdown(
        "**Cómo usarlo:** (1) escribe las condiciones del tratamiento en la columna izquierda; "
        "(2) mira el perfil de carbono y los resultados a la derecha; "
        "(3) lee la sección **¿Qué está pasando?** debajo de la gráfica: se actualiza con tus valores."
    )
    if precarga:
        st.info(
            f"Valores cargados desde el Módulo 2: el objetivo era {precarga['Cobj']:.2f} wt % "
            f"a {precarga['x_obj_mm']:.2f} [mm]. Puedes editarlos."
        )

    col_parametros, col_resultados = st.columns([1, 2])

    # ----- Columna izquierda: parámetros -----
    with col_parametros:
        st.subheader("Parámetros")
        T_C = st.number_input(
            "Temperatura de cementación [°C]", min_value=T_MIN, max_value=T_MAX,
            value=precarga.get("T_C", 927.0), step=5.0, format="%.1f",
            help="Intervalo de demostración del proyecto: 900–1050 °C.",
        )
        t_h = st.number_input(
            "Tiempo de tratamiento [h]", min_value=0.1, max_value=1000.0,
            value=precarga.get("t_h", 10.0), step=0.5, format="%.2f",
        )
        C0 = st.number_input(
            "Concentración inicial C₀ [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX,
            value=precarga.get("C0", 0.20), step=0.05, format="%.2f",
        )
        Cs = st.number_input(
            "Concentración superficial Cs [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX,
            value=precarga.get("Cs", 1.00), step=0.05, format="%.2f",
            help="Depende del potencial de carbono de la atmósfera carburizante.",
        )
        Cobj = st.number_input(
            "Concentración objetivo Cobj [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX,
            value=precarga.get("Cobj", 0.40), step=0.05, format="%.2f",
        )
        x_max_mm = st.number_input(
            "Profundidad máxima a visualizar [mm]", min_value=0.1, max_value=20.0,
            value=precarga.get("x_max_mm", 2.0), step=0.5, format="%.1f",
        )

        usar_espesor = st.checkbox("Comprobar el supuesto de sólido semiinfinito (indicar espesor)")
        espesor_mm = None
        if usar_espesor:
            espesor_mm = st.number_input(
                "Espesor de la pieza [mm]", min_value=0.1, max_value=200.0,
                value=10.0, step=0.5, format="%.1f",
                help="Si se cementa por las dos caras, escribe la mitad del espesor.",
            )

    r = calcular_modulo1(T_C, t_h, C0, Cs, Cobj, x_max_mm, espesor_mm)

    # ----- Columna derecha: resultados -----
    with col_resultados:
        st.subheader("Resultados")

        if r["errores"]:
            for mensaje in r["errores"]:
                st.error(mensaje)
            return

        c1, c2, c3 = st.columns(3)
        c1.metric("D [m²/s]", f"{r['D']:.3e}",
                  help="Coeficiente de difusión del carbono en Fe-γ a esa temperatura (Arrhenius).")
        c2.metric("L = √(Dt) [mm]", f"{r['L']:.3f}",
                  help="Longitud característica de difusión. En la fórmula de Fick aparece 2·L.")
        c3.metric("x para Cobj [mm]", f"{r['x_obj']:.3f}" if r["x_obj"] is not None else "—",
                  help="Profundidad a la que la concentración de carbono llega a Cobj.")

        for aviso in r["avisos"]:
            st.warning(aviso)

        st.plotly_chart(construir_figura(r["x"], r["C"], C0, Cs, Cobj, r["x_obj"]), width="stretch")

        st.caption(
            "La profundidad calculada es donde la concentración de carbono llega a Cobj. "
            "No es la profundidad efectiva de endurecimiento: esa depende del temple y de la dureza, "
            "y esta app no las calcula."
        )

    # ----- Lo que sucede, paso a paso (se actualiza con los valores de la pantalla) -----
    st.subheader("¿Qué está pasando?")
    st.markdown(explicar_simulacion(T_C, t_h, C0, Cs, Cobj, r))

    # ----- Explicación y procedencia de los parámetros -----
    with st.expander("¿Cómo se calculó?"):
        st.latex(r"D = D_0 \exp\!\left(-\frac{Q}{RT}\right)")
        st.latex(r"C(x,t) = C_0 + (C_s - C_0)\,\mathrm{erfc}\!\left(\frac{x}{2\sqrt{Dt}}\right)")
        st.latex(r"x_C = 2\,z\,\sqrt{Dt}, \qquad z = \mathrm{erfc}^{-1}\!\left(\frac{C_{obj}-C_0}{C_s-C_0}\right)")
        texto = (
            f"- Temperatura absoluta: T = {T_C:.0f} + {CERO_CELSIUS_K} = {T_C + CERO_CELSIUS_K:.2f} [K]\n"
            f"- Coeficiente de difusión: D = {r['D']:.3e} [m²/s]\n"
            f"- Longitud característica: L = √(Dt) = {r['L']:.3f} [mm]  (2L = {2 * r['L']:.3f} [mm])\n"
        )
        if r["z"] is not None:
            texto += f"- z = erfc⁻¹(...) = {r['z']:.4f} (sin unidades), y x = 2·z·L = {r['x_obj']:.3f} [mm]\n"
        if r["espesor_minimo"] is not None:
            texto += f"- Espesor mínimo para sólido semiinfinito: 4·L = {r['espesor_minimo']:.2f} [mm]\n"
        st.markdown(texto)

    with st.expander("Parámetros del modelo y su procedencia"):
        st.markdown(
            f"""
| Parámetro | Valor | Procedencia |
|---|---|---|
| D₀ | {D0:.1e} [m²/s] | Tabla de difusión de las diapositivas de clase (C en Fe-γ) |
| Q | {Q:.0f} [J/mol] | Tabla de difusión de las diapositivas de clase (C en Fe-γ) |
| R | {R} [J/(mol·K)] | Elegido porque reproduce los datos de referencia (ver Validación) |
| C₀, Cs, Cobj | los que escribiste | Valores de demostración, no son estándares industriales |
| Líneas A3 y Acm | aproximadas | Puntos rotulados del diagrama de clase (0.8 wt % a 723 °C y 2.11 wt % a 1147 °C) y el ejercicio de clase (0.42 wt % a 780 °C). Acm es una recta entre dos puntos. Solo sirven para avisar |
            """
        )
        st.caption(
            "Cs depende del potencial de carbono de la atmósfera; no sale directamente del diagrama Fe-C. "
            f"El máximo de {SOLUBILIDAD_MAX} wt % en los campos de concentración es la máxima solubilidad "
            "del carbono en austenita según el diagrama Fe-Fe₃C."
        )

# Simulador Difusión Carbono. Página 3: diseño inverso.
# Tú dices qué resultado quieres (profundidad y concentración) y la app dice con qué temperatura y tiempo
# se logra. Hay pocos controles y una curva de referencia gris para que se note el efecto de mover cada uno.
# Los cálculos salen de modelo.py. app.py solo llama a mostrar().

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from estilo import (
    C0_DEMO, C0_MAX, C0_MIN, COBJ_DEMO, COBJ_MAX, COBJ_MIN, COLOR_PERFIL, COLOR_REFERENCIA, COLOR_TEXTO,
    COLOR_X, CS_DEMO, CS_MAX, CS_MIN, ESTADO_PAGINA, ESTADO_PRECARGA, LAYOUT_BASE, PAGINA_SIMULADOR,
    T_MAX, T_MIN, X_OBJ_DEMO, X_OBJ_MAX, X_OBJ_MIN,
)
from modelo import calcular_diseno_inverso, calcular_temperatura, verificar_austenita

PASO_C = 25.0      # [°C] temperaturas de la tabla: 900, 925, ..., 1050
T_COMPARAR = 950.0 # [°C] temperatura en la que se compara contra la referencia


# ---------- Lógica (sin Streamlit, para poder probarla aparte) ----------
def calcular_modulo2(x_obj_mm, tol_mm, C0, Cs, Cobj):
    """Diseño inverso con los datos elegidos y con la referencia (valores de demostración).
    Regresa 'errores', 'avisos', 'res' (lo elegido) y 'ref' (la referencia)."""
    r = {"errores": [], "avisos": [], "res": None, "ref": None}
    if Cs <= C0:
        r["errores"].append("Cs debe ser mayor que C₀: la superficie tiene que tener más carbono que el núcleo.")
    elif not (C0 < Cobj < Cs):
        r["errores"].append(f"La concentración objetivo debe quedar entre C₀ = {C0:.2f} y Cs = {Cs:.2f} wt %.")
    elif tol_mm >= x_obj_mm:
        r["errores"].append("La tolerancia debe ser menor que la profundidad objetivo.")
    if r["errores"]:
        return r
    r["res"] = calcular_diseno_inverso(x_obj_mm, tol_mm, C0, Cs, Cobj, T_MIN, T_MAX, PASO_C)
    r["ref"] = calcular_diseno_inverso(X_OBJ_DEMO, 0.0, C0_DEMO, CS_DEMO, COBJ_DEMO, T_MIN, T_MAX, PASO_C)
    r["avisos"].extend(verificar_austenita(T_MIN, C0, Cs))  # a la T más baja es donde más se exige
    return r


def _t_en(res, T_C):
    """Tiempo [h] de la tabla a una temperatura dada."""
    i = int(np.argmin(np.abs(res["tabla"]["T_C"] - T_C)))
    return float(res["tabla"]["t_h"][i]), float(res["tabla"]["t_min_h"][i]), float(res["tabla"]["t_max_h"][i])


def explicar_efectos(r, x_obj_mm, tol_mm, C0, Cs, Cobj):
    """Texto que explica qué efecto tiene cada control, comparando contra la referencia."""
    t, t_min, t_max = _t_en(r["res"], T_COMPARAR)
    t_ref = _t_en(r["ref"], T_COMPARAR)[0]
    f_x = (x_obj_mm / X_OBJ_DEMO) ** 2
    texto = (
        f"**Referencia (curva gris):** {X_OBJ_DEMO:.2f} mm con {COBJ_DEMO:.2f} wt %, C₀ = {C0_DEMO:.2f} y "
        f"Cs = {CS_DEMO:.2f} wt %. A {T_COMPARAR:.0f} °C necesita {t_ref:.2f} h. **Tu elección necesita {t:.2f} h** "
        f"(× {t / t_ref:.2f}).\n\n"
        + (f"- **Profundidad objetivo:** el tiempo crece con el **cuadrado** de la profundidad (t ∝ x²). "
           f"Pedir {x_obj_mm:.2f} mm en lugar de {X_OBJ_DEMO:.2f} mm multiplica el tiempo por "
           f"({x_obj_mm:.2f}/{X_OBJ_DEMO:.2f})² = {f_x:.2f}.\n"
           if abs(x_obj_mm - X_OBJ_DEMO) > 1e-9 else
           f"- **Profundidad objetivo:** está igual que la referencia. Si la subes, el tiempo crece con el "
           f"**cuadrado** de la profundidad (t ∝ x²): el doble de profundidad pide cuatro veces el tiempo.\n")
        + f"- **Concentración objetivo:** entre más alta sea Cobj (más cerca de Cs), más difícil es que llegue lejos, "
        f"así que hace falta más tiempo. Aquí el factor z vale {r['res']['z']:.3f} "
        f"(referencia: {r['ref']['z']:.3f}); el tiempo es proporcional a 1/z².\n"
    )
    if tol_mm > 0:
        texto += (
            f"- **Tolerancia ± {tol_mm:.2f} mm:** no hace falta un tiempo exacto. A {T_COMPARAR:.0f} °C, cualquier "
            f"tiempo entre **{t_min:.2f} y {t_max:.2f} h** deja la profundidad dentro de "
            f"{x_obj_mm - tol_mm:.2f}–{x_obj_mm + tol_mm:.2f} mm (la franja naranja).\n"
        )
    else:
        texto += "- **Tolerancia:** está en 0, así que solo sirve el tiempo exacto de la curva.\n"
    if (C0, Cs) != (C0_DEMO, CS_DEMO):
        texto += ("- **C₀ y Cs:** los cambiaste respecto a la referencia. Una Cs más alta (o una C₀ más baja) "
                  "deja más espacio entre las concentraciones, cambia z y también cambia el tiempo.\n")
    texto += (
        f"- **Temperatura:** en toda la curva se cumple D(T)·t = constante = {r['res']['K_m2']:.3e} [m²]. "
        "Subir la temperatura acorta el tiempo de forma exponencial (Arrhenius)."
    )
    return texto


def construir_figura(r, x_obj_mm, tol_mm, T_sel=None, t_sel=None):
    """Curva temperatura–tiempo elegida (con su franja de tolerancia) y la curva de referencia en gris."""
    curva, ref = r["res"]["curva"], r["ref"]["curva"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ref["t_h"], y=ref["T_C"], mode="lines", name="Referencia",
                             line=dict(color=COLOR_REFERENCIA, width=3, dash="dash"),
                             hovertemplate="Referencia<br>t = %{x:.2f} h<br>T = %{y:.0f} °C<extra></extra>"))
    if tol_mm > 0:
        fig.add_trace(go.Scatter(x=curva["t_min_h"], y=curva["T_C"], mode="lines", showlegend=False,
                                 line=dict(color=COLOR_PERFIL, width=0.5), hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=curva["t_max_h"], y=curva["T_C"], mode="lines",
                                 name=f"Franja ± {tol_mm:.2f} mm", line=dict(color=COLOR_PERFIL, width=0.5),
                                 fill="tonextx", fillcolor="rgba(232,89,12,0.18)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=curva["t_h"], y=curva["T_C"], mode="lines", name=f"Tu objetivo: {x_obj_mm:.2f} mm",
                             line=dict(color=COLOR_PERFIL, width=4),
                             hovertemplate="t = %{x:.2f} h<br>T = %{y:.0f} °C<extra></extra>"))
    if T_sel is not None:
        fig.add_trace(go.Scatter(x=[t_sel], y=[T_sel], mode="markers+text", name="Tratamiento elegido",
                                 text=[f"  {T_sel:.0f} °C, {t_sel:.2f} h"], textposition="middle right",
                                 marker=dict(size=15, symbol="star", color=COLOR_X, line=dict(width=1.5, color=COLOR_TEXTO))))
    t_max = max(float(np.max(curva["t_max_h"])), float(np.max(ref["t_h"])))
    fig.update_layout(**LAYOUT_BASE)
    fig.update_layout(height=450, xaxis_title="Tiempo en el horno [h]", yaxis_title="Temperatura [°C]",
                      xaxis_range=[0, t_max * 1.05], yaxis_range=[T_MIN - 5, T_MAX + 5])
    return fig


def armar_tabla(res, con_tolerancia):
    """Tabla de combinaciones (T, t) lista para mostrar."""
    t = res["tabla"]
    datos = {"Temperatura [°C]": [f"{v:g}" for v in t["T_C"]], "Tiempo [h]": [f"{v:.2f}" for v in t["t_h"]]}
    if con_tolerancia:
        datos["Tiempo mínimo [h]"] = [f"{v:.2f}" for v in t["t_min_h"]]
        datos["Tiempo máximo [h]"] = [f"{v:.2f}" for v in t["t_max_h"]]
    return pd.DataFrame(datos)


def _llevar_al_simulador(T_C, t_h, C0, Cs, Cobj, x_obj_mm):
    """Botón: guarda el tratamiento elegido y cambia a la página de simulación."""
    st.session_state[ESTADO_PRECARGA] = {
        "T_C": round(float(T_C), 1), "t_h": round(float(t_h), 2),
        "C0": float(C0), "Cs": float(Cs), "Cobj": float(Cobj), "x_obj_mm": float(x_obj_mm),
    }
    st.session_state[ESTADO_PAGINA] = PAGINA_SIMULADOR


# ---------- Pantalla ----------
def mostrar():
    st.header("Diseño inverso")
    st.write(
        "Aquí se trabaja al revés que en la simulación: **tú dices qué resultado quieres** y la app te dice con qué "
        "combinaciones de temperatura y tiempo se logra. Mueve un control a la vez y compara contra la curva gris."
    )

    col_controles, col_grafica = st.columns([1, 2.3])
    with col_controles:
        st.subheader("¿Qué quieres lograr?")
        x_obj_mm = st.slider("Profundidad objetivo [mm]", X_OBJ_MIN, X_OBJ_MAX, X_OBJ_DEMO, 0.05,
                             help="Hasta dónde quieres que llegue la concentración objetivo.")
        Cobj = st.slider("Concentración objetivo Cobj [wt %]", COBJ_MIN, COBJ_MAX, COBJ_DEMO, 0.01,
                         help="Cuánto carbono quieres tener a esa profundidad.")
        tol_mm = st.slider("Tolerancia ± [mm]", 0.0, 0.20, 0.05, 0.01,
                           help="Cuánto puede variar la profundidad y seguir siendo aceptable.")
        with st.expander("Acero y atmósfera (opcional)"):
            C0 = st.slider("C₀: carbono inicial del acero [wt %]", C0_MIN, C0_MAX, C0_DEMO, 0.01, key="m2_C0")
            Cs = st.slider("Cs: carbono en la superficie [wt %]", CS_MIN, CS_MAX, CS_DEMO, 0.01, key="m2_Cs")

    r = calcular_modulo2(x_obj_mm, tol_mm, C0, Cs, Cobj)
    with col_grafica:
        if r["errores"]:
            for mensaje in r["errores"]:
                st.error(mensaje)
            return
        for aviso in r["avisos"]:
            st.warning(aviso)

        tabla = r["res"]["tabla"]
        t_ref = _t_en(r["ref"], T_COMPARAR)[0]
        t_950 = _t_en(r["res"], T_COMPARAR)[0]
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Tiempo a {tabla['T_C'][0]:.0f} °C [h]", f"{tabla['t_h'][0]:.2f}")
        c2.metric(f"Tiempo a {T_COMPARAR:.0f} °C [h]", f"{t_950:.2f}", delta=f"{t_950 - t_ref:+.2f} h vs referencia",
                  delta_color="inverse")
        c3.metric(f"Tiempo a {tabla['T_C'][-1]:.0f} °C [h]", f"{tabla['t_h'][-1]:.2f}")

        opciones = [float(v) for v in tabla["T_C"]]
        T_sel = st.select_slider("Elige una temperatura para ver su tiempo", options=opciones, value=T_COMPARAR,
                                 format_func=lambda v: f"{v:g} °C")
        t_sel = _t_en(r["res"], T_sel)[0]
        st.plotly_chart(construir_figura(r, x_obj_mm, tol_mm, T_sel, t_sel), width="stretch")
        st.button(f"Comprobar {T_sel:g} °C y {t_sel:.2f} h en la simulación", on_click=_llevar_al_simulador,
                  args=(T_sel, t_sel, C0, Cs, Cobj, x_obj_mm))

    st.subheader("¿Qué efecto tiene cada control?")
    st.markdown(explicar_efectos(r, x_obj_mm, tol_mm, C0, Cs, Cobj))

    st.subheader("Combinaciones posibles")
    st.dataframe(armar_tabla(r["res"], tol_mm > 0), width="stretch", hide_index=True)

    with st.expander("¿Y si ya tengo el tiempo? ¿Qué temperatura necesito?"):
        t_disp = st.slider("Tiempo disponible [h]", 0.5, 50.0, 10.0, 0.5, key="m2_t_disp")
        try:
            T_nec = float(calcular_temperatura(x_obj_mm, t_disp, C0, Cs, Cobj))
            st.metric("Temperatura necesaria [°C]", f"{T_nec:.0f}")
            if T_nec < T_MIN or T_nec > T_MAX:
                st.warning(f"Esa temperatura queda fuera del rango del simulador ({T_MIN:.0f}–{T_MAX:.0f} °C). "
                           "Conviene cambiar el tiempo.")
        except ValueError as error:
            st.error(str(error))

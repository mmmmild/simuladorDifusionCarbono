# Simulador Difusión Carbono. Módulo 2: diseño inverso (persona A).
# Aquí va la pantalla y la lógica que la alimenta. Los cálculos de física salen de modelo.py.
# app.py solo llama a mostrar().

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from estilo import (
    COLOR_TEXTO, COLOR_X, ESTADO_PAGINA, ESTADO_PRECARGA, FACTOR_SEMIINFINITO, LAYOUT_BASE,
    PAGINA_SIMULADOR, SOLUBILIDAD_MAX, T_MAX, T_MIN,
)
from modelo import (
    Q, R, calcular_diseno_inverso, calcular_longitud_difusion, calcular_temperatura, verificar_austenita,
)


# ---------- Lógica (sin Streamlit, para poder probarla aparte) ----------
def calcular_modulo2(x_obj_mm, tol_mm, C0, Cs, Cobj, T_min_C, T_max_C, paso_C):
    """Junta lo que necesita la pantalla del Módulo 2 (diseño inverso).
    Regresa un diccionario con 'errores' (no se puede calcular) y 'res' (lo que regresa
    calcular_diseno_inverso de modelo.py)."""
    r = {"errores": [], "avisos": [], "res": None}

    if Cs <= C0:
        r["errores"].append("Cs debe ser mayor que C₀: en cementación la superficie tiene más carbono que el núcleo.")
    elif not (C0 < Cobj < Cs):
        r["errores"].append("La concentración objetivo debe cumplir C₀ < Cobj < Cs. Con ese valor no existe solución.")
    elif T_min_C >= T_max_C:
        r["errores"].append("La temperatura mínima debe ser menor que la máxima.")
    elif tol_mm >= x_obj_mm:
        r["errores"].append("La tolerancia debe ser menor que la profundidad objetivo.")
    if r["errores"]:
        return r

    try:
        r["res"] = calcular_diseno_inverso(x_obj_mm, tol_mm, C0, Cs, Cobj, T_min_C, T_max_C, paso_C)
    except ValueError as error:
        r["errores"].append(str(error))
        return r

    # Chequeo aproximado de fases. Se revisa en la temperatura mínima, que es la más exigente:
    # la solubilidad del carbono sube con T y la línea A3 no depende de T.
    r["avisos"].extend(verificar_austenita(T_min_C, C0, Cs))
    return r


def armar_tabla(res, con_tolerancia):
    """Tabla de combinaciones (T, t) lista para mostrar. Todo sale de calcular_diseno_inverso."""
    t = res["tabla"]
    datos = {
        "T [°C]": [f"{v:g}" for v in t["T_C"]],
        "D [m²/s]": [f"{v:.3e}" for v in t["D_m2s"]],
        "t [h]": [f"{v:.2f}" for v in t["t_h"]],
    }
    if con_tolerancia:
        datos["t mín [h]"] = [f"{v:.2f}" for v in t["t_min_h"]]
        datos["t máx [h]"] = [f"{v:.2f}" for v in t["t_max_h"]]
    return pd.DataFrame(datos)


def explicar_diseno_inverso(res, x_obj_mm, Cobj):
    """Texto (Markdown) que explica cómo cambia el tiempo con la temperatura. Usa los números calculados."""
    tabla = res["tabla"]
    T0, T1 = tabla["T_C"][0], tabla["T_C"][-1]
    t0, t1 = tabla["t_h"][0], tabla["t_h"][-1]

    texto = (
        f"- Para tener **{Cobj:.2f} wt %** a **{x_obj_mm:.2f} [mm]**, el modelo da z = {res['z']:.4f} (sin unidades) "
        f"y K = D·t = {res['K_m2']:.3e} [m²]. **Todas** las combinaciones de la curva cumplen D(T)·t = K.\n"
        f"- Al subir la temperatura de {T0:g} a {T1:g} °C, D crece {t0 / t1:.1f} veces y el tiempo necesario "
        f"baja de {t0:.1f} [h] a {t1:.1f} [h].\n"
    )
    if len(tabla["T_C"]) >= 2:
        pct = (1.0 - tabla["t_h"][1] / tabla["t_h"][0]) * 100.0
        texto += f"- Solo de {T0:g} a {tabla['T_C'][1]:g} °C el tiempo ya baja {pct:.0f} %.\n"
    texto += (
        f"- Como t = K/D(T) y D sigue la ecuación de Arrhenius, ln(t) es una recta contra 1/T con pendiente "
        f"Q/R = {Q / R:.0f} [K]. Por eso el tiempo cae de forma exponencial, no lineal, al subir la temperatura."
    )
    return texto


def construir_mapa(res, x_obj_mm, tol_mm, T_sel=None, t_sel=None):
    """Mapa de calor: color = profundidad alcanzada [mm] para cada temperatura y tiempo.
    La línea oscura es la curva solución (profundidad = objetivo) y la franja es la tolerancia."""
    mapa, curva = res["mapa"], res["curva"]
    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        x=mapa["t_h"], y=mapa["T_C"], z=mapa["x_mm"],
        colorscale="YlOrRd",
        colorbar=dict(title=dict(text="Profundidad [mm]")),
        hovertemplate="t = %{x:.2f} h<br>T = %{y:.0f} °C<br>x = %{z:.3f} mm<extra></extra>",
    ))

    # Franja de tolerancia: x - tol (tiempo menor) y x + tol (tiempo mayor), con relleno entre las dos
    if tol_mm > 0:
        fig.add_trace(go.Scatter(
            x=curva["t_min_h"], y=curva["T_C"], mode="lines",
            name=f"x = {x_obj_mm - tol_mm:.2f} mm", line=dict(color=COLOR_TEXTO, width=1, dash="dash"),
        ))
        fig.add_trace(go.Scatter(
            x=curva["t_max_h"], y=curva["T_C"], mode="lines",
            name=f"x = {x_obj_mm + tol_mm:.2f} mm", line=dict(color=COLOR_TEXTO, width=1, dash="dash"),
            fill="tonextx", fillcolor="rgba(27,36,48,0.15)",
        ))

    # Curva solución
    fig.add_trace(go.Scatter(
        x=curva["t_h"], y=curva["T_C"], mode="lines",
        name=f"x = {x_obj_mm:.2f} mm (objetivo)", line=dict(color=COLOR_TEXTO, width=3),
        hovertemplate="t = %{x:.2f} h<br>T = %{y:.0f} °C<extra></extra>",
    ))

    # Tratamiento elegido
    if T_sel is not None and t_sel is not None:
        fig.add_trace(go.Scatter(
            x=[t_sel], y=[T_sel], mode="markers", name="Tratamiento elegido",
            marker=dict(size=14, symbol="star", color=COLOR_X, line=dict(width=1.5, color="black")),
        ))

    fig.update_layout(
        **LAYOUT_BASE,
        xaxis_title="Tiempo [h]",
        yaxis_title="Temperatura [°C]",
        xaxis_range=[float(mapa["t_h"][0]), float(mapa["t_h"][-1])],
        yaxis_range=[float(mapa["T_C"][0]), float(mapa["T_C"][-1])],
        height=500,
    )
    return fig


def _llevar_al_simulador(T_C, t_h, C0, Cs, Cobj, x_obj_mm):
    """Se ejecuta al presionar el botón del Módulo 2: guarda el tratamiento elegido
    y cambia a la página del simulador directo (Módulo 1)."""
    st.session_state[ESTADO_PRECARGA] = {
        "T_C": round(float(T_C), 1),
        "t_h": round(float(t_h), 2),
        "C0": float(C0), "Cs": float(Cs), "Cobj": float(Cobj),
        "x_max_mm": max(2.0, round(2.0 * float(x_obj_mm), 1)),
        "x_obj_mm": float(x_obj_mm),
    }
    st.session_state[ESTADO_PAGINA] = PAGINA_SIMULADOR


# ---------- Pantalla ----------
def mostrar():
    st.header("Módulo 2. Diseño inverso")
    st.write(
        "En vez de dar temperatura y tiempo, das el resultado que quieres (una concentración de carbono "
        "a cierta profundidad) y la app calcula qué combinaciones de temperatura y tiempo lo logran."
    )

    col_parametros, col_resultados = st.columns([1, 2])

    # ----- Columna izquierda: parámetros y elección del tratamiento -----
    with col_parametros:
        st.subheader("Objetivo")
        x_obj_mm = st.number_input(
            "Profundidad objetivo [mm]", min_value=0.05, max_value=5.0,
            value=0.80, step=0.05, format="%.2f",
        )
        tol_mm = st.number_input(
            "Tolerancia ± [mm]", min_value=0.0, max_value=1.0,
            value=0.05, step=0.01, format="%.2f",
            help="Con tolerancia 0 solo se muestra la curva exacta. Con tolerancia mayor que 0 se muestra "
                 "también la franja de combinaciones que quedan dentro de x ± tolerancia.",
        )
        C0 = st.number_input(
            "Concentración inicial C₀ [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX,
            value=0.20, step=0.05, format="%.2f",
        )
        Cs = st.number_input(
            "Concentración superficial Cs [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX,
            value=1.00, step=0.05, format="%.2f",
            help="Depende del potencial de carbono de la atmósfera carburizante.",
        )
        Cobj = st.number_input(
            "Concentración objetivo Cobj [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX,
            value=0.40, step=0.05, format="%.2f",
        )

        st.subheader("Temperaturas a explorar")
        T_min_C = st.number_input(
            "Temperatura mínima [°C]", min_value=T_MIN, max_value=T_MAX,
            value=900.0, step=5.0, format="%.0f",
        )
        T_max_C = st.number_input(
            "Temperatura máxima [°C]", min_value=T_MIN, max_value=T_MAX,
            value=1050.0, step=5.0, format="%.0f",
            help="Intervalo de demostración del proyecto: 900–1050 °C.",
        )
        paso_C = st.number_input(
            "Paso de la tabla [°C]", min_value=5.0, max_value=150.0,
            value=25.0, step=5.0, format="%.0f",
        )

        r = calcular_modulo2(x_obj_mm, tol_mm, C0, Cs, Cobj, T_min_C, T_max_C, paso_C)

        # Elegir un tratamiento de la tabla para comprobarlo en el Módulo 1
        T_sel = None
        t_sel = None
        if r["res"] is not None:
            tabla = r["res"]["tabla"]
            st.subheader("Tratamiento a comprobar")
            opciones = [float(v) for v in tabla["T_C"]]
            T_sel = st.selectbox(
                "Temperatura del tratamiento [°C]", opciones, index=len(opciones) // 2,
                format_func=lambda v: f"{v:g} °C",
            )
            i_sel = int(np.argmin(np.abs(tabla["T_C"] - T_sel)))
            t_sel = float(tabla["t_h"][i_sel])
            st.write(f"Tiempo necesario: **{t_sel:.2f} [h]**")
            st.button(
                "Comprobar en el simulador directo",
                on_click=_llevar_al_simulador,
                args=(T_sel, t_sel, C0, Cs, Cobj, x_obj_mm),
            )

    # ----- Columna derecha: resultados -----
    with col_resultados:
        st.subheader("Resultados")

        if r["errores"]:
            for mensaje in r["errores"]:
                st.error(mensaje)
            return

        res = r["res"]
        tabla = res["tabla"]

        for aviso in r["avisos"]:
            st.warning(aviso)

        c1, c2, c3 = st.columns(3)
        c1.metric(f"t a {tabla['T_C'][0]:g} °C [h]", f"{tabla['t_h'][0]:.2f}")
        c2.metric(f"t a {tabla['T_C'][-1]:g} °C [h]", f"{tabla['t_h'][-1]:.2f}")
        c3.metric("Reducción del tiempo", f"× {tabla['t_h'][0] / tabla['t_h'][-1]:.1f}",
                  help="Cuántas veces menos tiempo se necesita a la temperatura máxima que a la mínima.")

        tab_tabla, tab_mapa, tab_explicacion = st.tabs(["Tabla de combinaciones", "Mapa de calor", "Explicación"])

        with tab_tabla:
            st.dataframe(armar_tabla(res, tol_mm > 0), width="stretch", hide_index=True)
            if tol_mm > 0:
                st.caption(
                    f"Cada fila es una combinación que da exactamente {x_obj_mm:.2f} [mm]. "
                    f"Las columnas t mín y t máx son la ventana de tiempo que da entre "
                    f"{x_obj_mm - tol_mm:.2f} y {x_obj_mm + tol_mm:.2f} [mm] a esa temperatura."
                )
            else:
                st.caption(f"Cada fila es una combinación que da exactamente {x_obj_mm:.2f} [mm].")

        with tab_mapa:
            st.plotly_chart(construir_mapa(res, x_obj_mm, tol_mm, T_sel, t_sel), width="stretch")
            st.caption(
                "El color es la profundidad que se alcanza para Cobj con cada temperatura y tiempo. "
                "Una profundidad exacta es una curva (línea oscura), no una región. "
                "Si defines una tolerancia, la franja gris es la región viable."
            )

        with tab_explicacion:
            st.latex(r"D(T)\,t = K = \left[\frac{x_{obj}}{2z}\right]^2")
            st.latex(r"\ln t = \ln\frac{K}{D_0} + \frac{Q}{R}\cdot\frac{1}{T}")
            st.markdown(explicar_diseno_inverso(res, x_obj_mm, Cobj))
            st.caption(
                "El modelo solo dice cuánto tiempo hace falta. No considera crecimiento de grano, "
                "distorsión de la pieza, costo ni límites del horno: elegir la combinación real "
                "es una decisión de ingeniería."
            )

        # Resumen del tratamiento elegido
        if T_sel is not None:
            i_sel = int(np.argmin(np.abs(tabla["T_C"] - T_sel)))
            L_sel = float(calcular_longitud_difusion(t_sel, T_sel))
            st.markdown(
                f"**Tratamiento elegido:** {T_sel:g} °C durante {t_sel:.2f} [h]"
                + (f" (ventana {tabla['t_min_h'][i_sel]:.2f}–{tabla['t_max_h'][i_sel]:.2f} [h])" if tol_mm > 0 else "")
                + f". Para que el modelo de sólido semiinfinito sea razonable, el espesor "
                  f"debe ser de al menos 4·L = {FACTOR_SEMIINFINITO * L_sel:.2f} [mm]."
            )

    # ----- Fijar el tiempo y calcular la temperatura -----
    if r["res"] is not None:
        with st.expander("Si ya tengo el tiempo: ¿qué temperatura necesito?"):
            t_disp = st.number_input(
                "Tiempo disponible [h]", min_value=0.1, max_value=1000.0,
                value=10.0, step=0.5, format="%.1f",
            )
            try:
                T_req = float(calcular_temperatura(x_obj_mm, t_disp, C0, Cs, Cobj))
                st.markdown(
                    f"Para {Cobj:.2f} wt % a {x_obj_mm:.2f} [mm] en {t_disp:.1f} [h] se necesitan "
                    f"**{T_req:.0f} °C**  (T = −Q / [R · ln(D_req / D₀)])."
                )
                if not (T_MIN <= T_req <= T_MAX):
                    st.warning(f"Esa temperatura queda fuera del intervalo de demostración ({T_MIN:.0f}–{T_MAX:.0f} °C).")
            except ValueError as error:
                st.error(str(error))

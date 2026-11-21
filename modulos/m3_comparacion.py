# Simulador Difusión Carbono. Módulo 3: comparación de tratamientos (persona A).
# Compara de 2 a 3 tratamientos con la misma concentración objetivo.
# Los cálculos de física salen de modelo.py (comparar_tratamientos).
# app.py solo llama a mostrar().

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from estilo import (
    COLOR_COBJ, COLORES_TRATAMIENTOS, LAYOUT_BASE, SOLUBILIDAD_MAX, T_MAX, T_MIN,
)
from modelo import calcular_perfil, comparar_tratamientos, verificar_austenita

LETRAS = ["A", "B", "C"]
# Valores de partida: a mayor temperatura, menos tiempo (así se ve si dan profundidades parecidas)
VALORES_INICIALES = [
    {"T_C": 900.0, "t_h": 12.0},
    {"T_C": 950.0, "t_h": 6.0},
    {"T_C": 1000.0, "t_h": 3.0},
]


# ---------- Lógica (sin Streamlit, para poder probarla aparte) ----------
def calcular_modulo3(tratamientos, Cobj, x_max_mm):
    """Junta lo que necesita la pantalla del Módulo 3.
    'tratamientos' es una lista de diccionarios con nombre, T_C, t_h, C0 y Cs.
    Regresa: 'avisos' (textos), 'resultados' (lo de comparar_tratamientos),
    'x' [mm] y 'perfiles' (un arreglo de C [wt %] por tratamiento, o None si no se pudo calcular)."""
    r = {"avisos": [], "resultados": None, "x": None, "perfiles": []}

    resultados = comparar_tratamientos(tratamientos, Cobj)
    r["resultados"] = resultados
    r["x"] = np.linspace(0.0, x_max_mm, 400)

    for fila, trat in zip(resultados, tratamientos):
        if fila["aviso"]:
            r["avisos"].append(f"{fila['nombre']}: {fila['aviso']}")
        elif fila["profundidad_mm"] > x_max_mm:
            r["avisos"].append(
                f"{fila['nombre']}: la profundidad ({fila['profundidad_mm']:.2f} [mm]) queda fuera de la gráfica. "
                "Aumenta la profundidad máxima a visualizar."
            )
        # Chequeo aproximado de fases (A3 y Acm del diagrama de clase)
        for aviso in verificar_austenita(trat["T_C"], trat["C0"], trat["Cs"]):
            r["avisos"].append(f"{fila['nombre']}: {aviso}")
        try:
            r["perfiles"].append(calcular_perfil(r["x"], trat["t_h"], trat["C0"], trat["Cs"], trat["T_C"]))
        except ValueError:
            r["perfiles"].append(None)   # el aviso de arriba ya explica por qué (por ejemplo, Cs <= C0)
    return r


def _texto(valor, formato):
    """Número formateado, o una raya si no se pudo calcular (nan)."""
    return "—" if np.isnan(valor) else format(valor, formato)


def armar_tabla_comparacion(resultados):
    """Tabla comparativa lista para mostrar. Todo sale de comparar_tratamientos."""
    x_ref = resultados[0]["profundidad_mm"]
    filas = []
    for i, f in enumerate(resultados):
        filas.append({
            "Tratamiento": f["nombre"],
            "T [°C]": f"{f['T_C']:g}",
            "t [h]": f"{f['t_h']:g}",
            "C₀ [wt %]": f"{f['C0']:.2f}",
            "Cs [wt %]": f"{f['Cs']:.2f}",
            "D [m²/s]": f"{f['D_m2s']:.3e}",
            "L = √(Dt) [mm]": f"{f['L_mm']:.3f}",
            "x para Cobj [mm]": _texto(f["profundidad_mm"], ".3f"),
            "Dif. contra el primero [mm]": "—" if i == 0 else _texto(f["profundidad_mm"] - x_ref, "+.3f"),
            "t para igualar al primero [h]": _texto(f["t_igualar_h"], ".2f"),
        })
    return pd.DataFrame(filas)


def explicar_comparacion(resultados, Cobj):
    """Texto (Markdown) que explica cuál tratamiento llega más profundo y por qué. Usa los números calculados."""
    validos = [f for f in resultados if not np.isnan(f["profundidad_mm"])]
    if len(validos) < 2:
        return "No hay al menos dos tratamientos con resultado válido para comparar."

    mayor = max(validos, key=lambda f: f["profundidad_mm"])
    menor = min(validos, key=lambda f: f["profundidad_mm"])
    texto = (
        f"- Para **{Cobj:.2f} wt %**, **{mayor['nombre']}** llega más profundo ({mayor['profundidad_mm']:.3f} [mm]) "
        f"y **{menor['nombre']}** llega menos ({menor['profundidad_mm']:.3f} [mm]).\n"
    )

    ref = resultados[0]
    if not np.isnan(ref["profundidad_mm"]):
        for f in resultados[1:]:
            if np.isnan(f["profundidad_mm"]):
                continue
            razon_D = f["D_m2s"] / ref["D_m2s"]
            razon_t = f["t_h"] / ref["t_h"]
            razon_x = f["profundidad_mm"] / ref["profundidad_mm"]
            texto += (
                f"- **{f['nombre']} contra {ref['nombre']}**: D ×{razon_D:.2f}, tiempo ×{razon_t:.2f}, "
                f"D·t ×{razon_D * razon_t:.2f}, profundidad ×{razon_x:.2f}. "
                f"Para igualar la profundidad de {ref['nombre']}, {f['nombre']} necesitaría "
                f"{f['t_igualar_h']:.2f} [h] a {f['T_C']:g} °C (usa {f['t_h']:g} [h]).\n"
            )

    mismos_C = all(f["C0"] == ref["C0"] and f["Cs"] == ref["Cs"] for f in resultados)
    if mismos_C:
        texto += (
            "- **Por qué:** con los mismos C₀, Cs y Cobj, la profundidad es x = 2z·√(Dt), o sea que solo depende "
            "del producto D·t. Como D crece de forma exponencial con la temperatura (Arrhenius), una temperatura "
            "más alta puede compensar un tiempo menor."
        )
    else:
        texto += (
            "- **Por qué:** la profundidad es x = 2z·√(Dt). Aquí C₀ o Cs cambian entre tratamientos, así que "
            "también cambia z y la comparación ya no depende solo de D·t."
        )
    return texto


def construir_figura_comparacion(resultados, perfiles, x, Cobj, Cs_max):
    """Perfiles superpuestos de concentración [wt %] contra profundidad [mm], uno por tratamiento."""
    fig = go.Figure()

    for i, (f, C) in enumerate(zip(resultados, perfiles)):
        color = COLORES_TRATAMIENTOS[i]
        if C is not None:
            fig.add_trace(go.Scatter(
                x=x, y=C, mode="lines",
                name=f"{f['nombre']}: {f['T_C']:g} °C, {f['t_h']:g} h",
                line=dict(color=color, width=3),
                hovertemplate="x = %{x:.3f} mm<br>C = %{y:.3f} wt %<extra></extra>",
            ))
        x_obj = f["profundidad_mm"]
        if not np.isnan(x_obj) and x_obj <= x[-1]:
            fig.add_vline(x=x_obj, line_dash="dot", line_color=color)
            fig.add_trace(go.Scatter(
                x=[x_obj], y=[Cobj], mode="markers", showlegend=False,
                marker=dict(size=11, color=color, line=dict(width=2, color="white")),
                hovertemplate=f"{f['nombre']}: x = %{{x:.3f}} mm<extra></extra>",
            ))

    fig.add_hline(y=Cobj, line_dash="dot", line_color=COLOR_COBJ,
                  annotation_text=f"Cobj = {Cobj:.2f} wt %", annotation_position="top right")

    fig.update_layout(
        **LAYOUT_BASE,
        xaxis_title="Profundidad [mm]",
        yaxis_title="Concentración de carbono [wt %]",
        xaxis_range=[0, float(x[-1])],
        yaxis_range=[0, Cs_max * 1.12],
        hovermode="x unified",
        height=480,
    )
    return fig


# ---------- Pantalla ----------
def mostrar():
    st.header("Módulo 3. Comparación de tratamientos")
    st.write(
        "Compara hasta tres tratamientos con la misma concentración objetivo. "
        "Sirve para responder preguntas como: ¿se logra una profundidad parecida con una temperatura "
        "más alta y menos tiempo?"
    )

    # ----- Parámetros comunes -----
    c_comun = st.columns(3)
    with c_comun[0]:
        Cobj = st.number_input(
            "Concentración objetivo Cobj [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX,
            value=0.40, step=0.05, format="%.2f", key="m3_Cobj",
        )
    with c_comun[1]:
        x_max_mm = st.number_input(
            "Profundidad máxima a visualizar [mm]", min_value=0.1, max_value=20.0,
            value=2.0, step=0.5, format="%.1f", key="m3_xmax",
        )
    with c_comun[2]:
        n = st.radio("Número de tratamientos", [2, 3], horizontal=True, key="m3_n")

    # ----- Un bloque de parámetros por tratamiento -----
    tratamientos = []
    columnas = st.columns(n)
    for i, col in enumerate(columnas):
        with col:
            st.subheader(f"Tratamiento {LETRAS[i]}")
            nombre = st.text_input("Nombre", value=LETRAS[i], key=f"m3_nombre_{i}")
            T_C = st.number_input(
                "Temperatura [°C]", min_value=T_MIN, max_value=T_MAX,
                value=VALORES_INICIALES[i]["T_C"], step=5.0, format="%.1f", key=f"m3_T_{i}",
            )
            t_h = st.number_input(
                "Tiempo [h]", min_value=0.1, max_value=1000.0,
                value=VALORES_INICIALES[i]["t_h"], step=0.5, format="%.1f", key=f"m3_t_{i}",
            )
            C0 = st.number_input(
                "C₀ [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX,
                value=0.20, step=0.05, format="%.2f", key=f"m3_C0_{i}",
            )
            Cs = st.number_input(
                "Cs [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX,
                value=1.00, step=0.05, format="%.2f", key=f"m3_Cs_{i}",
            )
        tratamientos.append({"nombre": nombre.strip() or LETRAS[i], "T_C": T_C, "t_h": t_h, "C0": C0, "Cs": Cs})

    r = calcular_modulo3(tratamientos, Cobj, x_max_mm)
    resultados = r["resultados"]

    # ----- Resultados -----
    st.subheader("Resultados")

    columnas_metricas = st.columns(len(resultados))
    x_ref = resultados[0]["profundidad_mm"]
    for i, (col, f) in enumerate(zip(columnas_metricas, resultados)):
        valor = "—" if np.isnan(f["profundidad_mm"]) else f"{f['profundidad_mm']:.3f}"
        diferencia = None
        if i > 0 and not np.isnan(f["profundidad_mm"]) and not np.isnan(x_ref):
            diferencia = f"{f['profundidad_mm'] - x_ref:+.3f} [mm] contra {resultados[0]['nombre']}"
        col.metric(f"{f['nombre']}: x para Cobj [mm]", valor, delta=diferencia, delta_color="off")

    for aviso in r["avisos"]:
        st.warning(aviso)

    if any(p is not None for p in r["perfiles"]):
        Cs_max = max(t["Cs"] for t in tratamientos)
        st.plotly_chart(
            construir_figura_comparacion(resultados, r["perfiles"], r["x"], Cobj, Cs_max),
            width="stretch",
        )
    st.caption(
        "Cada línea punteada vertical marca la profundidad a la que ese tratamiento llega a Cobj. "
        "Esa profundidad no es la profundidad efectiva de endurecimiento: esa depende del temple y de la dureza, "
        "y esta app no las calcula."
    )

    st.subheader("Tabla comparativa")
    st.dataframe(armar_tabla_comparacion(resultados), width="stretch", hide_index=True)

    st.subheader("¿Cuál llega más profundo y por qué?")
    st.markdown(explicar_comparacion(resultados, Cobj))
    st.caption(
        "El modelo solo compara profundidades de carbono. No considera crecimiento de grano, distorsión, "
        "costo ni límites del horno: elegir el tratamiento real es una decisión de ingeniería."
    )

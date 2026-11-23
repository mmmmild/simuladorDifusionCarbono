# Simulador Difusión Carbono. Página 4: comparación de tratamientos.
# Tres tratamientos (temperatura y tiempo) con el mismo acero, la misma Cobj y una profundidad meta.
# La app dice cuál conviene: el que llega a la meta con menos tiempo de horno.
# Los cálculos salen de modelo.py. app.py solo llama a mostrar().

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from estilo import (
    C0_DEMO, C0_MAX, C0_MIN, COBJ_DEMO, COBJ_MAX, COBJ_MIN, COLOR_COBJ, COLOR_TEXTO, COLORES_TRATAMIENTOS,
    CS_DEMO, CS_MAX, CS_MIN, LAYOUT_BASE, T_H_MAX, T_H_MIN, T_MAX, T_MIN, X_OBJ_DEMO, X_OBJ_MAX, X_OBJ_MIN,
)
from modelo import calcular_perfil, calcular_tiempo, comparar_tratamientos, verificar_austenita

LETRAS = ["A", "B", "C"]
# Valores de partida: a mayor temperatura, menos tiempo
VALORES_INICIALES = [{"T_C": 900.0, "t_h": 12.0}, {"T_C": 950.0, "t_h": 7.0}, {"T_C": 1000.0, "t_h": 3.0}]


# ---------- Lógica (sin Streamlit, para poder probarla aparte) ----------
def calcular_modulo3(tratamientos, C0, Cs, Cobj, x_meta_mm):
    """Compara los tratamientos y elige el mejor. Regresa un diccionario con:
      'errores', 'avisos', 'filas' (una por tratamiento), 'mejor' (fila elegida o None),
      'x' [mm] y 'perfiles' [wt %] para la gráfica."""
    r = {"errores": [], "avisos": [], "filas": [], "mejor": None, "x": None, "perfiles": []}
    if Cs <= C0:
        r["errores"].append("Cs debe ser mayor que C₀.")
        return r
    if not (C0 < Cobj < Cs):
        r["errores"].append(f"La concentración objetivo debe quedar entre C₀ = {C0:.2f} y Cs = {Cs:.2f} wt %.")
        return r

    trats = [dict(t, C0=C0, Cs=Cs) for t in tratamientos]
    for fila in comparar_tratamientos(trats, Cobj):
        fila["cumple"] = fila["profundidad_mm"] >= x_meta_mm
        fila["t_meta_h"] = float(calcular_tiempo(x_meta_mm, C0, Cs, Cobj, fila["T_C"]))  # tiempo justo para la meta
        r["filas"].append(fila)
    for t in trats:
        for aviso in verificar_austenita(t["T_C"], C0, Cs):
            r["avisos"].append(f"{t['nombre']}: {aviso}")

    # Criterio: de los que llegan a la meta, el de menos tiempo de horno (si empatan, el de menor temperatura)
    cumplen = [f for f in r["filas"] if f["cumple"]]
    if cumplen:
        r["mejor"] = min(cumplen, key=lambda f: (f["t_h"], f["T_C"]))

    x_max = max(1.5 * x_meta_mm, 1.2 * max(f["profundidad_mm"] for f in r["filas"]))
    r["x"] = np.linspace(0.0, x_max, 300)
    r["perfiles"] = [calcular_perfil(r["x"], t["t_h"], C0, Cs, t["T_C"]) for t in trats]
    return r


def _mismas(f, g):
    """True si dos tratamientos tienen la misma temperatura y el mismo tiempo."""
    return abs(f["T_C"] - g["T_C"]) < 1e-9 and abs(f["t_h"] - g["t_h"]) < 1e-9


def _nombres(lista):
    """'A', 'A y B' o 'A, B y C'."""
    nombres = [f["nombre"] for f in lista]
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]


def _sugerencia_ahorro(filas, referencia, x_meta_mm):
    """Texto de cómo ahorrar tiempo respecto a 'referencia' (o vacío si no se puede ahorrar)."""
    rapido = min(filas, key=lambda f: (f["t_meta_h"], f["T_C"]))
    if rapido["t_meta_h"] >= referencia["t_h"] - 0.01:
        return ""
    if rapido["T_C"] > referencia["T_C"] + 1e-9:
        return (f"\n\n**Para ahorrar más tiempo:** a {rapido['T_C']:g} °C (tratamiento {rapido['nombre']}) el carbono "
                f"difunde más rápido y bastarían **{rapido['t_meta_h']:.2f} h** para llegar justo a la meta.")
    exceso = referencia["profundidad_mm"] - x_meta_mm
    return (f"\n\n**Para ahorrar tiempo:** a {referencia['T_C']:g} °C bastarían **{referencia['t_meta_h']:.2f} h** "
            f"para llegar justo a la meta; con {referencia['t_h']:g} h te pasas {exceso:.3f} mm.")


def recomendar(r, x_meta_mm):
    """Texto con la recomendación y el porqué. Toma en cuenta tratamientos repetidos y empates."""
    filas, mejor = r["filas"], r["mejor"]

    # Caso 1: los tres son iguales -> no hay nada que comparar
    if all(_mismas(f, filas[0]) for f in filas):
        f = filas[0]
        llegan = "llegan" if f["cumple"] else "no llegan"
        texto = (f"**Los tres tratamientos son iguales** ({f['T_C']:g} °C, {f['t_h']:g} h), así que dan el mismo "
                 f"resultado: {f['profundidad_mm']:.3f} mm, y {llegan} a la meta de {x_meta_mm:.2f} mm. "
                 "Cambia la temperatura o el tiempo de alguno para compararlos.")
        if f["cumple"]:
            texto += _sugerencia_ahorro([f], f, x_meta_mm)
        else:
            texto += f"\n\nPara llegar a la meta necesitarían **{f['t_meta_h']:.2f} h** a {f['T_C']:g} °C."
        return texto

    # Caso 2: ninguno llega
    if mejor is None:
        cercano = max(filas, key=lambda f: (f["profundidad_mm"], -f["t_h"]))
        iguales = [f for f in filas if _mismas(f, cercano)]
        rapido = min(filas, key=lambda f: (f["t_meta_h"], f["T_C"]))
        return (
            f"**Ninguno llega a la meta de {x_meta_mm:.2f} mm.** El que más se acerca es **{_nombres(iguales)}** "
            f"({cercano['T_C']:g} °C, {cercano['t_h']:g} h: {cercano['profundidad_mm']:.3f} mm)."
            f"\n\n**Para llegar:** el camino más corto es a {rapido['T_C']:g} °C (tratamiento {rapido['nombre']}), "
            f"con **{rapido['t_meta_h']:.2f} h**."
        )

    # Caso 3: hay un mejor (puede tener tratamientos iguales a él)
    iguales = [f for f in filas if _mismas(f, mejor)]
    exceso = mejor["profundidad_mm"] - x_meta_mm
    if len(iguales) > 1:
        texto = (f"**Los mejores son {_nombres(iguales)}** (son iguales: {mejor['T_C']:g} °C, {mejor['t_h']:g} h): "
                 f"llegan a la meta con el **menor tiempo de horno**.")
    else:
        texto = (f"**El mejor es {mejor['nombre']}** ({mejor['T_C']:g} °C, {mejor['t_h']:g} h): llega a la meta con "
                 f"el **menor tiempo de horno**.")
    texto += (f" {'Alcanzan' if len(iguales) > 1 else 'Alcanza'} {mejor['profundidad_mm']:.3f} mm, "
              f"{exceso:.3f} mm más de lo pedido.")

    otros = [f for f in filas if f["cumple"] and not _mismas(f, mejor)]
    mas_tiempo = [f for f in otros if f["t_h"] > mejor["t_h"] + 1e-9]
    mismo_tiempo = [f for f in otros if abs(f["t_h"] - mejor["t_h"]) <= 1e-9]
    if mas_tiempo:
        verbo = "tarda" if len(mas_tiempo) == 1 else "tardan"
        texto += (f" También {'cumple' if len(mas_tiempo) == 1 else 'cumplen'} "
                  + ", ".join(f"{f['nombre']} ({f['t_h']:g} h)" for f in mas_tiempo) + f", pero {verbo} más.")
    if mismo_tiempo:
        texto += (f" {_nombres(mismo_tiempo)} {'tarda' if len(mismo_tiempo) == 1 else 'tardan'} lo mismo, pero con "
                  "más temperatura, que gasta más energía y hace crecer el grano (eso no lo calcula el modelo).")
    return texto + _sugerencia_ahorro(filas, mejor, x_meta_mm)


def construir_figura_barras(r, x_meta_mm):
    """Barras: profundidad que alcanza cada tratamiento, con la meta como línea."""
    fig = go.Figure()
    for f, color in zip(r["filas"], COLORES_TRATAMIENTOS):
        fig.add_trace(go.Bar(
            x=[f"{f['nombre']}<br>{f['T_C']:g} °C · {f['t_h']:g} h"], y=[f["profundidad_mm"]], name=f["nombre"],
            marker=dict(color=color, line=dict(color=COLOR_TEXTO, width=3 if f is r["mejor"] else 0)),
            text=[f"{f['profundidad_mm']:.3f} mm" + (" ✓" if f["cumple"] else "")], textposition="outside",
            hovertemplate="%{y:.3f} mm<extra></extra>",
        ))
    fig.add_hline(y=x_meta_mm, line_dash="dash", line_color=COLOR_COBJ, line_width=3,
                  annotation_text=f"Meta: {x_meta_mm:.2f} mm", annotation_position="top left")
    fig.update_layout(**LAYOUT_BASE)
    fig.update_layout(height=380, showlegend=False, yaxis_title="Profundidad para Cobj [mm]",
                      yaxis_range=[0, 1.25 * max(max(f["profundidad_mm"] for f in r["filas"]), x_meta_mm)])
    return fig


def construir_figura_perfiles(r, Cobj, x_meta_mm, Cs):
    """Perfiles de carbono de los tres tratamientos."""
    fig = go.Figure()
    for f, C, color in zip(r["filas"], r["perfiles"], COLORES_TRATAMIENTOS):
        fig.add_trace(go.Scatter(x=r["x"], y=C, mode="lines", name=f"{f['nombre']}: {f['T_C']:g} °C, {f['t_h']:g} h",
                                 line=dict(color=color, width=3),
                                 hovertemplate="x = %{x:.3f} mm<br>C = %{y:.3f} wt %<extra></extra>"))
    fig.add_hline(y=Cobj, line_dash="dot", line_color=COLOR_COBJ, annotation_text=f"Cobj = {Cobj:.2f} wt %",
                  annotation_position="top right")
    fig.add_vline(x=x_meta_mm, line_dash="dash", line_color=COLOR_COBJ, annotation_text="Meta",
                  annotation_position="top")
    fig.update_layout(**LAYOUT_BASE)
    fig.update_layout(height=380, hovermode="x unified", xaxis_title="Profundidad desde la superficie [mm]",
                      yaxis_title="Carbono [wt %]", yaxis_range=[0, Cs * 1.1])
    return fig


def armar_tabla(r):
    """Tabla comparativa lista para mostrar."""
    return pd.DataFrame([{
        "Tratamiento": f["nombre"], "T [°C]": f"{f['T_C']:g}", "t [h]": f"{f['t_h']:g}",
        "Profundidad [mm]": f"{f['profundidad_mm']:.3f}", "¿Llega a la meta?": "Sí" if f["cumple"] else "No",
        "Tiempo justo para la meta [h]": f"{f['t_meta_h']:.2f}",
    } for f in r["filas"]])


# ---------- Pantalla ----------
def mostrar():
    st.header("Comparación de tratamientos")
    st.write(
        "Pon tres tratamientos lado a lado y define una **profundidad meta**. La app te dice cuál conviene: "
        "el que llega a la meta con **menos tiempo de horno**."
    )

    c1, c2 = st.columns(2)
    with c1:
        x_meta = st.slider("Profundidad meta [mm]", X_OBJ_MIN, X_OBJ_MAX, X_OBJ_DEMO, 0.05, key="m3_meta")
    with c2:
        Cobj = st.slider("Concentración objetivo Cobj [wt %]", COBJ_MIN, COBJ_MAX, COBJ_DEMO, 0.01, key="m3_Cobj")
    with st.expander("Acero y atmósfera (los mismos para los tres)"):
        a1, a2 = st.columns(2)
        with a1:
            C0 = st.slider("C₀ [wt %]", C0_MIN, C0_MAX, C0_DEMO, 0.01, key="m3_C0")
        with a2:
            Cs = st.slider("Cs [wt %]", CS_MIN, CS_MAX, CS_DEMO, 0.01, key="m3_Cs")

    tratamientos = []
    for i, col in enumerate(st.columns(3)):
        with col:
            with st.container(border=True):
                st.markdown(f"**Tratamiento {LETRAS[i]}**")
                T_C = st.slider("Temperatura [°C]", T_MIN, T_MAX, VALORES_INICIALES[i]["T_C"], 5.0, key=f"m3_T_{i}")
                t_h = st.slider("Tiempo [h]", T_H_MIN, T_H_MAX, VALORES_INICIALES[i]["t_h"], 0.5, key=f"m3_t_{i}")
        tratamientos.append({"nombre": LETRAS[i], "T_C": T_C, "t_h": t_h})

    r = calcular_modulo3(tratamientos, C0, Cs, Cobj, x_meta)
    if r["errores"]:
        for mensaje in r["errores"]:
            st.error(mensaje)
        return
    for aviso in r["avisos"]:
        st.warning(aviso)

    st.subheader("¿Cuál conviene?")
    if r["mejor"] is not None:
        st.success(recomendar(r, x_meta))
    else:
        st.warning(recomendar(r, x_meta))

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(construir_figura_barras(r, x_meta), width="stretch")
    with g2:
        st.plotly_chart(construir_figura_perfiles(r, Cobj, x_meta, Cs), width="stretch")

    st.dataframe(armar_tabla(r), width="stretch", hide_index=True)
    st.markdown(
        "**¿Por qué?** Con el mismo acero y la misma Cobj, la profundidad es x = 2z·√(D·t): solo depende del "
        "producto D·t. Como D crece de forma exponencial con la temperatura, **una temperatura más alta compensa "
        "un tiempo menor**. Por eso el tratamiento más caliente suele necesitar menos horas."
    )
    st.caption("El criterio es solo el tiempo de horno. El modelo no considera crecimiento de grano, consumo de "
               "energía, distorsión ni costo: con más temperatura esos efectos aumentan, y la decisión final es de "
               "ingeniería.")

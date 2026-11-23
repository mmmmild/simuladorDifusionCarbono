# Simulador Difusión Carbono. Módulo 6: microestructura, flujo de carbono e importancia en la industria.
# A partir del mismo perfil de carbono del Módulo 1 se calcula:
#   A) qué microestructura tendría cada profundidad si la pieza se enfría LENTO (regla de la palanca), y
#   B) cuánto carbono entra por la superficie (primera ley de Fick) y cuánto se acumula.
# Al final hay una sección sobre por qué esto importa en la industria.
# Los cálculos salen de modelo.py. app.py solo llama a mostrar().

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from estilo import (
    COLOR_CEMENTITA, COLOR_FERRITA, COLOR_PERFIL, COLOR_PERLITA, COLOR_TEXTO, COLORES_TRATAMIENTOS,
    LAYOUT_BASE, SOLUBILIDAD_MAX, T_MAX, T_MIN,
)
from modelo import (
    C_CEMENTITA, C_EUTECTOIDE, C_FERRITA_MAX, DENSIDAD_ACERO,
    calcular_carbono_absorbido, calcular_flujo, calcular_longitud_difusion, calcular_microconstituyentes,
    calcular_perfil, calcular_profundidad, verificar_austenita,
)

KG_M2S_A_G_M2H = 1000.0 * 3600.0  # [kg/(m²·s)] -> [g/(m²·h)]  (números más fáciles de leer)
NOMBRES = {"ferrita": "Ferrita proeutectoide", "perlita": "Perlita", "cementita": "Cementita proeutectoide"}
COLORES = {"ferrita": COLOR_FERRITA, "perlita": COLOR_PERLITA, "cementita": COLOR_CEMENTITA}


# ---------- Lógica (sin Streamlit, para poder probarla aparte) ----------
def calcular_modulo6(T_C, t_h, C0, Cs, x_max_mm):
    """Junta todo lo que necesita la pantalla del Módulo 6. Regresa un diccionario.
    Si Cs <= C0 no se puede calcular nada ('errores')."""
    r = {"errores": [], "avisos": []}
    if Cs <= C0:
        r["errores"].append("Cs debe ser mayor que C₀: en cementación la superficie tiene más carbono que el núcleo.")
        return r

    # Perfil de carbono y microestructura a cada profundidad
    r["x"] = np.linspace(0.0, x_max_mm, 400)                       # [mm]
    r["C"] = calcular_perfil(r["x"], t_h, C0, Cs, T_C)             # [wt %]
    r["fr"] = calcular_microconstituyentes(r["C"])                 # fracciones de 0 a 1
    r["L"] = float(calcular_longitud_difusion(t_h, T_C))           # [mm]
    # Profundidad donde el carbono vale 0.8 wt % (frontera hipereutectoide / hipoeutectoide)
    r["x_eut"] = float(calcular_profundidad(t_h, C0, Cs, C_EUTECTOIDE, T_C)) if C0 < C_EUTECTOIDE < Cs else None

    # Flujo en la superficie y carbono acumulado a lo largo del tratamiento
    r["t"] = np.linspace(t_h / 100.0, t_h, 300)                                     # [h] (en t = 0 el flujo es infinito)
    r["J0_t"] = calcular_flujo(0.0, r["t"], C0, Cs, T_C) * KG_M2S_A_G_M2H          # [g/(m²·h)]
    r["M_t"] = calcular_carbono_absorbido(r["t"], C0, Cs, T_C) * 1000.0            # [g/m²]
    r["J0"] = float(r["J0_t"][-1])                                                   # [g/(m²·h)] al final
    r["J0_cuarto"] = float(calcular_flujo(0.0, t_h / 4.0, C0, Cs, T_C) * KG_M2S_A_G_M2H)  # [g/(m²·h)] a t/4
    r["M"] = float(r["M_t"][-1])                                                     # [g/m²] al final
    # Flujo contra profundidad en tres momentos del tratamiento
    r["tiempos_J"] = (t_h / 4.0, t_h / 2.0, t_h)                                     # [h]
    r["J_x"] = [calcular_flujo(r["x"], ti, C0, Cs, T_C) * KG_M2S_A_G_M2H for ti in r["tiempos_J"]]

    r["avisos"].extend(verificar_austenita(T_C, C0, Cs))
    return r


def explicar_microestructura(r, C0, Cs):
    """Texto que cuenta qué microestructura queda a cada profundidad (enfriamiento lento)."""
    sup = calcular_microconstituyentes(Cs)
    nuc = calcular_microconstituyentes(C0)
    pasos = []
    if Cs > C_EUTECTOIDE:
        pasos.append(
            f"**En la superficie hay {Cs:.2f} wt % de C, más que el eutectoide (0.8 wt %).** Esa zona es "
            f"**hipereutectoide**: al enfriar lento quedaría {sup['perlita'] * 100:.1f} % de perlita y "
            f"{sup['cementita'] * 100:.1f} % de cementita proeutectoide."
        )
    elif Cs == C_EUTECTOIDE:
        pasos.append("**En la superficie hay justo 0.8 wt % de C (eutectoide):** al enfriar lento sería 100 % perlita.")
    else:
        pasos.append(
            f"**En la superficie hay {Cs:.2f} wt % de C, menos que el eutectoide (0.8 wt %).** Toda la capa es "
            f"**hipoeutectoide**: al enfriar lento quedaría {sup['perlita'] * 100:.1f} % de perlita."
        )
    if r["x_eut"] is not None:
        pasos.append(
            f"**A {r['x_eut']:.3f} [mm] de profundidad el carbono baja a 0.8 wt %.** Ahí la estructura sería "
            f"100 % perlita. Más adentro, la perlita disminuye y aparece ferrita proeutectoide."
        )
    pasos.append(
        f"**En el núcleo queda C₀ = {C0:.2f} wt %:** {nuc['perlita'] * 100:.1f} % de perlita y "
        f"{nuc['ferrita'] * 100:.1f} % de ferrita proeutectoide. A partir de unos 4·L = {4 * r['L']:.2f} [mm] "
        f"ya casi no llega carbono."
    )
    return "\n".join(f"{i}. {p}" for i, p in enumerate(pasos, start=1)) + "\n"


def explicar_flujo(r, t_h):
    """Texto que cuenta cómo cambia el flujo de carbono durante el tratamiento."""
    J_cuarto = r["J0_cuarto"]
    return (
        f"1. **Al principio entra mucho carbono.** La superficie pasa de golpe de C₀ a Cs y el gradiente es muy "
        f"grande, por eso el flujo empieza muy alto.\n"
        f"2. **Luego el flujo baja.** Mientras el carbono se acumula, el perfil se suaviza y el gradiente en la "
        f"superficie es menor. El flujo baja como 1/√t: a las {t_h / 4:g} h es de {J_cuarto:.2f} [g/(m²·h)] "
        f"y al final ({t_h:g} h) es de {r['J0']:.2f} [g/(m²·h)], la mitad.\n"
        f"3. **El carbono total sigue creciendo, pero cada vez más lento.** Hasta las {t_h:g} h entraron "
        f"{r['M']:.1f} [g] de carbono por cada m² de superficie. Crece como √t: con el doble de tiempo, "
        f"entra √2 ≈ 1.41 veces más carbono, no el doble.\n"
        f"4. **El frente avanza.** En la gráfica de la derecha, el flujo dentro de la pieza llega cada vez más "
        f"profundo, aunque con menos intensidad.\n"
    )


# ---------- Gráficas ----------
def _layout(fig, **extra):
    """Aplica el formato común y luego lo propio de cada gráfica (sin repetir llaves)."""
    fig.update_layout(**LAYOUT_BASE)
    fig.update_layout(**extra)
    return fig


def construir_figura_fracciones(r):
    """Área apilada: fracción de cada microconstituyente [%] contra profundidad, con el perfil de C encima."""
    fig = go.Figure()
    for clave in ("cementita", "perlita", "ferrita"):
        fig.add_trace(go.Scatter(
            x=r["x"], y=r["fr"][clave] * 100.0, mode="lines", name=NOMBRES[clave], stackgroup="micro",
            line=dict(width=0.5, color=COLORES[clave]), fillcolor=COLORES[clave],
            hovertemplate="x = %{x:.3f} mm<br>" + NOMBRES[clave] + " = %{y:.1f} %<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=r["x"], y=r["C"], mode="lines", name="Carbono C(x) [wt %]", yaxis="y2",
        line=dict(color=COLOR_TEXTO, width=2.5, dash="dash"),
        hovertemplate="x = %{x:.3f} mm<br>C = %{y:.3f} wt %<extra></extra>",
    ))
    if r["x_eut"] is not None and r["x_eut"] <= r["x"][-1]:
        fig.add_vline(x=r["x_eut"], line_dash="dot", line_color=COLOR_TEXTO,
                      annotation_text="0.8 wt % (100 % perlita)", annotation_position="top")
    return _layout(
        fig, height=440, margin=dict(l=10, r=60, t=60, b=10), hovermode="x unified",
        xaxis=dict(title="Profundidad desde la superficie [mm]", range=[0, float(r["x"][-1])]),
        yaxis=dict(title="Fracción del microconstituyente [%]", range=[0, 100]),
        yaxis2=dict(title="Carbono [wt %]", overlaying="y", side="right", showgrid=False, rangemode="tozero"),
    )


def construir_figura_corte(r, C0, Cs):
    """Banda de color que simula un corte de la pieza: color = concentración de carbono."""
    fig = go.Figure(go.Heatmap(
        x=r["x"], y=["Pieza"], z=[r["C"]], zmin=C0, zmax=Cs, colorscale="YlOrRd",
        colorbar=dict(title=dict(text="C [wt %]"), thickness=12),
        hovertemplate="x = %{x:.3f} mm<br>C = %{z:.3f} wt %<extra></extra>",
    ))
    x_fin = float(r["x"][-1])
    zonas = []
    if r["x_eut"] is not None and r["x_eut"] < x_fin:
        fig.add_vline(x=r["x_eut"], line_dash="dash", line_color=COLOR_TEXTO, line_width=2)
        zonas.append((r["x_eut"] / 2.0, "Hipereutectoide"))
        inicio_hipo = r["x_eut"]
    else:
        inicio_hipo = 0.0
    x_nucleo = 4.0 * r["L"]
    fin_hipo = min(x_nucleo, x_fin)
    if fin_hipo > inicio_hipo:
        zonas.append(((inicio_hipo + fin_hipo) / 2.0, "Hipoeutectoide"))
    if x_nucleo < x_fin:
        fig.add_vline(x=x_nucleo, line_dash="dot", line_color=COLOR_TEXTO)
        zonas.append(((x_nucleo + x_fin) / 2.0, "Núcleo (≈ C₀)"))
    for x_txt, texto in zonas:
        fig.add_annotation(x=x_txt, y="Pieza", text=f"<b>{texto}</b>", showarrow=False,
                           font=dict(color=COLOR_TEXTO, size=13), bgcolor="rgba(255,255,255,0.75)")
    return _layout(
        fig, height=190, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(title="Profundidad desde la superficie [mm]  (superficie a la izquierda)"),
        yaxis=dict(showticklabels=False),
    )


def construir_figura_dona(C_sel):
    """Dona con la microestructura a una profundidad elegida."""
    fr = calcular_microconstituyentes(C_sel)
    claves = [c for c in ("ferrita", "perlita", "cementita") if fr[c] > 1e-6]
    fig = go.Figure(go.Pie(
        labels=[NOMBRES[c] for c in claves], values=[fr[c] * 100.0 for c in claves],
        marker=dict(colors=[COLORES[c] for c in claves], line=dict(color="#FFFFFF", width=2)),
        hole=0.58, sort=False, textinfo="percent", hovertemplate="%{label}: %{value:.1f} %<extra></extra>",
    ))
    fig.add_annotation(text=f"<b>{C_sel:.2f}</b><br>wt % C", showarrow=False, font=dict(size=16, color=COLOR_TEXTO))
    return _layout(fig, height=320, margin=dict(l=10, r=10, t=10, b=10),
                   legend=dict(orientation="h", yanchor="top", y=-0.02, x=0))


def construir_figura_flujo_tiempo(r):
    """Flujo en la superficie [g/(m²·h)] y carbono acumulado [g/m²] contra el tiempo."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=r["t"], y=r["M_t"], mode="lines", name="Carbono acumulado [g/m²]", yaxis="y2",
        line=dict(color=COLORES_TRATAMIENTOS[1], width=2), fill="tozeroy", fillcolor="rgba(28,126,214,0.12)",
        hovertemplate="t = %{x:.2f} h<br>M = %{y:.1f} g/m²<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=r["t"], y=r["J0_t"], mode="lines", name="Flujo en la superficie [g/(m²·h)]",
        line=dict(color=COLOR_PERFIL, width=3),
        hovertemplate="t = %{x:.2f} h<br>J = %{y:.2f} g/(m²·h)<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[r["t"][-1]], y=[r["J0"]], mode="markers", name="Final del tratamiento",
        marker=dict(size=11, color=COLOR_PERFIL, line=dict(width=2, color="#FFFFFF")),
        hovertemplate="J = %{y:.2f} g/(m²·h)<extra></extra>",
    ))
    J_max_vis = float(np.percentile(r["J0_t"], 97))  # recorta el pico inicial para que se lea la curva
    return _layout(
        fig, height=400, margin=dict(l=10, r=60, t=60, b=10), hovermode="x unified",
        xaxis=dict(title="Tiempo de tratamiento [h]"),
        yaxis=dict(title="Flujo en la superficie [g/(m²·h)]", range=[0, J_max_vis * 1.05]),
        yaxis2=dict(title="Carbono acumulado [g/m²]", overlaying="y", side="right", showgrid=False, rangemode="tozero"),
    )


def construir_figura_flujo_profundidad(r):
    """Flujo de carbono dentro de la pieza [g/(m²·h)] contra profundidad, en tres momentos."""
    fig = go.Figure()
    for ti, J, color in zip(r["tiempos_J"], r["J_x"], COLORES_TRATAMIENTOS[::-1]):
        fig.add_trace(go.Scatter(
            x=r["x"], y=J, mode="lines", name=f"t = {ti:g} h", line=dict(color=color, width=3),
            hovertemplate="x = %{x:.3f} mm<br>J = %{y:.2f} g/(m²·h)<extra></extra>",
        ))
    return _layout(
        fig, height=400, hovermode="x unified",
        xaxis=dict(title="Profundidad desde la superficie [mm]", range=[0, float(r["x"][-1])]),
        yaxis=dict(title="Flujo de carbono [g/(m²·h)]", rangemode="tozero"),
    )


# ---------- Pantalla ----------
def mostrar():
    st.header("Módulo 6. Microestructura, flujo de carbono e industria")
    st.write(
        "Con el mismo perfil de carbono de los otros módulos, aquí se ve (A) qué microestructura tendría cada zona "
        "de la pieza si se enfría lento y (B) cuánto carbono entra por la superficie. Al final se explica por qué "
        "esto importa en la industria."
    )

    # ----- Datos del tratamiento -----
    st.subheader("Datos del tratamiento")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        T_C = st.number_input("Temperatura [°C]", min_value=T_MIN, max_value=T_MAX, value=927.0, step=5.0,
                              format="%.1f", key="m6_T")
    with c2:
        t_h = st.number_input("Tiempo [h]", min_value=0.1, max_value=1000.0, value=10.0, step=0.5,
                              format="%.2f", key="m6_t")
    with c3:
        C0 = st.number_input("C₀ [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX, value=0.20, step=0.05,
                             format="%.2f", key="m6_C0")
    with c4:
        Cs = st.number_input("Cs [wt %]", min_value=0.0, max_value=SOLUBILIDAD_MAX, value=1.00, step=0.05,
                             format="%.2f", key="m6_Cs")
    with c5:
        x_max_mm = st.number_input("Profundidad a graficar [mm]", min_value=0.1, max_value=20.0, value=2.0,
                                   step=0.5, format="%.1f", key="m6_xmax")

    r = calcular_modulo6(T_C, t_h, C0, Cs, x_max_mm)
    if r["errores"]:
        for mensaje in r["errores"]:
            st.error(mensaje)
        return
    for aviso in r["avisos"]:
        st.warning(aviso)

    # ===== A. Microestructura =====
    st.divider()
    st.subheader("A. ¿Qué microestructura tendría cada zona si se enfría lento?")
    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(
            "Cuando la austenita se enfría **lentamente** por debajo de 723 °C, se transforma según el diagrama "
            "Fe–Fe₃C. Con la **regla de la palanca** se calcula qué fracción queda de cada microconstituyente, "
            "usando los valores del diagrama de clase:"
        )
        st.markdown(
            f"- **Hipoeutectoide** (C ≤ {C_EUTECTOIDE} wt %): perlita + ferrita proeutectoide\n"
            f"- **Eutectoide** (C = {C_EUTECTOIDE} wt %): 100 % perlita\n"
            f"- **Hipereutectoide** (C > {C_EUTECTOIDE} wt %): perlita + cementita proeutectoide"
        )
    with der:
        st.latex(r"W_{perlita} = \frac{C - 0.02}{0.8 - 0.02} \quad (C \le 0.8)")
        st.latex(r"W_{perlita} = \frac{6.67 - C}{6.67 - 0.8} \quad (C > 0.8)")
        st.caption(f"Valores del diagrama de clase: {C_FERRITA_MAX} wt % (ferrita), {C_EUTECTOIDE} wt % (eutectoide), "
                   f"{C_CEMENTITA} wt % (cementita).")

    st.markdown("**Corte de la pieza:** el color indica cuánto carbono hay a cada profundidad.")
    st.plotly_chart(construir_figura_corte(r, C0, Cs), width="stretch")
    st.plotly_chart(construir_figura_fracciones(r), width="stretch")

    st.markdown("**Inspecciona una profundidad:** mueve el control para ver la microestructura en ese punto.")
    col_ctrl, col_dona = st.columns([2, 3])
    with col_ctrl:
        x_sel = st.slider("Profundidad [mm]", min_value=0.0, max_value=float(x_max_mm),
                          value=min(0.10, float(x_max_mm)), step=0.01, key="m6_xsel")
        C_sel = float(calcular_perfil(x_sel, t_h, C0, Cs, T_C))
        fr_sel = calcular_microconstituyentes(C_sel)
        tipo = ("hipereutectoide" if C_sel > C_EUTECTOIDE + 1e-9
                else "eutectoide" if abs(C_sel - C_EUTECTOIDE) <= 1e-9 else "hipoeutectoide")
        st.metric("Carbono a esa profundidad", f"{C_sel:.3f} wt %")
        st.markdown(
            f"A **{x_sel:.2f} [mm]** el acero es **{tipo}**:\n\n"
            f"- Ferrita proeutectoide: {fr_sel['ferrita'] * 100:.1f} %\n"
            f"- Perlita: {fr_sel['perlita'] * 100:.1f} %\n"
            f"- Cementita proeutectoide: {fr_sel['cementita'] * 100:.1f} %"
        )
    with col_dona:
        st.plotly_chart(construir_figura_dona(C_sel), width="stretch")

    st.markdown("**¿Qué está pasando?**")
    st.markdown(explicar_microestructura(r, C0, Cs))
    st.info(
        "Esto es para **enfriamiento lento** (equilibrio). En la práctica, después de cementar se **templa**: la "
        "austenita se transforma en martensita y no en perlita. El temple y la dureza no se calculan en esta app."
    )

    # ===== B. Flujo =====
    st.divider()
    st.subheader("B. ¿Cuánto carbono entra? Flujo en la superficie")
    izq, der = st.columns([3, 2])
    with izq:
        st.markdown(
            "La **primera ley de Fick** dice que el flujo es proporcional al gradiente de concentración. "
            "Al derivar la solución erfc se obtiene el flujo dentro de la pieza y en la superficie. "
            "Sumando el flujo a lo largo del tiempo sale el carbono total que entró por cada m² de superficie."
        )
        st.caption(
            f"Para pasar de wt % a masa se usa la densidad del hierro, {DENSIDAD_ACERO:.0f} [kg/m³] "
            "(a temperatura ambiente; a la temperatura de cementación es un poco menor, así que es una aproximación)."
        )
    with der:
        st.latex(r"J = -D\,\frac{\partial C}{\partial x} = (C_s - C_0)\sqrt{\frac{D}{\pi t}}\;e^{-x^2/4Dt}")
        st.latex(r"M(t) = 2\,(C_s - C_0)\sqrt{\frac{D\,t}{\pi}}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Flujo en la superficie al final [g/(m²·h)]", f"{r['J0']:.2f}")
    m2.metric("Carbono que entró [g/m²]", f"{r['M']:.1f}")
    m3.metric("Carbono que entró [mg/cm²]", f"{r['M'] / 10.0:.2f}")

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(construir_figura_flujo_tiempo(r), width="stretch")
        st.caption("El pico inicial se recorta para que se lea la curva: en t → 0 el modelo da un flujo infinito, "
                   "porque supone que la superficie llega a Cs al instante.")
    with g2:
        st.plotly_chart(construir_figura_flujo_profundidad(r), width="stretch")
        st.caption("Flujo dentro de la pieza en tres momentos del tratamiento.")

    st.markdown("**¿Qué está pasando?**")
    st.markdown(explicar_flujo(r, t_h))

    # ===== C. Industria =====
    st.divider()
    st.subheader("C. ¿Por qué importa en la industria?")
    st.write(
        "La cementación permite tener en una misma pieza dos cosas que normalmente no van juntas: una superficie "
        "dura y resistente al desgaste, y un núcleo tenaz que aguanta golpes."
    )
    fila1 = st.columns(2)
    fila2 = st.columns(2)
    tarjetas = [
        ("🔧 ¿Dónde se usa?",
         "En piezas que rozan o reciben cargas repetidas en la superficie pero también golpes: engranes, piñones, "
         "árboles de levas, ejes, pasadores y componentes de transmisiones (automotriz, maquinaria agrícola e "
         "industrial)."),
        ("💪 ¿Qué se gana?",
         "Se parte de un acero de bajo carbono, más barato y tenaz, y solo se enriquece la capa que lo necesita. "
         "Después del temple, la superficie queda dura y resistente al desgaste y a la fatiga de contacto, y el "
         "núcleo sigue siendo tenaz."),
        ("⚠️ ¿Qué pasa si la capa sale mal?",
         "Si es muy delgada, la superficie se desgasta o falla pronto. Si queda con demasiado carbono (zona "
         "hipereutectoide, sección A), puede formarse cementita en los límites de grano, que es frágil, y al templar "
         "queda austenita retenida. Si es más profunda de lo necesario, se gasta tiempo y energía de horno de más."),
        ("🖥️ ¿Cómo ayuda un simulador?",
         "Permite planear temperatura y tiempo antes de usar el horno (Módulo 2), comparar opciones (Módulo 3), ver "
         "si la superficie quedará hipereutectoide (sección A) y entender cuánto carbono tiene que aportar la "
         "atmósfera del horno en cada momento (sección B). En la industria el ciclo se ajusta además con ensayos."),
    ]
    for columna, (titulo, texto) in zip(list(fila1) + list(fila2), tarjetas):
        with columna:
            with st.container(border=True):
                st.markdown(f"**{titulo}**")
                st.write(texto)

    st.markdown(
        """
**Cómo se conecta con lo que calcula esta app**

| Lo que ves en la app | Qué significa en el proceso real |
|---|---|
| El perfil de carbono y la profundidad para Cobj (Módulo 1) | Qué tan gruesa queda la capa enriquecida |
| La curva temperatura–tiempo (Módulo 2) | Subir la temperatura acorta el tiempo de horno (menos costo por pieza), pero el modelo no calcula efectos como el crecimiento de grano |
| La zona hipereutectoide (sección A) | Por eso se controla Cs con el potencial de carbono de la atmósfera: para no dejar exceso de carbono en la superficie |
| El flujo alto al inicio (sección B) | Al principio la atmósfera tiene que aportar mucho carbono; por eso en la práctica se usan ciclos de enriquecimiento seguidos de una etapa de difusión |
        """
    )
    st.caption("Esta sección describe el uso de la cementación de forma general. La app no modela el temple, "
               "la dureza ni la atmósfera del horno.")

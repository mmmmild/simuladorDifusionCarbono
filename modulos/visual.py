# Simulador Difusión Carbono. Gráficas del "corte de la pieza" (las usan Teoría y Simulación).
# Se dibuja un pedazo rectangular de acero visto de lado: la superficie arriba y la profundidad hacia abajo.
# El color es la concentración de carbono. El ancho del rectángulo es solo para que se vea como una pieza:
# el modelo es en una dimensión, así que el color solo cambia con la profundidad.

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from estilo import COLOR_COBJ, COLOR_PERFIL, COLOR_TEXTO, ESCALA_CARBONO, FACTOR_SEMIINFINITO, LAYOUT_BASE
from modelo import calcular_longitud_difusion, calcular_perfil, calcular_profundidad

ANCHO_MM = 3.0        # [mm] ancho dibujado del pedazo de acero (solo visual)
N_PROFUNDIDAD = 150   # puntos en la profundidad
N_ANCHO = 12          # columnas del rectángulo (todas iguales, es solo para dibujar)


def profundidad_a_graficar(t_h, T_C, C0, Cs, Cobj):
    """Profundidad máxima del dibujo [mm]: llega hasta donde casi no hay carbono (4·L) o un poco más
    allá de la profundidad objetivo, lo que sea mayor. Se redondea hacia arriba a 0.5 mm."""
    L = float(calcular_longitud_difusion(t_h, T_C))   # [mm]
    x_max = FACTOR_SEMIINFINITO * L
    if C0 < Cobj < Cs:
        x_max = max(x_max, 1.25 * float(calcular_profundidad(t_h, C0, Cs, Cobj, T_C)))
    return float(np.ceil(x_max / 0.5) * 0.5)


def _perfil(y_mm, t_h, C0, Cs, T_C):
    """Perfil de carbono; en t = 0 la pieza todavía tiene C0 en todos lados."""
    if t_h <= 0:
        return np.full_like(y_mm, C0, dtype=float)
    return calcular_perfil(y_mm, t_h, C0, Cs, T_C)


def _rectangulo(C):
    """Convierte el perfil (una columna) en un rectángulo de N_ANCHO columnas iguales."""
    return np.tile(np.asarray(C)[:, None], (1, N_ANCHO))


def construir_cortes_estaticos(T_C, tiempos_h, C0, Cs):
    """Varios cortes de la pieza lado a lado, uno por tiempo (para la página de teoría)."""
    x_max = profundidad_a_graficar(max(tiempos_h), T_C, C0, Cs, -1.0)
    y = np.linspace(0.0, x_max, N_PROFUNDIDAD)
    x = np.linspace(0.0, ANCHO_MM, N_ANCHO)
    titulos = ["Antes de entrar al horno" if t <= 0 else f"Después de {t:g} h" for t in tiempos_h]
    fig = make_subplots(rows=1, cols=len(tiempos_h), shared_yaxes=True, subplot_titles=titulos,
                        horizontal_spacing=0.03)
    for i, t in enumerate(tiempos_h, start=1):
        fig.add_trace(go.Heatmap(
            x=x, y=y, z=_rectangulo(_perfil(y, t, C0, Cs, T_C)), coloraxis="coloraxis",
            hovertemplate="profundidad = %{y:.2f} mm<br>C = %{z:.2f} wt %<extra></extra>",
        ), row=1, col=i)
        fig.update_xaxes(showticklabels=False, row=1, col=i)
    fig.update_layout(**LAYOUT_BASE)
    fig.update_layout(
        height=380, margin=dict(l=10, r=10, t=50, b=10),
        coloraxis=dict(colorscale=ESCALA_CARBONO, cmin=C0, cmax=Cs,
                       colorbar=dict(title=dict(text="C [wt %]"), thickness=12)),
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_yaxes(title_text="Profundidad desde la superficie [mm]", row=1, col=1)
    return fig


def construir_animacion(T_C, t_h, C0, Cs, Cobj, n_cuadros=25):
    """Figura animada: a la izquierda el corte de la pieza y a la derecha el perfil de carbono, con la misma
    profundidad en el eje vertical. Con el botón ▶ se ve cómo entra el carbono desde t ≈ 0 hasta t_h.
    La línea azul punteada marca dónde se alcanza Cobj en cada momento."""
    x_max = profundidad_a_graficar(t_h, T_C, C0, Cs, Cobj)
    y = np.linspace(0.0, x_max, N_PROFUNDIDAD)                # [mm]
    x = np.linspace(0.0, ANCHO_MM, N_ANCHO)                   # [mm] (solo visual)
    tiempos = t_h * np.arange(1, n_cuadros + 1) / n_cuadros   # [h]
    hay_objetivo = C0 < Cobj < Cs

    def trazas(t):
        C = _perfil(y, t, C0, Cs, T_C)
        x_obj = float(calcular_profundidad(t, C0, Cs, Cobj, T_C)) if hay_objetivo else None
        lista = [
            go.Heatmap(x=x, y=y, z=_rectangulo(C), coloraxis="coloraxis",
                       hovertemplate="profundidad = %{y:.3f} mm<br>C = %{z:.3f} wt %<extra></extra>"),
            go.Scatter(x=C, y=y, mode="lines", name="Perfil C(x)", line=dict(color=COLOR_PERFIL, width=3),
                       hovertemplate="C = %{x:.3f} wt %<br>profundidad = %{y:.3f} mm<extra></extra>"),
        ]
        if hay_objetivo:
            lista += [
                go.Scatter(x=[0.0, ANCHO_MM], y=[x_obj, x_obj], mode="lines", name=f"Llega a Cobj = {Cobj:.2f} wt %",
                           line=dict(color=COLOR_COBJ, width=3, dash="dash"), hoverinfo="skip"),
                go.Scatter(x=[Cobj], y=[x_obj], mode="markers+text", name="Profundidad para Cobj",
                           text=[f"  {x_obj:.2f} mm"], textposition="middle right", showlegend=False,
                           marker=dict(size=11, color=COLOR_COBJ, line=dict(width=2, color="#FFFFFF")),
                           hovertemplate="profundidad = %{y:.3f} mm<extra></extra>"),
            ]
        return lista

    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, column_widths=[0.38, 0.62],
                        horizontal_spacing=0.12,
                        subplot_titles=("Corte de la pieza (superficie arriba)", "Perfil de carbono"))
    finales = trazas(t_h)
    columnas = [1, 2, 1, 2]
    for traza, col in zip(finales, columnas):
        fig.add_trace(traza, row=1, col=col)
    if hay_objetivo:  # línea fija de Cobj en el perfil
        fig.add_trace(go.Scatter(x=[Cobj, Cobj], y=[0.0, x_max], mode="lines", showlegend=False,
                                 line=dict(color=COLOR_COBJ, width=1, dash="dot"), hoverinfo="skip"), row=1, col=2)

    indices = list(range(len(finales)))
    fig.frames = [go.Frame(data=trazas(t), traces=indices, name=f"{t:.2f}") for t in tiempos]

    fig.update_layout(**LAYOUT_BASE)
    fig.update_layout(
        height=580, margin=dict(l=10, r=10, t=95, b=90),
        legend=dict(orientation="h", yanchor="bottom", y=1.10, x=0),
        coloraxis=dict(colorscale=ESCALA_CARBONO, cmin=C0, cmax=Cs,
                       colorbar=dict(title=dict(text="C [wt %]"), thickness=12, x=0.355, xanchor="left", len=0.85)),
        updatemenus=[dict(
            type="buttons", direction="left", x=0.0, y=-0.08, xanchor="left", yanchor="top", showactive=False,
            buttons=[
                dict(label="▶ Ver la difusión", method="animate",
                     args=[None, dict(frame=dict(duration=180, redraw=True), transition=dict(duration=0),
                                      fromcurrent=False, mode="immediate")]),
                dict(label="⏸ Pausa", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
            ],
        )],
        sliders=[dict(
            active=len(tiempos) - 1, x=0.25, y=-0.06, len=0.75, xanchor="left", yanchor="top",
            currentvalue=dict(prefix="Tiempo: ", suffix=" h", font=dict(color=COLOR_TEXTO)),
            steps=[dict(label=f"{t:.1f}", method="animate",
                        args=[[f"{t:.2f}"], dict(frame=dict(duration=0, redraw=True), mode="immediate")])
                   for t in tiempos],
        )],
    )
    fig.update_xaxes(showticklabels=False, range=[0.0, ANCHO_MM], row=1, col=1)
    fig.update_xaxes(title_text="Carbono [wt %]", range=[0.0, Cs * 1.12], row=1, col=2)
    fig.update_yaxes(autorange="reversed")
    fig.update_yaxes(title_text="Profundidad desde la superficie [mm]", row=1, col=1)
    return fig

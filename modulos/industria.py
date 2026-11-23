# Simulador Difusión Carbono. Página 5: importancia de la cementación en la industria.
# Es una descripción general (sin cifras de mercado ni datos de empresas). app.py solo llama a mostrar().

import streamlit as st

from estilo import C0_DEMO, COLOR_TEXTO, CS_DEMO, T_DEMO
from modelo import calcular_longitud_difusion
from modulos.visual import ANCHO_MM, construir_cortes_estaticos

T_H_DIBUJO = 10.0  # [h]


def construir_figura_pieza():
    """Corte de una pieza cementada con las dos zonas rotuladas (superficie y núcleo)."""
    fig = construir_cortes_estaticos(T_DEMO, (T_H_DIBUJO,), C0_DEMO, CS_DEMO)
    L = float(calcular_longitud_difusion(T_H_DIBUJO, T_DEMO))  # [mm]
    fig.layout.annotations = ()  # quita el título del subgráfico
    fig.add_annotation(x=ANCHO_MM / 2, y=0.5 * L, text="<b>Superficie rica en carbono</b><br>dura después del temple:"
                       "<br>resiste desgaste", showarrow=False, font=dict(color="#FFFFFF", size=13))
    fig.add_annotation(x=ANCHO_MM / 2, y=3.2 * L, text="<b>Núcleo con poco carbono</b><br>tenaz: aguanta golpes",
                       showarrow=False, font=dict(color=COLOR_TEXTO, size=13))
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
    return fig


def mostrar():
    st.header("Importancia en la industria")
    izq, der = st.columns([3, 2])
    with izq:
        st.write(
            "La cementación permite tener en **una misma pieza** dos propiedades que normalmente no van juntas: "
            "una **superficie dura** que resiste el desgaste y un **núcleo tenaz** que aguanta golpes sin romperse."
        )
        st.write(
            "Se parte de un acero de bajo carbono, más barato y tenaz, y solo se enriquece con carbono la capa que "
            "lo necesita. Después del temple, esa capa queda dura y el interior conserva su tenacidad."
        )
    with der:
        st.plotly_chart(construir_figura_pieza(), width="stretch")
        st.caption(f"Corte calculado con el simulador: {T_DEMO:.0f} °C, {T_H_DIBUJO:g} h, C₀ = {C0_DEMO:.2f} y "
                   f"Cs = {CS_DEMO:.2f} wt %. La dureza no la calcula la app; el texto describe lo que pasa al templar.")

    fila1 = st.columns(2)
    fila2 = st.columns(2)
    tarjetas = [
        ("🔧 ¿Dónde se usa?",
         "En piezas que rozan o reciben cargas repetidas en la superficie, pero que también deben aguantar golpes: "
         "engranes, piñones, árboles de levas, ejes, pasadores y componentes de transmisiones (automotriz, "
         "maquinaria agrícola e industrial)."),
        ("💪 ¿Qué se gana?",
         "Una superficie resistente al desgaste y a la fatiga de contacto, con un núcleo tenaz. Así la pieza dura más "
         "sin tener que fabricarla toda de un acero con mucho carbono, que sería más frágil."),
        ("⚠️ ¿Qué pasa si la capa sale mal?",
         "Si es muy delgada, la superficie se desgasta o falla pronto. Si queda con demasiado carbono, pueden formarse "
         "carburos frágiles y, al templar, austenita retenida. Si es más profunda de lo necesario, se gasta tiempo y "
         "energía de horno de más."),
        ("🖥️ ¿Cómo ayuda un simulador?",
         "Permite planear temperatura y tiempo antes de usar el horno, comparar opciones y entender el efecto de cada "
         "variable. En la industria el ciclo se ajusta además con ensayos sobre piezas reales."),
    ]
    for columna, (titulo, texto) in zip(list(fila1) + list(fila2), tarjetas):
        with columna:
            with st.container(border=True):
                st.markdown(f"**{titulo}**")
                st.write(texto)

    st.subheader("Cómo se conecta con lo que calcula esta app")
    st.markdown(
        """
| En la app | En el proceso real |
|---|---|
| **Simulación:** perfil de carbono y profundidad para Cobj | Qué tan gruesa queda la capa enriquecida con carbono |
| **Diseño inverso:** curva temperatura–tiempo | Subir la temperatura acorta el tiempo de horno (menos costo por pieza), aunque aumentan efectos que el modelo no calcula, como el crecimiento de grano |
| **Comparación:** cuál llega a la meta con menos tiempo | Elegir el ciclo de horno más corto que cumple la especificación |
| **Rango de Cs** (por debajo del límite de solubilidad) | Por eso se controla el carbono de la atmósfera del horno: para no dejar exceso de carbono en la superficie |
        """
    )
    st.caption("Esta página describe el uso de la cementación de forma general. La app no modela el temple, la dureza "
               "ni la atmósfera del horno.")

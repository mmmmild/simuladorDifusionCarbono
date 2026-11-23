# Simulador Difusión Carbono. Portada (se muestra arriba de la página de Fundamento teórico).

import streamlit as st

from estilo import (
    CARRERA, COLOR_PERFIL, COLOR_TEXTO, FACULTAD, INTEGRANTES, NOMBRE_PROYECTO,
    PROFESORA, SUBTITULO_PROYECTO, UNIVERSIDAD,
)


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

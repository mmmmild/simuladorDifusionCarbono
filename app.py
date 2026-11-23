# Simulador Difusión Carbono. Navegación de la app (Streamlit).
# UNAM, Facultad de Ingeniería. Ingeniería de Materiales.
#
# Este archivo SOLO navega. Cada página vive en su archivo dentro de modulos/ y expone
# una función mostrar(). Para agregar una página: se importa arriba y se registra en PAGINAS.
# Se corre desde la carpeta del proyecto con:  python -m streamlit run app.py

import streamlit as st

import estilo
from modulos import industria, m1_simulacion, m2_inverso, m3_comparacion, m4_teoria

# Nombre que se ve en la barra lateral  ->  función que dibuja la página
PAGINAS = {
    estilo.PAGINA_TEORIA: m4_teoria.mostrar,
    estilo.PAGINA_SIMULADOR: m1_simulacion.mostrar,
    estilo.PAGINA_INVERSO: m2_inverso.mostrar,
    estilo.PAGINA_COMPARACION: m3_comparacion.mostrar,
    estilo.PAGINA_INDUSTRIA: industria.mostrar,
}


def main():
    # Esta tiene que ser la primera instrucción de Streamlit
    st.set_page_config(page_title=estilo.NOMBRE_PROYECTO, page_icon="🔬", layout="wide")

    st.sidebar.title(estilo.NOMBRE_PROYECTO)
    # La llave permite que el botón del diseño inverso cambie de página
    seleccion = st.sidebar.radio("Secciones", list(PAGINAS.keys()), key=estilo.ESTADO_PAGINA)
    st.sidebar.caption("Modelo: segunda ley de Fick, carbono en Fe-γ. Valores de demostración.")
    st.sidebar.caption(f"{estilo.UNIVERSIDAD} · {estilo.FACULTAD}")

    PAGINAS[seleccion]()


if __name__ == "__main__":
    main()

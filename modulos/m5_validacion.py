# Simulador Difusión Carbono. Módulo 5: validación y limitaciones.
# (Borrador completo escrito por la persona A para que la persona B lo revise y lo adapte con sus palabras.)
#
# La tabla de pruebas sale de validacion.py (ejecutar_validacion). Los números del cálculo manual y del
# Caso E salen de modelo.py y de esa tabla; no están escritos a mano.
# app.py solo llama a mostrar().

import numpy as np
import pandas as pd
import streamlit as st

from estilo import FACTOR_SEMIINFINITO, SOLUBILIDAD_MAX, T_MAX, T_MIN
from modelo import (
    CERO_CELSIUS_K, D0, Q, R,
    calcular_difusividad, calcular_longitud_difusion, calcular_profundidad, calcular_z,
)
from validacion import ejecutar_validacion


# ---------- Lógica (sin Streamlit, para poder probarla aparte) ----------
def _formato(valor):
    """Texto para mostrar un valor de la tabla de pruebas."""
    return f"{valor:.4g}" if isinstance(valor, float) else str(valor)


def tabla_pruebas(filas):
    """Convierte las filas de validacion.py en un DataFrame listo para mostrar (todo como texto)."""
    return pd.DataFrame([
        {
            "Caso": f["caso"],
            "Magnitud": f["magnitud"],
            "Referencia": _formato(f["referencia"]),
            "Calculado": _formato(f["calculado"]),
            "Tolerancia": f["tolerancia"],
            "Resultado": "PASA" if f["pasa"] else "FALLA",
        }
        for f in filas
    ])


def calculo_manual(T_C=927.0, t_h=10.0, C0=0.20, Cs=1.00, Cobj=0.40):
    """El Caso A/B escrito paso a paso (el mismo cálculo que hace modelo.py, pero a la vista).
    Regresa un diccionario con cada paso y con lo que calcula modelo.py para compararlo."""
    T_K = T_C + CERO_CELSIUS_K                              # [K]
    exponente = Q / (R * T_K)                               # [-]
    D = D0 * np.exp(-exponente)                             # [m²/s]
    t_s = t_h * 3600.0                                      # [s]
    L_mm = np.sqrt(D * t_s) * 1e3                           # [mm]
    cociente = (Cobj - C0) / (Cs - C0)                      # [-]
    z = float(calcular_z(C0, Cs, Cobj))                     # [-] erfc⁻¹(cociente)
    x_mm = 2.0 * z * L_mm                                   # [mm]
    return {
        "T_K": T_K, "exponente": exponente, "D": float(D), "t_s": t_s, "L_mm": float(L_mm),
        "cociente": cociente, "z": z, "x_mm": float(x_mm),
        "D_modelo": float(calcular_difusividad(T_C)),
        "L_modelo": float(calcular_longitud_difusion(t_h, T_C)),
        "x_modelo": float(calcular_profundidad(t_h, C0, Cs, Cobj, T_C)),
    }


# ---------- Pantalla ----------
def mostrar():
    st.header("Módulo 5. Validación y limitaciones")
    st.write(
        "Aquí se muestra qué tan confiable es el cálculo (comparado con casos de referencia) y, "
        "sobre todo, **qué NO hace el modelo**. Un resultado de esta app es una solución matemática bajo "
        "supuestos, no la propiedad de un acero real."
    )

    filas = ejecutar_validacion()
    total = len(filas)
    pasaron = sum(1 for f in filas if f["pasa"])

    # ===== 1. Pruebas numéricas =====
    st.subheader("1. Pruebas numéricas")
    c1, c2 = st.columns(2)
    c1.metric("Pruebas que pasan", f"{pasaron} de {total}")
    c2.metric("Casos de validación", len({f["caso"] for f in filas}))
    if pasaron == total:
        st.success("Todas las pruebas pasan.")
    else:
        st.error("Hay pruebas que fallan. Revisa la tabla.")

    casos = ["Todos"] + list(dict.fromkeys(f["caso"] for f in filas))
    elegido = st.selectbox("Mostrar caso", casos, key="m5_caso")
    filas_mostradas = filas if elegido == "Todos" else [f for f in filas if f["caso"] == elegido]
    st.dataframe(tabla_pruebas(filas_mostradas), width="stretch", hide_index=True)

    st.markdown(
        """
| Caso | Qué comprueba | De dónde sale la referencia |
|---|---|---|
| A | D a 900, 927 y 1000 °C | Valores de referencia del proyecto (calculados con los parámetros de clase) |
| B | Perfil a 927 °C y 10 h, y profundidad para Cobj = 0.40 wt % | Valores de referencia del proyecto |
| C | Tiempos del diseño inverso (x = 0.75 mm, Cobj = 0.60 wt %) | Valores de referencia del proyecto |
| D | Efecto de Cobj sobre la profundidad | Valores de referencia del proyecto |
| E | Problema de libro: problema 5.13 de Callister | Respuesta del libro (ver abajo) |
| Consist. | Ida y vuelta entre funciones, condiciones de frontera, D·t constante | Propiedades matemáticas que deben cumplirse |
| Diseño inv. | Curva y tabla del diseño inverso | Propiedades matemáticas que deben cumplirse |
| Fases | Avisos de A3 y Acm | Puntos del diagrama de clase |
| Microestr. | Regla de la palanca (Módulo 6) | Cálculos a mano con el diagrama de clase |
| Flujo | Flujo y carbono absorbido (Módulo 6) | Derivada e integral numéricas del perfil y cálculo a mano |
| Errores | El modelo avisa cuando los datos no tienen sentido | Debe lanzar un error |
        """
    )

    # ===== 2. Caso E: problema de libro =====
    filas_E = [f for f in filas if f["caso"] == "E"]
    if len(filas_E) >= 2:
        st.subheader("2. Un problema de libro (Caso E) y el papel de R")
        libro, con_R_modelo, con_R_libro = filas_E[0]["referencia"], filas_E[0]["calculado"], filas_E[1]["calculado"]
        dif_modelo = (con_R_modelo - libro) / libro * 100.0   # [%]
        dif_libro = (con_R_libro - libro) / libro * 100.0     # [%]
        st.markdown(
            f"""
El problema de libro pide el tiempo para llegar a 0.30 wt % de C a 4 mm de profundidad a 1100 °C
(C₀ = 0.10 wt %, Cs = 0.90 wt %).

| | Tiempo [h] | Diferencia contra el libro |
|---|---|---|
| Respuesta del libro (1.13 × 10⁵ s) | {libro:.2f} | — |
| Este modelo (R = {R} [J/(mol·K)]) | {con_R_modelo:.2f} | {dif_modelo:+.2f} % |
| Mismo cálculo con R = 8.31 [J/(mol·K)] (la del libro) | {con_R_libro:.2f} | {dif_libro:+.2f} % |

La diferencia no es un error del modelo: el libro usa R = 8.31 [J/(mol·K)] y redondea a tres cifras;
este proyecto usa R = {R} [J/(mol·K)], que es el valor aceptado con menos redondeo. Con la R del libro
el resultado coincide mejor. Por eso la tolerancia del Caso E es de 1 %.
            """
        )

    # ===== 3. Cálculo manual =====
    st.subheader("3. Cálculo manual (para repetirlo con calculadora)")
    m = calculo_manual()
    st.markdown(
        f"""
Datos: T = 927 °C, t = 10 h, C₀ = 0.20 wt %, Cs = 1.00 wt %, Cobj = 0.40 wt % (valores de demostración).

1. T = 927 + {CERO_CELSIUS_K} = **{m['T_K']:.2f} [K]**
2. Q / (R·T) = {Q:.0f} / ({R} × {m['T_K']:.2f}) = **{m['exponente']:.4f}**
3. D = D₀·exp(−Q/RT) = {D0:.1e} × exp(−{m['exponente']:.4f}) = **{m['D']:.3e} [m²/s]**
   (referencia del Caso A: 8.33 × 10⁻¹² [m²/s])
4. t = 10 h × 3600 = {m['t_s']:.0f} [s]; L = √(D·t) = **{m['L_mm']:.4f} [mm]**
5. (Cobj − C₀)/(Cs − C₀) = (0.40 − 0.20)/(1.00 − 0.20) = **{m['cociente']:.2f}**
6. z = erfc⁻¹({m['cociente']:.2f}) = **{m['z']:.4f}** (se busca en tablas o con una calculadora científica)
7. x = 2·z·L = 2 × {m['z']:.4f} × {m['L_mm']:.4f} = **{m['x_mm']:.3f} [mm]**
   (referencia del Caso B: 0.89 [mm])
        """
    )
    st.caption(
        f"Comprobación contra modelo.py: D = {m['D_modelo']:.3e} [m²/s], L = {m['L_modelo']:.3f} [mm], "
        f"x = {m['x_modelo']:.3f} [mm]. Es el mismo cálculo, escrito paso a paso."
    )

    # ===== 4. Procedencia de los parámetros =====
    st.subheader("4. De dónde sale cada dato")
    st.markdown(
        f"""
| Tipo | Dato | Valor |
|---|---|---|
| **De las diapositivas de clase** | D₀ (C en Fe-γ) | {D0:.1e} [m²/s] |
| | Q (C en Fe-γ) | {Q:.0f} [J/mol] |
| | Punto eutectoide | 0.8 wt % C a 723 °C (diagrama de clase) |
| | Máxima solubilidad de C en austenita | {SOLUBILIDAD_MAX} wt % a 1147 °C (diagrama de clase) |
| | Austenita a 780 °C | 0.42 wt % C (ejercicio de clase) |
| **Elegido por el equipo** | R | {R} [J/(mol·K)] (reproduce las referencias; ver Caso E) |
| | Intervalo de temperatura | {T_MIN:.0f}–{T_MAX:.0f} °C |
| | Criterio de sólido semiinfinito | espesor ≥ {FACTOR_SEMIINFINITO:.0f}·L |
| | Línea Acm | recta entre dos puntos del diagrama (aproximación) |
| **Valores de demostración** | C₀, Cs, Cobj, T, t, x | Los que aparecen por defecto; no son estándares industriales |
| **Calculados** | D, L, z, perfil, profundidad, tiempo, temperatura | Salen de `modelo.py` |
        """
    )
    st.caption(
        "La Cs real depende del potencial de carbono de la atmósfera del horno; no sale del diagrama Fe–Fe₃C. "
        "El diagrama solo marca hasta dónde puede disolverse el carbono en austenita."
    )

    # ===== 5. Supuestos =====
    st.subheader("5. Supuestos físicos del modelo")
    st.markdown(
        """
1. **Sólido semiinfinito:** la pieza es mucho más gruesa que la profundidad de difusión (espesor ≥ 4·L).
2. **Difusión en una dirección:** el carbono avanza perpendicular a una superficie plana. No hay efectos de esquinas ni de curvatura.
3. **D constante:** el coeficiente de difusión es el mismo en toda la pieza y todo el tiempo, y **no depende de la concentración de carbono**.
4. **Temperatura constante y uniforme:** no se modelan el calentamiento ni el enfriamiento.
5. **Concentración superficial constante:** la superficie alcanza Cs desde el inicio y se mantiene (no se modela la rapidez con la que la atmósfera entrega carbono).
6. **Concentración inicial uniforme:** el núcleo parte de C₀ en toda la pieza.
7. **Una sola fase (austenita):** se supone austenita durante todo el tratamiento. Las líneas A3 y Acm solo generan avisos.
8. **Sin carburos:** no se forma cementita ni otras fases.
9. **Acero sin aleantes:** se usan los parámetros del carbono en Fe-γ. Los elementos de aleación cambian D y la actividad del carbono.
10. **Sin pérdidas:** no se modelan descarburación, oxidación ni reacciones en la superficie.
11. **wt % tratado como concentración:** se supone densidad constante, sin cambio de volumen.
12. **Arrhenius ideal:** D₀ y Q son constantes en el intervalo de temperatura; se ignoran la difusión por límites de grano y otros atajos.
        """
    )

    # ===== 6. Limitaciones =====
    st.subheader("6. Limitaciones: lo que NO se considera")
    st.markdown(
        """
- Dureza, temple, revenido, austenita retenida, esfuerzos residuales y distorsión.
- **Profundidad efectiva de endurecimiento:** esa se define con un criterio de dureza, no de concentración. Esta app **no la calcula**.
- Elementos de aleación y su efecto en D y en la solubilidad del carbono.
- Dependencia de D con la concentración de carbono.
- Control del potencial de carbono de la atmósfera (determina la Cs real).
- Transformaciones de fase durante el calentamiento y el enfriamiento.
- Formación de carburos si Cs supera el límite Acm.
- Tamaño de grano y microestructura real.
- Geometría real de la pieza (espesores pequeños, esquinas, cementación por dos caras).
- Incertidumbre de D₀ y Q: se toman como exactos.
        """
    )

    st.info(
        "**Modelo contra acero real.** Lo que sale de esta app (perfiles, profundidades, tiempos, temperaturas) son "
        "resultados **matemáticos** de la segunda ley de Fick con los supuestos de arriba. Sirven para comparar "
        "tratamientos y entender el efecto de la temperatura y el tiempo. Las propiedades de un acero industrial "
        "(dureza, profundidad efectiva, microestructura) dependen de fenómenos que este modelo no incluye y "
        "se determinan con ensayos."
    )

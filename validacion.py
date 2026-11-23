# Simulador Difusión Carbono. Validación numérica del modelo.
#
# Compara lo que calcula modelo.py contra:
#   - Casos A–D: valores de referencia que nos dieron (vienen redondeados, por eso
#     cada prueba tiene una tolerancia).
#   - Pruebas de consistencia: cosas que tienen que cumplirse siempre (ida y vuelta
#     entre funciones, condiciones de frontera, errores cuando los datos no tienen sentido).
#
# Se corre con:  python validacion.py
# Más adelante la pestaña "Validación" de la app usa ejecutar_validacion() de aquí.

import sys

import numpy as np

from modelo import (
    CERO_CELSIUS_K,
    D0,
    Q,
    calcular_z,
    calcular_difusividad,
    calcular_perfil,
    calcular_profundidad,
    calcular_tiempo,
    calcular_temperatura,
    calcular_longitud_difusion,
    calcular_diseno_inverso,
    calcular_solubilidad_acm,
    calcular_temperatura_austenita_minima,
    verificar_austenita,
    comparar_tratamientos,
    calcular_microconstituyentes,
    calcular_flujo,
    calcular_carbono_absorbido,
    DENSIDAD_ACERO,
)

C0 = 0.20   # [wt %]  valor de demostración
CS = 1.00   # [wt %]  valor de demostración


def _comparar(caso, magnitud, referencia, calculado, tolerancia, relativa=False):
    """Una fila de resultados: pasa si |calculado - referencia| cabe en la tolerancia.
    Si relativa=True, la tolerancia es una fracción de la referencia (0.005 = 0.5 %)."""
    limite = tolerancia * abs(referencia) if relativa else tolerancia
    return {
        "caso": caso,
        "magnitud": magnitud,
        "referencia": referencia,
        "calculado": float(calculado),
        "tolerancia": f"{tolerancia * 100:g} %" if relativa else f"±{tolerancia:g}",
        "pasa": bool(abs(calculado - referencia) <= limite),
    }


def _debe_dar_error(caso, magnitud, funcion, *argumentos):
    """Una fila que pasa si la función avisa con ValueError (datos sin sentido físico)."""
    try:
        funcion(*argumentos)
        lanzo = False
    except ValueError:
        lanzo = True
    return {
        "caso": caso,
        "magnitud": magnitud,
        "referencia": "ValueError",
        "calculado": "ValueError" if lanzo else "no avisó",
        "tolerancia": "-",
        "pasa": lanzo,
    }


def _debe_ser_cierto(caso, magnitud, condicion):
    """Una fila que pasa si la condición es verdadera (para pruebas de tipo sí/no)."""
    condicion = bool(condicion)
    return {"caso": caso, "magnitud": magnitud, "referencia": "True",
            "calculado": str(condicion), "tolerancia": "-", "pasa": condicion}


def ejecutar_validacion():
    """Corre todas las pruebas y regresa una lista de filas (diccionarios)."""
    filas = []

    # ---- Caso A: coeficiente de difusión [m²/s], tolerancia 0.5 % (las referencias tienen 3 cifras) ----
    referencias_D = {900: 5.92e-12, 927: 8.33e-12, 1000: 1.95e-11}
    for T_C, D_ref in referencias_D.items():
        filas.append(_comparar("A", f"D a {T_C} °C [m²/s]", D_ref, calcular_difusividad(T_C), 0.005, relativa=True))

    # ---- Caso B: perfil a 927 °C, 10 h [wt %], tolerancia ±0.001 (las referencias tienen 3 decimales) ----
    referencias_perfil = {0.00: 1.000, 0.25: 0.797, 0.50: 0.615, 0.75: 0.466, 1.00: 0.357, 1.50: 0.242, 2.00: 0.208}
    for x_mm, C_ref in referencias_perfil.items():
        C = calcular_perfil(x_mm, 10, C0, CS, 927)
        filas.append(_comparar("B", f"C en x = {x_mm:.2f} [mm] [wt %]", C_ref, C, 0.001))
    x_B = calcular_profundidad(10, C0, CS, 0.40, 927)
    filas.append(_comparar("B", "x para Cobj = 0.40 [mm]", 0.89, x_B, 0.01))

    # ---- Caso C: diseño inverso, Cobj = 0.60 wt %, x = 0.75 mm [h], tolerancia ±0.1 h ----
    referencias_tiempo = {900: 29.0, 925: 21.1, 950: 15.6, 975: 11.7, 1000: 8.8}
    for T_C, t_ref in referencias_tiempo.items():
        t = calcular_tiempo(0.75, C0, CS, 0.60, T_C)
        filas.append(_comparar("C", f"t a {T_C} °C [h]", t_ref, t, 0.1))

    # ---- Caso D: efecto de Cobj a 927 °C, 10 h [mm], tolerancia ±0.01 mm ----
    referencias_Cobj = {0.30: 1.19, 0.40: 0.89, 0.50: 0.69, 0.60: 0.52, 0.80: 0.25}
    for Cobj, x_ref in referencias_Cobj.items():
        x = calcular_profundidad(10, C0, CS, Cobj, 927)
        filas.append(_comparar("D", f"x para Cobj = {Cobj:.2f} [mm]", x_ref, x, 0.01))

    # ---- Caso E: problema de libro (Callister 5.13), carbono en Fe-γ ----
    # Datos que capturó el equipo (confirmar con el enunciado del libro):
    #   C0 = 0.10, Cs = 0.90, Cobj = 0.30 [wt %], x = 4 [mm], T = 1100 [°C]. Respuesta del libro: t = 1.13e5 [s].
    # El libro redondea a 3 cifras y usa R = 8.31, mientras que el modelo usa R = 8.3145 (valor aceptado de R).
    # Con R = 8.3145 la diferencia es de -0.8 %, por eso la tolerancia es de 1 %.
    t_libro_h = 1.13e5 / 3600.0   # [h]
    t_E = calcular_tiempo(4.0, 0.10, 0.90, 0.30, 1100)
    filas.append(_comparar("E", "t para 4 mm a 1100 °C [h] (libro)", t_libro_h, t_E, 0.01, relativa=True))

    # Mismo problema, pero con la R del libro (8.31). Se calcula aquí a mano para mostrar de dónde sale la
    # diferencia: con R = 8.31 el modelo y el libro coinciden dentro de 0.5 %.
    R_LIBRO = 8.31   # [J/(mol·K)]
    D_libro = D0 * np.exp(-Q / (R_LIBRO * (1100.0 + CERO_CELSIUS_K)))                       # [m²/s]
    t_E_R831 = (4e-3 / (2.0 * calcular_z(0.10, 0.90, 0.30))) ** 2 / D_libro / 3600.0         # [h]
    filas.append(_comparar("E", "mismo caso con R = 8.31 del libro [h]", t_libro_h, t_E_R831, 0.005, relativa=True))

    # ---- Consistencia: que las funciones sean coherentes entre sí ----
    # 1) Ida y vuelta: tiempo -> profundidad
    t_ida = calcular_tiempo(0.80, C0, CS, 0.40, 950)
    filas.append(_comparar("Consist.", "x(t(x)) = 0.80 [mm]", 0.80, calcular_profundidad(t_ida, C0, CS, 0.40, 950), 1e-9))

    # 2) Ida y vuelta: tiempo -> temperatura
    T_vuelta = calcular_temperatura(0.80, t_ida, C0, CS, 0.40)
    filas.append(_comparar("Consist.", "T(t(T)) = 950 [°C]", 950.0, T_vuelta, 1e-6))

    # 3) En x = profundidad(Cobj), el perfil tiene que valer Cobj
    x_c = calcular_profundidad(10, C0, CS, 0.40, 927)
    filas.append(_comparar("Consist.", "C(x(Cobj)) = 0.40 [wt %]", 0.40, calcular_perfil(x_c, 10, C0, CS, 927), 1e-9))

    # 4) Condiciones de frontera: C(0,t) = Cs  y  C(muy lejos,t) = C0
    filas.append(_comparar("Consist.", "C(0, t) = Cs [wt %]", CS, calcular_perfil(0.0, 10, C0, CS, 927), 1e-12))
    filas.append(_comparar("Consist.", "C(50 mm, t) = C0 [wt %]", C0, calcular_perfil(50.0, 10, C0, CS, 927), 1e-9))

    # 5) Curva solución: D*t = K constante para todas las temperaturas (misma x y Cobj)
    temperaturas = np.array([900.0, 950.0, 1000.0, 1050.0])
    tiempos = calcular_tiempo(0.80, C0, CS, 0.40, temperaturas)          # [h]
    productos = calcular_difusividad(temperaturas) * tiempos * 3600.0    # D*t [m²]
    filas.append(_comparar("Consist.", "D*t constante (máx - mín) [m²]", 0.0, productos.max() - productos.min(), 1e-15))

    # 6) A mayor temperatura, mayor D y menor tiempo requerido
    d_sube = bool(np.all(np.diff(calcular_difusividad(temperaturas)) > 0))
    t_baja = bool(np.all(np.diff(tiempos) < 0))
    filas.append({
        "caso": "Consist.", "magnitud": "D sube y t baja con T", "referencia": "True",
        "calculado": str(d_sube and t_baja), "tolerancia": "-", "pasa": d_sube and t_baja,
    })

    # 7) Longitud característica: L = raíz(D*t). Cálculo manual con D = 8.33e-12 [m²/s] (Caso A) y t = 36000 [s]:
    #    raíz(8.33e-12 * 36000) = 5.48e-4 m = 0.548 mm
    filas.append(_comparar("Consist.", "L = raíz(Dt) a 927 °C, 10 h [mm]", 0.548, calcular_longitud_difusion(10, 927), 0.002))

    # 8) Comparación de tratamientos: la profundidad coincide con calcular_profundidad
    trats = [
        {"nombre": "A", "T_C": 900, "t_h": 12, "C0": C0, "Cs": CS},
        {"nombre": "B", "T_C": 950, "t_h": 6, "C0": C0, "Cs": CS},
        {"nombre": "C", "T_C": 1000, "t_h": 3, "C0": C0, "Cs": CS},
    ]
    resultado = comparar_tratamientos(trats, 0.40)
    for t_dato, fila in zip(trats, resultado):
        esperado = calcular_profundidad(t_dato["t_h"], C0, CS, 0.40, t_dato["T_C"])
        filas.append(_comparar("Consist.", f"comparar_tratamientos '{fila['nombre']}' [mm]", esperado, fila["profundidad_mm"], 1e-12))

    # 9) Tiempo para igualar la profundidad del primer tratamiento (t_igualar_h)
    #    - el primero se iguala a sí mismo con su propio tiempo
    #    - para los demás, con ese tiempo y SU temperatura se obtiene la profundidad del primero
    x_ref = resultado[0]["profundidad_mm"]
    filas.append(_comparar("Consist.", "t_igualar_h del primero = su t [h]", float(trats[0]["t_h"]), resultado[0]["t_igualar_h"], 1e-9))
    for t_dato, fila in zip(trats[1:], resultado[1:]):
        x_check = calcular_profundidad(fila["t_igualar_h"], C0, CS, 0.40, t_dato["T_C"])
        filas.append(_comparar("Consist.", f"x con t_igualar_h de '{fila['nombre']}' [mm]", x_ref, x_check, 1e-9))

    # 10) Lo mismo con un tratamiento que tiene Cs distinto (el tiempo se calcula con SUS concentraciones)
    trats_Cs = [
        {"nombre": "A", "T_C": 925, "t_h": 8, "C0": C0, "Cs": CS},
        {"nombre": "B", "T_C": 975, "t_h": 4, "C0": C0, "Cs": 1.20},
    ]
    res_Cs = comparar_tratamientos(trats_Cs, 0.40)
    x_check = calcular_profundidad(res_Cs[1]["t_igualar_h"], C0, 1.20, 0.40, 975)
    filas.append(_comparar("Consist.", "t_igualar_h con Cs distinto: x [mm]", res_Cs[0]["profundidad_mm"], x_check, 1e-9))

    # 11) Un tratamiento inválido no tumba la comparación: sale nan y un aviso
    trats_mal = [
        {"nombre": "A", "T_C": 925, "t_h": 8, "C0": C0, "Cs": CS},
        {"nombre": "B", "T_C": 975, "t_h": 4, "C0": 0.90, "Cs": 0.50},   # Cs <= C0: no tiene sentido
    ]
    res_mal = comparar_tratamientos(trats_mal, 0.40)
    filas.append({
        "caso": "Consist.", "magnitud": "tratamiento inválido: nan y aviso", "referencia": "True",
        "calculado": str(bool(np.isnan(res_mal[1]["profundidad_mm"]) and res_mal[1]["aviso"] != "" and res_mal[0]["aviso"] == "")),
        "tolerancia": "-",
        "pasa": bool(np.isnan(res_mal[1]["profundidad_mm"]) and res_mal[1]["aviso"] != "" and res_mal[0]["aviso"] == ""),
    })

    # ---- Diseño inverso (Módulo 2): calcular_diseno_inverso ----
    # 1) El Caso C otra vez, pero ahora a través de la función completa del diseño inverso
    di = calcular_diseno_inverso(0.75, 0.0, C0, CS, 0.60, 900.0, 1000.0, paso_C=25.0)
    for T_C, t_ref in zip(di["tabla"]["T_C"], di["tabla"]["t_h"]):
        filas.append(_comparar("Diseño inv.", f"Caso C vía tabla: t a {T_C:.0f} °C [h]",
                               referencias_tiempo[int(round(T_C))], t_ref, 0.1))

    # 2) La tabla tiene las filas esperadas: 900, 925, ..., 1050 son 7 filas
    di = calcular_diseno_inverso(0.80, 0.05, C0, CS, 0.40, 900.0, 1050.0, paso_C=25.0)
    filas.append(_comparar("Diseño inv.", "filas de la tabla (900–1050, paso 25)", 7, len(di["tabla"]["T_C"]), 0))

    # 3) Cada fila cumple D*t = K (la curva solución)
    productos = di["tabla"]["D_m2s"] * di["tabla"]["t_h"] * 3600.0
    filas.append(_comparar("Diseño inv.", "D*t = K en todas las filas (error relativo máx)", 0.0,
                           float(np.max(np.abs(productos - di["K_m2"]) / di["K_m2"])), 1e-12))

    # 4) La banda de tolerancia: x - tol < x < x + tol  =>  t_min < t < t_max
    filas.append({
        "caso": "Diseño inv.", "magnitud": "t_min < t < t_max en toda la tabla", "referencia": "True",
        "calculado": str(bool(np.all(di["tabla"]["t_min_h"] < di["tabla"]["t_h"]) and np.all(di["tabla"]["t_h"] < di["tabla"]["t_max_h"]))),
        "tolerancia": "-",
        "pasa": bool(np.all(di["tabla"]["t_min_h"] < di["tabla"]["t_h"]) and np.all(di["tabla"]["t_h"] < di["tabla"]["t_max_h"])),
    })

    # 5) Ida y vuelta de la banda: con t_max a 950 °C se alcanza x + tol, con t_min se alcanza x - tol
    i950 = int(np.argmin(np.abs(di["tabla"]["T_C"] - 950.0)))
    x_arriba = calcular_profundidad(di["tabla"]["t_max_h"][i950], C0, CS, 0.40, 950.0)
    x_abajo = calcular_profundidad(di["tabla"]["t_min_h"][i950], C0, CS, 0.40, 950.0)
    filas.append(_comparar("Diseño inv.", "x(t_max) = 0.85 [mm]", 0.85, x_arriba, 1e-9))
    filas.append(_comparar("Diseño inv.", "x(t_min) = 0.75 [mm]", 0.75, x_abajo, 1e-9))

    # 6) Con tolerancia 0 la ventana se cierra en una sola curva
    di0 = calcular_diseno_inverso(0.80, 0.0, C0, CS, 0.40, 900.0, 1050.0)
    filas.append(_comparar("Diseño inv.", "tol = 0: t_max - t_min [h]", 0.0,
                           float(np.max(di0["tabla"]["t_max_h"] - di0["tabla"]["t_min_h"])), 1e-12))

    # 7) Mapa de calor: forma correcta y cada celda coincide con calcular_profundidad
    mapa = di["mapa"]
    filas.append({
        "caso": "Diseño inv.", "magnitud": "forma de la matriz del mapa (T x t)", "referencia": "(80, 80)",
        "calculado": str(mapa["x_mm"].shape), "tolerancia": "-", "pasa": mapa["x_mm"].shape == (80, 80),
    })
    i, j = 10, 20
    esperado = calcular_profundidad(mapa["t_h"][j], C0, CS, 0.40, mapa["T_C"][i])
    filas.append(_comparar("Diseño inv.", "celda del mapa [10, 20] [mm]", float(esperado), float(mapa["x_mm"][i, j]), 1e-12))

    # 8) El mapa cubre toda la banda: la profundidad crece con el tiempo y con la temperatura
    crece_t = bool(np.all(np.diff(mapa["x_mm"], axis=1) > 0))
    crece_T = bool(np.all(np.diff(mapa["x_mm"], axis=0) > 0))
    filas.append({
        "caso": "Diseño inv.", "magnitud": "x crece con t y con T en el mapa", "referencia": "True",
        "calculado": str(crece_t and crece_T), "tolerancia": "-", "pasa": crece_t and crece_T,
    })

    # ---- Chequeo de fases (aproximado): líneas Acm y A3 del diagrama de clase ----
    # Los puntos de referencia son los rotulados en el diagrama de clase y el ejercicio resuelto de las diapositivas.
    filas.append(_comparar("Fases", "Acm a 723 °C [wt %] (eutectoide)", 0.80, float(calcular_solubilidad_acm(723.0)), 1e-9))
    filas.append(_comparar("Fases", "Acm a 1147 °C [wt %] (máx. solubilidad)", 2.11, float(calcular_solubilidad_acm(1147.0)), 1e-9))
    filas.append(_comparar("Fases", "A3 a 0.42 wt % [°C] (ejercicio de clase)", 780.0, calcular_temperatura_austenita_minima(0.42), 1e-9))
    filas.append(_comparar("Fases", "A3 a 0.80 wt % [°C] (eutectoide)", 723.0, calcular_temperatura_austenita_minima(0.80), 1e-9))
    # Ida y vuelta: para C entre 0.8 y 2.11 wt %, Acm(T_min(C)) debe devolver C
    filas.append(_comparar("Fases", "Acm(T_min(1.35 wt %)) = 1.35 [wt %]", 1.35,
                           float(calcular_solubilidad_acm(calcular_temperatura_austenita_minima(1.35))), 1e-9))
    T_acm = np.array([800.0, 900.0, 1000.0, 1100.0])
    filas.append(_debe_ser_cierto("Fases", "Acm sube con la temperatura", np.all(np.diff(calcular_solubilidad_acm(T_acm)) > 0)))
    C_a3 = np.array([0.0, 0.2, 0.42, 0.6, 0.8])
    filas.append(_debe_ser_cierto("Fases", "A3 baja al subir C (0 a 0.8 wt %)",
                                  np.all(np.diff([calcular_temperatura_austenita_minima(c) for c in C_a3]) < 0)))
    filas.append(_debe_ser_cierto("Fases", "valores de demostración (0.20/1.00) sin avisos de 900 a 1050 °C",
                                  all(verificar_austenita(T, C0, CS) == [] for T in (900, 925, 950, 975, 1000, 1025, 1050))))
    filas.append(_debe_ser_cierto("Fases", "Cs = 1.50 a 900 °C avisa (supera Acm)", len(verificar_austenita(900, C0, 1.50)) == 1))
    filas.append(_debe_ser_cierto("Fases", "Cs = 1.30 a 900 °C avisa (cerca de Acm)", len(verificar_austenita(900, C0, 1.30)) == 1))
    filas.append(_debe_ser_cierto("Fases", "Cs = 1.50 a 1050 °C no avisa", verificar_austenita(1050, C0, 1.50) == []))
    filas.append(_debe_ser_cierto("Fases", "C0 = 0.02 a 850 °C avisa (debajo de A3)", len(verificar_austenita(850, 0.02, CS)) == 1))
    filas.append(_debe_ser_cierto("Fases", "T fuera del diagrama (600 °C) avisa una sola vez", len(verificar_austenita(600, C0, CS)) == 1))

    # ---- Microestructura en enfriamiento lento (regla de la palanca, valores del diagrama de clase) ----
    # Cálculos a mano: perlita(0.30) = (0.30-0.02)/(0.8-0.02) = 0.3590; cementita(1.00) = (1.00-0.8)/(6.67-0.8) = 0.0341;
    # cementita(2.11) = (2.11-0.8)/(6.67-0.8) = 0.2232
    filas.append(_comparar("Microestr.", "perlita con 0.30 wt % (ejercicio de clase)", 0.3590, calcular_microconstituyentes(0.30)["perlita"], 1e-4))
    filas.append(_comparar("Microestr.", "perlita con 0.80 wt % (eutectoide)", 1.0, calcular_microconstituyentes(0.80)["perlita"], 1e-12))
    filas.append(_comparar("Microestr.", "ferrita con 0.02 wt %", 1.0, calcular_microconstituyentes(0.02)["ferrita"], 1e-12))
    filas.append(_comparar("Microestr.", "cementita proeut. con 1.00 wt %", 0.0341, calcular_microconstituyentes(1.00)["cementita"], 1e-4))
    filas.append(_comparar("Microestr.", "cementita proeut. con 2.11 wt %", 0.2232, calcular_microconstituyentes(2.11)["cementita"], 1e-4))
    C_prueba = np.linspace(0.0, 2.11, 300)
    fr = calcular_microconstituyentes(C_prueba)
    suma = fr["ferrita"] + fr["perlita"] + fr["cementita"]
    filas.append(_comparar("Microestr.", "ferrita + perlita + cementita = 1", 0.0, float(np.max(np.abs(suma - 1.0))), 1e-12))
    izq = calcular_microconstituyentes(0.8 - 1e-9)["perlita"]
    der = calcular_microconstituyentes(0.8 + 1e-9)["perlita"]
    filas.append(_comparar("Microestr.", "perlita continua en 0.8 wt %", 0.0, abs(izq - der), 1e-6))

    # ---- Flujo de carbono y carbono absorbido (927 °C, 10 h, valores de demostración) ----
    # 1) J = -D dC/dx: se compara con la derivada numérica del perfil (diferencias centradas)
    D927 = float(calcular_difusividad(927))                       # [m²/s]
    h = 1e-4                                                      # [mm] paso de la derivada
    for x_mm in (0.0, 0.5):
        if x_mm == 0.0:   # en la superficie se usa diferencia hacia adelante de 2o orden
            c0_, c1_, c2_ = calcular_perfil(np.array([0.0, h, 2 * h]), 10, C0, CS, 927)
            dCdx = (-3 * c0_ + 4 * c1_ - c2_) / (2 * h * 1e-3)    # [wt %/m]
        else:
            ca, cb = calcular_perfil(np.array([x_mm - h, x_mm + h]), 10, C0, CS, 927)
            dCdx = (cb - ca) / (2 * h * 1e-3)                     # [wt %/m]
        J_num = -D927 * dCdx / 100.0 * DENSIDAD_ACERO             # [kg/(m²·s)]
        filas.append(_comparar("Flujo", f"J en x = {x_mm} mm vs -D·dC/dx [kg/(m²·s)]", J_num,
                               float(calcular_flujo(x_mm, 10, C0, CS, 927)), 1e-4, relativa=True))
    # 2) El flujo en la superficie baja como 1/raíz(t): con 4 veces el tiempo, la mitad
    filas.append(_comparar("Flujo", "J(0, 40 h) / J(0, 10 h) = 1/2", 0.5,
                           float(calcular_flujo(0, 40, C0, CS, 927) / calcular_flujo(0, 10, C0, CS, 927)), 1e-12))
    # 3) Carbono absorbido = área entre el perfil y C0 (integral numérica)
    x_int = np.linspace(0.0, 20.0, 20001)                         # [mm]
    area = np.trapezoid(calcular_perfil(x_int, 10, C0, CS, 927) - C0, x_int * 1e-3) if hasattr(np, "trapezoid") \
        else np.trapz(calcular_perfil(x_int, 10, C0, CS, 927) - C0, x_int * 1e-3)
    M_num = area / 100.0 * DENSIDAD_ACERO                         # [kg/m²]
    filas.append(_comparar("Flujo", "M = área bajo el perfil [kg/m²]", M_num,
                           float(calcular_carbono_absorbido(10, C0, CS, 927)), 1e-6, relativa=True))
    # 4) Cálculo a mano con D = 8.33e-12 m²/s (Caso A):
    #    M = 2 * (0.80/100 * 7870) * raíz(8.33e-12 * 36000 / pi) = 0.03890 kg/m² = 38.90 g/m²
    filas.append(_comparar("Flujo", "M a 927 °C, 10 h [g/m²] (a mano)", 38.90,
                           float(calcular_carbono_absorbido(10, C0, CS, 927)) * 1000.0, 0.1))
    filas.append(_comparar("Flujo", "M(40 h) / M(10 h) = 2 (crece con raíz(t))", 2.0,
                           float(calcular_carbono_absorbido(40, C0, CS, 927) / calcular_carbono_absorbido(10, C0, CS, 927)), 1e-12))

    # ---- Errores: el modelo tiene que avisar cuando los datos no tienen sentido ----
    filas.append(_debe_dar_error("Errores", "Cobj >= Cs", calcular_profundidad, 10, C0, CS, 1.20, 927))
    filas.append(_debe_dar_error("Errores", "Cobj <= C0", calcular_profundidad, 10, C0, CS, 0.10, 927))
    filas.append(_debe_dar_error("Errores", "Cs <= C0", calcular_perfil, 1.0, 10, 0.80, 0.50, 927))
    filas.append(_debe_dar_error("Errores", "tiempo <= 0", calcular_perfil, 1.0, 0, C0, CS, 927))
    filas.append(_debe_dar_error("Errores", "T bajo cero absoluto", calcular_difusividad, -300))
    filas.append(_debe_dar_error("Errores", "T imposible (D_req >= D0)", calcular_temperatura, 100.0, 0.001, C0, CS, 0.40))
    filas.append(_debe_dar_error("Errores", "más de 3 tratamientos", comparar_tratamientos, trats + trats[:1], 0.40))
    filas.append(_debe_dar_error("Errores", "diseño inverso: tolerancia >= profundidad", calcular_diseno_inverso, 0.05, 0.05, C0, CS, 0.40, 900.0, 1050.0))
    filas.append(_debe_dar_error("Errores", "diseño inverso: tolerancia negativa", calcular_diseno_inverso, 0.80, -0.01, C0, CS, 0.40, 900.0, 1050.0))
    filas.append(_debe_dar_error("Errores", "diseño inverso: T mínima >= T máxima", calcular_diseno_inverso, 0.80, 0.05, C0, CS, 0.40, 1050.0, 900.0))
    filas.append(_debe_dar_error("Errores", "diseño inverso: paso <= 0", calcular_diseno_inverso, 0.80, 0.05, C0, CS, 0.40, 900.0, 1050.0, 0.0))
    filas.append(_debe_dar_error("Errores", "diseño inverso: Cobj >= Cs", calcular_diseno_inverso, 0.80, 0.05, C0, CS, 1.20, 900.0, 1050.0))
    filas.append(_debe_dar_error("Errores", "microestructura: C > 6.67 wt %", calcular_microconstituyentes, 7.0))
    filas.append(_debe_dar_error("Errores", "flujo: tiempo <= 0", calcular_flujo, 0.0, 0.0, C0, CS, 927))

    return filas


def _formato(valor):
    """Texto para mostrar un valor en la tabla."""
    return f"{valor:.4g}" if isinstance(valor, float) else str(valor)


def main():
    filas = ejecutar_validacion()

    print(f"{'Caso':<13}{'Magnitud':<40}{'Referencia':>12}{'Calculado':>12}{'Tolerancia':>12}  Resultado")
    print("-" * 101)
    for f in filas:
        resultado = "PASA" if f["pasa"] else "FALLA"
        print(f"{f['caso']:<13}{f['magnitud']:<40}{_formato(f['referencia']):>12}"
              f"{_formato(f['calculado']):>12}{f['tolerancia']:>12}  {resultado}")

    total = len(filas)
    pasaron = sum(f["pasa"] for f in filas)
    print("-" * 101)
    print(f"{pasaron} de {total} pruebas pasaron.")
    sys.exit(0 if pasaron == total else 1)


if __name__ == "__main__":
    main()

# Simulador Difusión Carbono. Modelo matemático (difusión de carbono en austenita).
# UNAM, Facultad de Ingeniería. Ingeniería de Materiales.
#
# Este archivo SOLO calcula, no tiene nada de interfaz. Así lo podemos probar
# con validacion.py antes de conectarlo con Streamlit.
#
# Modelo: segunda ley de Fick, sólido semiinfinito, Cs constante en la superficie:
#     C(x,t) = C0 + (Cs - C0) * erfc( x / (2 * raíz(D*t)) )
# y el coeficiente de difusión sale de Arrhenius:
#     D = D0 * exp( -Q / (R*T) )
#
# Unidades al llamar las funciones (las de ingeniería, no las del SI):
#     temperatura T_C [°C], tiempo t_h [h], profundidad x_mm [mm],
#     concentraciones C0, Cs, Cobj [wt %]
# Las conversiones a SI (K, s, m) se hacen aquí adentro, en un solo lugar.
#
# Las funciones aceptan números sueltos o arreglos de NumPy (sirve para las
# gráficas y el mapa de calor). Las concentraciones C0, Cs y Cobj son números sueltos.

import numpy as np
from scipy.special import erfc, erfcinv

# ---------- Parámetros y de dónde sale cada uno ----------
D0 = 2.3e-5       # [m²/s]      factor preexponencial, C en Fe-γ. Tabla de las diapositivas de clase.
Q = 148000.0      # [J/mol]     energía de activación, C en Fe-γ. Tabla de las diapositivas de clase.
R = 8.3145        # [J/(mol·K)] constante de los gases. Usamos 8.3145 y no 8.31 porque con este
                  #             valor sí se reproducen los datos de referencia (ver validacion.py).

# ---------- Conversiones de unidades ----------
CERO_CELSIUS_K = 273.15    # [K]   0 °C en kelvin
SEGUNDOS_POR_HORA = 3600.0 # [s/h]
METROS_POR_MM = 1e-3       # [m/mm]

# ---------- Líneas del diagrama Fe-Fe₃C de clase (valores APROXIMADOS) ----------
# Solo sirven para AVISAR si el modelo de una sola fase (austenita) podría no valer.
# No cambian ningún cálculo de difusión.
#
# Acm: recta entre los dos puntos rotulados en el diagrama de clase (la línea real es algo curva).
PUNTOS_ACM = ((723.0, 0.80), (1147.0, 2.11))    # (T [°C], C [wt %])
# A3: puntos (C [wt %], T [°C]) unidos con rectas:
#   (0.00, 912): transformación α→γ del hierro puro. Valor conocido; NO está rotulado en el diagrama de clase.
#   (0.42, 780): del ejercicio resuelto de las diapositivas (acero de 0.30 wt % a 780 °C: austenita de 0.42 wt %).
#   (0.80, 723): eutectoide, rotulado en el diagrama de clase.
PUNTOS_A3 = ((0.00, 912.0), (0.42, 780.0), (0.80, 723.0))
MARGEN_ACM = 0.15   # [wt %] margen de prudencia al comparar Cs con Acm (decisión de diseño, no medido),
                    # porque la recta puede sobreestimar la solubilidad en la parte media.


# ---------- Funciones auxiliares (revisan que los datos tengan sentido) ----------
def _validar_concentraciones(C0, Cs, Cobj=None):
    """Revisa C0 < Cobj < Cs [wt %]. Si algo no tiene sentido físico, avisa con ValueError."""
    if C0 < 0:
        raise ValueError("C0 no puede ser negativa [wt %].")
    if Cs <= C0:
        raise ValueError("Para cementar se necesita Cs > C0: la superficie debe tener más carbono que el núcleo.")
    if Cobj is not None and not (C0 < Cobj < Cs):
        raise ValueError("La concentración objetivo debe cumplir C0 < Cobj < Cs.")


def _validar_positivo(valor, nombre):
    """Revisa que un dato (o todos los datos de un arreglo) sea mayor que cero."""
    if np.any(np.asarray(valor, dtype=float) <= 0):
        raise ValueError(f"{nombre} debe ser mayor que cero.")


# ---------- Funciones principales ----------
def calcular_difusividad(T_C):
    """Coeficiente de difusión del carbono en Fe-γ.
    Entrada: T_C [°C]. Salida: D [m²/s]. (Arrhenius: D = D0 * exp(-Q/(R*T)) con T en kelvin)"""
    T_K = np.asarray(T_C, dtype=float) + CERO_CELSIUS_K
    if np.any(T_K <= 0):
        raise ValueError("La temperatura debe estar por encima del cero absoluto.")
    return D0 * np.exp(-Q / (R * T_K))


def calcular_z(C0, Cs, Cobj):
    """z = erfc⁻¹[(Cobj - C0)/(Cs - C0)]. Es un número sin unidades que usan la
    profundidad y el tiempo. Solo existe si C0 < Cobj < Cs."""
    _validar_concentraciones(C0, Cs, Cobj)
    return erfcinv((Cobj - C0) / (Cs - C0))


def calcular_perfil(x_mm, t_h, C0, Cs, T_C):
    """Perfil de concentración de carbono C(x,t).
    Entradas: x_mm [mm], t_h [h], C0 y Cs [wt %], T_C [°C]. Salida: C [wt %]."""
    _validar_concentraciones(C0, Cs)
    _validar_positivo(t_h, "El tiempo")
    x_mm = np.asarray(x_mm, dtype=float)
    if np.any(x_mm < 0):
        raise ValueError("La profundidad no puede ser negativa.")

    x_m = x_mm * METROS_POR_MM            # [m]
    t_s = t_h * SEGUNDOS_POR_HORA         # [s]
    D = calcular_difusividad(T_C)         # [m²/s]
    return C0 + (Cs - C0) * erfc(x_m / (2.0 * np.sqrt(D * t_s)))


def calcular_profundidad(t_h, C0, Cs, Cobj, T_C):
    """Profundidad a la que se alcanza Cobj:  x = 2 * z * raíz(D*t).
    Entradas: t_h [h], C0, Cs, Cobj [wt %], T_C [°C]. Salida: x [mm]."""
    _validar_positivo(t_h, "El tiempo")
    z = calcular_z(C0, Cs, Cobj)
    D = calcular_difusividad(T_C)                       # [m²/s]
    t_s = t_h * SEGUNDOS_POR_HORA                       # [s]
    x_m = 2.0 * z * np.sqrt(D * t_s)                    # [m]
    return x_m / METROS_POR_MM


def calcular_tiempo(x_mm, C0, Cs, Cobj, T_C):
    """Tiempo necesario para tener Cobj a la profundidad x (diseño inverso):
    t = [x/(2z)]² / D.
    Entradas: x_mm [mm], C0, Cs, Cobj [wt %], T_C [°C]. Salida: t [h]."""
    _validar_positivo(x_mm, "La profundidad objetivo")
    z = calcular_z(C0, Cs, Cobj)
    x_m = np.asarray(x_mm, dtype=float) * METROS_POR_MM  # [m]
    K = (x_m / (2.0 * z)) ** 2                           # [m²]  (es la constante D*t de la curva solución)
    D = calcular_difusividad(T_C)                        # [m²/s]
    return (K / D) / SEGUNDOS_POR_HORA


def calcular_temperatura(x_mm, t_h, C0, Cs, Cobj):
    """Temperatura necesaria si fijamos el tiempo (Fick despejado + Arrhenius despejado):
    D_req = [x/(2z)]² / t   y   T = -Q / (R * ln(D_req/D0)).
    Entradas: x_mm [mm], t_h [h], C0, Cs, Cobj [wt %]. Salida: T [°C]."""
    _validar_positivo(x_mm, "La profundidad objetivo")
    _validar_positivo(t_h, "El tiempo")
    z = calcular_z(C0, Cs, Cobj)
    x_m = np.asarray(x_mm, dtype=float) * METROS_POR_MM
    t_s = np.asarray(t_h, dtype=float) * SEGUNDOS_POR_HORA
    D_req = (x_m / (2.0 * z)) ** 2 / t_s                 # [m²/s]
    # Arrhenius solo llega a D0 cuando T -> infinito, así que D_req tiene que ser menor que D0.
    if np.any(D_req >= D0):
        raise ValueError("Con ese tiempo no hay temperatura posible (D requerida >= D0).")
    T_K = -Q / (R * np.log(D_req / D0))
    return T_K - CERO_CELSIUS_K


def calcular_longitud_difusion(t_h, T_C):
    """Longitud característica de difusión L = raíz(D*t).
    Entradas: t_h [h], T_C [°C]. Salida: L [mm].
    (Ojo: en la fórmula de Fick aparece 2*L, no L.)"""
    _validar_positivo(t_h, "El tiempo")
    D = calcular_difusividad(T_C)
    L_m = np.sqrt(D * np.asarray(t_h, dtype=float) * SEGUNDOS_POR_HORA)
    return L_m / METROS_POR_MM


# ---------- Chequeo de fases (aproximado) ----------
def calcular_solubilidad_acm(T_C):
    """Solubilidad máxima del carbono en austenita (línea Acm, aproximada).
    Entrada: T_C [°C] (el diagrama cubre de 723 a 1147 °C). Salida: C [wt %]."""
    T_puntos = [p[0] for p in PUNTOS_ACM]
    C_puntos = [p[1] for p in PUNTOS_ACM]
    return np.interp(np.asarray(T_C, dtype=float), T_puntos, C_puntos)


def calcular_temperatura_austenita_minima(C):
    """Temperatura por encima de la cual una aleación con C [wt %] es toda austenita (aproximada).
    Hasta 0.8 wt % es la línea A3; de 0.8 a 2.11 wt % es la línea Acm. Salida: T [°C]."""
    C = float(C)
    if C <= PUNTOS_A3[-1][0]:
        C_puntos = [p[0] for p in PUNTOS_A3]
        T_puntos = [p[1] for p in PUNTOS_A3]
        return float(np.interp(C, C_puntos, T_puntos))
    T_puntos = [p[0] for p in PUNTOS_ACM]
    C_puntos = [p[1] for p in PUNTOS_ACM]
    return float(np.interp(C, C_puntos, T_puntos))


def verificar_austenita(T_C, C0, Cs):
    """Revisa, de forma aproximada, que el modelo de una sola fase (austenita) tenga sentido.
    Entradas: T_C [°C], C0 y Cs [wt %]. Regresa una lista de textos de aviso (vacía si todo está bien).
    Es solo una advertencia: no frena ningún cálculo."""
    avisos = []
    T_C = float(T_C)
    T_bajo, T_alto = PUNTOS_ACM[0][0], PUNTOS_ACM[-1][0]
    if T_C < T_bajo or T_C > T_alto:
        avisos.append(f"{T_C:g} °C queda fuera del rango del diagrama usado para el chequeo de fases "
                      f"({T_bajo:g}–{T_alto:g} °C).")
        return avisos

    T_minima = calcular_temperatura_austenita_minima(C0)
    if T_C < T_minima:
        avisos.append(f"A {T_C:g} °C la aleación con C₀ = {C0:.2f} [wt %] podría no ser toda austenita "
                      f"(A3 ≈ {T_minima:.0f} °C, aproximada). El modelo de una sola fase perdería validez.")

    solubilidad = float(calcular_solubilidad_acm(T_C))
    if Cs > solubilidad:
        avisos.append(f"Cs = {Cs:.2f} [wt %] supera la solubilidad del carbono en austenita a {T_C:g} °C "
                      f"(≈ {solubilidad:.2f} [wt %], línea Acm aproximada). Pueden formarse carburos en la superficie "
                      "y el modelo de una sola fase dejaría de representar el sistema.")
    elif Cs > solubilidad - MARGEN_ACM:
        avisos.append(f"Cs = {Cs:.2f} [wt %] está cerca del límite de solubilidad a {T_C:g} °C "
                      f"(≈ {solubilidad:.2f} [wt %], línea Acm aproximada). Como la línea es aproximada, "
                      "revísalo en el diagrama.")
    return avisos


def comparar_tratamientos(tratamientos, Cobj):
    """Compara de 1 a 3 tratamientos con la misma concentración objetivo.
    'tratamientos' es una lista de diccionarios, cada uno con las llaves:
        "T_C" [°C], "t_h" [h], "C0" [wt %], "Cs" [wt %]  y, opcional, "nombre".
    Regresa una lista de diccionarios con: nombre, T_C, t_h, C0, Cs,
        D_m2s [m²/s], L_mm [mm], profundidad_mm [mm], t_igualar_h [h] y aviso (texto; vacío si todo bien).
    t_igualar_h es el tiempo que ese tratamiento necesitaría, a SU temperatura, para llegar a la misma
    profundidad que el primer tratamiento de la lista (para el primero es su propio tiempo).
    Si un tratamiento no cumple C0 < Cobj < Cs, su profundidad sale como nan y se explica en 'aviso'."""
    if not 1 <= len(tratamientos) <= 3:
        raise ValueError("Se pueden comparar de 1 a 3 tratamientos.")

    resultados = []
    for i, trat in enumerate(tratamientos, start=1):
        fila = {
            "nombre": trat.get("nombre", f"Tratamiento {i}"),
            "T_C": trat["T_C"],
            "t_h": trat["t_h"],
            "C0": trat["C0"],
            "Cs": trat["Cs"],
            "D_m2s": float(calcular_difusividad(trat["T_C"])),
            "L_mm": float(calcular_longitud_difusion(trat["t_h"], trat["T_C"])),
            "aviso": "",
        }
        try:
            fila["profundidad_mm"] = float(
                calcular_profundidad(trat["t_h"], trat["C0"], trat["Cs"], Cobj, trat["T_C"])
            )
        except ValueError as error:
            fila["profundidad_mm"] = float("nan")
            fila["aviso"] = str(error)
        resultados.append(fila)

    # Tiempo que necesitaría cada tratamiento, a su temperatura, para igualar la profundidad del primero.
    # Sirve para responder: ¿se logra la misma profundidad con más temperatura y menos tiempo?
    x_referencia = resultados[0]["profundidad_mm"]
    for fila, trat in zip(resultados, tratamientos):
        fila["t_igualar_h"] = float("nan")
        if np.isnan(x_referencia):
            continue
        try:
            fila["t_igualar_h"] = float(calcular_tiempo(x_referencia, trat["C0"], trat["Cs"], Cobj, trat["T_C"]))
        except ValueError:
            pass   # este tratamiento no cumple C0 < Cobj < Cs; ya trae su aviso
    return resultados


def calcular_diseno_inverso(x_mm, tol_mm, C0, Cs, Cobj, T_min_C, T_max_C,
                            paso_C=25.0, n_curva=200, n_mapa=80):
    """Diseño inverso: para cada temperatura, el tiempo que hace falta para tener Cobj
    a la profundidad x (todo sale de t = [x/(2z)]² / D, no se inventa ningún punto).

    Entradas: x_mm [mm] profundidad objetivo, tol_mm [mm] tolerancia (0 = solo la curva exacta),
              C0, Cs, Cobj [wt %], T_min_C y T_max_C [°C], paso_C [°C] entre filas de la tabla.
    Regresa un diccionario con:
      "tabla": T_C [°C], D_m2s [m²/s], t_h [h] (tiempo para x exacta),
               t_min_h y t_max_h [h] (tiempos para x - tol y x + tol: ventana de tiempo viable)
      "curva": igual que la tabla pero con n_curva puntos (para dibujar la curva solución)
      "mapa":  T_C [°C], t_h [h] y x_mm [mm] (matriz con la profundidad alcanzada para cada T y t)
      "K_m2":  constante D*t [m²] de la curva solución   "z": número sin unidades
    """
    _validar_positivo(x_mm, "La profundidad objetivo")
    if tol_mm < 0:
        raise ValueError("La tolerancia no puede ser negativa.")
    if tol_mm >= x_mm:
        raise ValueError("La tolerancia debe ser menor que la profundidad objetivo.")
    if T_min_C >= T_max_C:
        raise ValueError("La temperatura mínima debe ser menor que la máxima.")
    if paso_C <= 0:
        raise ValueError("El paso de temperatura debe ser mayor que cero.")
    z = calcular_z(C0, Cs, Cobj)   # también revisa que C0 < Cobj < Cs

    def tiempos(T_C):
        """Tiempos [h] para x - tol, x y x + tol a la(s) temperatura(s) T_C."""
        t_lo = calcular_tiempo(x_mm - tol_mm, C0, Cs, Cobj, T_C)
        t_obj = calcular_tiempo(x_mm, C0, Cs, Cobj, T_C)
        t_hi = calcular_tiempo(x_mm + tol_mm, C0, Cs, Cobj, T_C)
        return t_lo, t_obj, t_hi

    # Tabla (el +paso/2 es para que el último valor no se pierda por redondeo)
    T_tabla = np.arange(T_min_C, T_max_C + paso_C / 2.0, paso_C)
    t_lo, t_obj, t_hi = tiempos(T_tabla)
    tabla = {"T_C": T_tabla, "D_m2s": calcular_difusividad(T_tabla),
             "t_h": t_obj, "t_min_h": t_lo, "t_max_h": t_hi}

    # Curva solución (más puntos, para que se vea suave)
    T_curva = np.linspace(T_min_C, T_max_C, n_curva)
    c_lo, c_obj, c_hi = tiempos(T_curva)
    curva = {"T_C": T_curva, "t_h": c_obj, "t_min_h": c_lo, "t_max_h": c_hi}

    # Mapa: profundidad alcanzada para cada pareja (T, t). Las filas son T y las columnas son t.
    T_mapa = np.linspace(T_min_C, T_max_C, n_mapa)
    t_mapa = np.linspace(0.7 * c_lo.min(), 1.3 * c_hi.max(), n_mapa)
    x_mapa = calcular_profundidad(t_mapa[np.newaxis, :], C0, Cs, Cobj, T_mapa[:, np.newaxis])
    mapa = {"T_C": T_mapa, "t_h": t_mapa, "x_mm": x_mapa}

    K_m2 = (x_mm * METROS_POR_MM / (2.0 * z)) ** 2
    return {"tabla": tabla, "curva": curva, "mapa": mapa, "K_m2": float(K_m2), "z": float(z)}


# ---------- Prueba rápida: python modelo.py ----------
if __name__ == "__main__":
    print("Difusividad del carbono en Fe-γ:")
    for T in (900, 927, 1000):
        print(f"  T = {T} °C  ->  D = {calcular_difusividad(T):.3e} [m²/s]")

    print("\nPerfil a 927 °C, 10 h (C0 = 0.20 wt %, Cs = 1.00 wt %):")
    for x in (0.0, 0.5, 1.0, 2.0):
        C = calcular_perfil(x, 10, 0.20, 1.00, 927)
        print(f"  x = {x:.2f} [mm]  ->  C = {C:.3f} [wt %]")

    x_obj = calcular_profundidad(10, 0.20, 1.00, 0.40, 927)
    print(f"\nProfundidad donde C = 0.40 wt %: {x_obj:.3f} [mm]")


# ---------- Microestructura en enfriamiento lento (regla de la palanca) ----------
# Puntos del diagrama Fe-Fe₃C de clase (rotulados en el diagrama):
C_FERRITA_MAX = 0.02    # [wt %] máxima solubilidad del C en ferrita (a 723 °C)
C_EUTECTOIDE = 0.8      # [wt %] eutectoide (723 °C)
C_CEMENTITA = 6.67      # [wt %] cementita Fe₃C


def calcular_microconstituyentes(C):
    """Fracciones (de 0 a 1) de ferrita proeutectoide, perlita y cementita proeutectoide que tendría
    un acero con C [wt %] si se ENFRÍA LENTO (equilibrio). Es la regla de la palanca justo debajo de 723 °C:
      hipoeutectoide (C <= 0.8):  perlita = (C - 0.02)/(0.8 - 0.02),  el resto es ferrita proeutectoide
      hipereutectoide (C > 0.8):  perlita = (6.67 - C)/(6.67 - 0.8),  el resto es cementita proeutectoide
    Acepta un número o un arreglo. Regresa un diccionario con 'ferrita', 'perlita' y 'cementita'.
    OJO: no es lo que pasa al templar (eso da martensita y no se calcula aquí)."""
    C_arr = np.asarray(C, dtype=float)
    if np.any(C_arr < 0) or np.any(C_arr > C_CEMENTITA):
        raise ValueError("La concentración debe estar entre 0 y 6.67 wt % (cementita).")
    hipo = C_arr <= C_EUTECTOIDE
    perlita = np.where(
        hipo,
        np.clip((C_arr - C_FERRITA_MAX) / (C_EUTECTOIDE - C_FERRITA_MAX), 0.0, 1.0),
        (C_CEMENTITA - C_arr) / (C_CEMENTITA - C_EUTECTOIDE),
    )
    ferrita = np.where(hipo, 1.0 - perlita, 0.0)
    cementita = np.where(hipo, 0.0, 1.0 - perlita)
    if C_arr.ndim == 0:   # si entró un número, regresa números
        return {"ferrita": float(ferrita), "perlita": float(perlita), "cementita": float(cementita)}
    return {"ferrita": ferrita, "perlita": perlita, "cementita": cementita}


# ---------- Flujo de carbono (primera ley de Fick aplicada a la solución erfc) ----------
# Para pasar de wt % a masa por volumen se usa la densidad del hierro a temperatura ambiente.
# Es una APROXIMACIÓN: a la temperatura de cementación la densidad es un poco menor (dilatación).
DENSIDAD_ACERO = 7870.0  # [kg/m³]  (7.87 g/cm³, densidad del hierro)


def _wt_a_kg_m3(C_wt):
    """Convierte una concentración (o diferencia de concentraciones) de wt % a [kg/m³]."""
    return np.asarray(C_wt, dtype=float) / 100.0 * DENSIDAD_ACERO


def calcular_flujo(x_mm, t_h, C0, Cs, T_C):
    """Flujo de carbono J [kg/(m²·s)] a la profundidad x y al tiempo t.
    Sale de derivar la solución erfc:  J = -D dC/dx = (Cs - C0) * raíz(D/(pi*t)) * exp(-x²/(4*D*t)).
    En la superficie (x = 0) queda J = (Cs - C0) * raíz(D/(pi*t)): baja como 1/raíz(t).
    Entradas: x_mm [mm], t_h [h], C0 y Cs [wt %], T_C [°C]."""
    _validar_concentraciones(C0, Cs)
    _validar_positivo(t_h, "El tiempo")
    x_m = np.asarray(x_mm, dtype=float) * METROS_POR_MM   # [m]
    if np.any(x_m < 0):
        raise ValueError("La profundidad no puede ser negativa.")
    t_s = np.asarray(t_h, dtype=float) * SEGUNDOS_POR_HORA  # [s]
    D = calcular_difusividad(T_C)                           # [m²/s]
    return _wt_a_kg_m3(Cs - C0) * np.sqrt(D / (np.pi * t_s)) * np.exp(-x_m ** 2 / (4.0 * D * t_s))


def calcular_carbono_absorbido(t_h, C0, Cs, T_C):
    """Carbono que entró por cada m² de superficie hasta el tiempo t, M [kg/m²].
    Es el área entre el perfil y C0 (o la suma del flujo en la superficie):  M = 2 (Cs - C0) raíz(D t / pi).
    Crece como raíz(t). Entradas: t_h [h], C0 y Cs [wt %], T_C [°C]."""
    _validar_concentraciones(C0, Cs)
    _validar_positivo(t_h, "El tiempo")
    t_s = np.asarray(t_h, dtype=float) * SEGUNDOS_POR_HORA  # [s]
    D = calcular_difusividad(T_C)                           # [m²/s]
    return 2.0 * _wt_a_kg_m3(Cs - C0) * np.sqrt(D * t_s / np.pi)

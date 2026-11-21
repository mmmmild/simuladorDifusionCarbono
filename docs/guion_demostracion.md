# Guion de demostración y defensa

Duración sugerida: **10 a 12 minutos** de demostración y el resto para preguntas.
Todos los números de este guion salen del código con los valores por defecto de la app
(C₀ = 0.20, Cs = 1.00, Cobj = 0.40 wt %). Si cambias algún valor por defecto, vuelve a revisarlos.

## Antes de presentar (5 minutos)

1. Abre una terminal en la carpeta del proyecto y corre `python validacion.py`. Debe terminar con `78 de 78 pruebas pasaron.`
2. Arranca la app: `python -m streamlit run app.py`.
3. Abre cada módulo una vez para que no haya sorpresas.
4. Toma capturas de pantalla de los módulos 1, 2 y 3 como respaldo por si falla el internet o el equipo.

## Reparto sugerido

| Parte | Quién | Minutos |
|---|---|---|
| Portada, resumen teórico y qué NO calcula (parte de arriba de la página 1) | Persona B | 1 |
| Simulador directo (parte de abajo de la página 1) | Persona A | 2 |
| Módulo 2: diseño inverso (el principal) | Persona A | 4 |
| Módulo 3: comparación | Persona A | 2 |
| Módulo 4: teoría (solo Arrhenius y por qué austenita) | Persona B | 1.5 |
| Módulo 5: validación y limitaciones | Persona B | 2 |

## Paso a paso

### Página 1, parte de arriba: portada y resumen teórico (1 min)
- Presenta la portada (universidad, profesora, equipo) y recorre los seis pasos del resumen teórico sin leerlos completos.
- Di la pregunta de diseño: *¿qué temperatura y tiempo necesito para alcanzar cierta concentración de carbono a cierta profundidad?*
- Di claramente: **la app calcula concentración de carbono, no dureza ni profundidad efectiva de endurecimiento.**

### Página 1, parte de abajo: simulador (Módulo 1) (2 min)
Baja hasta el título **Simulador** (o usa el enlace "Ir directo al simulador").
Valores por defecto: 927 °C, 10 h, C₀ = 0.20, Cs = 1.00, Cobj = 0.40.
- Resultado esperado: **D = 8.326 × 10⁻¹² m²/s**, **L = 0.547 mm**, profundidad para Cobj = **0.891 mm**.
- Señala en la gráfica: Cs en la superficie, C₀ lejos, y la línea de Cobj que cruza el perfil en x ≈ 0.89 mm.
- Lee la sección **¿Qué está pasando?** debajo de la gráfica: cuenta, con los números actuales, qué ocurre. Con los valores por defecto, si duplicas el tiempo a 20 h la profundidad pasa de 0.891 a **1.260 mm** (× 1.41, no × 2).
- Abre "¿Cómo se calculó?" para mostrar la ecuación y el paso a paso.
- Prueba un cambio: sube Cs a 1.50 y baja la temperatura a 900 °C. Debe aparecer un aviso de que Cs supera la solubilidad del carbono en austenita a esa temperatura.

### Módulo 2. Diseño inverso (4 min)
Valores por defecto: profundidad 0.80 mm, tolerancia ± 0.05 mm, Cobj = 0.40, de 900 a 1050 °C, paso 25 °C.
- Resultado esperado de la tabla (tiempo necesario):

| T [°C] | 900 | 925 | 950 | 975 | 1000 | 1025 | 1050 |
|---|---|---|---|---|---|---|---|
| t [h] | 11.35 | 8.27 | 6.10 | 4.56 | 3.45 | 2.63 | 2.03 |

- Explica la curva: cualquier punto sobre ella da la misma profundidad porque **D·t = K** es constante (K = 2.418 × 10⁻⁷ m²).
- Explica la banda: a 975 °C, el tiempo que da 0.80 mm ± 0.05 mm es de **4.01 a 5.15 h**.
- Selecciona 975 °C en "Tratamiento a comprobar" y pulsa **"Comprobar en el simulador directo"**. Te lleva al Módulo 1 con 975 °C y 4.56 h; la profundidad sale **0.800 mm**. Con esto cierras el círculo: el diseño inverso se comprueba con el cálculo directo.
- Abre "Si ya tengo el tiempo: ¿qué temperatura necesito?": con 10 h, la temperatura para 0.80 mm es de unos **910 °C**.

### Módulo 3. Comparación (2 min)
Valores por defecto: A = 900 °C / 12 h, B = 950 °C / 6 h, C = 1000 °C / 3 h.
- Resultado esperado: profundidades **0.823, 0.793 y 0.746 mm**. Al pasar de A a B el tiempo se reduce a la mitad pero D solo aumenta 1.86 veces, por eso D·t baja un poco y la profundidad también.
- Para igualar a A (0.823 mm): B necesitaría 6.45 h y C, 3.64 h.
- Idea para decir: subir la temperatura acorta el tratamiento; lo que el modelo no dice es qué le pasa al grano de la austenita, eso queda fuera del alcance.

### Módulo 4 (1.5 min)
- Arrhenius: D sube **5.6 veces** entre 900 y 1050 °C. Muestra la gráfica de ln D contra 1000/T (recta de pendiente −Q/R).
- Aclara el punto científico: **el carbono difunde más rápido en ferrita (BCC) que en austenita (FCC).** Se modela en austenita porque es la fase estable a esa temperatura, disuelve mucho más carbono (2.11 wt % contra 0.02 wt %) y se transforma en martensita al templar.

### Módulo 5 (2 min)
- Muestra el contador: **78 de 78 pruebas pasan**.
- Caso E: el libro (Callister, problema 5.13) da 31.39 h; el modelo da 31.13 h (−0.8 %). Con R = 8.31, la del libro, da 31.35 h (−0.1 %). La diferencia viene de R, no de un error.
- Muestra la tabla de procedencia: diapositivas / elegido por el equipo / demostración / calculado.
- Cierra con los supuestos y con "Modelo contra acero real".

## Preguntas que pueden hacer y cómo contestar

**1. ¿Por qué modelan en austenita y no en ferrita?**
Porque a 900–1050 °C un acero de bajo carbono está en el campo austenítico, la austenita disuelve hasta 2.11 wt % de C (la ferrita, 0.02 wt %) y se transforma en martensita al templar. Ojo: no es porque difunda más rápido; en ferrita el carbono difunde más rápido.

**2. ¿Por qué R = 8.3145 y no 8.31?**
8.3145 es el valor aceptado. Con él se reproducen los casos de referencia A, B y C. Con 8.31 fallaban varias pruebas. El problema de Callister sí usa 8.31, y con ese valor el modelo queda a −0.1 % del libro, contra −0.8 % con 8.3145. La diferencia es de R, no del modelo.

**3. ¿La profundidad que calculan es la profundidad de capa cementada o de endurecimiento?**
No. Es la profundidad a la que el carbono llega a la concentración objetivo que el usuario elige. La profundidad efectiva de endurecimiento se define con un criterio de dureza después del temple, y la app no calcula dureza.

**4. ¿Qué significa que D·t sea constante?**
Para una x y una Cobj dadas, la solución de Fick depende solo de x/(2√(Dt)), así que D·t = [x/(2z)]² = K. Cualquier pareja (T, t) con ese producto da lo mismo. Es la curva del Módulo 2.

**5. ¿De dónde salen D₀ y Q?**
De la tabla de difusión de las diapositivas de clase (carbono en Fe-γ). No se inventaron ni se ajustaron.

**6. ¿Qué pasa si Cs es mayor que lo que disuelve la austenita?**
La app muestra un aviso (no bloquea): podrían formarse carburos y el modelo de una sola fase dejaría de ser válido. La línea Acm que usa es una recta entre dos puntos del diagrama de clase, es una aproximación.

**7. ¿Cuándo deja de valer el supuesto de sólido semiinfinito?**
Cuando el espesor es menor que unas 4 veces L = √(Dt). Con 927 °C y 10 h, 4L ≈ 2.19 mm. El Módulo 1 tiene una casilla para indicar el espesor y avisa.

**8. ¿Cómo validaron el modelo?**
Con cinco tipos de pruebas: casos de referencia (A–D), un problema de libro (E), consistencia entre funciones (por ejemplo, ida y vuelta tiempo ↔ profundidad), chequeo de fases y errores. La tabla completa está en el Módulo 5 y se corre con `python validacion.py`.

**9. ¿Cs sale del diagrama Fe–Fe₃C?**
No. Cs depende del potencial de carbono de la atmósfera. El diagrama solo dice hasta dónde puede disolverse el carbono en austenita. En la app, Cs es un valor que el usuario elige (por defecto, un valor de demostración).

**10. ¿Por qué la banda de tolerancia no es simétrica en el tiempo?**
Porque la tolerancia está en la profundidad (x ± tol) y se convierte a tiempo con t ∝ x². Esa relación es cuadrática, así que el tiempo para x + tol se aleja más del central que el de x − tol.

**11. ¿Qué haría falta para acercarse a una pieza real?**
Que D dependa de la concentración y de los aleantes, el calentamiento y el enfriamiento reales, la cinética de transferencia de carbono en la superficie, la geometría de la pieza y, para predecir propiedades, un modelo de temple y dureza. Nada de eso está en esta versión y el Módulo 5 lo dice.

**12. ¿Por qué usan Arrhenius?**
Porque la difusión es un proceso activado térmicamente: la fracción de saltos atómicos que vencen la barrera Q crece como exp(−Q/RT). Al graficar ln D contra 1/T sale una recta de pendiente −Q/R.

## Si algo falla durante la demostración

- La app no abre: corre `python -m pip install -r requirements.txt` y luego `python -m streamlit run app.py` desde la carpeta que contiene `app.py`.
- Un módulo marca error: muestra las capturas de respaldo y corre `python validacion.py` en la terminal para mostrar que el modelo sí funciona.
- Te preguntan algo que no sabes: di qué supone el modelo y que eso está listado en el Módulo 5. No inventes un valor.

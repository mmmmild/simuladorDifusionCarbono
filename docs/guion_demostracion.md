# Guion de demostración y defensa

Duración sugerida: **10 minutos** de demostración y el resto para preguntas.
Los números salen del código con los valores por defecto de la app (C₀ = 0.20, Cs = 1.00, Cobj = 0.40 wt %).

## Antes de presentar

1. Corre `python validacion.py`. Debe terminar con `93 de 93 pruebas pasaron.`
2. Abre la app (link de Streamlit o `python -m streamlit run app.py`) y recorre las 5 secciones.
3. Toma capturas de respaldo por si falla el internet.

## Reparto sugerido

| Parte | Minutos |
|---|---|
| 1. Fundamento teórico | 3 |
| 2. Simulación | 3 |
| 3. Diseño inverso | 2 |
| 4. Comparación | 1 |
| 5. Industria | 1 |

## Paso a paso

### 1. Fundamento teórico (3 min)
- Presenta la portada.
- Explica las 4 tarjetas: se calienta, la atmósfera da carbono, el carbono se mete (difusión) y se templa (fuera del simulador).
- Muestra los cortes de la pieza a 0, 1, 4 y 10 h: el carbono entra cada vez más profundo, pero no al mismo ritmo que el tiempo.
- Recorre rápido: difusión intersticial, leyes de Fick, Arrhenius (D se multiplica por 5.6 entre 900 y 1050 °C) y por qué austenita.
- Punto clave: el carbono difunde **más rápido en ferrita**; se usa austenita por estabilidad, solubilidad y temple.

### 2. Simulación (3 min)
- Con los valores por defecto (927 °C, 10 h): **L = 0.547 mm**, profundidad para Cobj = **0.891 mm**, espesor mínimo de pieza **2.19 mm**.
- Presiona **▶ Ver la difusión**: el corte se oscurece desde arriba y la línea azul (Cobj) baja.
- Mueve el tiempo a 20 h: la profundidad pasa a **1.260 mm** (× 1.41, no × 2).
- Lee "¿Qué está pasando?" y muestra la tabla "¿Por qué estos rangos?".

### 3. Diseño inverso (2 min)
- Valores por defecto (0.80 mm, 0.40 wt %, ± 0.05 mm): a 950 °C hacen falta **6.10 h**; a 900 °C, 11.35 h; a 1050 °C, 2.03 h.
- Sube la profundidad a 1.60 mm (el doble): a 950 °C el tiempo pasa a **24.42 h** (4 veces). La curva naranja se aleja de la gris.
- Regresa a 0.80 mm y sube Cobj a 0.50 wt %: a 950 °C pasa a **10.26 h**.
- Elige 950 °C y pulsa **Comprobar en la simulación**: la profundidad sale **0.800 mm**.

### 4. Comparación (1 min)
- Meta 0.80 mm. A (900 °C, 12 h) llega a 0.823 mm, B (950 °C, 7 h) a 0.857 mm y C (1000 °C, 3 h) a 0.746 mm.
- La app recomienda **B**: llega a la meta con menos tiempo. Y dice que C llegaría con solo 3.45 h.

### 5. Industria (1 min)
- Superficie dura + núcleo tenaz; dónde se usa; qué pasa si la capa sale mal.

## Preguntas que pueden hacer y cómo contestar

**1. ¿Por qué modelan en austenita y no en ferrita?**
Porque a 900–1050 °C el acero de bajo carbono está en austenita, que disuelve hasta 2.11 wt % de C (la ferrita, 0.02 wt %) y se transforma en martensita al templar. No es porque difunda más rápido: en ferrita el carbono difunde más rápido.

**2. ¿Por qué R = 8.3145 y no 8.31?**
Es el valor aceptado y reproduce los casos de referencia. El problema de Callister usa 8.31; con ese valor el modelo queda a −0.1 % del libro, y con 8.3145 a −0.8 %.

**3. ¿La profundidad que calculan es la de endurecimiento?**
No. Es la profundidad a la que el carbono llega a la concentración objetivo. La profundidad efectiva de endurecimiento se define con dureza después del temple, y la app no calcula dureza.

**4. ¿Por qué los rangos de los controles?**
Están explicados en la sección de Simulación. Resumen: la temperatura asegura austenita con margen sobre A3 y queda lejos de 1147 °C; Cs llega hasta 1.15 wt % para no pasar el límite de solubilidad a 900 °C; C₀ corresponde a aceros de bajo carbono. Los eligió el equipo con el diagrama de clase.

**5. ¿Qué significa que D·t sea constante en el diseño inverso?**
Para una x y una Cobj dadas, la solución depende solo de x/(2√(Dt)), así que D·t = [x/(2z)]² es constante. Cualquier pareja (T, t) con ese producto da el mismo resultado.

**6. ¿Cómo eligen el mejor tratamiento?**
De los que llegan a la meta, el de menos tiempo de horno. El modelo no considera crecimiento de grano ni costo de energía, y la app lo dice.

**7. ¿Cuándo deja de valer el modelo?**
Si la pieza es más delgada que unas 4·L (sólido semiinfinito), si Cs supera la solubilidad (carburos) o si el acero no es todo austenita. También supone D constante, temperatura constante y acero sin aleantes.

**8. ¿Cómo validaron el modelo?**
Con `python validacion.py`: casos de referencia, un problema de libro (Callister 5.13), consistencia entre funciones y errores. 93 pruebas pasan.

## Si algo falla durante la demostración

- La app no abre: `python -m pip install -r requirements.txt` y luego `python -m streamlit run app.py`.
- Un error en pantalla: muestra las capturas de respaldo y corre `python validacion.py`.
- Una pregunta que no sabes: di qué supone el modelo. No inventes un valor.

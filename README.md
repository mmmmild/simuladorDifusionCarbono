# Simulador Difusión Carbono

**Simulador interactivo para analizar y diseñar condiciones de difusión de carbono en aceros.**

**Universidad Nacional Autónoma de México**

Facultad de Ingeniería · Ingeniería de Materiales

**Profesora:** Artemisa Mazón Martínez

**Equipo:**
- Meza Prieto Adriel
- Uriostegui Rodriguez Adolfo Saúl
- Vega Hurtado Mildred Dessire

La app responde una pregunta de diseño:

> ¿Qué combinación de temperatura y tiempo necesito para alcanzar una concentración de carbono
> determinada a una profundidad específica?

## Qué hace y qué no hace

**Sí calcula:** el perfil de concentración de carbono C(x,t), la profundidad a la que la concentración llega a un
valor objetivo, el tiempo o la temperatura necesarios, y la comparación de hasta tres tratamientos.

**No calcula:** dureza, temple, revenido ni *profundidad efectiva de endurecimiento*. La profundidad que
reporta es la profundidad a una concentración objetivo de carbono, no una propiedad mecánica.

## Módulos

| # | Módulo | Qué permite |
|---|---|---|
| 1 | Inicio y simulación directa | Arriba, portada y resumen teórico; debajo, el simulador: das T y t y obtienes el perfil de carbono, D, L = √(Dt) y la profundidad para Cobj, con una explicación paso a paso que se actualiza con tus valores |
| 2 | Diseño inverso (principal) | Das profundidad y Cobj, obtienes todas las parejas (T, t) con banda de tolerancia, un mapa y la opción de comprobarlas en el Módulo 1 |
| 3 | Comparación de tratamientos | Hasta 3 tratamientos lado a lado, con tabla y explicación |
| 4 | Fundamento teórico | Difusión, leyes de Fick, Arrhenius, por qué austenita |
| 5 | Validación y limitaciones | Pruebas numéricas, cálculo manual, procedencia de los datos, supuestos y límites |

## Modelo

Segunda ley de Fick en una dimensión, sólido semiinfinito, D constante:

```
C(x,t) = C0 + (Cs − C0) · erfc[ x / (2·√(D·t)) ]
D = D0 · exp(−Q / (R·T))
```

Diseño inverso: con z = erfc⁻¹[(Cobj − C0)/(Cs − C0)], la profundidad es x = 2·z·√(D·t), el tiempo es
t = [x/(2z)]²/D y la temperatura es T = −Q / [R·ln(D_req/D0)], con D_req = [x/(2z)]²/t. Para x y Cobj fijos,
D·t = K es constante.

### Parámetros y de dónde salen

| Tipo | Dato | Valor |
|---|---|---|
| Diapositivas de clase | D₀ (C en Fe-γ) | 2.3 × 10⁻⁵ m²/s |
| Diapositivas de clase | Q (C en Fe-γ) | 148 000 J/mol |
| Diagrama Fe–Fe₃C de clase | Eutectoide / máxima solubilidad del C en austenita | 0.8 wt % a 723 °C / 2.11 wt % a 1147 °C |
| Ejercicio de clase | Austenita a 780 °C | 0.42 wt % C |
| Elegido por el equipo | R | 8.3145 J/(mol·K) |
| Elegido por el equipo | Intervalo de temperatura | 900–1050 °C |
| Elegido por el equipo | Sólido semiinfinito | espesor ≥ 4·L |
| Valores de demostración | C₀ / Cs / Cobj | 0.20 / 1.00 / 0.40 wt % (no son estándares industriales) |

Las líneas A3 y Acm del chequeo de fases son **aproximaciones** (Acm es una recta entre dos puntos del diagrama de
clase). Solo generan avisos y nunca bloquean un cálculo.

## Cómo ejecutarlo

Requiere Python 3.10 o superior.

Desde la carpeta del repositorio (la que contiene `app.py`):

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit abre la app en `http://localhost:8501`. En GitHub Codespaces, el puerto 8501 se abre desde la pestaña
**Ports** (o con la ventana emergente que aparece al iniciar). Si aparece `streamlit: command not found`, se usa `python -m streamlit` como arriba.

## Validación

```bash
python validacion.py
```

Compara el modelo contra casos de referencia y contra propiedades que siempre deben cumplirse. Termina con
`78 de 78 pruebas pasaron.` y código de salida 0 si todo está bien. La misma tabla se ve en el Módulo 5.

| Caso | Qué comprueba |
|---|---|
| A, B, C, D | D, perfil, diseño inverso y efecto de Cobj contra los valores de referencia del proyecto |
| E | Problema 5.13 de Callister: el libro da 1.13 × 10⁵ s y el modelo da una diferencia de −0.8 %. Con R = 8.31 (la que usa el libro) la diferencia baja a −0.1 % |
| Consistencia | Ida y vuelta entre funciones, condiciones de frontera, D·t constante, L = √(Dt) |
| Fases | Avisos de A3 y Acm |
| Errores | El modelo avisa cuando los datos no tienen sentido físico |

## Supuestos principales

Sólido semiinfinito y unidimensional, D constante (independiente de la concentración), temperatura constante,
Cs constante desde el inicio, una sola fase (austenita), sin carburos, sin aleantes, wt % tratado como
concentración. La lista completa y los fenómenos que no se consideran están en el Módulo 5 de la app.

## Estructura del repositorio

```
.
├── app.py                    # navegación (barra lateral); no tiene cálculos
├── modelo.py                 # física: Fick, Arrhenius, diseño inverso, chequeo de fases
├── validacion.py             # pruebas numéricas (python validacion.py)
├── estilo.py                 # colores, límites y nombres de páginas compartidos
├── modulos/
│   ├── inicio.py             # portada y resumen teórico (arriba de la página 1)
│   ├── m1_simulacion.py      # Módulo 1 (el simulador, debajo del resumen teórico)
│   ├── m2_inverso.py         # Módulo 2
│   ├── m3_comparacion.py     # Módulo 3
│   ├── m4_teoria.py          # Módulo 4
│   └── m5_validacion.py      # Módulo 5
├── docs/
│   └── guion_demostracion.md # guion y preguntas de defensa
├── .streamlit/config.toml    # tema claro (fondo blanco)
├── requirements.txt
└── README.md
```

El modelo está separado de la interfaz: `modelo.py` no importa Streamlit, así que se puede probar y usar sin la app.

## Tecnologías

Python · Streamlit · Plotly · NumPy · SciPy (`erfc`, `erfcinv`) · Pandas

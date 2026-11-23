# Simulador Difusión Carbono

**Simulador interactivo para analizar y diseñar condiciones de difusión de carbono en aceros.**

**Universidad Nacional Autónoma de México**

Facultad de Ingeniería · Ingeniería de Materiales

**Profesora:** Artemisa Mazón Martínez

**Equipo:**
- Meza Prieto Adriel
- Uriostegui Rodriguez Adolfo Saúl
- Vega Hurtado Mildred Dessire

## ¿Qué hace?

Calcula cómo se reparte el carbono dentro de una pieza de acero durante la cementación: el perfil de
concentración C(x,t), la profundidad a la que se llega a una concentración objetivo, y el tiempo o la
temperatura necesarios para lograrla. Muestra la difusión con una animación del corte de la pieza.

**No calcula** dureza, temple ni profundidad efectiva de endurecimiento.

## ¿Para qué sirve?

- **Diseñar un tratamiento de cementación.** Si sabes qué concentración de carbono necesitas y a qué
  profundidad, la app te da las combinaciones de temperatura y tiempo que lo logran.
- **Entender el efecto de cada variable.** Muestra cómo cambia el carbono dentro de la pieza al mover la
  temperatura, el tiempo o las concentraciones. Por ejemplo, duplicar el tiempo no duplica la profundidad:
  la aumenta √2 veces (unas 1.41 veces).
- **Elegir entre opciones.** Compara tres tratamientos y dice cuál llega a la profundidad meta con menos
  tiempo de horno.
- **Aprender difusión con números.** Conecta la teoría (leyes de Fick y Arrhenius) con resultados que se
  pueden comprobar a mano.

Es una herramienta de cálculo y de aprendizaje: sirve para estimar y comparar, pero **no sustituye los ensayos**.

## Secciones de la app

| # | Sección | Qué tiene |
|---|---|---|
| 1 | Fundamento teórico | Portada, qué pasa en realidad durante la cementación (con cortes de la pieza), difusión, leyes de Fick, Arrhenius y por qué austenita |
| 2 | Simulación | Controles de temperatura, tiempo y concentraciones; animación de la difusión en un corte de la pieza; explicación paso a paso y el porqué de cada rango |
| 3 | Diseño inverso | Tres controles (profundidad, concentración objetivo y tolerancia); curva temperatura–tiempo con una curva de referencia para ver el efecto de cada control |
| 4 | Comparación de tratamientos | Tres tratamientos contra una profundidad meta; dice cuál conviene y por qué |
| 5 | Importancia en la industria | Dónde se usa la cementación, qué se gana, qué pasa si sale mal y cómo se conecta con la app |

## Modelo

Segunda ley de Fick en una dimensión, sólido semiinfinito, D constante:

```
C(x,t) = C0 + (Cs − C0) · erfc[ x / (2·√(D·t)) ]
D = D0 · exp(−Q / (R·T))
```

Con z = erfc⁻¹[(Cobj − C0)/(Cs − C0)]: profundidad x = 2·z·√(D·t), tiempo t = [x/(2z)]²/D y temperatura
T = −Q / [R·ln(D_req/D0)]. D₀ = 2.3 × 10⁻⁵ m²/s y Q = 148 000 J/mol (carbono en Fe-γ, diapositivas de clase);
R = 8.3145 J/(mol·K).

## Cómo ejecutarlo

Desde la carpeta del repositorio (la que contiene `app.py`):

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Validación

```bash
python validacion.py
```

Compara el modelo contra casos de referencia, un problema de libro (Callister 5.13) y propiedades que siempre
deben cumplirse. Debe terminar con `93 de 93 pruebas pasaron.`

## Estructura del repositorio

```
.
├── app.py                    # navegación (barra lateral); no tiene cálculos
├── modelo.py                 # física: Fick, Arrhenius, diseño inverso, chequeo de fases
├── validacion.py             # pruebas numéricas (python validacion.py)
├── estilo.py                 # colores, rangos de los controles y nombres de las secciones
├── modulos/
│   ├── inicio.py             # portada
│   ├── visual.py             # gráficas del corte de la pieza (animación)
│   ├── m4_teoria.py          # 1. Fundamento teórico
│   ├── m1_simulacion.py      # 2. Simulación
│   ├── m2_inverso.py         # 3. Diseño inverso
│   ├── m3_comparacion.py     # 4. Comparación de tratamientos
│   └── industria.py          # 5. Importancia en la industria
├── docs/
│   └── guion_demostracion.md # guion y preguntas de defensa
├── .streamlit/config.toml    # tema claro (fondo blanco)
├── requirements.txt
└── README.md
```

## Tecnologías

Python · Streamlit · Plotly · NumPy · SciPy (`erfc`, `erfcinv`) · Pandas

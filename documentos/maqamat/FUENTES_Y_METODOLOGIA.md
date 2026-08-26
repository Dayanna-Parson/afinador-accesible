# Fuentes, licencia y metodología

## Fuente musical de referencia

La referencia principal consultada para los grados de los maqamat fue:

- Riad Assoum, **Maqamusic**, complemento accesible para NVDA:
  <https://github.com/riadassoum/Maqamusic>
- Archivo de datos y teoría consultado:
  <https://github.com/riadassoum/Maqamusic/blob/main/globalPlugins/maqamKeyboard/maqamat.py>

Maqamusic declara licencia **GNU GPL v2**. AfinadorAccesible no incluye ni
importa su código, su sintetizador, sus textos, su SoundFont ni sus recursos.
Los enlaces se conservan para atribución, estudio y revisión. Los valores que
la app utiliza se han expresado como datos propios de validación y como una
adaptación independiente al orden físico de la lira.

## Qué significa “adaptación a la lira”

La fuente describe grados desde una tónica. La lira tiene, en cambio, dieciséis
cuerdas naturales ya dispuestas en un orden fijo. El algoritmo de control hace
esto para cada maqam:

1. Toma la tónica y los siete grados de referencia en cents.
2. Para cada cuerda de la lira, identifica el grado diatónico correspondiente.
3. Busca la octava de ese grado más próxima a la frecuencia original de la
   cuerda.
4. Calcula el desplazamiento respecto de la afinación de fábrica.
5. Redondea el resultado a pasos de 50 cents y lo expresa como un entero de
   “cuartos de tono”.

El código de comprobación se llama `calcular_retoques_referencia_lira()` y está
en `app/afinaciones_maqam_lira.py`. No se ejecuta para decidir una afinación
durante el uso normal: sirve para que los tests comparen las tablas estáticas
con los grados de referencia.

## Convenciones de datos

- `1` en una tabla de retoques = subir 50 cents.
- `-1` = bajar 50 cents.
- `2` = subir un semitono occidental.
- `-2` = bajar un semitono occidental.
- La frecuencia se calcula mediante una relación exponencial, no sumando Hz:
  `frecuencia = referencia × 2^(cents/1200)`.

El afinador permite cambiar La4; esa calibración desplaza proporcionalmente
todas las referencias sin cambiar los intervalos del maqam.

## Alcance y honestidad musical

24‑EDO es una representación de trabajo útil para una lira que se afina en
pasos de 50 cents. No afirma que toda interpretación de música árabe use
exactamente 50 cents para cada neutralidad interválica. La práctica real puede
variar por región, escuela, instrumento, cantante, contexto melódico y gusto
interpretativo.

Si una fuente fiable o una música especialista propone una variante concreta,
la forma correcta de incorporarla es crear un perfil propio, documentar su
procedencia y no sobrescribir silenciosamente el mapa integrado.

# Fuentes, licencia y metodología

## Fuente musical de referencia

Para los grados de los maqamat usé como referencia:

- Riad Assoum, **Maqamusic**, complemento accesible para NVDA:
  <https://github.com/riadassoum/Maqamusic>
- El archivo de datos y teoría que consulté:
  <https://github.com/riadassoum/Maqamusic/blob/main/globalPlugins/maqamKeyboard/maqamat.py>

Maqamusic tiene licencia **GNU GPL v2**. No incluyo ni importo su código, su
sintetizador, sus textos, su SoundFont ni ningún recurso suyo — solo dejo los
enlaces para atribución, estudio y revisión. Los valores que uso en mi app
los expresé como datos propios de validación, y la adaptación al orden físico
de la lira es independiente.

## Qué significa "adaptación a la lira"

La fuente describe grados desde una tónica. Mi lira, en cambio, tiene
dieciséis cuerdas naturales ya dispuestas en un orden fijo. Para cada maqam,
el algoritmo de control hace esto:

1. Toma la tónica y los siete grados de referencia en cents.
2. Para cada cuerda de la lira, identifica el grado diatónico correspondiente.
3. Busca la octava de ese grado más próxima a la frecuencia original de la
   cuerda.
4. Calcula el desplazamiento respecto de la afinación de fábrica.
5. Redondea el resultado a pasos de 50 cents y lo expresa como un entero de
   “cuartos de tono”.

Esa cuenta la hace `calcular_retoques_referencia_lira()`, en
`app/afinaciones_maqam_lira.py`. No se ejecuta mientras uso la app: existe
para que los tests comparen mis tablas estáticas contra los grados de
referencia.

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

24-EDO me sirve como aproximación de trabajo para una lira que se afina en
pasos de 50 cents. No estoy afirmando que toda interpretación de música
árabe use exactamente 50 cents en cada nota neutra — la práctica real varía
por región, escuela, instrumento, intérprete y contexto melódico.

Si alguna vez una fuente fiable o una música especialista me propone una
variante concreta, la incorporo como un perfil propio, documento de dónde
sale, y no sobrescribo en silencio el mapa que ya tengo integrado.

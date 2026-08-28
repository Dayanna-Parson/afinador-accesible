# Música árabe y accesibilidad

Hay dos mundos que casi nunca se cruzan en internet: la teoría de los
maqamat y las herramientas hechas de verdad para gente ciega. Yo vivo en los
dos a la vez, así que esto es lo que aprendí uniéndolos.

## Cómo llegué hasta aquí

Todo empezó por accidente, escuchando música egipcia y notando que algo
sonaba "distinto" de una forma que no sabía nombrar. No era una nota rara,
era una nota que sonaba a mitad de camino entre dos que yo ya conocía. Ese
"a mitad de camino" tiene nombre: cuarto de tono. Y una vez que supe que
existía, quise poder tocarlo — no solo escucharlo.

Mi lira Aklot no venía preparada para eso. Así que en vez de resignarme, me
puse a construir el afinador que necesitaba para hacerlo posible.

## Por qué usé Maqamusic como referencia

Maqamusic es un complemento de NVDA hecho por Riad Assoum para tocar maqamat
con el teclado del ordenador. No copié su código ni sus sonidos: usé sus
datos de grados y tónicas como referencia para construir mi propio catálogo,
adaptado al orden físico de las 16 cuerdas de mi lira — que no es el mismo
problema que tocar un teclado. Verifiqué cada uno de los 25 maqamat que
integré contra esa fuente antes de darlo por bueno.

Esto me importa dejarlo claro: la información con procedencia y atribución
no es un trámite legal aburrido. Es lo que me permite confiar en mis propios
datos sin tener que reinventar la teoría musical desde cero, y es lo que le
permite a cualquiera que use mi app comprobar de dónde salen esos números en
vez de fiarse a ciegas — nunca mejor dicho.

## Por qué la accesibilidad no es un añadido

Cuando busqué afinadores para instrumentos de cuerda, encontré muchos que se
llamaban "accesibles" y no lo eran de verdad: un botón sin nombre, un
indicador que solo cambia de color, una lista que no anuncia nada al
navegar con flechas. Accesible no es "funciona con un lector de pantalla de
casualidad". Es diseñar cada control pensando en cómo se anuncia, cómo se
recorre con teclado, y qué pasa cuando algo falla y la app tiene que decirlo
en voz alta en vez de quedarse callada.

Por eso mi afinador anuncia el nivel de señal del micrófono, avisa si la
captura de audio se ha cortado, y nunca dispara dos anuncios que se pisen
entre sí. No es un lujo añadido para "hacerlo accesible también": es la
mitad del programa.

## Las dos cosas juntas

Lo que más me gusta de este proyecto es que no tuve que elegir entre hacer
algo musicalmente honesto y hacerlo accesible de verdad. Un dato bien
verificado y un control bien anunciado son la misma exigencia aplicada a dos
sitios distintos: no mentir sobre lo que la herramienta puede hacer, y no
dejar a nadie fuera de poder usarla.

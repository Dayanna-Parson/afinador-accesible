# Visión personal del proyecto — AfinadorAccesible

## Punto de partida

Este proyecto nace porque una persona ciega que aprende lira por su cuenta
necesita un afinador de Windows que pueda usar de verdad: con teclado, mensajes
claros y lector de pantalla, sin tener que depender de una app móvil ni de una
interfaz visual inaccesible.

Aprender a programar se vuelve una consecuencia de esa necesidad. Si no puedo
explicar con precisión cómo tiene que funcionar mi afinador, tampoco puedo
pedirle a otra persona que lo construya bien.

## El problema real

El problema no es reconocer una frecuencia aislada. Es poder preparar un
instrumento para tocar sin perderse entre cents, gráficos sin texto, controles
mal etiquetados o configuraciones de audio opacas.

La aplicación debe servir tanto a quien usa NVDA con la pantalla apagada como a
quien ve: información textual, controles estándar e indicador visual son
complementarios; ninguno sustituye al otro.

## Límites deliberados

La app se centra en instrumentos reales de su autora:

- Lira Aklot de 16 cuerdas.
- Guitarra acústica y electroclásica de seis cuerdas.
- Ukelele soprano con afinación reentrante.

No se añaden instrumentos o afinaciones simplemente por hacer una lista larga.
Una opción entra cuando tiene una explicación musical, una forma segura de
aplicarla y una prueba razonable con el instrumento correspondiente.

## Música árabe sin falsas promesas

Los maqamat son una parte importante de la identidad del afinador. La lira puede
adaptarse a sus grados mediante retoques por cuartos de tono; esto permite
escuchar y estudiar colores modales que no aparecen en la afinación occidental
estándar.

Pero la documentación y la interfaz deben decir siempre la verdad: una lira
diatónica retuneada no sustituye la técnica, la modulación ni la entonación viva
de un oud, nay o qanun. Un instrumento con trastes tampoco gana cuartos de tono
por seleccionar un maqam. La precisión de los datos y la honestidad sobre estos
límites son más importantes que prometer una función espectacular.

## Principios que no se negocian

1. La accesibilidad se diseña antes de añadir la función, no después.
2. Todo se puede hacer con teclado y cada control debe tener nombre y propósito.
3. El lector de pantalla no debe recibir anuncios continuos ni contradictorios.
4. La información importante no depende solo de color, iconos o sonido.
5. La afinación estándar se representa exactamente; los mapas de maqam se
   verifican contra referencias y pruebas.
6. Un fallo de audio o de configuración debe explicarse: nunca fallar en
   silencio.
7. Los perfiles personales pertenecen a la persona usuaria y se preservan.
8. La seguridad de las cuerdas vale más que permitir cualquier combinación sin
   aviso.

## Hacia dónde puede crecer

La prioridad es estabilizar antes de ampliar. Las mejoras futuras deben venir
de pruebas reales: claridad de las instrucciones, robustez de entrada de audio,
referencias de sonido propias para cada instrumento y una distribución sencilla
para Windows. No hace falta convertir el afinador en una enciclopedia musical
para que sea potente; debe seguir siendo rápido de entender y agradable de usar.

— Dayanna Parson, agosto de 2026

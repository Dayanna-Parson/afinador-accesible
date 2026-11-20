# Sonidos del Afinador Accesible

Esta carpeta está preparada para sonidos opcionales de la aplicación. No son
necesarios para afinar ni sustituyen ningún anuncio del lector de pantalla.

Cuando se añadan, deben ser archivos WAV cortos, 16-bit, 44100 Hz, con nombres
claros: `afinada.wav`, `iniciar_escucha.wav`, `detener_escucha.wav` y `error.wav`.
La aplicación deberá funcionar igualmente si un archivo no existe o si la
persona desactiva los sonidos.

Los botones conservarán texto y ayuda accesible; ningún sonido ni icono será la
única forma de comunicar un estado.

## Sonidos del tono de referencia

`referencias/` contiene los sonidos que usa el tono de referencia. Ahora mismo son
provisionales: generados, una nota por cada cuerda de la lira, que también se usan para la
guitarra y el ukelele.

- Formato: WAV PCM (mejor mono, 16 bits, 44100 Hz), unos segundos de nota sostenida.
- El nombre **debe** llevar la frecuencia exacta de la nota en hercios, con coma o punto:
  `09_cuerda_9_La4_440,00Hz.wav`. Lo demás del nombre es libre. Sin frecuencia en el nombre,
  el archivo se ignora.
- No hace falta una grabación por cuerda: se usa la más cercana y se sube o baja hasta la
  frecuencia exacta. Cuanto más cerca esté, más natural suena; una cada pocas notas basta.
- Grabaciones propias de un instrumento: en una subcarpeta con su nombre, `referencias/lira/`,
  `referencias/guitarra/` o `referencias/ukelele/`. Si existe y tiene sonidos, ese
  instrumento usa solo los suyos; si no, los generales de `referencias/`.

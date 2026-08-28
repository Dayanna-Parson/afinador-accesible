# Guía de revisión de los maqamat

Esto es para mí misma dentro de un tiempo, para quien continúe el proyecto,
o para cualquiera con curiosidad: permite revisar la parte musical sin tener
que instalar el repositorio de Maqamusic.

## Archivos que hay que leer primero

1. `app/afinaciones_maqam_lira.py`: datos integrados y función de referencia.
2. `tests/test_maqamat.py`: pruebas que convierten los grados en el ajuste de
   las dieciséis cuerdas.
3. `app/motor_audio.py`: conversión de nota, cents y frecuencia.
4. `app/interfaz/ventana_principal.py`: selección de escala y reproducción de la afinación completa.
5. `documentos/maqamat/FUENTES_Y_METODOLOGIA.md`: alcance, fuente y licencia.

## Preguntas obligatorias antes de cambiar un maqam

1. ¿La fuente diferencia una escala de un maqam completo con *sayr*? No reducir
   la explicación cultural a siete números.
2. ¿La tónica, su posible desplazamiento de 50 cents y los siete grados están
   anotados explícitamente?
3. ¿La adaptación conserva los grados en las octavas que realmente tiene la
   lira, sin duplicar cuerdas consecutivas?
4. ¿La variante pertenece a una familia existente o necesita una familia nueva?
5. ¿Se han actualizado el catálogo, las pruebas, README, ayuda y este material?
6. ¿La nueva fuente permite reutilizar código o texto? Si no está clara la
   licencia, incorporar solo una referencia y datos comprobables, nunca copiar.

## Pruebas necesarias

Ejecutar:

```text
python -m unittest discover -s tests -v
```

Además, abrir la app, elegir la familia y pulsar `Ctrl+Mayús+P` para escuchar la
afinación completa. La prueba automática confirma el mapa matemático; la
prueba humana confirma que la interfaz, el audio y los anuncios siguen siendo
utilizables.

## Errores que no se deben repetir

- Confundir la primera cuerda física, Sol3, con la tónica de todos los maqamat.
- Cambiar la afinación de fábrica: debe seguir siendo solo natural y sin
  retoques.
- Llamar “maqam para guitarra” a lo que solo retoca las cuerdas al aire: los
  trastes no adquieren cuartos de tono.
- Prometer fidelidad absoluta de 24‑EDO a cualquier práctica interpretativa.
- Copiar código GPL a este repositorio sin decidir antes la licencia del
  proyecto.

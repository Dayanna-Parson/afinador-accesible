# Guía técnica para desarrolladoras

Lee este documento antes de modificar el afinador.

## Propósito

Afinador Accesible es una aplicación Windows para lira Aklot de 16 cuerdas,
guitarra y ukelele soprano. Su prioridad es que una persona ciega pueda afinar
de forma autónoma, sin impedir una interfaz clara a quien ve.

## Principios no negociables

- Toda la interfaz, mensajes, comentarios y registros están en español.
- wxPython solo se actualiza desde el hilo principal. El audio y otros trabajos
  lentos se comunican con `wx.CallAfter`.
- Un control sin nombre, estado o ayuda comprensible en NVDA es un error crítico.
- No se usa Espacio como atajo global.
- La captura se pausa antes de reproducir una referencia y se reanuda con cuidado.
- Los cambios deben ser quirúrgicos y respetar los bloques `ANCLAJE`.

## Capas del proyecto

- `app/interfaz/ventana_principal.py`: ventana y coordinación wxPython.
- `app/interfaz_gui.py`: compatibilidad temporal para importaciones antiguas.
- `app/motor_audio.py`: captura, YIN y generación de tonos; no conoce widgets.
- `app/afinaciones_maqam_lira.py`: afinaciones estáticas de la lira en 24-EDO.
- `app/gestor_ajustes.py`: persistencia de preferencias del usuario.
- `app/conector_nvda.py`: anuncios al lector de pantalla, con limitación de repeticiones.
- `app/control_microfono.py`: comprobación opcional del silencio de Windows.

## Maqamat y precisión

Una afinación de la lira es una representación fija de siete grados en 24-EDO
(50 cents por cuarto de tono). No representa por sí sola ajnas, sayr, modulación
ni las variaciones regionales de la interpretación. Las tablas son explícitas;
`tests/test_maqamat.py` comprueba cada una contra sus grados de referencia y
evita cuerdas consecutivas duplicadas.

## Pruebas antes de entregar

```powershell
python -m unittest discover -s tests -v
python -m compileall -q app tests iniciar_afinador.py
```

Además, se debe probar en Windows con NVDA: recorrido con Tab y Mayús+Tab,
anuncios de cambio de cuerda, inicio/parada de escucha, WASAPI y reproducción
de referencias.

# Auditoría de patrones de EPUB TTS v4

Esta revisión compara el afinador con el código fuente local de EPUB TTS v4,
especialmente `app/interfaz/ui_recursos.py`, `app/motor/reproductor_sonidos.py`
y `app/interfaz/ventana_principal.py`.

## Patrones incorporados

- **Recursos visuales seguros**: los botones conservan siempre texto; los iconos
  se obtienen primero de `recursos/iconos/*.png` y después de `wx.ArtProvider`.
  `SetName()` deja un nombre explícito para NVDA salvo cuando un botón cambia de
  texto dinámicamente, como iniciar/detener escucha.
- **Pestañas y teclado**: `Ctrl+1`, `Ctrl+2` y `Ctrl+3` cambian explícitamente a
  Afinar, Afinaciones especiales y Audio y ajustes. Las flechas no fuerzan el
  foco al cambiar de pestaña. Tab y Mayús+Tab permanecen circulares dentro de la
  pestaña activa.
- **Ayuda local**: `F1` abre `ayuda.html` con el navegador predeterminado. La
  ayuda describe los atajos, la lira, los maqamat y los retoques por cuerda.
- **Ayudas breves**: los controles con una decisión no evidente usan
  `SetHelpText()`; los `SpinCtrlDouble` mantienen además sus anuncios dedicados
  de foco porque wx no los expone con fiabilidad en todos los lectores.
- **Diálogos**: guardar una afinación usa un diálogo nativo con nombre claro;
  las acciones de reemplazo piden confirmación antes de sobrescribir.

## Patrones deliberadamente no trasladados

- Gestión de biblioteca, EPUB/PDF, voces, proveedores de nube, actualizaciones
  automáticas, cuotas y copias de seguridad: no corresponden al afinador.
- Inicio maximizado: EPUB TTS lo necesita por sus bibliotecas y listas; el
  afinador conserva una ventana normal y ampliable.
- Efectos WAV de interfaz: la infraestructura de EPUB TTS es adecuada, pero el
  afinador no añade sonidos de relleno hasta contar con sonidos musicales que
  tengan sentido. El pitido de afinación y los tonos de referencia ya existen y
  no dependen de archivos externos.

## Reglas para cambios futuros

1. Nunca capturar flechas globalmente: son necesarias en cuadros combinados,
   controles numéricos y lectores de pantalla.
2. Un icono no puede ser la única etiqueta de un botón.
3. Un diálogo debe abrir con un foco predecible y cerrar sin dejar el foco en
   una pestaña oculta.
4. Todo atajo nuevo debe aparecer en `README.md` y `ayuda.html`.
5. Antes de añadir una función, comprobar que aporta algo a afinar; no trasladar
   características solo porque existan en EPUB TTS.

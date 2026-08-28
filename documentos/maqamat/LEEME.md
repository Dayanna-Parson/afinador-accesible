# Maqamat en AfinadorAccesible

Esta carpeta reúne la parte musical y técnica de las afinaciones árabes del
afinador. La escribo pensando en tres lecturas distintas: quien quiere
aprender, quien quiere comprobar una afinación, y quien vaya a mantener el
código más adelante (incluida yo misma, dentro de un año).

## Por dónde empezar

1. [Guía para explorar los maqamat](GUIA_PARA_EXPLORAR.md): conceptos básicos,
   límites de la lira y cómo usarlo en la app.
2. [Catálogo y datos de la aplicación](CATALOGO_Y_DATOS.md): los 25 maqamat,
   sus familias, tónicas y los grados que uso para validarlos.
3. [Fuentes y metodología](FUENTES_Y_METODOLOGIA.md): de dónde salen los
   datos, su licencia, y cómo convierto una escala en una afinación de lira.
4. [Guía de revisión](GUIA_DE_REVISION.md): qué comprobar antes de tocar un
   dato de maqam.
5. [Ideas para artículos y audios](IDEAS_PARA_WEB.md): punto de partida para
   contar todo esto en tiflotutos.com.

## Dónde está la fuente de verdad del programa

La app no lee estos documentos al arrancar. Los datos que de verdad usa están
en `app/afinaciones_maqam_lira.py`:

- `AFINACIONES_LIRA_MAQAM_24EDO`: los retoques que la app aplica a cada
  cuerda de la lira.
- `FAMILIAS_MAQAM_LIRA`: el orden del selector en la interfaz.
- `REFERENCIAS_GRADOS_MAQAM_24EDO`: la tónica y los grados contra los que
  pruebo cada adaptación.

`tests/test_maqamat.py` verifica esos datos cada vez que corro las pruebas.
Estos documentos explican el porqué; el módulo Python y sus tests son los que
deciden el comportamiento real de la aplicación.

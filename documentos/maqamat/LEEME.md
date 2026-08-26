# Maqamat en AfinadorAccesible

Esta carpeta reúne la parte musical y técnica de las afinaciones árabes del
afinador. Está pensada para tres públicos a la vez: quien quiere aprender,
quien desea comprobar una afinación y quien vaya a mantener el código.

## Por dónde empezar

1. [Guía para explorar los maqamat](GUIA_PARA_EXPLORAR.md): conceptos básicos,
   límites de la lira y modo de uso de la aplicación.
2. [Catálogo y datos de la aplicación](CATALOGO_Y_DATOS.md): los 25 maqamat,
   sus familias, tónicas y grados usados para validarlos.
3. [Fuentes y metodología](FUENTES_Y_METODOLOGIA.md): procedencia de los datos,
   licencia y cómo se transforma una escala en una afinación de lira.
4. [Guía de revisión](GUIA_DE_REVISION.md): qué revisar antes de cambiar un dato.
5. [Ideas para artículos y audios](IDEAS_PARA_WEB.md): punto de partida para
   explicar este universo musical en la web de Dayanna.

## Dónde está la fuente de verdad del programa

El código que se ejecuta no lee estos documentos. Los datos operativos están
en `app/afinaciones_maqam_lira.py`:

- `AFINACIONES_LIRA_MAQAM_24EDO`: retoques que la app pide realizar en cada
  cuerda de la lira.
- `FAMILIAS_MAQAM_LIRA`: orden del selector de la interfaz.
- `REFERENCIAS_GRADOS_MAQAM_24EDO`: tónica y grados contra los que se prueban
  las adaptaciones.

`tests/test_maqamat.py` verifica esos datos en cada ejecución de las pruebas.
Los documentos explican el porqué; el archivo Python y sus tests determinan el
comportamiento exacto de la aplicación.

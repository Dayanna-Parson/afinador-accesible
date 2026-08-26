# Pruebas manuales antes de una versión estable

Estas comprobaciones requieren una persona usuaria y no pueden sustituirse por pruebas automáticas.

1. Con NVDA activo, recorre cada pestaña con Tab y Mayús+Tab. En los extremos, el foco debe llegar al selector de pestañas; nunca debe quedarse atrapado ni caer en un control desactivado.
2. Cambia entre lira, guitarra y ukelele. Comprueba que los controles exclusivos de la lira se omiten al navegar cuando no correspondan.
3. Guarda un perfil, cárgalo, renómbralo y elimínalo. Confirma que la eliminación pide confirmación y que los presets integrados siguen intactos.
4. Exporta perfiles a JSON e impórtalos de nuevo: debe informar de los añadidos y omitir nombres duplicados sin reemplazarlos.
5. Cambia Do–Re–Mi por C–D–E y toca una nota conocida. Verifica que la nota detectada y el anuncio usan el formato elegido.
6. Inicia escucha con el micrófono y con Scarlett. Comprueba dispositivo, canal, WASAPI si corresponde, aviso de señal y detener/reanudar escucha.
7. Prueba con la escala de Windows al 100 %, 125 % y 150 %. Ningún control debe quedar inaccesible: la página debe desplazarse verticalmente.

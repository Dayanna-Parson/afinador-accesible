# Pendiente antes de pasar `review-claude` a `main`

Esta lista existe para no perder de vista lo que falta una vez que ya haya
probado la rama en real (lira, guitarra, ukelele, con auriculares y con la
Scarlett). Nada de esto se hace antes de esa prueba real.

## 1. Empaquetar como app portable

Igual que `crear_portable.py` en Epub TTS Accesible: un ejecutable que se
abre y funciona, sin instalar Python ni dependencias a mano.

- Incluir el motor Rust ya compilado (`motor_rust/`), no solo el respaldo en
  Python puro — quien lo abra no debería notar la diferencia de rendimiento.
- Revisar qué hace falta compilar aparte (el propio `motor_rust`, y si en
  algún momento se añade algo similar a `auxiliar_sapi32.exe` de Epub TTS,
  también tendría que entrar en el paquete).
- Confirmar que el portable arranca con la afinación de fábrica por defecto y
  sin ajustes previos de otra máquina.

## 2. Traducción de la interfaz (i18n)

Mismo patrón que Epub TTS: `gettext`, con `_()` envolviendo cada cadena
visible o hablada, catálogos en `locale/es/` y `locale/en/`, y
`compilar_i18n.py` para generar los `.mo` antes de dar cualquier cambio por
terminado.

- Revisar toda la interfaz nueva de `review-claude` (las tres pestañas, los
  diálogos de perfiles, la ayuda) en busca de cadenas sin envolver.
- Cuidado especial con los nombres de nota y de maqam: son datos, no texto de
  interfaz — no se traducen con `_()`, se traducen con el propio
  `_traducir_notas_texto()` que ya existe para el cifrado americano.

## 3. Envío a Winget

Mismo proceso que ya se siguió con Epub TTS: preparar los manifiestos de
`winget/` (version/installer/locale.yaml) y, cuando el portable esté validado
y estable, enviarlos a `microsoft/winget-pkgs`.

## Recordatorio

No hace falta que lo pidas otra vez: en cuanto digas que ya probaste la rama
de verdad con los tres instrumentos, retomo esta lista en orden.

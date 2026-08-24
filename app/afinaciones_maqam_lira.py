"""Afinaciones estáticas de maqam para la lira Aklot de 16 cuerdas.

Cada entrada es una adaptación a 24-EDO: un cuarto de tono son 50 cents. Los
valores indican cuartos de tono respecto a la afinación de fábrica de la lira.
La fuente musical de los siete grados es la tabla de maqamat de Maqamusic;
esta tabla de cuerdas es una adaptación independiente al orden físico
Sol–La–Si–Do–Re–Mi–Fa de la lira, repetido por octavas.

Referencia consultable: https://github.com/riadassoum/Maqamusic/blob/main/globalPlugins/maqamKeyboard/maqamat.py
Un maqam completo incluye también ajnas y sayr. Estas entradas describen solo
la afinación fija que una lira puede mantener en un momento dado.
"""

import math

# ANCLAJE_INICIO: AFINACIONES_LIRA_MAQAM_24EDO
AFINACIONES_LIRA_MAQAM_24EDO = {
    "Diatónica de fábrica (notas de Do mayor; comienza en Sol grave)": {},
    "Maqam Rast (sobre Sol)": {
        "Cuerda 3 (Si)": -1, "Cuerda 7 (Fa)": 1, "Cuerda 10 (Si)": -1, "Cuerda 14 (Fa)": 1,
    },
    "Maqam Bayati (sobre Re)": {
        "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -1, "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -1,
    },
    "Maqam Hijaz (sobre Re)": {
        "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -2, "Cuerda 7 (Fa)": 2,
        "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -2, "Cuerda 14 (Fa)": 2,
    },
    "Maqam Rast (sobre Do)": {
        "Cuerda 3 (Si)": -1, "Cuerda 6 (Mi)": -1, "Cuerda 10 (Si)": -1, "Cuerda 13 (Mi)": -1,
    },
    "Maqam Saba (sobre Re)": {
        "Cuerda 1 (Sol)": -2, "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -1,
        "Cuerda 8 (Sol)": -2, "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -1, "Cuerda 15 (Sol)": -2,
    },
    "Maqam Kurd (sobre Re)": {
        "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -2, "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -2,
    },
    "Maqam Nahawand (sobre Do)": {
        "Cuerda 2 (La)": -2, "Cuerda 6 (Mi)": -2, "Cuerda 9 (La)": -2,
        "Cuerda 13 (Mi)": -2, "Cuerda 16 (La)": -2,
    },
    "Maqam Ajam (sobre Si bemol)": {
        "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -2, "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -2,
    },
    "Maqam Sikah (sobre Mi medio bemol)": {
        "Cuerda 3 (Si)": -1, "Cuerda 6 (Mi)": -1, "Cuerda 10 (Si)": -1, "Cuerda 13 (Mi)": -1,
    },
    "Maqam Suznak (sobre Do)": {
        "Cuerda 2 (La)": -2, "Cuerda 6 (Mi)": -1, "Cuerda 9 (La)": -2,
        "Cuerda 13 (Mi)": -1, "Cuerda 16 (La)": -2,
    },
    "Maqam Nikriz (sobre Do)": {
        "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -2, "Cuerda 7 (Fa)": 2,
        "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -2, "Cuerda 14 (Fa)": 2,
    },
    "Maqam Athar Kurd (sobre Do)": {
        "Cuerda 2 (La)": -2, "Cuerda 5 (Re)": -2, "Cuerda 6 (Mi)": -2, "Cuerda 7 (Fa)": 2,
        "Cuerda 9 (La)": -2, "Cuerda 12 (Re)": -2, "Cuerda 13 (Mi)": -2,
        "Cuerda 14 (Fa)": 2, "Cuerda 16 (La)": -2,
    },
    "Maqam Hijazkar (sobre Do)": {
        "Cuerda 2 (La)": -2, "Cuerda 5 (Re)": -2, "Cuerda 9 (La)": -2,
        "Cuerda 12 (Re)": -2, "Cuerda 16 (La)": -2,
    },
    "Maqam Bayati Shuri (sobre Re)": {
        "Cuerda 2 (La)": -2, "Cuerda 6 (Mi)": -1, "Cuerda 9 (La)": -2,
        "Cuerda 13 (Mi)": -1, "Cuerda 16 (La)": -2,
    },
    "Maqam Farahfaza (sobre Sol)": {
        "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -2, "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -2,
    },
    "Maqam Mahur (sobre Do)": {"Cuerda 6 (Mi)": -1, "Cuerda 13 (Mi)": -1},
    "Maqam Awj Ara (sobre Si medio bemol)": {
        "Cuerda 2 (La)": -1, "Cuerda 3 (Si)": -1, "Cuerda 6 (Mi)": -1, "Cuerda 7 (Fa)": 1,
        "Cuerda 9 (La)": -1, "Cuerda 10 (Si)": -1, "Cuerda 13 (Mi)": -1,
        "Cuerda 14 (Fa)": 1, "Cuerda 16 (La)": -1,
    },
    "Maqam Shawq Afza (sobre Do)": {"Cuerda 2 (La)": -2, "Cuerda 9 (La)": -2, "Cuerda 16 (La)": -2},
    "Maqam Lami (sobre Re)": {
        "Cuerda 2 (La)": -2, "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -2, "Cuerda 9 (La)": -2,
        "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -2, "Cuerda 16 (La)": -2,
    },
    "Maqam Saba Zamzam (sobre Re)": {
        "Cuerda 1 (Sol)": -2, "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -2,
        "Cuerda 8 (Sol)": -2, "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -2, "Cuerda 15 (Sol)": -2,
    },
    "Maqam Bayati Husseini (sobre Re)": {
        "Cuerda 3 (Si)": -1, "Cuerda 6 (Mi)": -1, "Cuerda 10 (Si)": -1, "Cuerda 13 (Mi)": -1,
    },
    "Maqam Nayruz (sobre Do)": {
        "Cuerda 2 (La)": -1, "Cuerda 3 (Si)": -2, "Cuerda 6 (Mi)": -1,
        "Cuerda 9 (La)": -1, "Cuerda 10 (Si)": -2, "Cuerda 13 (Mi)": -1, "Cuerda 16 (La)": -1,
    },
}
# ANCLAJE_FIN: AFINACIONES_LIRA_MAQAM_24EDO


# ANCLAJE_INICIO: REFERENCIAS_GRADOS_MAQAM_24EDO
# Datos de control usados solo en las pruebas. Permiten comprobar que cada adaptación
# estática conserva los siete grados de la fuente, sin que la aplicación los calcule
# dinámicamente al arrancar.
REFERENCIAS_GRADOS_MAQAM_24EDO = {
    "Maqam Rast (sobre Sol)": (7, 0, (0, 200, 350, 500, 700, 900, 1050)),
    "Maqam Bayati (sobre Re)": (2, 0, (0, 150, 300, 500, 700, 800, 1000)),
    "Maqam Hijaz (sobre Re)": (2, 0, (0, 100, 400, 500, 700, 800, 1000)),
    "Maqam Rast (sobre Do)": (0, 0, (0, 200, 350, 500, 700, 900, 1050)),
    "Maqam Saba (sobre Re)": (2, 0, (0, 150, 300, 400, 700, 800, 1000)),
    "Maqam Kurd (sobre Re)": (2, 0, (0, 100, 300, 500, 700, 800, 1000)),
    "Maqam Nahawand (sobre Do)": (0, 0, (0, 200, 300, 500, 700, 800, 1100)),
    "Maqam Ajam (sobre Si bemol)": (10, 0, (0, 200, 400, 500, 700, 900, 1100)),
    "Maqam Sikah (sobre Mi medio bemol)": (4, -50, (0, 150, 350, 550, 700, 850, 1050)),
    "Maqam Suznak (sobre Do)": (0, 0, (0, 200, 350, 500, 700, 800, 1100)),
    "Maqam Nikriz (sobre Do)": (0, 0, (0, 200, 300, 600, 700, 900, 1000)),
    "Maqam Athar Kurd (sobre Do)": (0, 0, (0, 100, 300, 600, 700, 800, 1100)),
    "Maqam Hijazkar (sobre Do)": (0, 0, (0, 100, 400, 500, 700, 800, 1100)),
    "Maqam Bayati Shuri (sobre Re)": (2, 0, (0, 150, 300, 500, 600, 900, 1000)),
    "Maqam Farahfaza (sobre Sol)": (7, 0, (0, 200, 300, 500, 700, 800, 1000)),
    "Maqam Mahur (sobre Do)": (0, 0, (0, 200, 350, 500, 700, 900, 1100)),
    "Maqam Awj Ara (sobre Si medio bemol)": (11, -50, (0, 150, 350, 500, 700, 850, 1000)),
    "Maqam Shawq Afza (sobre Do)": (0, 0, (0, 200, 400, 500, 700, 800, 1100)),
    "Maqam Lami (sobre Re)": (2, 0, (0, 100, 300, 500, 600, 800, 1000)),
    "Maqam Saba Zamzam (sobre Re)": (2, 0, (0, 100, 300, 400, 700, 800, 1000)),
    "Maqam Bayati Husseini (sobre Re)": (2, 0, (0, 150, 300, 500, 700, 850, 1000)),
    "Maqam Nayruz (sobre Do)": (0, 0, (0, 200, 350, 500, 700, 850, 1000)),
}

INDICES_DIATONICOS_NATURALES = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}
INDICES_DIATONICOS_TONICAS = {**INDICES_DIATONICOS_NATURALES, 10: 6}


def calcular_retoques_referencia_lira(preset_lira, indice_tonica, cents_tonica, grados):
    """Obtiene los retoques teóricos para que las pruebas validen la tabla estática."""
    frecuencia_tonica = 440.0 * (2 ** (((indice_tonica - 9) / 12) + cents_tonica / 1200))
    indice_diatonico_tonica = INDICES_DIATONICOS_TONICAS[indice_tonica]
    retoques = {}
    for nombre_cuerda, indice_nota, octava in preset_lira:
        frecuencia_base = 440.0 * (2 ** ((indice_nota - 9 + 12 * (octava - 4)) / 12))
        grado = (INDICES_DIATONICOS_NATURALES[indice_nota] - indice_diatonico_tonica) % len(grados)
        candidatas = [
            frecuencia_tonica * (2 ** ((grados[grado] + 1200 * desplazamiento) / 1200))
            for desplazamiento in range(-3, 4)
        ]
        frecuencia_objetivo = min(candidatas, key=lambda frecuencia: abs(math.log2(frecuencia / frecuencia_base)))
        cuartos_tono = int(round(1200 * math.log2(frecuencia_objetivo / frecuencia_base) / 50))
        if cuartos_tono:
            retoques[nombre_cuerda] = cuartos_tono
    return retoques
# ANCLAJE_FIN: REFERENCIAS_GRADOS_MAQAM_24EDO

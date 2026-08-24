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

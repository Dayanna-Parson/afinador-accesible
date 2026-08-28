"""Presets de instrumento y escalas/afinaciones, sin ninguna dependencia de wxPython.

Separado de app/interfaz/ventana_principal.py para que las pruebas de coherencia de
afinaciones (tests/test_maqamat.py) puedan importar estos datos en cualquier máquina,
incluida una sin wxPython instalado — la interfaz gráfica no hace falta para verificar
que una afinación es correcta.
"""

from app.afinaciones_maqam_lira import AFINACIONES_LIRA_MAQAM_24EDO

CROMATICO = "Cromático (cualquier nota)"

NOMBRE_LIRA = "Lira de 16 cuerdas (Aklot)"
NOMBRE_GUITARRA = "Guitarra"
NOMBRE_UKELELE = "Ukelele"
NOMBRE_AFINACION_PERSONALIZADA = "Personalizada (retoques manuales)"

PRESETS_INSTRUMENTO = {
    CROMATICO: None,
    NOMBRE_LIRA: [
        ("Cuerda 1 (Sol)", 7, 3), ("Cuerda 2 (La)", 9, 3), ("Cuerda 3 (Si)", 11, 3), ("Cuerda 4 (Do)", 0, 4),
        ("Cuerda 5 (Re)", 2, 4), ("Cuerda 6 (Mi)", 4, 4), ("Cuerda 7 (Fa)", 5, 4), ("Cuerda 8 (Sol)", 7, 4),
        ("Cuerda 9 (La)", 9, 4), ("Cuerda 10 (Si)", 11, 4), ("Cuerda 11 (Do)", 0, 5), ("Cuerda 12 (Re)", 2, 5),
        ("Cuerda 13 (Mi)", 4, 5), ("Cuerda 14 (Fa)", 5, 5), ("Cuerda 15 (Sol)", 7, 5), ("Cuerda 16 (La)", 9, 5),
    ],
    NOMBRE_UKELELE: [
        ("Cuerda 1 (Sol)", 7, 4), ("Cuerda 2 (Do)", 0, 4),
        ("Cuerda 3 (Mi)", 4, 4), ("Cuerda 4 (La)", 9, 4),
    ],
    NOMBRE_GUITARRA: [
        ("Cuerda 6 (Mi)", 4, 2), ("Cuerda 5 (La)", 9, 2), ("Cuerda 4 (Re)", 2, 3),
        ("Cuerda 3 (Sol)", 7, 3), ("Cuerda 2 (Si)", 11, 3), ("Cuerda 1 (Mi)", 4, 4),
    ],
}

# Guitarra y ukelele: afinaciones alternativas estándar, ampliamente documentadas. En un
# instrumento con trastes el retoque solo desplaza la cuerda al aire entera — los trastes
# siguen fijos en semitonos occidentales, así que estas afinaciones no dan acceso a cuartos
# de tono nuevos en el mástil, solo a otras disposiciones de acordes/resonancias.
ESCALAS_POR_INSTRUMENTO = {
    NOMBRE_LIRA: dict(AFINACIONES_LIRA_MAQAM_24EDO),
    NOMBRE_GUITARRA: {
        "Estándar (Mi La Re Sol Si Mi)": {},
        "Drop D (Re La Re Sol Si Mi)": {"Cuerda 6 (Mi)": -4},
        "Open G (Re Sol Re Sol Si Re)": {"Cuerda 6 (Mi)": -4, "Cuerda 5 (La)": -4, "Cuerda 1 (Mi)": -4},
        "Open D (Re La Re Fa# La Re)": {
            "Cuerda 6 (Mi)": -4, "Cuerda 3 (Sol)": -2, "Cuerda 2 (Si)": -4, "Cuerda 1 (Mi)": -4,
        },
        "DADGAD (Re La Re Sol La Re)": {"Cuerda 6 (Mi)": -4, "Cuerda 2 (Si)": -4, "Cuerda 1 (Mi)": -4},
    },
    NOMBRE_UKELELE: {
        "Estándar (Sol Do Mi La, reentrante)": {},
    },
}

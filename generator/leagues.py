"""Ligen-Register. Reihenfolge = Reihenfolge der Filter-Chips."""

# key, Chip-Label, Badge-Label, Farbe
LEAGUES = [
    ("nfl",     "NFL",           "NFL",     "#4fa3d1"),
    ("cfb",     "College",       "College", "#c98a3a"),
    ("bl1",     "Bundesliga",    "BL",      "#cf4f4f"),
    ("dfb",     "DFB-Pokal",     "Pokal",   "#7d8f4a"),
    ("ucl",     "Champions Lg.", "CL",      "#7a6fd0"),
    ("f1",      "Formel 1",      "F1",      "#b9bcc4"),
    ("cycling", "Radsport",      "Rad",     "#5aa06f"),
    ("atp",     "ATP",           "ATP",     "#3fa8a0"),
    ("wta",     "WTA",           "WTA",     "#b56aa0"),
]

KEYS = [row[0] for row in LEAGUES]
LABELS = [(row[0], row[1]) for row in LEAGUES]

# Typische Dauer in Minuten. Der Renderer leitet daraus "laeuft gerade" ab,
# weil es laut Spec keine Ergebnis- und keine Live-Daten gibt.
DURATION = {
    "nfl": 210,
    "cfb": 210,
    "bl1": 115,
    "dfb": 125,
    "ucl": 115,
    "f1": 120,
    "cycling": 300,
    "atp": 0,
    "wta": 0,
}

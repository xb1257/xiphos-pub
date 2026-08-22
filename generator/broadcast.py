"""Deutsche TV-/Streaming-Zuordnung.

Es gibt keine kostenlose Datenquelle fuer Live-Sport-Rechte in Deutschland
(JustWatch hat kein freies API und deckt nur VOD, TheSportsDB liefert das
TV-Feld fuer DE leer). Deshalb festes Mapping pro Wettbewerb, Stand August 2026.
Einmal pro Sommer pruefen.
"""

# Fallback pro Liga, wenn keine Regel greift.
BY_LEAGUE = {
    "nfl": ["RTL", "Sky"],
    "cfb": ["DAZN"],
    "bl1": ["Sky"],
    "dfb": ["Sky"],
    "ucl": ["DAZN", "Prime"],
    "f1": ["Sky"],
    "cycling": ["Eurosport"],
    "atp": ["Sky"],
    "wta": ["Sky"],
}

# Turnier-Sonderrechte Tennis: Teiltreffer im Turniernamen.
TENNIS_RIGHTS = [
    ("wimbledon", ["Prime"]),
    ("australian open", ["Eurosport"]),
    ("roland", ["Eurosport"]),
    ("french open", ["Eurosport"]),
    ("us open", ["Sky"]),
]

# Radsport-Sonderrechte.
CYCLING_RIGHTS = [
    ("tour de france", ["ARD", "Eurosport"]),
    ("giro", ["Eurosport"]),
    ("vuelta", ["Eurosport"]),
    ("flandern", ["ARD", "Eurosport"]),
    ("roubaix", ["ARD", "Eurosport"]),
    ("sanremo", ["Eurosport"]),
    ("lombardia", ["Eurosport"]),
    ("liege", ["Eurosport"]),
]


def _match(name, table, default):
    low = (name or "").lower()
    for needle, channels in table:
        if needle in low:
            return channels
    return default


def bundesliga(local_dt):
    """Rechte-Split nach Anstosszeit (Q24b), Zyklus 2025/26-2027/28.

    Freitag und Samstag 15:30 (Konferenz) sind der einzige harte Split:
    Sky zeigt die Einzelspiele am Freitag und die Samstagsspiele, DAZN die
    Samstag-Konferenz und den Sonntag. local_dt ist Ortszeit Deutschland.
    """
    wd = local_dt.weekday()  # 0 = Montag
    hhmm = local_dt.hour * 60 + local_dt.minute
    if wd == 4:                      # Freitag
        return ["Sky"]
    if wd == 5:                      # Samstag
        if hhmm == 15 * 60 + 30:     # Konferenz-Slot
            return ["Sky", "DAZN"]
        return ["Sky"]
    if wd == 6:                      # Sonntag
        return ["DAZN"]
    return ["Sky", "DAZN"]           # Nachholtermine unter der Woche


def channels(league, name=None, local_dt=None):
    if league == "bl1" and local_dt is not None:
        return bundesliga(local_dt)
    if league in ("atp", "wta"):
        return _match(name, TENNIS_RIGHTS, BY_LEAGUE[league])
    if league == "cycling":
        return _match(name, CYCLING_RIGHTS, BY_LEAGUE[league])
    return list(BY_LEAGUE.get(league, []))

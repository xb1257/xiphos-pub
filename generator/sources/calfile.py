"""Handgepflegte Kalender aus TOML (Radsport, ATP, WTA, Champions League).

Warum TOML und nicht YAML: tomllib ist seit Python 3.11 Stdlib, pyyaml waere
eine Dependency und damit ein pip install im Workflow (Q40a).

Format je Datei:

    coverage = "2026-12-20"        # bis wann gepflegt, Pflicht
    tz = "Europe/Berlin"           # Standard-Zeitzone der Startzeiten

    [[event]]
    name  = "Vuelta a Espana"
    stage = "Etappe 1 / 21"
    date  = 2026-08-22
    time  = "17:30"                # weglassen = ganztaegig
    until = 2026-09-13             # optional: ganztaegige Serie bis einschliesslich
    meta  = "Grand Tour"
    url   = "https://www.lavuelta.es/"
    tz    = "Europe/Madrid"        # optional, ueberschreibt die Datei-Zeitzone
"""
import datetime
import os
import tomllib
from zoneinfo import ZoneInfo

from .. import broadcast
from ..net import FAIL, OK, PARTIAL

CAL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "calendars")
STALE_DAYS = 14


def fetch(league, win_from, win_to, today, status):
    path = os.path.join(CAL_DIR, league + ".toml")
    try:
        with open(path, "rb") as fh:
            doc = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as err:
        status.set(league, FAIL, "Kalenderdatei defekt: %s" % err)
        return []

    default_tz = ZoneInfo(doc.get("tz", "Europe/Berlin"))
    coverage = doc.get("coverage")
    if isinstance(coverage, str):
        coverage = datetime.date.fromisoformat(coverage)

    events = []
    for entry in doc.get("event", []):
        date = entry.get("date")
        if isinstance(date, str):
            date = datetime.date.fromisoformat(date)
        span_end = entry.get("until") or date
        if isinstance(span_end, str):
            span_end = datetime.date.fromisoformat(span_end)
        if date is None or span_end < win_from or date > win_to:
            continue
        tz = ZoneInfo(entry["tz"]) if entry.get("tz") else default_tz
        row = {
            "lg": league,
            "n": entry.get("name") or "?",
            "s": entry.get("stage") or entry.get("round") or "",
            "m": entry.get("meta") or "",
            "u": entry.get("url"),
            "tv": entry.get("tv") or broadcast.channels(league, name=entry.get("name")),
        }
        if entry.get("home") and entry.get("away"):
            row["home"] = entry["home"]
            row["away"] = entry["away"]
            row.pop("n", None)
        until = entry.get("until")
        if isinstance(until, str):
            until = datetime.date.fromisoformat(until)
        if until and not entry.get("time"):
            # Mehrtaegiges Turnier: eine ganztaegige Row pro Tag (Q26a).
            total = (until - date).days + 1
            for n in range(total):
                cur = date + datetime.timedelta(days=n)
                if not (win_from <= cur <= win_to):
                    continue
                day = dict(row)
                day["allday"] = cur.isoformat()
                day["s"] = (row["s"] + " · " if row["s"] else "") + "Tag %d / %d" % (n + 1, total)
                events.append(day)
            continue

        clock = entry.get("time")
        if clock:
            hh, mm = str(clock)[:5].split(":")
            local = datetime.datetime(date.year, date.month, date.day, int(hh), int(mm), tzinfo=tz)
            row["t"] = local.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if entry.get("dur"):
                row["dur"] = int(entry["dur"])
        else:
            row["allday"] = date.isoformat()
        events.append(row)

    _status(league, coverage, today, status)
    return events


def _status(league, coverage, today, status):
    """Veralterungs-Warnung (Q39): Reichweite sichtbar, .partial kurz vor Ablauf."""
    if coverage is None:
        status.set(league, PARTIAL, "keine Pflege-Reichweite hinterlegt")
        return
    left = (coverage - today).days
    label = coverage.strftime("%d.%m.")
    if left < 0:
        print("WARN %s: Kalender endete am %s, Pflege ueberfaellig" % (league, label))
        status.set(league, FAIL, "Termine nur bis %s gepflegt" % label, coverage=label)
    elif left < STALE_DAYS:
        print("WARN %s: Kalender nur noch %d Tage gepflegt (bis %s)" % (league, left, label))
        status.set(league, PARTIAL, "nur bis %s gepflegt" % label, coverage=label)
    else:
        status.set(league, OK, None, coverage=label)

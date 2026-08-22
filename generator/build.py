#!/usr/bin/env python3
"""Sportcal-Generator: baut data.json fuer die statische Shell.

Aufruf: python3 -m generator.build [--out data.json]

Kein pip install, nur Stdlib. Zeitstempel im Output sind ausschliesslich UTC —
Tagesgrenzen und Uhrzeiten entstehen im Browser in der Gerktezeitzone.
"""
import argparse
import datetime
import json
import os
import sys

from . import leagues
from .net import FAIL, Status
from .sources import calfile, espn, openf1, openligadb

PAD_BEFORE = 1   # Puffer, weil westliche Zeitzonen einen Tag zurueckfallen
PAD_AFTER = 2    # Puffer fuer heute+6 plus oestliche Zeitzonen
CAL_LEAGUES = ("ucl", "cycling", "atp", "wta")


def season_year(today):
    """Fussball-Saison: 2026/27 ist Saison 2026, Umbruch Anfang Juli."""
    return today.year if today.month >= 7 else today.year - 1


def build(today):
    win_from = today - datetime.timedelta(days=PAD_BEFORE)
    win_to = today + datetime.timedelta(days=6 + PAD_AFTER)
    status = Status()
    events = []

    for key in ("nfl", "cfb"):
        events += espn.fetch(key, win_from, win_to, status)
    for key in ("bl1", "dfb"):
        events += openligadb.fetch(key, win_from, win_to, season_year(today), status)
    events += openf1.fetch(win_from, win_to, today.year, status)
    for key in CAL_LEAGUES:
        events += calfile.fetch(key, win_from, win_to, today, status)

    for ev in events:
        if ev.get("allday"):
            ev.pop("dur", None)          # ganztaegig kennt keinen Live-Zustand
        else:
            ev.setdefault("dur", leagues.DURATION.get(ev["lg"], 120))
        for empty in [k for k, v in ev.items() if v in (None, "", [])]:
            del ev[empty]

    events.sort(key=lambda e: (e.get("allday") or e.get("t", ""), e["lg"]))
    return {
        "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "window": {"from": win_from.isoformat(), "to": win_to.isoformat()},
        "sources": status.as_list(leagues.LABELS),
        "events": events,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data.json")
    ap.add_argument("--date", help="Buildtag ueberschreiben, Format YYYY-MM-DD (Tests)")
    args = ap.parse_args(argv)

    today = datetime.date.fromisoformat(args.date) if args.date else \
        datetime.datetime.now(datetime.timezone.utc).date()
    doc = build(today)

    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, args.out)

    dead = [s["key"] for s in doc["sources"] if s["state"] == FAIL]
    print("%d Events, %d Quellen, %d ausgefallen -> %s"
          % (len(doc["events"]), len(doc["sources"]), len(dead), args.out))
    if dead:
        print("WARN ausgefallen: %s" % ", ".join(dead))
    # Ein Teilausfall darf den Build nicht abbrechen: die Shell rendert dann
    # den Cache-Stand und der Footer zeigt .fail.
    return 0


if __name__ == "__main__":
    sys.exit(main())

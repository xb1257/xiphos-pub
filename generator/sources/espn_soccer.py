"""Champions League aus dem ESPN-Soccer-Feed (Q43a).

Der Feed existiert und traegt z.B. ger.1 zuverlaessig, ist fuer 2026/27 aber
leer, solange die Auslosung der Ligaphase aussteht. Deshalb meldet fetch()
ueber den Rueckgabewert, ob wirklich Termine kamen - build.py faellt dann auf
generator/calendars/ucl.toml zurueck.
"""
from datetime import datetime, timezone

from .. import broadcast
from ..net import get_json

PATHS = {"ucl": "uefa.champions"}
URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/%s/scoreboard?dates=%s-%s&limit=200"


def fetch(league, win_from, win_to):
    """Rueckgabe: (events, erreichbar). erreichbar=False heisst Netzfehler,
    eine leere Liste bei erreichbar=True heisst "Feed noch nicht gefuellt"."""
    url = URL % (PATHS[league], win_from.strftime("%Y%m%d"), win_to.strftime("%Y%m%d"))
    data, origin = get_json(url, "espn-soccer-" + league)
    if data is None:
        return [], False

    events = []
    for ev in data.get("events") or []:
        comp = (ev.get("competitions") or [{}])[0]
        home = away = None
        for c in comp.get("competitors") or []:
            name = (c.get("team") or {}).get("shortDisplayName") \
                or (c.get("team") or {}).get("displayName")
            if c.get("homeAway") == "home":
                home = name
            else:
                away = name
        if not home or not away:
            continue
        start = ev.get("date")
        if not start:
            continue
        events.append({
            "lg": league,
            "t": _utc(start),
            "home": home,
            "away": away,
            "m": _round(ev, comp),
            "tv": broadcast.channels(league),
        })
    return events, True


def _utc(raw):
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc) \
        .strftime("%Y-%m-%dT%H:%M:%SZ")


def _round(ev, comp):
    for note in comp.get("notes") or []:
        head = note.get("headline")
        if head:
            return head
    venue = (comp.get("venue") or {}).get("fullName")
    return venue or ""

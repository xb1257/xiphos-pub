"""Bundesliga und DFB-Pokal aus OpenLigaDB. Keyless, liefert matchDateTimeUTC."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from .. import broadcast
from ..net import FAIL, OK, PARTIAL, get_json

URL = "https://api.openligadb.de/getmatchdata/%s/%d"
BERLIN = ZoneInfo("Europe/Berlin")


def fetch(league, win_from, win_to, season, status):
    data, origin = get_json(URL % (league, season), "oldb-" + league)
    if data is None:
        status.set(league, FAIL, "OpenLigaDB nicht erreichbar")
        return []
    status.set(league, OK if origin == "live" else PARTIAL,
               None if origin == "live" else "Cache-Stand")

    events = []
    for m in data:
        raw = m.get("matchDateTimeUTC")
        if not raw:
            continue
        start = _parse(raw)
        if not (win_from <= start.date() <= win_to):
            continue
        local = start.astimezone(BERLIN)
        group = (m.get("group") or {}).get("groupName")
        events.append({
            "lg": league,
            "t": raw,
            "home": _name(m.get("team1")),
            "away": _name(m.get("team2")),
            "m": group or "",
            "tv": broadcast.channels(league, local_dt=local),
        })
    return events


def _parse(raw):
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)


def _name(team):
    """shortName ist bei Amateurvereinen oft Muell ("scst"), dann teamName."""
    team = team or {}
    short = (team.get("shortName") or "").strip()
    full = (team.get("teamName") or "").strip()
    if short and len(short) >= 4 and not short.islower():
        return short
    return full or short or "?"

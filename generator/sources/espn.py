"""NFL und College Football aus der ESPN-Site-API.

Undokumentiert, kein SLA, aber keyless und CORS-offen. Fuer College Football
existiert keine kostenlose Alternative.
"""
from .. import broadcast
from ..net import FAIL, OK, PARTIAL, get_json

PATHS = {
    "nfl": "football/nfl",
    "cfb": "football/college-football",
}
URL = "https://site.api.espn.com/apis/site/v2/sports/%s/scoreboard?dates=%s-%s&limit=200"


def fetch(league, win_from, win_to, status):
    url = URL % (PATHS[league], win_from.strftime("%Y%m%d"), win_to.strftime("%Y%m%d"))
    data, origin = get_json(url, "espn-" + league)
    if data is None:
        status.set(league, FAIL, "ESPN nicht erreichbar")
        return []
    status.set(league, OK if origin == "live" else PARTIAL,
               None if origin == "live" else "Cache-Stand")

    events = []
    for ev in data.get("events") or []:
        comp = (ev.get("competitions") or [{}])[0]
        home = away = None
        for c in comp.get("competitors") or []:
            side = {"name": _team(c), "rank": c.get("curatedRank", {}).get("current")}
            if c.get("homeAway") == "home":
                home = side
            else:
                away = side
        if not home or not away:
            continue
        venue = ((comp.get("venue") or {}).get("fullName")) or None
        note = (ev.get("week") or {}).get("text") or _season_note(ev)
        meta = " · ".join(x for x in (note, venue) if x)
        events.append({
            "lg": league,
            "t": ev.get("date"),
            "home": home["name"],
            "away": away["name"],
            "rank_home": _rank(home),
            "rank_away": _rank(away),
            "m": meta,
            "tv": broadcast.channels(league),
        })
    return events


def _team(competitor):
    team = competitor.get("team") or {}
    return team.get("shortDisplayName") or team.get("displayName") or team.get("name") or "?"


def _rank(side):
    rank = side.get("rank")
    if rank and 0 < rank < 26:
        return rank
    return None


def _season_note(ev):
    season = ev.get("season") or {}
    return season.get("slug", "").replace("-", " ").title() or None

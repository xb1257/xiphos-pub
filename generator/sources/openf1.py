"""Formel 1 aus OpenF1. Jede Session einzeln (Q16a): FP, Quali, Sprint, Rennen."""
from datetime import datetime, timezone

from .. import broadcast
from ..net import FAIL, OK, PARTIAL, get_json

SESSIONS_URL = "https://api.openf1.org/v1/sessions?year=%d"
MEETINGS_URL = "https://api.openf1.org/v1/meetings?year=%d"

# Deutsche Session-Namen. Alles, was nicht hier steht, wird uebernommen wie geliefert.
NAMES = {
    "Practice 1": "1. Freies Training",
    "Practice 2": "2. Freies Training",
    "Practice 3": "3. Freies Training",
    "Qualifying": "Qualifying",
    "Sprint Qualifying": "Sprint-Qualifying",
    "Sprint": "Sprint",
    "Race": "Rennen",
}
# Dauer je Session-Typ in Minuten, fuer die Live-Ableitung im Renderer.
DURATION = {"Race": 120, "Sprint": 45, "Sprint Qualifying": 45, "Qualifying": 60}


def fetch(win_from, win_to, year, status):
    sessions, origin = get_json(SESSIONS_URL % year, "openf1-sessions")
    if sessions is None:
        status.set("f1", FAIL, "OpenF1 nicht erreichbar")
        return []
    meetings, _ = get_json(MEETINGS_URL % year, "openf1-meetings")
    names = {}
    for meet in meetings or []:
        names[meet.get("meeting_key")] = meet.get("meeting_name") or meet.get("location")
    status.set("f1", OK if origin == "live" else PARTIAL,
               None if origin == "live" else "Cache-Stand")

    events = []
    for s in sessions:
        if s.get("is_cancelled"):
            continue
        raw = s.get("date_start")
        if not raw:
            continue
        start = datetime.fromisoformat(raw).astimezone(timezone.utc)
        if not (win_from <= start.date() <= win_to):
            continue
        meeting = names.get(s.get("meeting_key")) or s.get("location") or "Formel 1"
        if "testing" in meeting.lower() or "test" in (s.get("session_name") or "").lower():
            continue
        session = s.get("session_name") or s.get("session_type") or ""
        events.append({
            "lg": "f1",
            "t": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "n": meeting,
            "s": NAMES.get(session, session),
            "m": " · ".join(x for x in (s.get("circuit_short_name"), s.get("country_name")) if x),
            "dur": DURATION.get(session, 60),
            "tv": broadcast.channels("f1"),
        })
    return events

"""Tennis aus dem ESPN-Feed: Turnierzeitraeume statt Handpflege (Q42a).

Der Feed liefert Name, Start, Ende und ein major-Flag fuer Grand Slams, aber
keine Kategorie. Die Auswahl "500 und hoeher" trifft deshalb die Allowlist
unten - Namensmuster, nicht IDs, weil Turniernamen den Sponsor tauschen aber
das Muster ueberleben und die Liste lesbar bleibt.

Pflege: einmal pro Saison gegen den offiziellen Kalender pruefen. Ein Turnier,
das hier fehlt, erscheint nicht; ein Grand Slam erscheint immer.
"""
import datetime

from .. import broadcast
from ..net import FAIL, OK, PARTIAL, get_json

URL = "https://site.api.espn.com/apis/site/v2/sports/tennis/%s/scoreboard?dates=%s-%s&limit=200"

# Muster (klein geschrieben, Teiltreffer) -> Kategorie fuer die Kontextzeile.
ALLOW = {
    "atp": [
        ("bnp paribas open", "Masters 1000"),
        ("miami open", "Masters 1000"),
        ("monte-carlo", "Masters 1000"),
        ("mutua madrid", "Masters 1000"),
        ("internazionali bnl", "Masters 1000"),
        ("national bank open", "Masters 1000"),
        ("cincinnati open", "Masters 1000"),
        ("shanghai masters", "Masters 1000"),
        ("paris masters", "Masters 1000"),
        ("atp finals", "ATP Finals"),
        ("abn amro", "ATP 500"),
        ("dubai duty free", "ATP 500"),
        ("qatar exxonmobil", "ATP 500"),
        ("rio open", "ATP 500"),
        ("abierto mexicano", "ATP 500"),
        ("barcelona open", "ATP 500"),
        ("bmw open", "ATP 500"),
        ("hamburg open", "ATP 500"),
        ("terra wortmann", "ATP 500"),
        ("hsbc championships", "ATP 500"),
        ("mubadala dc open", "ATP 500"),
        ("japan open", "ATP 500"),
        ("china open", "ATP 500"),
        ("erste bank open", "ATP 500"),
        ("swiss indoors", "ATP 500"),
    ],
    "wta": [
        ("qatar total energies", "WTA 1000"),
        ("dubai duty free", "WTA 1000"),
        ("bnp paribas open", "WTA 1000"),
        ("miami open", "WTA 1000"),
        ("mutua madrid", "WTA 1000"),
        ("internazionali bnl", "WTA 1000"),
        ("national bank open", "WTA 1000"),
        ("cincinnati open", "WTA 1000"),
        ("china open", "WTA 1000"),
        ("wuhan open", "WTA 1000"),
        ("wta finals", "WTA Finals"),
        ("brisbane international", "WTA 500"),
        ("mubadala abu dhabi", "WTA 500"),
        ("porsche tennis grand prix", "WTA 500"),
        ("credit one charleston", "WTA 500"),
        ("internationaux de strasbourg", "WTA 500"),
        ("berlin tennis open", "WTA 500"),
        ("bad homburg", "WTA 500"),
        ("eastbourne", "WTA 500"),
        ("mubadala dc open", "WTA 500"),
        ("korea open", "WTA 500"),
        ("toray pan pacific", "WTA 500"),
        ("ningbo open", "WTA 500"),
        ("guadalajara open", "WTA 500"),
    ],
}


# Namen, die ein Allowlist-Muster treffen wuerden, aber nicht gemeint sind.
DENY = ("next gen",)


def _category(league, name):
    low = (name or "").lower()
    if any(bad in low for bad in DENY):
        return None
    for needle, label in ALLOW.get(league, []):
        if needle in low:
            return label
    return None


def fetch(league, win_from, win_to, status):
    url = URL % (league, win_from.strftime("%Y%m%d"), win_to.strftime("%Y%m%d"))
    data, origin = get_json(url, "espn-tennis-" + league)
    if data is None:
        status.set(league, FAIL, "ESPN nicht erreichbar")
        return []
    status.set(league, OK if origin == "live" else PARTIAL,
               None if origin == "live" else "Cache-Stand")

    events = []
    for ev in data.get("events") or []:
        name = ev.get("name") or ""
        category = _category(league, name)
        if category is None and not ev.get("major"):
            continue                       # unter Kategorie 500, bewusst ausgelassen
        if category is None:
            category = "Grand Slam"
        start = _date(ev.get("date"))
        end = _end(ev.get("endDate"), start)
        if start is None or end < win_from or start > win_to:
            continue
        total = (end - start).days + 1
        venue = (ev.get("venue") or {}).get("address", {}).get("city") \
            or (ev.get("venue") or {}).get("fullName")
        meta = " · ".join(x for x in (category, venue) if x)
        tv = broadcast.channels(league, name=name)
        link = _link(ev)
        for n in range(total):
            day = start + datetime.timedelta(days=n)
            if not (win_from <= day <= win_to):
                continue
            events.append({
                "lg": league,
                "allday": day.isoformat(),
                "n": _short(ev, name),
                "s": "Tag %d / %d" % (n + 1, total),
                "m": meta,
                "u": link,
                "tv": tv,
            })
    return events


def _short(ev, name):
    short = ev.get("shortName") or ""
    return short if 0 < len(short) <= len(name) else name


def _date(raw):
    if not raw:
        return None
    return datetime.date.fromisoformat(raw[:10])


def _end(raw, start):
    """endDate ist bei ESPN der Tageswechsel nach dem Finaltag (…T03:59Z)."""
    if not raw:
        return start
    end = datetime.date.fromisoformat(raw[:10])
    hour = int(raw[11:13]) if len(raw) > 12 else 0
    if hour < 12 and end > start:
        end -= datetime.timedelta(days=1)
    return end


def _link(ev):
    for link in ev.get("links") or []:
        if link.get("href") and "web" in (link.get("rel") or []):
            return link["href"]
    return None

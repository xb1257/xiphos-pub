"""HTTP-Zugriff und Quellen-Status. Nur Stdlib."""
import json
import os
import time
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (compatible; sportcal/2.0; +https://github.com/xb1257/xiphos-pub)"
CACHE_DIR = os.environ.get("SPORTCAL_CACHE", os.path.join(os.path.dirname(__file__), "..", ".cache"))

OK, PARTIAL, FAIL = "ok", "partial", "fail"


class Status:
    """Sammelt pro Quelle, wie gut der Build gelaufen ist (Footer .ok/.partial/.fail)."""

    def __init__(self):
        self.entries = {}

    def set(self, key, state, note=None, coverage=None):
        prev = self.entries.get(key, {})
        # Ein einmal gemeldeter Fehler wird nicht wieder auf ok geschoenfaerbt.
        rank = {OK: 0, PARTIAL: 1, FAIL: 2}
        if prev and rank[prev["state"]] > rank[state]:
            state = prev["state"]
            note = prev.get("note") or note
        self.entries[key] = {
            "state": state,
            "note": note,
            "coverage": coverage or prev.get("coverage"),
        }

    def as_list(self, labels):
        out = []
        for key, label in labels:
            e = self.entries.get(key, {"state": FAIL, "note": "nicht geladen", "coverage": None})
            out.append({"key": key, "label": label, **e})
        return out


def _cache_path(name):
    return os.path.join(CACHE_DIR, name + ".json")


def get_json(url, cache_name, timeout=25, retries=2):
    """Holt JSON. Bei Fehler den letzten guten Stand aus dem Cache.

    Rueckgabe: (daten, quelle) mit quelle in {"live", "cache", None}.
    """
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            data = json.loads(raw.decode("utf-8"))
            _write_cache(cache_name, data)
            return data, "live"
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError) as err:
            last_err = err
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    cached = _read_cache(cache_name)
    if cached is not None:
        print("WARN %s nicht erreichbar (%s), nutze Cache" % (url, last_err))
        return cached, "cache"
    print("WARN %s nicht erreichbar (%s), kein Cache" % (url, last_err))
    return None, None


def _write_cache(name, data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(_cache_path(name), "w", encoding="utf-8") as fh:
            json.dump(data, fh)
    except OSError as err:
        print("WARN Cache nicht schreibbar: %s" % err)


def _read_cache(name):
    try:
        with open(_cache_path(name), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None

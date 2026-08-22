# CLAUDE.md

Guidance für Claude Code in diesem Repository.

## Projekt

Sportcal — deutschsprachiger Sport-Terminkalender (Europe/Berlin als Redaktions-,
Gerätezeitzone als Anzeigezone). Zeigt **heute + 6 Folgetage**.

**Spec: `docs/spec-sportcal-v2.md`** — jede Design- und Architekturentscheidung
ist dort mit Q-Nummer begründet. Vor Änderungen lesen.

Zwei Teile:

1. `index.html` — statische Design-Shell plus Renderer (~290 Zeilen JS, Vanilla, ES5-Stil).
   Enthält **kein** Event-Markup. Holt `data.json` und rendert im Browser.
2. `generator/` — Python 3, **ausschliesslich Stdlib** (kein pip install, kein requirements.txt).
   Baut `data.json`. Läuft 2×/Tag in GitHub Actions.

Kein Build, kein Framework, kein CDN, keine externen Assets.

## Befehle

```
python3 -m generator.build --out data.json          # data.json bauen
python3 -m generator.build --out /tmp/d.json --date 2026-08-22   # Buildtag fixieren
node tests/render_harness.js /tmp/d.json            # Renderer ohne Browser pruefen
TZ=America/New_York node tests/render_harness.js /tmp/d.json     # Zeitzonen-Gegenprobe
HIDE=nfl,f1 node tests/render_harness.js /tmp/d.json             # Filter vorbelegen
python3 -m http.server 8000                         # lokal anschauen
```

Es gibt kein Lint- und kein Unit-Test-Setup. `tests/render_harness.js` ist ein
DOM-Stub, der den Renderer aus `index.html` per `eval` laufen lässt — er ist der
einzige Weg, die Zeitzonen- und Tagesgrenzenlogik ohne Browser zu prüfen.
`DEBUG_JS=1` macht verschluckte Render-Fehler sichtbar.

## Datenfluss

```
generator/build.py
  ├─ sources/espn.py        nfl, cfb        ESPN Hidden API, keyless, kein SLA
  ├─ sources/openligadb.py  bl1, dfb        OpenLigaDB, keyless
  ├─ sources/openf1.py      f1              OpenF1, alle Sessions einzeln
  └─ sources/calfile.py     ucl, cycling,   generator/calendars/*.toml, handgepflegt
                            atp, wta
  → data.json  →  index.html rendert clientseitig
```

**Keine API-Keys, keine Secrets.** Wer eine Quelle mit Key vorschlägt, verletzt die Spec.

Quellen-Cache liegt in `.cache/` (lokal) bzw. `actions/cache` (CI). Fällt eine
Quelle aus, wird der letzte gute Stand benutzt und der Footer-Status auf
`partial`/`fail` gesetzt. Ein Teilausfall bricht den Build **nicht** ab.

## Zeit-Regeln (kritischer Pfad)

- `data.json` enthält **ausschliesslich UTC** (`"t": "2026-08-28T18:30:00Z"`).
- Tagesgruppierung *und* Uhrzeiten entstehen im Browser in der Gerätezeitzone.
  Ein Event um 01:30 Berlin liegt in New York am Vortag — deshalb liefert der
  Generator `PAD_BEFORE`/`PAD_AFTER` Tage Puffer um das 7-Tage-Fenster.
- Ganztägige Events (`"allday": "2026-08-25"`) sind Kalendertage und werden
  **nicht** umgerechnet.
- `"dur"` (Minuten) existiert nur, damit der Renderer `.is-live`/`.is-done`
  ableiten kann. Es gibt **keine Ergebnisse und keine Live-Daten** (Spec Q23b).

## data.json Schema

```json
{
  "generated": "2026-08-22T17:52:28Z",
  "window": {"from": "2026-08-21", "to": "2026-08-30"},
  "sources": [{"key":"nfl","label":"NFL","state":"ok","note":null,"coverage":null}],
  "events": [
    {"lg":"bl1","t":"2026-08-28T18:30:00Z","home":"Bayern","away":"Stuttgart",
     "m":"1. Spieltag","tv":["Sky"],"dur":115},
    {"lg":"atp","allday":"2026-08-25","n":"US Open","s":"Tag 1 / 20",
     "m":"Grand Slam · New York","u":"https://www.usopen.org/","tv":["Sky"]}
  ]
}
```

`home`/`away` = Begegnung (Heim zuerst), `n` = Einzelevent, `s` = Zusatz
(Etappe, Session, Turniertag), `m` = Kontextzeile, `u` = Link, `tv` = Sender.
Leere Felder werden vor dem Schreiben entfernt.

## Ligen

Die Liste steht an **zwei** Stellen und muss synchron bleiben:
`generator/leagues.py` (Generator) und das `LEAGUES`-Array in `index.html` (Labels).
Farben stehen **nur** im CSS als `.lg-<key>{--c:…;--a:…}` — nie inline, nie in `data.json`.

Keys: `nfl cfb bl1 dfb ucl f1 cycling atp wta`

## Handgepflegte Kalender

`generator/calendars/*.toml` (TOML, weil `tomllib` Stdlib ist und YAML eine
Dependency wäre). `coverage` ist Pflicht: läuft die Pflege-Reichweite in unter
14 Tagen ab, wird die Quelle `partial`, danach `fail`, jeweils mit Log-Warnung.

- `cycling.toml`, `atp.toml`, `wta.toml` — 1×/Jahr, Kalender stehen im Herbst fest
- `ucl.toml` — **4–5×/Saison**: Auslosung Ligaphase Ende August, Playoffs Dezember,
  Viertelfinale Februar

## Streaming

`generator/broadcast.py`, festes Mapping pro Wettbewerb, Stand August 2026.
Einzige Regel-Ableitung: Bundesliga nach Anstosszeit (Fr + Sa → Sky, Sa-Konferenz
15:30 → Sky + DAZN, So → DAZN). UCL nennt bewusst beide Rechteinhaber.
**Einmal pro Sommer prüfen**, Rechte wechseln in Zyklen (UCL 2027/28: DAZN raus).

## Deploy

`.github/workflows/build.yml` — Cron 03:00 + 15:00 UTC, `workflow_dispatch`,
Push auf `main`. Deploy per **Pages-Artifact**, nicht per Commit: der Bot
schreibt nie ins Repo. Voraussetzung: Settings → Pages → Source = "GitHub Actions".

## Repo-Hygiene

- Kein `Co-Authored-By`-Trailer in Commit-Messages.
- Nie `git worktree prune`; nur gezielt `git worktree remove <pfad>`.
- Wer einen PR/CI-Lauf startet, überwacht ihn selbst bis grün/rot/gemerged.
- Vor der Ausführung eine Todo-Liste; danach nur Status, keine Diffs im Chat.
- Subagenten: Modell bei jedem Dispatch explizit setzen (Skill `agent-budget`).

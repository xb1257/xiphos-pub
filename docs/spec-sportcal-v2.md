# Sportcal v2 — Spec

Bestätigt 2026-08-22. Ergebnis der Grilling-Session (Q1–Q39).

## Ziel

Statische, kostenlose Wochenübersicht der Sporttermine (heute + 6 Folgetage),
Zeiten in der Gerätezeitzone, ein Build pro Halbtag, keine API-Keys.

## Architektur

| Aspekt | Entscheidung | Q |
|---|---|---|
| Modell | `index.html` = Design-Shell + JS-Renderer; `data.json` von GitHub Actions erzeugt | 19a |
| Rendering | clientseitig; Tagesgruppierung UND Uhrzeiten aus UTC-Stempeln in Gerätezeitzone | 19a, Zusatz |
| Generator | Python 3, ausschliesslich Stdlib (`urllib`, `zoneinfo`, `json`) — kein pip install | 3 |
| Deploy | Actions → Pages-Artifact (`actions/deploy-pages`), keine Bot-Commits | 20a |
| Repo | `xiphos-pub`, Single-Purpose, Ausgabe an Root | 13 |
| Cron | 2x/Tag 03:00 + 15:00 UTC, plus `workflow_dispatch` | 21b |
| Fenster | heute + 6 Folgetage, clientseitig aus Gerätedatum; Generator liefert +/-1 Tag Puffer | 4, 19a |
| Offline | localStorage-First rendern, dann `data.json` nachladen; Skeleton nur beim Erstbesuch | 22c |
| Quellenausfall | letzter guter JSON-Stand pro Quelle im Repo-Cache, Footer `.ok`/`.partial`/`.fail` | 17a |
| Keys | keine. Alle Quellen keyless oder YAML | 39-Folge |

## Datenquellen

| Liga | Key | Farbe | Quelle | Auth |
|---|---|---|---|---|
| NFL | `nfl` | `#4fa3d1` | ESPN Hidden API `site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard` | — |
| College FB | `cfb` | `#c98a3a` | ESPN Hidden API `.../football/college-football/scoreboard` | — |
| Bundesliga | `bl1` | `#cf4f4f` | OpenLigaDB `api.openligadb.de/getmatchdata/bl1` | — |
| DFB-Pokal | `dfb` | neu | OpenLigaDB `getmatchdata/dfb` | — |
| Champions Lg. | `ucl` | `#7a6fd0` | ESPN Hidden API `soccer/uefa.champions`, TOML als Fallback (Q43a) | — |
| Formel 1 | `f1` | neu | OpenF1, alle Sessions einzeln (FP1-3, Quali, Sprint, Rennen) | — |
| Radsport | `cycling` | `#5aa06f` | YAML im Repo | — |
| Tennis ATP | `atp` | `#3fa8a0` | ESPN Hidden API `tennis/atp` + Allowlist 500+ (Q42a) | — |
| Tennis WTA | `wta` | `#b56aa0` | ESPN Hidden API `tennis/wta` + Allowlist 500+ (Q42a) | — |

Verworfen: Ergast (tot, 404), football-data.org (Key), ProCyclingStats/FirstCycling
(403 Cloudflare, robots.txt sperrt Agenten), Sofascore (403), TheSportsDB fuer Tennis
(crowd-sourced, lueckenhaft), Scraping generell (Q12 auf spaeter verschoben).

## YAML-Pflege

| Quelle | Rhythmus | Auslöser |
|---|---|---|
| Radsport | 1x/Jahr | Kalender steht im Herbst |
| Tennis | 1x/Saison | nur die Allowlist der Turniere ab Kategorie 500, Termine kommen aus ESPN (Q42a) |
| UCL | nur Notfall | ESPN liefert nach der Auslosung; TOML ist Rueckfallebene (Q43a) |

Veralterungs-Schutz (Q39 a+d):
- Generator setzt Footer-Status einer YAML-Quelle auf `.partial`, wenn ihr
  letztes Event < 14 Tage in der Zukunft liegt, und schreibt eine Warnung ins Actions-Log.
- Footer zeigt dauerhaft die Pflege-Reichweite, z.B. "UCL-Termine bis 20.12. gepflegt".

## Streaming Deutschland

Keine automatisierte Gratis-Quelle existiert (JustWatch kein Free-API und nur VOD,
TheSportsDB `eventstv.php` leer, Senderseiten nur HTML). Deshalb festes Mapping
Wettbewerb → Sender im Repo (Q11a), mit zwei Sonderfällen:

| Wettbewerb | Sender | Regel |
|---|---|---|
| Formel 1 | Sky/WOW | fest; RTL 5 Free-TV-Rennen 2026 als Override |
| Bundesliga | Sky **oder** DAZN | **Regel nach Anstoßzeit** (Q24b): Fr + Sa 15:30 Einzelspiel → Sky; Sa-Konferenz + So → DAZN |
| Champions Lg. | "DAZN · Prime" | beide nennen, Prime-Auswahl ist nicht ableitbar (Q25a) |
| DFB-Pokal | Sky | ARD/ZDF Highlights; RTL-Free-TV-Spiele als Override |
| NFL | RTL · Sky | |
| College FB | DAZN | |
| Radsport | ARD · Eurosport | Tour de France gesichert, Giro/Vuelta unverifiziert |
| Tennis | Eurosport / Prime | AO + French Open Eurosport, Wimbledon Prime exklusiv, US Open unsicher |

Rechte-Stand August 2026. Einmal pro Sommer prüfen. UCL-Zyklus wechselt 2027/28 (DAZN raus).

## Anzeige-Verhalten

- **Keine Ergebnisse, kein Spielstand** (Q23b). Reiner Terminkalender: was, wann, wo läuft.
- `.is-live` clientseitig aus Startzeit + typischer Dauer pro Sportart abgeleitet.
- Gelaufene Events bleiben chronologisch stehen, gedimmt via `.is-done` (Q36a).
- Mehrtägige Events: **jeden Tag eine Row** (Q26a). Radsport-Etappen mit Startzeit,
  Tennis-Turniertage ganztägig ("ATP 500 Wien · Tag 4").
- Ganztages-Rows stehen **oben** in der Tages-Section, Zeit-Spalte gedimmt "ganztägig" (Q28a, Q35b).
- Leere Tage: Platzhalter-Section "keine Termine" (Q38b). Ein nur **filterbedingt** leerer
  Tag muss anders aussehen als ein von Natur aus leerer.
- Header zeigt erkannte Zeitzone via `Intl` plus Build-Stand getrennt (Q29a).

## Design (minimales Redesign, Q30b)

- Dark-Theme bleibt, Basis von warm-braun auf **neutrales Grau** (Q31b) — nur die
  Werte von `--bg --panel --line` in `:root`.
- Heutiger Tag: Label "Heute" + farbige linke Kante in `--amber` (Q32c).
- Ligafarben als **CSS-Klassen** `.lg-<key>{--c:…;--a:…}`, jede Farbe genau einmal
  definiert (Q33a). Das Inline-Duplikat aus v1 entfällt.
- Filterleiste **eingeklappt** mit Zustandstext "3 von 9 Ligen ausgeblendet" plus
  Alle/Keine-Schalter (Q34c+d).
- Sender als **monochromes Label** mit dünnem Rahmen in der `.meta`-Zeile (Q37b).
  Keine Sender-Farben — 9 Ligafarben sind das Farbbudget.
- Ein Breakpoint bei 560 px bleibt.
- localStorage-Key `sportcal.hidden` bleibt, Objekt der **ausgeblendeten** Ligen.

## Risiken

- ESPN Hidden API ist undokumentiert und hat kein SLA. Für College Football
  existiert kein kostenloser Fallback.
- Radsport braucht Handpflege (Etappentermine, Startzeiten nur als Richtwert).
- Tennis: ESPN liefert keine Turnierkategorie, die 500+-Auswahl ist eine
  Namens-Allowlist in `generator/sources/espn_tennis.py` und einmal pro Saison zu pruefen.
- UCL haengt am ESPN-Feed, der bis zur Auslosung leer ist. Bleibt er leer, greift die TOML.
- Zeitzonen-Logik ist der kritische Pfad: Tagesgrenzen fallen im Browser,
  ein Event um 01:30 Berlin liegt in New York am Vortag.

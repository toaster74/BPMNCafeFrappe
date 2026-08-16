# AGENTS.md

## Pflicht: Dokumentation aktuell halten

Bei **jeder neuen Funktion oder Verhaltensänderung** dieses Moduls sind die
folgenden Dokumente zu aktualisieren, bevor die Arbeit als abgeschlossen gilt:

- `docs/ANFORDERUNGEN.md` – Datenmodell, Regeln, Generator, API, Architektur.
- `docs/BENUTZERDOKUMENTATION.md` – Benutzerabläufe und Funktionsweise.

Konkret betrifft das insbesondere:

- neue oder geänderte **DocType-Felder** (Tabellen in beiden Docs),
- neue oder geänderte **Plausibilitätsregeln**,
- Änderungen am **BPMN-Generator** (Elemente, Flüsse, Swimlanes),
- Änderungen an der **Client-Logik** oder **API**,
- neue **Doctypes** bzw. Unterpakete (dann auch `pyproject.toml` package-data!).

## Verifikation vor Abschluss

- Python: Generator-/Validierungs-Tests per `python3` ausführen (siehe Vorgehen
  im Verlauf), `bpmn_workflow/bpmn/__init__.py` und Doctype-Controller prüfen.
- JS: `node --check bpmn_workflow/public/js/bpmn_workflow.js`.
- JSON-Dateien der Doctypes auf gültiges JSON prüfen.
- Nach dem Deploy auf dem Server: `bench migrate` und `bench build`.
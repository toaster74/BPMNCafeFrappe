# bpmn_workflow

Frappe-App zum Erstellen, Bearbeiten und Auflisten von Workflows, die als
**BPMN 2.0-Modelle** gespeichert und mit **bpmn-js** (Open Source, MIT) grafisch
dargestellt werden.

## Dokumentation

- **`docs/ANFORDERUNGEN.md`** – vollständige Modulbeschreibung (Datenmodell,
  Regeln, Generator, API, Architektur) zur Rekonstruktion.
- **`docs/BENUTZERDOKUMENTATION.md`** – Schritt-für-Schritt-Anleitung zum
  Anlegen eines Workflows.

## Funktionsumfang (Überblick)

- **Doctype `BPMN Workflow`** – Workflow mit Metadaten (Autor, Prozess-Owner,
  Designer, Inkrafttreten).
- **Kindtabelle `BPMN Workflow Step`** – Schritte mit Typ, Folgeschritten,
  Bedingung, Rolle, Tool.
- **Doctype `BPMN Rolle`** – Rollen, jeweils als Swimlane im Diagramm.
- Automatische Generierung eines **BPMN 2.0-XML** (semantisches Modell) aus den
  Schritten; Layout wird clientseitig von **bpmn-auto-layout** berechnet.
- Grafische Anzeige im Formular (bpmn-js), inkl. Swimlanes und
  Abzweigungen (exklusive Gateways mit beschrifteten Bedingungen).
- **PDF-Export** des gerenderten Diagramms (A4, Querformat).
- **GraphML-Export** für yEd (inkl. Formen, Bedingungen und Layout).
- Plausibilitätsprüfung der Schritt-Eingaben (Client + Server).

## Installation

Voraussetzung: ein laufendes Frappe-Bench (getestet mit v15).

```bash
# 1. App ins Bench holen (lokaler Pfad)
bench get-app /pfad/zu/diesem/repo

# 2. Installieren
bench --site dein-site install-app bpmn_workflow

# 3. Nach jedem Pull / Code-Änderungen:
bench --site dein-site migrate
bench build
```

## Nutzung (Kurzfassung)

1. **BPMN Rolle** anlegen (Rollenname + Beschreibung).
2. **BPMN Workflow** neu anlegen: Name, Verantwortliche, Inkrafttreten.
3. **Workflow Steps** eintragen: Step Name, Typ (`Funktion`/`Abzweigung`),
   Next Step(s) (kommagetrennt), bei Abzweigung eine Bedingung, Rolle + Tool.
4. **Generate BPMN Model** klicken – das Diagramm erscheint unter
   **BPMN Model → BPMN Preview**, das XML darunter.
5. Speichern; optional **PDF Export** oder **GraphML Export** (für yEd).

Ausführlich: `docs/BENUTZERDOKUMENTATION.md`.

## Technische Details

- **BPMN-Erzeugung**: `bpmn_workflow/bpmn/__init__.py` erzeugt aus den flachen
  Schritt-Daten ein semantisches BPMN 2.0-Modell (ohne BPMNDI). Jeder
  `Funktion`-Schritt wird ein `userTask` (mit `documentation` Rolle/Tool),
  zusammengehörige `Abzweigung`-Zeilen werden ein `exclusiveGateway` mit
  bedingten Sequenzflüssen.
- **Visualisierung**: `bpmn_workflow/public/js/bpmn_workflow.js` lädt
  bpmn-auto-layout + bpmn-js (Viewer) und rendert das XML im Formular.
- **Vendored Libraries**: siehe `bpmn_workflow/public/VENDORED_LICENSES.md`.

## Aufbau

```
bpmn_workflow/
├── hooks.py                          # App-Metadaten, doctype_js, Modul
├── modules.txt                       # Modul „BPMN Workflow“
├── bpmn/                             # BPMN-XML-Generator (Python)
├── bpmn_workflow/                    # Modulordner (Name = Modul)
│   ├── config/                       # Workspace-Metadaten
│   └── doctype/
│       ├── bpmn_workflow/            # Haupt-DocType + Controller
│       ├── bpmn_workflow_step/       # Kind-DocType (Schritt)
│       └── bpmn_rolle/               # DocType Rolle
└── public/
    ├── js/
    │   ├── bpmn_workflow.js          # Client-Logik
    │   ├── bpmn-auto-layout/         # vendored (esbuild-Bundle)
    │   ├── bpmn-js/                  # vendored (Viewer-Bundle)
    │   └── bpmn-pdf/                 # vendored (jsPDF + svg2pdf Bundle)
    ├── css/vendor/                   # bpmn-js CSS (vendored)
    └── VENDORED_LICENSES.md
docs/
├── ANFORDERUNGEN.md                  # Modul-/Anforderungsdokumentation
└── BENUTZERDOKUMENTATION.md          # Benutzeranleitung
```

## Entwicklungshinweis

Neue Funktionen müssen in `docs/ANFORDERUNGEN.md` und
`docs/BENUTZERDOKUMENTATION.md` dokumentiert werden (siehe `AGENTS.md`).
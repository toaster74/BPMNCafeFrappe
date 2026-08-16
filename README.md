# bpmn_workflow

Frappe-App zum Erstellen, Bearbeiten und Auflisten von Workflows, die als
**BPMN 2.0-Modelle** gespeichert und mit **bpmn-js** (Open Source, MIT) grafisch
dargestellt werden.

## Funktionsumfang

- **Doctype `BPMN Workflow`** — ein Workflow mit Name und Beschreibung
- **Kindtabelle `BPMN Workflow Step`** — pro Schritt wird abgefragt:
  - **Step Name**: Bezeichnung des Schritts
  - **Next Step(s)**: welche Schritte danach folgen (kommagetrennt)
  - **Assigned To**: welche Person/User den Schritt ausführt (Link zu `User`)
  - **Tool**: mit welchem Tool der Schritt umgesetzt wird
- Beim Speichern wird automatisch ein **BPMN 2.0-XML** (inkl. Diagramm-Layout/BPMNDI)
  aus den Schritten erzeugt und im Feld `bpmn_xml` abgelegt.
- Das BPMN-Modell wird direkt im Formular mit **bpmn-js** gerendert.
- Standard-Listenansicht für alle Workflows (autoname = Workflow-Name).

## Installation

Voraussetzung: ein laufendes Frappe-Bench (Frappe >= v14, getestet mit v14/v15).

```bash
# 1. App ins Bench holen (lokaler Pfad)
bench get-app /pfad/zu/diesem/repo

# 2. Installieren
bench --site dein-site install-app bpmn_workflow

# 3. Entwicklungsserver neu starten / Assets bauen
bench build
bench --site dein-site migrate
```

## Nutzung

1. Im Workspace-Modul **BPMN Workflow** öffnen.
2. Neuen **BPMN Workflow** anlegen.
3. Unter **Workflow Steps** die Schritte eintragen. Beispiel:

   | Step Name        | Next Step(s)      | Assigned To | Tool     |
   |------------------|-------------------|-------------|----------|
   | Anfrage prüfen   | Angebot erstellen | max@mail.de | ERPNext  |
   | Angebot erstellen| Angebot senden    | anna@mail.de| ERPNext  |
   | Angebot senden   |                   | tom@mail.de | Mail     |

4. **Generate BPMN Model** klicken oder einfach speichern — das BPMN-XML wird
   erzeugt und das Diagramm unter **BPMN Model → BPMN Preview** angezeigt.
5. Im Bearbeiten-Modus der Tabelle die Schritte nach Belieben ändern und erneut
   generieren.

Schritte ohne Vorgänger werden automatisch mit dem **Start-Event** verbunden,
Schritte ohne Nachfolger mit dem **End-Event**. Verzweigungen und Zusammenführungen
(ein Schritt → mehrere, mehrere → ein Schritt) werden unterstützt.

## Technische Details

- **BPMN-Erzeugung**: `bpmn_workflow/bpmn/__init__.py` erzeugt aus den flachen
  Schritt-Daten ein vollständiges BPMN 2.0-XML inklusive BPMNDI (Auto-Layout,
  links-nach-rechts). Jeder Schritt wird als `userTask` mit `documentation`
  (Ausführender / Tool) abgebildet.
- **Visualisierung**: `bpmn_workflow/public/js/bpmn_workflow.js` lädt bpmn-js
  (Viewer) und rendert das XML im Formular.
- **Vendored Libraries**: siehe `bpmn_workflow/public/VENDORED_LICENSES.md`.

## Aufbau

```
code/
├── pyproject.toml / setup.py
├── bpmn_workflow/
│   ├── hooks.py
│   ├── config/            # Desktop-/Docs-Metadaten
│   ├── bpmn/              # BPMN-XML-Generator (Python)
│   ├── doctype/
│   │   ├── bpmn_workflow/         # Haupt-DocType + Controller
│   │   └── bpmn_workflow_step/    # Kind-DocType (Schritt)
│   └── public/
│       ├── js/bpmn_workflow.js    # Client-Logik
│       ├── js/bpmn-js/            # bpmn-js (vendored)
│       └── css/                   # bpmn-js CSS (vendored)
```
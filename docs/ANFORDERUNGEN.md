# BPMN Workflow – Anforderungen & Modulbeschreibung

Dieses Dokument beschreibt das Frappe-Modul **bpmn_workflow** vollständig und
präzise genug, dass es rekonstruiert werden kann. Es dient als verbindliche
Referenz für Funktionsumfang, Datenmodell, Regeln und Architektur.

> **Wichtig:** Bei jeder neuen Funktion **muss** dieses Dokument sowie die
> `BENUTZERDOKUMENTATION.md` aktualisiert werden (vgl. `AGENTS.md`).

---

## 1. Zweck & Überblick

Die App verwaltet **Workflows** als **BPMN 2.0-Modelle**. Der Benutzer definiert
einen Workflow als flache Liste von Schritten (Step-Name, Nachfolger, Rolle,
Bedingung, …). Daraus wird automatisch ein BPMN 2.0-XML erzeugt, das direkt im
Formular mit **bpmn-js** grafisch angezeigt und als **PDF** exportiert werden kann.

**Kernprinzipien:**

- Der Benutzer modelliert **ohne** Diagramm-Editor: rein datengetrieben.
- Das BPMN-XML enthält nur das **semantische Modell** (kein BPMNDI / keine
  Koordinaten). Das Layout wird clientseitig zur Anzeigezeit von der Bibliothek
  **bpmn-auto-layout** berechnet.
- Jede BPMN-**Rolle** wird als eigene **Swimlane (Lane)** dargestellt.

---

## 2. Technische Grundlagen

| Bereich        | Wahl                                                             |
|----------------|------------------------------------------------------------------|
| Framework      | Frappe / ERPNext (getestet mit v15.91.3)                         |
| Sprache Server | Python 3 (>= 3.10)                                               |
| Sprache Client | JavaScript (Browser, keine Build-Pipeline nötig)                 |
| BPMN-Viewer    | bpmn-js (vendored, MIT)                                          |
| Auto-Layout    | bpmn-auto-layout v2.0.0-alpha.2 (vendored, MIT)                  |
| PDF-Export     | jsPDF + svg2pdf.js (vendored, MIT)                               |
| Build-Werkzeug | esbuild (nur zum Erzeugen der vendored Bundles)                  |

Alle fremden Bibliotheken liegen unter `bpmn_workflow/public/` und sind in
`bpmn_workflow/public/VENDORED_LICENSES.md` dokumentiert.

---

## 3. Datenmodell

### 3.1 DocType `BPMN Workflow`

Autoname über `field:workflow_name` (eindeutiger Workflow-Name).

| Feldname             | Typ         | Required | Bedeutung                                     |
|----------------------|-------------|----------|-----------------------------------------------|
| `workflow_name`      | Data        | ja       | Eindeutiger Name des Workflows (Autoname)     |
| `workflow_description` | Small Text| nein     | Kurzbeschreibung                              |
| `autor`              | Link `User` | ja       | Autor des Workflows                           |
| `prozess_owner`      | Link `User` | ja       | Prozess-Owner                                 |
| `workflow_designer`  | Link `User` | ja       | Workflow-Designer                             |
| `inkrafttreten`      | Date        | ja       | Datum des Inkrafttretens                      |
| `steps`              | Table `BPMN Workflow Step` | nein | Die Workflow-Schritte (Kindtabelle)      |
| `generate_bpmn`      | Button      | –        | erzeugt XML zur Vorschau ohne Speichern (`generate_bpmn`) |
| `pdf_export`         | Button      | –        | exportiert das gerenderte Diagramm als PDF (`pdf_export`) |
| `bpmn_preview`       | HTML        | –        | Container `<div id="bpmn-preview-container">` für bpmn-js |
| `bpmn_xml`           | Code (XML)  | –        | generiertes BPMN-XML (read-only, auto-gefüllt) |

Feldreihenfolge:
`workflow_name, workflow_description, autor, prozess_owner, workflow_designer,
inkrafttreten, steps_section, steps, bpmn_section, generate_bpmn, pdf_export,
bpmn_preview, bpmn_xml`.

Berechtigungen: nur **System Manager** (create/read/write/delete).

### 3.2 DocType `BPMN Workflow Step` (Kindtabelle, istable)

| Feldname      | Typ           | Required | Bedeutung                                                          |
|---------------|---------------|----------|--------------------------------------------------------------------|
| `step_name`   | Data          | ja       | Eindeutige Referenz des Schritts; gleicher Name in mehreren Zeilen = eine Abzweigung |
| `step_type`   | Select        | ja       | `Funktion` (Default) oder `Abzweigung`                             |
| `next_step`   | Data          | nein     | Kommagetrennte Namen der Folgeschritte; leer = letzter Schritt     |
| `bedingung`   | Data          | nein     | Bedingung, nur bei `Abzweigung` erlaubt und dann Pflicht           |
| `assigned_to` | Link `BPMN Rolle` | nein | Ausführende Rolle; **bei `Abzweigung` verboten**                   |
| `tool`        | Data          | nein     | Werkzeug zur Umsetzung (in `documentation` des Tasks)              |

### 3.3 DocType `BPMN Rolle`

| Feldname      | Typ         | Required | Bedeutung                          |
|---------------|-------------|----------|------------------------------------|
| `rollenname`  | Data        | ja       | Eindeutiger Rollenname (Autoname)  |
| `beschreibung`| Small Text  | nein     | Beschreibung der Rolle             |

Jede Rolle wird im Diagramm als eigene **Swimlane** dargestellt.

---

## 4. Modellierungs-Regeln (Plausibilität)

Server (`bpmn_workflow.py::_validate_steps`) und Client
(`public/js/bpmn_workflow.js`, `validate`-Event auf der Kindtabelle) prüfen
identische Regeln:

1. **Abzweigung ohne Bedingung** → Fehler: „a condition (Bedingung) is required
   for a gateway (Abzweigung)“.
2. **Abzweigung mit Rolle** → Fehler: „a gateway (Abzweigung) must not have a
   role (Rolle)“.
3. **Funktion mit Bedingung** → Fehler: „a condition (Bedingung) is not allowed
   for a function (Funktion)“.

Die Serverprüfung läuft in `BPMNWorkflow.validate()` (schützt auch die API).
Danach wird `bpmn_xml` neu generiert.

---

## 5. BPMN-Generator

Datei: `bpmn_workflow/bpmn/__init__.py` – Funktion `generate_bpmn_xml(step_records)`.

**Eingabe:** Liste von Dicts
`{name, next_steps (list), step_type, bedingung, assigned_to, tool}`.

**Ausgabe:** BPMN 2.0-XML **ohne BPMNDI** (nur semantisches Modell).

### 5.1 Abbildung der Knoten

| Modellelement                       | BPMN-Element         |
|-------------------------------------|----------------------|
| Einzelner Schritt (`Funktion`)      | `userTask` (id `Task_<slug>`), mit `<documentation>` „Rolle: … \| Tool: …“ |
| Mehrere Zeilen gleichen Namens mit `step_type = Abzweigung` | **ein** `exclusiveGateway` (id `Gateway_<slug>`), Name = Step-Name |
| Startpunkt                          | `startEvent` `StartEvent_1` |
| Endpunkt                            | `endEvent` `EndEvent_1` |
| Übergang                            | `sequenceFlow`; `name` = `bedingung` (nur bei Abzweigungen) |

Ein Name gilt genau dann als Gateway, wenn **mindestens eine Zeile** mit diesem
Namen `step_type == "Abzweigung"` hat.

### 5.2 Flussregeln

- Schritte ohne **Nachfolger** gehen zum `EndEvent_1`.
- Schritte ohne **Vorgänger** werden vom `StartEvent_1` aus verbunden.
- Für Abzweigungen erzeugt **jede Zeile** einen eigenen ausgehenden Fluss mit der
  Bedingung als Fluss-Beschriftung.
- Zeigt eine `next_step` auf einen Namen, der nicht existiert, wird sie **ignoriert**.
- Leerer Workflow → direkter `StartEvent_1 → EndEvent_1`-Fluss.

### 5.3 Swimlanes

- Eine Lane pro Rolle, in Reihenfolge des ersten Auftretens.
- `StartEvent_1` liegt in der Lane des **ersten** Schritts, `EndEvent_1` in der
  Lane des **letzten** Schritts.
- Eine **Abzweigung hat keine eigene Rolle**: sie wird in die Lane der
  **aufrufenden Funktion** gelegt (des Schritts, dessen `next_step` auf die
  Abzweigung zeigt). Gibt es keinen Aufrufer (Abzweigung als Startpunkt), fällt
  sie auf die Rolle **`Unassigned`** zurück. Schritt-Zeilen vom Typ `Funktion`
  ohne Rolle erhalten ebenfalls `Unassigned`.
- Es werden keine Phantom-Lanes erzeugt: eine Lane existiert nur für Rollen, die
  tatsächlich Knoten enthalten.

---

## 6. Client-Logik (`public/js/bpmn_workflow.js`)

Über `hooks.py::doctype_js` wird die Datei automatisch für den DocType
`BPMN Workflow` geladen.

| Funktion | Aufgabe |
|----------|---------|
| `refresh` | lädt BPMN-Assets und rendert das Diagramm |
| `after_save` | rendert nach Speichern neu |
| `generate_bpmn` | ruft die Whitelist-Methode `get_generated_bpmn` auf, setzt `bpmn_xml`, rendert ohne zu speichern |
| `pdf_export` | exportiert das gerenderte Diagramm als PDF; ohne gerendertes Diagramm: Meldung „Generate the BPMN diagram first.“ |
| `load_bpmn_assets` | lädt CSS + bpmn-js + bpmn-auto-layout einmalig (`window.BpmnJS`, `window.BpmnAutoLayout`) |
| `render_bpmn_diagram` | ruft `BpmnAutoLayout.layoutProcess(xml)` → XML mit BPMNDI → `render_viewer` |
| `render_viewer` | erstellt bpmn-js-Viewer, `importXML`, Zoom `fit-viewport`; Viewer wird auf `frm.bpmn_viewer` gespeichert |
| `export_bpmn_pdf` | `viewer.saveSVG()` → `svg_to_canvas` → jsPDF A4 Querformat, Bild zentriert eingebettet |
| `svg_to_canvas` | setzt `width`/`height` aus `viewBox` (falls fehlend), rastert SVG 2× auf Canvas |

**Viewer-Werkzeugleiste** (Zoom & Vollbild): `render_viewer` baut eine
Toolbar oben rechts im Preview-Container mit vier Buttons:

- **Zoom Out (−)** → `canvas.zoom(0.8)`
- **Zoom In (+)** → `canvas.zoom(1.25)`
- **Fit** → `canvas.zoom("fit-viewport", "auto")`
- **Vollbild (⛶)** → Fullscreen-API auf den Preview-Container
  (`container.requestFullscreen()`, Fallback `webkitRequestFullscreen`)

Die CSS-Basis dafür wird einmalig per `inject_viewer_css()` eingefügt
(`<style id="bpmn-viewer-css">`, absolute Toolbar + `.bpmn-canvas`-Layer).
`build_toolbar(frm, container)` erzeugt die Buttons und verdrahtet die Klicks;
`toggle_fullscreen(container)` schaltet Vollbild an/aus. Beim
`fullscreenchange`-Event wird nach 100 ms automatisch
`canvas.zoom("fit-viewport")` aufgerufen, damit das Diagramm nach der
Größenänderung passt. Die Referenzen `active_viewer` / `active_container`
dienen diesem Re-Fit.

**Asserts:** Der PDF-Export setzt voraus, dass ein Diagramm gerendert wurde
(`frm.bpmn_viewer` gesetzt). Ein leerer `bpmn_xml` zeigt im Preview-Container
einen Hinweistext.

---

## 7. Whitelisted-Methoden (API)

`bpmn_workflow.bpmn_workflow.doctype.bpmn_workflow.bpmn_workflow`:

| Methode | Argumente | Rückgabe |
|---------|-----------|----------|
| `get_generated_bpmn` (whitelisted) | `step_records` (list oder JSON-String) | BPMN-XML (semantisch, ohne BPMNDI) |

Client-Aufruf erfolgt mit dem **vollen Modulpfad** (nicht `frm.call`), da es sich
um eine Modul-Funktion handelt, nicht um eine Doc-Methode.

---

## 8. Installation & Update

```bash
# App ins Bench holen
bench get-app /pfad/zu/diesem/repo

# Installieren
bench --site dein-site install-app bpmn_workflow

# Nach Code-Änderungen (jeder Pull) immer ausführen:
bench --site dein-site migrate
bench build
```

Wichtig: `pyproject.toml`-Keys in `[tool.setuptools.package-data]` müssen gültige
Python-Paketnamen sein (keine Wildcards). Jedes neue Unterpaket (z. B. ein neuer
DocType-Ordner) muss dort ergänzt werden.

---

## 9. Projektstruktur

```
bpmn_workflow/
├── __init__.py
├── hooks.py                          # App-Metadaten, doctype_js, Modul
├── modules.txt                       # Modul „BPMN Workflow“
├── patches.txt
├── bpmn/
│   └── __init__.py                   # BPMN-XML-Generator
├── bpmn_workflow/                    # Modulordner (Name = Modul)
│   ├── config/                       # desktop.py (Workspace-Kachel)
│   └── doctype/
│       ├── bpmn_workflow/            # DocType + Controller
│       ├── bpmn_workflow_step/       # Kind-DocType Schritt
│       └── bpmn_rolle/               # DocType Rolle
└── public/
    ├── js/
    │   ├── bpmn_workflow.js          # Client-Logik
    │   ├── bpmn-auto-layout/         # vendored (esbuild-Bundle)
    │   ├── bpmn-js/                  # vendored (Viewer-Bundle)
    │   └── bpmn-pdf/                 # vendored (jsPDF + svg2pdf Bundle)
    ├── css/vendor/                   # bpmn-js CSS (vendored)
    └── VENDORED_LICENSES.md          # Lizenzen + Rebuild-Anleitungen
docs/
├── ANFORDERUNGEN.md                  # dieses Dokument
└── BENUTZERDOKUMENTATION.md          # Benutzeranleitung
```

---

## 10. Dokumentationspflicht

- Bei **jeder neuen Funktion** sind `docs/ANFORDERUNGEN.md` und
  `docs/BENUTZERDOKUMENTATION.md` zu aktualisieren (Feld-Tabellen, Regeln,
  Generatoren, API, Benutzerabläufe).
- Die aktuelle Version des Generators, des Datenmodells und der
  Plausibilitätsregeln in diesem Dokument **immer** dem Code nachführen.
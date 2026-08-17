# Project: BPMN PDF Export Generator
**Erstellt von:** Opabst  
**Datum:** Aug 2026  
**Version:** 0.8.2

---

## 1. Executive Summary

Dieses Projekt bietet eine vollständige PDF-Generierungs-Pipeline für BPMN-Diagramme, die in Frappe/ERPNext verwendet werden. Es verbindet drei Hauptkomponenten:

1. **BPMN XML Layout-Engine** (`bpmn-auto-layout`): Verwendet BPMN-Model (semantisch) → automatisch berechnetes BPMNDI Layout → exportierte XML.
2. **BPMN Web Viewer** (`bpmn-js`): Rendert das gerenderte XML auf einem Web-Canvas (bpmnViewer) mit Zoom/Vollbild/Drag-Pan.
3. **SVG-to-PDF Pipeline**: Wandelt das gerenderte Canvas → SVG → Canvas → jsPDF A4 Querformat, zentriert, eingebettet.

Die Web-Implementierung (bpmn_workflow) läuft auf dem ERPNext-Client (bpmn-viewer.production.min.js), während die Node.js-Implementierung (bpmn-server) als Backend-Export verwendet wird.

---

## 2. Technical Architecture

### Client-Side (Frappe Web Client)
- **Module**: `bpmn_workflow` (public/js/bpmn_workflow.js)
- **Assets**: bpmn-viewer.css, bpmn-viewer.production.min.js (bpmn-js), bpmn-auto-layout.js, bpmn-pdf.js, bpmn-pdf.worker.js
- **Functions**:
  - `render_bpmn_diagram()`: Lädt BPMN-XML, ruft `BpmnAutoLayout.layoutProcess(xml)` → XML mit BPMNDI (BPMNDI.xmi) → `render_viewer()`.
  - `render_viewer()`: Erstellt BPMN-Viewer in `#bpmn-preview-container`, führt `importXML(layouted_xml)`, passt Größe mit `fit-viewport` an.
  - `export_bpmn_pdf()`: `viewer.saveSVG()` → `svg_to_canvas()` (BPMN-pdf-worker) → `jsPDF` → Browser-Download.
  - `graphml_export()`: `viewer.saveXML()` → GraphML (yEd-kompatibel, mit `BPMNShape`/`Bounds` und `EdgeLabel`).
- **Panning**: Manuell implementiert via `canvas.scroll({dx,dy})` (da Bundle kein `moveCanvas`/`zoomScroll` enthält). Drag-Pan (Linksklick), Mausrad-Pan (natürlich), Cursor `grab`/`grabbing`.
- **Fullscreen**: `container.requestFullscreen()` mit Re-Fit nach `fullscreenchange`.

### Server-Side (Node.js)
- **Module**: `bpmn-server` (bpmn-server/index.js)
- **Functions**:
  - `app.use('/bpmn-pdf')`: Endpoint für PDF-Export.
  - `app.get('/bpmn-workflow')`: Serves bpmn_workflow.js.
  - `worker_threads` mit `BPMNPDF`-Worker für PDF-Rendering.
  - `get_generated_bpmn()`: Whitelist-Methode für `get_generated_bpmn`-Call (Client → Whitelist-Methode).
- **Assets**: bpmn-viewer.production.min.js, bpmn-auto-layout.js, bpmn-js-worker.js, bpmn-pdf.worker.js.

### API Methods (Whitelist)
- `get_generated_bpmn(step_records)`: Konvertiert `step_records` (List oder JSON) → BPMN-XML (semantisch, ohne BPMNDI) → Client-Rendern.

---

## 3. Features

| Feature                      | Status | Beschreibung                                      |
|-----------------------------|--------|--------------------------------------------------|
| `render_bpmn_diagram`      | ✓      | BPMN-XML (semantisch) → `layoutProcess(xml)` → Layout (BPMNDI) → `render_viewer`. |
| `fit-viewport`             | ✓      | Automatischer Zoom für Canvas-Große nach Rendern. |
| `drag-pan`                 | ✓      | Manuell per `canvas.scroll({dx,dy})`.            |
| `wheel-pan`                | ✓      | Mausrad scrollt Diagramm (natürlich).             |
| `zoom-in/out`              | ✓      | Buttons −/+.                                      |
| `fullscreen`               | ✓      | Vollbildmodus mit Auto-Fit.                      |
| `PDF-Export`               | ✓      | SVG → Canvas → jsPDF A4 Querformat + Download.   |
| `GraphML-Export`           | ✓      | yEd-kompatibles GraphML mit `BPMNDI` und `EdgeLabel`. |
| `bpmn_xml` Display         | ✓ →    | XML in DocType Feld (read-only).                  |
| `collapsed_xml`            | ✗ →    | XML in zusammengeklapptem Abschnitt.               |

---

## 4. Requirements

- **Frappe**: ≥ 15.x
- **Node.js**: ≥ 18.x
- **npm**: ≥ 8.x
- **bpmn-js**: ≥ 12.2.0
- **bpmn-auto-layout**: v2.3.0+ (Client, semantisches Layout)
- **jsPDF**: ≥ 2.5.x
- **frappe-bpmn-js-worker**: Client/Worker für PDF-Rendering.

---

## 5. Workflow

1. **Benutzer erstellt BPMN-Diagramm DocType** (mit `step_records` und `bpmn_label`).
2. **Rendern**: `render_bpmn_diagram()` → `layoutProcess(xml)` → `render_viewer()`.
3. **Präsentation**: Canvas zeigt Diagramm im DocType (Preview). Benutzer kann zoomen, scrollen, Vollbild.
4. **PDF-Export**: `export_bpmn_pdf()` → jsPDF → Download.
5. **GraphML-Export**: `graphml_export()` → graphml.xml Download.

---

## 6. Testing

- **Smoke Test** (`node --check`): `public/js/bpmn_workflow.js` → Syntax OK.
- **jsdom Smoke Test**: Drag-Pan + Wheel-Pan (Mock canvas) → funktioniert.
- **Integrationstest**: `bench start`, Browser-Test mit BPMN-Export (PDF, GraphML).

---

## 7. Deployment

1. **Clone Repository** (`git clone --depth=1`, `.gitignore`, `bpmn-pdf` Worker).
2. **Install**: `npm install`, `bench --site=Default install-app <app>`.
3. **Deploy**: `bench build` (optional, da JS im Client direkt), `bench migrate`.
4. **Erste Schritte**: In DocType BPMN Workflow → "Generate BPMN Model" → Preview → Export.

---

## 8. Maintenance

- **Updates**: `npm update`, `bpmn-js`/`bpmn-auto-layout` Abhängigkeiten prüfen.
- **Bugs**: Fehlerbericht in Issue Tracker, PRs für Fixes.
- **Sicherheit**: `bpmn-js`/`jsPDF` Sicherheitsupdates.

---

*Generated Aug 2026 by AI Assistant.*

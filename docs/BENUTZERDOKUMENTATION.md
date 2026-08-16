# BPMN Workflow – Benutzerdokumentation

Die App **BPMN Workflow** erstellt **Workflow-Diagramme** (BPMN 2.0) ohne
Diagramm-Editor: Sie beschreiben die Schritte als Tabelle, und die App erzeugt
daraus das Diagramm, das direkt im Formular angezeigt und als PDF exportiert
werden kann.

---

## 1. Ein Workflow in 5 Schritten

1. **BPMN-Rollen** anlegen (wer macht was) – optional, aber empfohlen.
2. **BPMN Workflow** anlegen (Name, Verantwortliche, Datum).
3. **Schritte** eintragen (Funktionen und Abzweigungen).
4. **„Generate BPMN Model“** klicken → Diagramm wird erzeugt und angezeigt.
5. **Speichern**, optional **„PDF Export“** für eine PDF-Datei.

---

## 2. Vorbereitung: Rollen anlegen

Jede Rolle wird im Diagramm als **eigene Zeile (Swimlane)** dargestellt.

1. Modul **BPMN Workflow** öffnen.
2. **BPMN Rolle → Neu**.
3. **Rollenname** eintragen (z. B. „Sachbearbeiter“, „Prüfer“, „Freigabe“).
4. Optional **Beschreibung**.
5. Speichern.

> Fehlt eine Rolle, wird der Schritt trotzdem abgebildet – in der Lane
> **„Unassigned“**.

---

## 3. Workflow anlegen

1. Modul **BPMN Workflow** → **BPMN Workflow → Neu**.
2. **Stammdaten:**
   - **Workflow Name**: eindeutiger Name (wird zum Dateinamen der PDF).
   - **Description**: kurze Beschreibung (optional).
   - **Autor**, **Prozess-Owner**, **Workflow-Designer**: jeweils ein Benutzer.
   - **Inkrafttreten**: Datum, ab dem der Workflow gilt.

---

## 4. Schritte erfassen

Im Bereich **Workflow Steps** pro Zeile:

| Spalte       | Bedeutung                                                            |
|--------------|----------------------------------------------------------------------|
| **Step Name**| Name des Schritts (eindeutige Referenz für Verknüpfungen)             |
| **Typ**      | `Funktion` (ein Arbeitsschritt) oder `Abzweigung` (eine Entscheidung) |
| **Next Step(s)** | Namen der Folgeschritte, **kommagetrennt**. Leer = letzter Schritt. |
| **Bedingung**| Bedingung, nur bei `Abzweigung` (Pflicht)                             |
| **Rolle**    | Ausführende BPMN-Rolle (nur bei `Funktion`)                           |
| **Tool**     | Werkzeug zur Umsetzung, z. B. ERPNext (optional)                      |

### 4.1 Funktion (Typ = Funktion)

Ein normaler Arbeitsschritt. **Rolle** angeben, **Bedingung leer lassen**.

### 4.2 Abzweigung / Entscheidung (Typ = Abzweigung)

Eine **Entscheidung** mit mehreren möglichen Wegen. Dazu:

- **Gleicher Step Name** in **mehreren Zeilen** – jede Zeile ist ein Weg.
- **Bedingung** in jeder Zeile = welche Bedingung auf welchen Weg führt.
- **Rolle bleibt leer.**

Beispiel „Werktagsprüfung“:

| Step Name         | Typ        | Next Step(s) | Bedingung        | Rolle |
|-------------------|------------|--------------|------------------|-------|
| Wareneingang      | Funktion   | Werktagsprüfung |              | Prüfer |
| Werktagsprüfung   | Abzweigung | Montag       | Tag ist Montag   |       |
| Werktagsprüfung   | Abzweigung | Dienstag     | Tag ist Dienstag |       |
| Montag            | Funktion   |              |                  | Bearbeiter |
| Dienstag          | Funktion   |              |                  | Bearbeiter |

Ergebnis: eine Entscheidungs-Raute „Werktagsprüfung“ mit zwei ausgehenden,
beschrifteten Wegen zu „Montag“ und „Dienstag“.

> Die Abzweigung erscheint in der Swimlane der **aufrufenden Funktion**
> (hier: „Prüfer“), da sie selbst keine Rolle hat.

### 4.3 Verzweigen ohne Abzweigung

Mehrere Ziele in **Next Step(s)** (kommagetrennt) erzeugen mehrere ausgehende
Flüsse – z. B. ein Schritt, der mehrere Folgeaktivitäten anstößt.

---

## 5. Plausibilitätsprüfung (automatisch)

Beim Erfassen und Speichern wird geprüft:

- Abzweigung **ohne Bedingung** → Fehlermeldung.
- Abzweigung **mit Rolle** → Fehlermeldung.
- Funktion **mit Bedingung** → Fehlermeldung.

Bei Verstoß wird die Eingabe (bzw. das Speichern) abgebrochen und der Fehler
angezeigt.

---

## 6. Diagramm erzeugen & anzeigen

1. **„Generate BPMN Model“** klicken.
2. Unter **BPMN Model → BPMN Preview** erscheint das Diagramm:
   - **Start** (Kreis) → **Schritte** (Rechtecke) → **Ende** (dicker Kreis).
   - **Rauten** = Abzweigungen, beschriftete Flüsse = Bedingungen.
   - **Swimlanes** = eine Zeile pro Rolle.
   - Das Layout wird automatisch berechnet.
3. Das **BPMN XML** wird darunter als Code angezeigt (nur lesbar).

> Das Diagramm wird auch **nach jedem Speichern** automatisch neu gezeichnet.
> Fehler im Layout erscheinen als Fehlermeldung.

---

## 7. PDF-Export

1. Sicherstellen, dass das Diagramm gerendert wurde (Schritt 6).
2. **„PDF Export“** klicken.
3. Es wird eine PDF (A4, Querformat) mit dem Namen `<Workflow Name>.pdf`
   heruntergeladen.

> Ohne gerendertes Diagramm erscheint: „Generate the BPMN diagram first.“

---

## 8. Häufige Fragen

**Ich sehe keine Bedingung im Diagramm.** – Bedingungen werden nur bei
`Abzweigung` unterstützt und erscheinen als Beschriftung des Flusses.

**Meine Abzweigung erscheint nicht als Raute.** – Sicherstellen, dass der Typ
`Abzweigung` ist und alle Zeilen mit dem Entscheidungsnamen identisch heißen.

**Was passiert, wenn ich einen falschen Next Step eingebe?** – Der Verweis wird
ignoriert; der Schritt gilt dann als letzter Schritt (geht zum Ende).

**Eine Funktion darf doch mehrere Nachfolger haben?** – Ja, einfach kommasepariert
in **Next Step(s)** eintragen.

---

## 9. Dokumentationspflicht

Bei **neuen Funktionen** wird diese Anleitung sowie die
`ANFORDERUNGEN.md` entsprechend erweitert (vgl. `AGENTS.md`).
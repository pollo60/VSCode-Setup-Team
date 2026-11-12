# VS Code Setup – Team

Eine bereinigte Team-Fassung des bestehenden Entwickler-Setups: VS-Code-
Einstellungen, Erweiterungsliste, Agenten, Promptvorlagen und ein
Wiederherstellungsskript. Die Einrichtung verändert VS Code; sie ist keine
eigene App. Das Skript unterstützt zurzeit **macOS**, nicht Windows.

## Einrichten

1. [VS Code](https://code.visualstudio.com/) installieren und einmal öffnen.
   Das Repository klonen und VS Code vor dem Wiederherstellen schließen.
2. Einstellungen in `vscode/settings.json`, Tastenkürzel und
   `inventar/erweiterungen.txt` prüfen. Die Liste ist ein Snapshot, keine
   Empfehlung, alle Erweiterungen blind zu installieren.
3. Im Repository im Terminal zuerst eine Vorschau ausführen:

   ```bash
   bash wiederherstellen.sh --dry-run --extensions
   ```

4. Nach Prüfung gezielt einrichten:

   ```bash
   bash wiederherstellen.sh
   # Optional: alle Erweiterungen aus der Liste installieren:
   bash wiederherstellen.sh --extensions
   # Optional: Agenten bzw. Promptvorlagen für andere Projekte hinzufügen:
   bash wiederherstellen.sh --creative-agents
   bash wiederherstellen.sh --agents --prompts
   ```

   Vorhandene Dateien werden übersprungen, nicht ersetzt; nötige Einstellungen
   bei Bedarf manuell vergleichen und übernehmen. `--extensions` lädt
   Marketplace-Erweiterungen und deren aktuelle Versionen herunter; einzelne
   können fehlen oder inkompatibel sein. Jede Option kann mit `--dry-run`
   vorab geprüft werden.

Die beiden Agenten in `.github/agents/` sind im ausgecheckten Arbeitsbereich
verfügbar. `--creative-agents` installiert sie optional in
`~/.copilot/agents`. Die historischen Rollen `--agents` und `--prompts` sind
ebenfalls optional; die eingebauten Agenten bleiben erhalten.

## Datenschutz und Grenzen

- Die Einstellungen stammen aus dem Entwickler-Setup und sind **keine
  Datenschutz-Härtung**: Unter anderem ist Sitzungssynchronisierung aktiviert
  und einige Bestätigungen sind ausgeschaltet. Vor Übernahme prüfen und an die
  Teamrichtlinien anpassen. Lokaler Agent bedeutet nicht lokales Modell.
- Die persönliche MCP-Konfiguration und lokalen Pfade sind nicht enthalten;
  `vscode/mcp.json` startet leer. Die Copilot-Vorlage enthält MarkItDown:
  `uvx` muss separat installiert werden und kann beim ersten Start Software
  herunterladen. Lokale Server, Modelle, Docker und Google-Zugänge werden
  nicht automatisch eingerichtet.
- Die Adobe-Vorlage ist optional und enthält nur Variablenreferenzen. Ein Abo
  allein garantiert keinen API-Zugang; vor externer Übertragung, Kosten und
  Werkzeugfreigaben bewusst entscheiden. Niemals Schlüssel, Prompts oder
  private Daten in dieses öffentliche Repository aufnehmen.
- Die persönlichen Sicherungen, Inventare, Wissensdaten, importierten
  Fremdquellen und Kreativ-Prototypen des Ausgangsordners sind bewusst nicht
  Teil dieser Veröffentlichung. Der optionale `studio_lokal`-Server wird
  hier nicht mitgeliefert.
- Der [Hardware-Check](studio-lokal/hardware-check.sh) liefert unter macOS
  grobe Ollama-Empfehlungen, installiert aber keine Modelle. Für lokale
  Modelle Ollama und die Erweiterung gesondert einrichten und im Modellwähler
  ausdrücklich ein lokales Modell wählen.

Zum Schutz vor versehentlicher Aufnahme privater Dateien ist `.gitignore` eine
explizite Freigabeliste. Neue Dateien vor dem Freigeben und Committen prüfen.

## Tests

```bash
python3 -m unittest discover -s tests -v
bash -n wiederherstellen.sh studio-lokal/hardware-check.sh
```

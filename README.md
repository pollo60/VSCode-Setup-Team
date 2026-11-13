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

## Optional: iPhone-Zugriff über VS Code Remote Tunnels (macOS)

Nur auf dem eigenen oder ausdrücklich freigegebenen Mac einrichten und
Organisationsrichtlinien beachten. Jeder verwendet sein eigenes GitHub- oder
Microsoft-Konto und einen eigenen, eindeutigen Hostnamen; keine Zugangsdaten
oder den Hostnamen einer anderen Person übernehmen. Remote-Zugriff ermöglicht
Arbeit auf dem Mac und verwendet Microsofts authentifizierten Tunneldienst.
Keine anonyme Freigabe oder Router-Portweiterleitung ist nötig.

1. VS Code installieren, Server-Lizenzbedingungen prüfen und die eigene
   Anmeldung interaktiv abschließen. Für einen ersten Test in VS Code
   **Remote Tunnels: Turn on Remote Tunnel Access** ausführen und vom iPhone
   über <https://insiders.vscode.dev/agents> mit demselben Konto verbinden.
   Verfügbarkeit der Agents-Oberfläche und einzelner Sitzungen kann variieren.
2. Ist noch kein Tunneldienst vorhanden, im Terminal das VS-Code-CLI verwenden:

   ```bash
   TUNNEL="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code-tunnel"
   "$TUNNEL" tunnel user login
   "$TUNNEL" tunnel service install --name MEIN-EINDEUTIGER-HOSTNAME
   "$TUNNEL" tunnel status
   ```

   Den Platzhalter ersetzen und die interaktiven Anweisungen befolgen. Bei
   einem bestehenden Dienst diesen nicht ungeprüft neu installieren. Bei
   anderem Installationspfad `TUNNEL` entsprechend anpassen.
3. Optional den überwachten Start nach macOS-Anmeldung einrichten:

   ```bash
   /usr/bin/python3 tunnel/watchdog.py --install --cli "$TUNNEL"
   ```

   Das installiert einen Benutzer-LaunchAgent und ergänzt, falls nötig, den
   Login-Link für den vorhandenen VS-Code-Dienst. Alle fünf Minuten wird der
   lokale Status geprüft; erst nach drei bestätigten Fehlzuständen und einer
   erneuten Prüfung wird der Dienst neu gestartet, höchstens alle 30 Minuten.
   Unbekannte Statuswerte und Prüffehler führen nicht zu Neustarts. VS Codes
   Dienst selbst startet bei Prozessabbruch automatisch neu.
4. Status mit `"$TUNNEL" tunnel status` prüfen und den iPhone-Test auch über
   Mobilfunk wiederholen. Nach einem echten Neustart erneut anmelden und testen.
   Der Mac muss Strom und Internet haben und darf nicht schlafen; FileVault,
   abgelaufene Anmeldung, Dienststörungen und eine geschlossene VS-Code-
   Agentensitzung können den Zugriff trotzdem verhindern. Dies ist keine
   Garantie für ständige Erreichbarkeit und kein externer Verfügbarkeitstest.
   Warnungen stehen im macOS-Systemlog unter `com.altay.vscode-tunnel-watchdog`.

Zum Entfernen zuerst den Watchdog mit
`launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.altay.vscode-tunnel-watchdog.plist"`
stoppen und dessen plist sowie `~/Library/Application Support/VSCode-Tunnel-Watchdog`
entfernen. Den VS-Code-Dienst bei Bedarf separat mit
`"$TUNNEL" tunnel service uninstall` entfernen; anschließend den von dieser
Einrichtung angelegten Tunnel-LaunchAgent-Link entfernen. Bestehende eigene
LaunchAgents nicht löschen.

## Optional: aktuelle lokale Modellfähigkeiten (macOS)

Das Inventar prüft nur ausdrücklich konfigurierte Ollama-APIs auf
`127.0.0.1`, lädt keine Modelle und scannt kein Netzwerk. Modellnamen,
Größe, vom Server gemeldete Fähigkeiten und Kontextmetadaten werden alle
fünf Minuten lokal aktualisiert. Offline-Server und unvollständige Angaben
werden als solche ausgewiesen. Es werden weder Prompts noch Zugangsdaten
ausgelesen; die Bestandsdatei kann trotzdem sensible Modellnamen enthalten
und gehört nicht in ein öffentliches Repository.

Auf jedem gewünschten Mac einmal im Team-Ordner ausführen:

```bash
/usr/bin/python3 studio-lokal/model-inventory.py --install
```

Die Konfiguration und Ergebnisse liegen benutzerlokal unter
`~/Library/Application Support/VSCode-Model-Inventory/`. Für eine aktuelle
Abfrage in VS Code oder der Codex-App:

```bash
/usr/bin/python3 "$HOME/Library/Application Support/VSCode-Model-Inventory/model-inventory.py" --refresh
```

`--show` zeigt den letzten Stand und meldet veraltete oder nicht erreichbare
Endpunkte mit Fehlerstatus. `--refresh` meldet offline/teilweise ebenfalls
einen Fehlerstatus. Der Zeitstempel gilt für die Prüfung, nicht als Garantie
der zukünftigen Erreichbarkeit. `AGENTS.md` weist unterstützte Agenten in
**diesem Repository** an, vor Aussagen zu lokalen Modellen frisch zu prüfen;
andere Projekte oder Anwendungen übernehmen das nicht automatisch.

Für einen zweiten eigenen Mac muss zuerst eine ausdrücklich erlaubte,
authentifizierte private Verbindung bestehen. Beispielsweise kann eine
separat eingerichtete SSH-Verbindung mit `ssh -N -L
127.0.0.1:11435:127.0.0.1:11434 BENUTZER@HOST` die dortige Ollama-API
lokal weiterleiten. SSH-Zugang, Identität des Hosts und dessen Betrieb müssen
vorher geprüft werden; dieses Setup aktiviert weder SSH noch Portfreigaben
und startet die Verbindung nicht automatisch. In der privaten `config.json`
danach einen weiteren Eintrag ergänzen:

```json
{"endpoints": [{"name": "local", "port": 11434}, {"name": "other-mac", "port": 11435}]}
```

Nur lokale Loopback-Ports werden abgefragt. Für automatische Erfassung auf
beiden Macs das Inventar auf beiden installieren oder eine separat verwaltete
dauerhafte private Weiterleitung verwenden. Die vom Ollama-Server gemeldeten
Fähigkeiten sind keine Leistungsmessung, kein Beweis lokaler Ausführung
und keine Zusage, dass VS Code oder Codex das Modell auswählen kann.

Zum Entfernen den Job mit
`launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.vscode.model-inventory.plist"`
stoppen und die dazugehörige plist sowie den oben genannten Inventarordner
entfernen.

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

#!/bin/bash
set -euo pipefail

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Dieser Hardware-Check unterstützt derzeit nur macOS." >&2
  exit 1
fi

memory_bytes="$(sysctl -n hw.memsize)"
cpu="$(sysctl -n machdep.cpu.brand_string)"
memory_gib=$((memory_bytes / 1073741824))
echo "Prozessor: $cpu"
echo "Arbeitsspeicher: ${memory_gib} GiB (bei Apple Silicon mit GPU geteilt)"
echo "Freier Speicher im Setup-Dateisystem:"
df -h "$(dirname "$0")" | tail -n 1

if (( memory_gib < 16 )); then
  echo "Empfehlung: mit qwen2.5:1.5b beginnen; ein Modell und einen Medienauftrag gleichzeitig."
elif (( memory_gib < 32 )); then
  echo "Empfehlung: mit qwen2.5:3b beginnen; Speicherbedarf und Kontextgröße beobachten."
else
  echo "Empfehlung: qwen2.5:7b als Ausgangspunkt prüfen; verfügbare GPU und Speicher beachten."
fi
echo "Dies sind Richtwerte, keine Zusage für Geschwindigkeit oder Tool-Unterstützung."

for tool in ollama ffmpeg ffprobe; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "$tool: $(command -v "$tool")"
  else
    echo "$tool: nicht im PATH"
  fi
done
if command -v curl >/dev/null 2>&1; then
  if curl --noproxy '*' --silent --show-error --fail --max-time 2 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
    echo "Ollama API: auf 127.0.0.1:11434 erreichbar"
  else
    echo "Ollama API: auf 127.0.0.1:11434 nicht erreichbar"
  fi
fi

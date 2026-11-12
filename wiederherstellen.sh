#!/bin/bash
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
user_dir="${VSCODE_USER_DIR:-$HOME/Library/Application Support/Code/User}"
dry_run=false
install_extensions=false
install_agents=false
install_creative_agents=false
install_prompts=false
copilot_agents_dir="${COPILOT_AGENTS_DIR:-$HOME/.copilot/agents}"
copilot_mcp_file="${COPILOT_MCP_FILE:-$HOME/.copilot/mcp-config.json}"

for arg in "$@"; do
  case "$arg" in
    --dry-run) dry_run=true ;;
    --extensions) install_extensions=true ;;
    --agents) install_agents=true ;;
    --creative-agents) install_creative_agents=true ;;
    --prompts) install_prompts=true ;;
    *) echo "Unbekannte Option: $arg" >&2; exit 2 ;;
  esac
done

if [[ "$install_creative_agents" == true ]]; then
  for file in langzeit-auftrag.agent.md medienproduktion.agent.md; do
    src="$root/.github/agents/$file"
    dst="$copilot_agents_dir/$file"
    [[ -f "$src" ]] || { echo "Agent fehlt: $src" >&2; exit 1; }
    if [[ -e "$dst" || -L "$dst" ]]; then
      echo "Übersprungen, bereits vorhanden: $dst"
    elif [[ "$dry_run" == true ]]; then
      echo "Würde kopieren: $src -> $dst"
    else
      mkdir -p "$copilot_agents_dir"
      cp -n "$src" "$dst"
      echo "Kopiert: $dst"
    fi
  done
fi

if [[ "$install_agents" == true ]]; then
  for file in altay-ask.agent.md altay-umsetzung.agent.md; do
    src="$root/agenten/$file"
    dst="$copilot_agents_dir/$file"
    [[ -f "$src" ]] || { echo "Agent fehlt: $src" >&2; exit 1; }
    if [[ -e "$dst" || -L "$dst" ]]; then
      echo "Übersprungen, bereits vorhanden: $dst"
    elif [[ "$dry_run" == true ]]; then
      echo "Würde kopieren: $src -> $dst"
    else
      mkdir -p "$copilot_agents_dir"
      cp -n "$src" "$dst"
      echo "Kopiert: $dst"
    fi
  done
fi

if [[ "$install_prompts" == true ]]; then
  for file in altay-recherche.prompt.md altay-code-review.prompt.md altay-handoff.prompt.md; do
    src="$root/promptvorlagen/$file"
    dst="$user_dir/prompts/$file"
    [[ -f "$src" ]] || { echo "Promptvorlage fehlt: $src" >&2; exit 1; }
    if [[ -e "$dst" || -L "$dst" ]]; then
      echo "Übersprungen, bereits vorhanden: $dst"
    elif [[ "$dry_run" == true ]]; then
      echo "Würde kopieren: $src -> $dst"
    else
      mkdir -p "$user_dir/prompts"
      cp -n "$src" "$dst"
      echo "Kopiert: $dst"
    fi
  done
fi

if [[ "$install_extensions" == true ]]; then
  if [[ -n "${VSCODE_CLI:-}" ]]; then
    cli="$VSCODE_CLI"
  elif command -v code >/dev/null 2>&1; then
    cli="$(command -v code)"
  elif [[ -x "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" ]]; then
    cli="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
  elif [[ -x "/Applications/Coding/Visual Studio Code.app/Contents/Resources/app/bin/code" ]]; then
    cli="/Applications/Coding/Visual Studio Code.app/Contents/Resources/app/bin/code"
  else
    echo "VS-Code-CLI nicht gefunden. Installiere VS Code und aktiviere den 'code'-Befehl." >&2
    exit 1
  fi
  [[ -x "$cli" ]] || { echo "VS-Code-CLI nicht ausführbar: $cli" >&2; exit 1; }
fi

for file in settings.json keybindings.json mcp.json; do
  src="$root/vscode/$file"
  dst="$user_dir/$file"
  [[ -f "$src" ]] || { echo "Backup fehlt: $src" >&2; exit 1; }
  if [[ -e "$dst" || -L "$dst" ]]; then
    echo "Übersprungen, bereits vorhanden: $dst"
  elif [[ "$dry_run" == true ]]; then
    echo "Würde kopieren: $src -> $dst"
  else
    mkdir -p "$user_dir"
    cp -n "$src" "$dst"
    echo "Kopiert: $dst"
  fi
done

src="$root/vscode/copilot-mcp-config.json"
dst="$copilot_mcp_file"
[[ -f "$src" ]] || { echo "Copilot-MCP-Backup fehlt: $src" >&2; exit 1; }
if [[ -e "$dst" || -L "$dst" ]]; then
  echo "Übersprungen, bereits vorhanden: $dst"
elif [[ "$dry_run" == true ]]; then
  echo "Würde kopieren: $src -> $dst"
else
  mkdir -p "$(dirname "$dst")"
  cp -n "$src" "$dst"
  echo "Kopiert: $dst"
fi

if [[ "$install_extensions" == true ]]; then
  list="$root/inventar/erweiterungen.txt"
  [[ -f "$list" ]] || { echo "Erweiterungsliste fehlt: $list" >&2; exit 1; }
  failed=0
  while IFS= read -r extension || [[ -n "$extension" ]]; do
    [[ -z "$extension" ]] && continue
    if [[ ! "$extension" =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$ ]]; then
      echo "Ungültige Erweiterungs-ID: $extension" >&2
      failed=1
    elif [[ "$dry_run" == true ]]; then
      echo "Würde installieren: $extension"
    elif ! "$cli" --install-extension "$extension"; then
      echo "Installation fehlgeschlagen: $extension" >&2
      failed=1
    fi
  done < "$list"
  [[ "$failed" == 0 ]] || exit 1
fi

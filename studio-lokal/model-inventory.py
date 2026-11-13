#!/usr/bin/env python3
"""Refresh a private inventory of explicitly configured local Ollama endpoints."""

import argparse
import datetime
import http.client
import json
import os
import plistlib
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
DATA = HOME / "Library/Application Support/VSCode-Model-Inventory"
AGENT = HOME / "Library/LaunchAgents/com.vscode.model-inventory.plist"
CONFIG = DATA / "config.json"
SNAPSHOT = DATA / "inventory.json"
INSTALLED = DATA / "model-inventory.py"


def atomic_json(path, value):
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=DATA, prefix=".inventory-")
    try:
        with os.fdopen(fd, "w") as file:
            json.dump(value, file, indent=2)
            file.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def endpoints(config):
    items = config.get("endpoints")
    if not isinstance(items, list) or not items:
        raise ValueError("config endpoints must be a non-empty list")
    names = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each endpoint must be an object")
        name, port = item.get("name"), item.get("port")
        if not isinstance(name, str) or not name.strip() or name in names:
            raise ValueError("endpoint names must be non-empty and unique")
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise ValueError("endpoint port must be an integer from 1 to 65535")
        names.add(name)
    return items


def request(port, path, body=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        headers = {"Content-Type": "application/json"} if body is not None else {}
        connection.request("POST" if body is not None else "GET", path,
                           body=json.dumps(body) if body is not None else None, headers=headers)
        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError(f"Ollama returned HTTP {response.status} for {path}")
        return json.loads(response.read(4 * 1024 * 1024 + 1))
    finally:
        connection.close()


def collect(config):
    result = {"checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "endpoints": []}
    for endpoint in endpoints(config):
        entry = {"name": endpoint["name"], "port": endpoint["port"], "models": []}
        result["endpoints"].append(entry)
        try:
            tags = request(endpoint["port"], "/api/tags")
            if not isinstance(tags, dict):
                raise ValueError("invalid Ollama response")
            models = tags.get("models")
            if not isinstance(models, list):
                raise ValueError("Ollama response has no models list")
            entry["status"] = "online"
            for model in models:
                if not isinstance(model, dict) or not isinstance(model.get("name"), str):
                    raise ValueError("invalid Ollama model entry")
                record = {"name": model["name"], "size_bytes": model.get("size"),
                          "details": model.get("details")}
                entry["models"].append(record)
                try:
                    info = request(endpoint["port"], "/api/show", {"model": model["name"]})
                    if not isinstance(info, dict):
                        raise ValueError("invalid model details")
                    record["capabilities"] = info.get("capabilities")
                    model_info = info.get("model_info", {})
                    if not isinstance(model_info, dict):
                        raise ValueError("invalid model metadata")
                    record["context_lengths"] = {
                        k: v for k, v in model_info.items() if k.endswith(".context_length")
                    }
                except (OSError, ValueError, RuntimeError, http.client.HTTPException) as error:
                    record["error"] = str(error)
                    entry["status"] = "partial"
        except (OSError, ValueError, RuntimeError, http.client.HTTPException) as error:
            entry["status"] = "unavailable"
            entry["error"] = str(error)
    return result


def refresh():
    with CONFIG.open() as file:
        config = json.load(file)
    inventory = collect(config)
    atomic_json(SNAPSHOT, inventory)
    print(json.dumps(inventory, indent=2))
    return 0 if all(item["status"] == "online" for item in inventory["endpoints"]) else 1


def install():
    if sys.platform != "darwin":
        raise RuntimeError("Scheduled installation requires macOS.")
    if any(path.exists() or path.is_symlink() for path in (AGENT, INSTALLED, CONFIG)):
        raise RuntimeError("Inventory configuration or installation already exists; not overwriting.")
    DATA.mkdir(parents=True, exist_ok=True, mode=0o700)
    AGENT.parent.mkdir(parents=True, exist_ok=True)
    with INSTALLED.open("xb") as file:
        file.write(Path(__file__).read_bytes())
    atomic_json(CONFIG, {"endpoints": [{"name": "local", "port": 11434}]})
    config = {"Label": "com.vscode.model-inventory",
              "ProgramArguments": [sys.executable, str(INSTALLED), "--refresh"],
              "StartInterval": 300, "RunAtLoad": True,
              "StandardOutPath": str(DATA / "last-run.log"),
              "StandardErrorPath": str(DATA / "last-run.log")}
    with AGENT.open("xb") as file:
        plistlib.dump(config, file)
    subprocess.run(["/bin/launchctl", "bootstrap", f"gui/{os.getuid()}", str(AGENT)], check=True)
    print(f"Installed. Edit {CONFIG} to add explicitly forwarded loopback ports.")


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--refresh", action="store_true")
    mode.add_argument("--show", action="store_true")
    args = parser.parse_args()
    try:
        if args.install:
            install()
        elif args.refresh:
            return refresh()
        else:
            with SNAPSHOT.open() as file:
                snapshot = json.load(file)
            print(json.dumps(snapshot, indent=2))
            age = datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(
                snapshot["checked_at"]
            )
            if age.total_seconds() < 0 or age.total_seconds() > 900:
                print("Model inventory is stale; run --refresh.", file=sys.stderr)
                return 1
            if any(item.get("status") != "online" for item in snapshot["endpoints"]):
                return 1
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Model inventory error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

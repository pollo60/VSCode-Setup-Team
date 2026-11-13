#!/usr/bin/env python3
"""Opt-in health monitoring for an existing macOS VS Code tunnel service."""

import argparse
import json
import os
import plistlib
import subprocess
import sys
import time
from pathlib import Path

LABEL = "com.altay.vscode-tunnel-watchdog"
SERVICE = "com.visualstudio.code.tunnel"
CLI = "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code-tunnel"
HOME = Path.home()
DATA = HOME / "Library/Application Support/VSCode-Tunnel-Watchdog"
AGENTS = HOME / "Library/LaunchAgents"


def log(message):
    print(message, flush=True)
    subprocess.run(["/usr/bin/logger", "-t", LABEL, message], check=False)


def status(cli):
    result = subprocess.run(
        [cli, "tunnel", "status"], capture_output=True, text=True, timeout=30, check=True
    )
    return json.loads(result.stdout)


def check(cli, now=None):
    now = time.time() if now is None else now
    state_file = DATA / "state.json"
    DATA.mkdir(parents=True, exist_ok=True)
    if state_file.exists():
        with state_file.open() as f:
            state = json.load(f)
    else:
        state = {}
    current = status(cli)
    if current.get("service_installed") is not True:
        log("Tunnel service is not installed; no recovery attempted.")
        return
    tunnel = current.get("tunnel")
    if tunnel is not None and not isinstance(tunnel, dict):
        raise ValueError("Unexpected tunnel status format")
    if tunnel and tunnel.get("tunnel") == "Connected":
        if state.get("failures"):
            log("Tunnel connected again.")
        state.update(failures=0, last_check=now)
    elif tunnel is None or tunnel.get("tunnel") in ("Disconnected", "Connecting"):
        previous = state.get("last_check", 0)
        failures = state.get("failures", 0) + 1 if 0 <= now - previous <= 900 else 1
        state.update(failures=failures, last_check=now)
        log(f"Tunnel not connected: confirmed check {failures}.")
        if failures >= 3 and now - state.get("last_restart", 0) >= 1800:
            latest = status(cli)
            if latest.get("service_installed") is True and (
                latest.get("tunnel") is None
                or isinstance(latest.get("tunnel"), dict)
                and latest["tunnel"].get("tunnel") in ("Disconnected", "Connecting")
            ):
                subprocess.run(
                    ["/bin/launchctl", "kickstart", "-k", f"gui/{os.getuid()}/{SERVICE}"],
                    check=True, timeout=30,
                )
                state.update(failures=0, last_restart=now)
                log("Restarted tunnel service after repeated disconnected checks.")
    else:
        raise ValueError("Unrecognized tunnel connection state")
    with state_file.open("w") as f:
        json.dump(state, f)


def install(cli):
    if sys.platform != "darwin":
        raise RuntimeError("The watchdog requires macOS.")
    if status(cli).get("service_installed") is not True:
        raise RuntimeError("Install and authenticate the VS Code tunnel service first; see README.")
    service_source = HOME / f"{SERVICE}.plist"
    service_link = AGENTS / f"{SERVICE}.plist"
    agent = AGENTS / f"{LABEL}.plist"
    installed = DATA / "watchdog.py"
    if not service_source.is_file():
        raise RuntimeError(f"VS Code service file not found: {service_source}")
    if agent.exists() or agent.is_symlink() or installed.exists():
        raise RuntimeError("Watchdog files already exist; refusing to overwrite them.")
    if service_link.is_symlink():
        if service_link.resolve() != service_source:
            raise RuntimeError("Existing tunnel LaunchAgent points elsewhere; not changing it.")
    elif service_link.exists():
        raise RuntimeError("Existing tunnel LaunchAgent is not the expected link; not changing it.")
    AGENTS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    with installed.open("xb") as f:
        f.write(Path(__file__).read_bytes())
    if not service_link.exists():
        service_link.symlink_to(service_source)
    config = {
        "Label": LABEL,
        "ProgramArguments": [sys.executable, str(installed), "--check", "--cli", cli],
        "StartInterval": 300,
        "RunAtLoad": True,
    }
    with agent.open("xb") as f:
        plistlib.dump(config, f)
    subprocess.run(["/bin/launchctl", "bootstrap", f"gui/{os.getuid()}", str(agent)], check=True)
    log("Watchdog installed. It runs after login and checks every five minutes.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", default=CLI, help="Absolute path to the VS Code tunnel CLI")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.install:
            install(args.cli)
        else:
            check(args.cli)
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as error:
        log(f"Watchdog error; no further recovery attempted: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

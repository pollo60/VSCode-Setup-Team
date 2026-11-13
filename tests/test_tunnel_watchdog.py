import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("watchdog", ROOT / "tunnel/watchdog.py")
watchdog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(watchdog)


class TunnelWatchdogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = patch.object(watchdog, "DATA", Path(self.tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_restarts_only_after_three_disconnected_checks(self):
        disconnected = {"service_installed": True, "tunnel": {"tunnel": "Disconnected"}}
        with patch.object(watchdog, "status", return_value=disconnected), \
             patch.object(watchdog, "log"), patch.object(watchdog.subprocess, "run") as run:
            watchdog.check("cli", 10000)
            watchdog.check("cli", 10300)
            run.assert_not_called()
            watchdog.check("cli", 10600)
            run.assert_called_once()
            watchdog.check("cli", 10900)
            watchdog.check("cli", 11200)
            watchdog.check("cli", 11500)
            run.assert_called_once()

    def test_connection_recovers_before_restart(self):
        disconnected = {"service_installed": True, "tunnel": None}
        connected = {"service_installed": True, "tunnel": {"tunnel": "Connected"}}
        with patch.object(watchdog, "status", side_effect=[disconnected, disconnected, connected]), \
             patch.object(watchdog, "log"), patch.object(watchdog.subprocess, "run") as run:
            for now in (10000, 10300, 10600):
                watchdog.check("cli", now)
            run.assert_not_called()
            self.assertEqual(json.loads((Path(self.tmp.name) / "state.json").read_text())["failures"], 0)

    def test_rechecks_before_restart_and_never_resurrects_uninstalled_service(self):
        disconnected = {"service_installed": True, "tunnel": None}
        connected = {"service_installed": True, "tunnel": {"tunnel": "Connected"}}
        with patch.object(watchdog, "status", side_effect=[disconnected, disconnected, disconnected, connected,
                                                          {"service_installed": False}]), \
             patch.object(watchdog, "log"), patch.object(watchdog.subprocess, "run") as run:
            for now in (10000, 10300, 10600, 10900):
                watchdog.check("cli", now)
            run.assert_not_called()

    def test_unknown_status_does_not_restart(self):
        with patch.object(watchdog, "status", return_value={"service_installed": True,
                                                           "tunnel": {"tunnel": "Unknown"}}), \
             patch.object(watchdog.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                watchdog.check("cli", 10000)
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()

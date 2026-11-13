import importlib.util
import json
import tempfile
import threading
import unittest
import contextlib
import io
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("inventory", ROOT / "studio-lokal/model-inventory.py")
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class ModelInventoryTests(unittest.TestCase):
    def test_http_collection_against_local_ollama_protocol(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.respond({"models": [{"name": "local-model", "size": 7}]})

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if payload != {"model": "local-model"}:
                    self.send_error(400)
                    return
                self.respond({"capabilities": ["tools"], "model_info": {"m.context_length": 8192}})

            def respond(self, value):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(value).encode())

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            result = inventory.collect({"endpoints": [{"name": "test", "port": server.server_port}]})
            self.assertEqual(result["endpoints"][0]["models"][0]["capabilities"], ["tools"])
            self.assertEqual(result["endpoints"][0]["status"], "online")
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_inventory_collects_reported_capabilities_and_offline_endpoint(self):
        config = {"endpoints": [{"name": "mini", "port": 11434}, {"name": "other", "port": 11435}]}

        def fake_request(port, path, body=None):
            if port == 11435:
                raise OSError("offline")
            if path == "/api/tags":
                return {"models": [{"name": "example", "size": 123}]}
            return {"capabilities": ["completion", "vision"],
                    "model_info": {"model.context_length": 4096, "unrelated": 1}}

        with patch.object(inventory, "request", side_effect=fake_request):
            result = inventory.collect(config)
        mini, other = result["endpoints"]
        self.assertEqual(mini["models"][0]["capabilities"], ["completion", "vision"])
        self.assertEqual(mini["models"][0]["context_lengths"], {"model.context_length": 4096})
        self.assertEqual(other["status"], "unavailable")

    def test_missing_model_details_are_not_silently_reported_as_success(self):
        config = {"endpoints": [{"name": "mini", "port": 11434}]}
        with patch.object(inventory, "request", side_effect=[{"models": [{"name": "m"}]},
                                                            OSError("model disappeared")]):
            entry = inventory.collect(config)["endpoints"][0]
        self.assertEqual(entry["status"], "partial")
        self.assertIn("model disappeared", entry["models"][0]["error"])

    def test_invalid_configuration_does_not_probe(self):
        with patch.object(inventory, "request") as probe:
            with self.assertRaises(ValueError):
                inventory.collect({"endpoints": [{"name": "x", "port": 0}]})
            probe.assert_not_called()

    def test_refresh_writes_private_offline_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            config = data / "config.json"
            snapshot = data / "inventory.json"
            config.write_text(json.dumps({"endpoints": [{"name": "local", "port": 11434}]}))
            with patch.object(inventory, "DATA", data), patch.object(inventory, "CONFIG", config), \
                 patch.object(inventory, "SNAPSHOT", snapshot), \
                 patch.object(inventory, "request", side_effect=OSError("offline")):
                self.assertEqual(inventory.refresh(), 1)
            self.assertEqual(json.loads(snapshot.read_text())["endpoints"][0]["status"], "unavailable")
            self.assertEqual(snapshot.stat().st_mode & 0o777, 0o600)

    def test_show_rejects_stale_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "inventory.json"
            snapshot.write_text(json.dumps({"checked_at": "2000-01-01T00:00:00+00:00",
                                            "endpoints": [{"status": "online"}]}))
            with patch.object(inventory, "SNAPSHOT", snapshot), \
                 patch("sys.argv", ["model-inventory.py", "--show"]), \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(inventory.main(), 1)
            self.assertIn("stale", error.getvalue())


if __name__ == "__main__":
    unittest.main()

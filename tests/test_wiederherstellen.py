import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RestoreTests(unittest.TestCase):
    def test_preview_and_restore_preserve_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            user = root / "vscode"
            agents = root / "agents"
            copilot = root / "copilot" / "mcp-config.json"
            user.mkdir()
            (user / "settings.json").write_text('{"existing": true}')
            env = os.environ.copy()
            env.update(VSCODE_USER_DIR=str(user), COPILOT_AGENTS_DIR=str(agents),
                       COPILOT_MCP_FILE=str(copilot), VSCODE_CLI="/usr/bin/true")
            command = ["bash", str(ROOT / "wiederherstellen.sh"), "--creative-agents"]
            subprocess.run(command + ["--dry-run", "--extensions"], env=env, check=True, capture_output=True)
            self.assertFalse(agents.exists())
            self.assertFalse(copilot.exists())
            self.assertFalse((user / "keybindings.json").exists())
            subprocess.run(command, env=env, check=True, capture_output=True)
            self.assertEqual((user / "settings.json").read_text(), '{"existing": true}')
            self.assertEqual((user / "mcp.json").read_text(), (ROOT / "vscode/mcp.json").read_text())
            self.assertTrue(copilot.is_file())
            self.assertTrue((agents / "langzeit-auftrag.agent.md").is_file())
            subprocess.run(command, env=env, check=True, capture_output=True)
            self.assertEqual((user / "settings.json").read_text(), '{"existing": true}')


if __name__ == "__main__":
    unittest.main()

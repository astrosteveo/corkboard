import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO, Fixture

HOOK = REPO / "hooks" / "session_start.py"


def run_hook(project_dir: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir), "CLAUDE_PLUGIN_ROOT": str(REPO)}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        cwd=project_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


class SessionStartHookTest(unittest.TestCase):
    def test_puts_the_summary_after_the_lead_line(self):
        result = run_hook(REPO)
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        lead, summary = result.stdout.split("\n\n", 1)
        self.assertEqual(
            lead,
            "This repo tracks its work in .project/ with corkboard. "
            "Use the corkboard:track skill before you start, finish or plan work.",
        )
        self.assertTrue(summary.startswith("Corkboard · v0.1"))
        self.assertLess(len(result.stdout), 10_000)  # Claude Code's limit for hook context

    def test_silent_outside_a_project(self):
        with tempfile.TemporaryDirectory() as folder:
            result = run_hook(Path(folder))
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_silent_when_the_project_is_broken(self):
        fixture = Fixture(self)
        (fixture.root / "items").chmod(0o000)
        self.addCleanup((fixture.root / "items").chmod, 0o755)
        result = run_hook(fixture.repo)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")

    def test_hooks_json_runs_this_script_on_session_start(self):
        config = json.loads((REPO / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        (entry,) = config["hooks"]["SessionStart"]
        (hook,) = entry["hooks"]
        self.assertEqual(hook["command"], 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py"')

    def test_plugin_manifest(self):
        manifest = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "corkboard")


if __name__ == "__main__":
    unittest.main()

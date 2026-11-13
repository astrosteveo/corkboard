import json
import tomllib
import unittest
from pathlib import Path

import corkboard
from corkboard import cli

REPO = Path(__file__).resolve().parents[1]


class PackageTest(unittest.TestCase):
    def test_package_imports(self):
        self.assertIn("standard library", corkboard.__doc__)

    def test_the_package_and_the_plugin_have_the_same_version(self):
        package = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        plugin = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(package["project"]["version"], plugin["version"])

    def test_the_installed_command_runs_cli_run(self):
        package = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(package["project"]["scripts"], {"corkboard": "corkboard.cli:run"})
        self.assertTrue(callable(cli.run))


if __name__ == "__main__":
    unittest.main()

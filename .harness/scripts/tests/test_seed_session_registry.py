from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".harness/scripts/seed_session_registry.py"


class SeedSessionRegistryTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["python3", str(SCRIPT), *args], cwd=ROOT, text=True, capture_output=True)

    def test_self_test_needs_no_extra_arguments(self) -> None:
        result = self.run_script("--self-test")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("SESSION_SEED_SELF_TEST=PASS", result.stdout)

    def test_approval_hash_matches_exact_written_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "registry.json"
            approval = Path(directory) / "seed-approval.json"
            result = self.run_script("--orchestrator-session", "orch-1", "--output", str(registry), "--approval", str(approval))
            self.assertEqual(0, result.returncode, result.stderr)
            approval_data = json.loads(approval.read_text())
            self.assertEqual(hashlib.sha256(registry.read_bytes()).hexdigest(), approval_data["registry_sha256"])

    def test_reseed_preserves_append_only_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "registry.json"
            approval = Path(directory) / "seed-approval.json"
            self.assertEqual(0, self.run_script("--orchestrator-session", "orch-1", "--output", str(registry), "--approval", str(approval)).returncode)
            first = json.loads(registry.read_text())
            self.assertEqual(0, self.run_script("--orchestrator-session", "orch-2", "--output", str(registry), "--approval", str(approval)).returncode)
            second = json.loads(registry.read_text())
            self.assertIn("orch-1", second["sessions"])
            self.assertIn("orch-2", second["sessions"])
            self.assertEqual(first["sessions"]["orch-1"], second["sessions"]["orch-1"])
            self.assertEqual(2, len(second["seed_history"]))

    def test_verify_rejects_tampered_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "registry.json"
            approval = Path(directory) / "seed-approval.json"
            self.assertEqual(0, self.run_script("--orchestrator-session", "orch-1", "--output", str(registry), "--approval", str(approval)).returncode)
            registry.write_text(registry.read_text() + "\n")
            result = self.run_script("--verify", "--output", str(registry), "--approval", str(approval))
            self.assertNotEqual(0, result.returncode)


if __name__ == "__main__":
    unittest.main()

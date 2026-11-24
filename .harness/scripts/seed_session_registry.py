#!/usr/bin/env python3
"""Create or extend the Orchestrator-controlled trust root for Phase 1 session roles."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

CANONICAL_REGISTRY = ".harness/sessions/registry.json"
CANONICAL_APPROVAL = ".harness/sessions/seed-approval.json"


def registry_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def approval_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def load_registry(path: Path) -> dict:
    if not path.exists():
        return {
            "schema_version": 1,
            "trust_root": "orchestrator",
            "append_only": True,
            "sessions": {},
            "seed_history": [],
        }
    value = json.loads(path.read_text())
    if value.get("trust_root") != "orchestrator" or value.get("append_only") is not True:
        raise SystemExit("existing registry is not an append-only Orchestrator trust root")
    value.setdefault("sessions", {})
    value.setdefault("seed_history", [])
    return value


def seed(registry_path: Path, approval_path: Path, orchestrator_session: str) -> None:
    if not orchestrator_session or not orchestrator_session.strip():
        raise SystemExit("orchestrator session is required")
    registry = load_registry(registry_path)
    existing = registry["sessions"].get(orchestrator_session)
    if existing and existing.get("role") != "orchestrator":
        raise SystemExit("session already exists with a different role")
    registry["sessions"][orchestrator_session] = {
        "role": "orchestrator",
        "trusted": True,
        "seed": True,
    }
    content = registry_bytes(registry)
    registry["seed_history"].append(
        {
            "approver_session_id": orchestrator_session,
            "registry_sha256": hashlib.sha256(content).hexdigest(),
        }
    )
    content = registry_bytes(registry)
    approval = {
        "schema_version": 1,
        "approver_session_id": orchestrator_session,
        "scope": "phase1-session-registry-bootstrap",
        "registry_sha256": hashlib.sha256(content).hexdigest(),
    }
    atomic_write(registry_path, content)
    atomic_write(approval_path, approval_bytes(approval))


def verify(registry_path: Path, approval_path: Path) -> None:
    content = registry_path.read_bytes()
    approval = json.loads(approval_path.read_text())
    if approval.get("registry_sha256") != hashlib.sha256(content).hexdigest():
        raise SystemExit("approval hash does not match registry bytes")
    registry = json.loads(content)
    if registry.get("append_only") is not True or registry.get("trust_root") != "orchestrator":
        raise SystemExit("registry trust-root invariants failed")
    if approval.get("approver_session_id") not in registry.get("sessions", {}):
        raise SystemExit("approver session is absent from registry")


def self_test() -> None:
    with tempfile.TemporaryDirectory() as directory:
        registry_path = Path(directory) / "registry.json"
        approval_path = Path(directory) / "seed-approval.json"
        seed(registry_path, approval_path, "orch-1")
        verify(registry_path, approval_path)
        first = json.loads(registry_path.read_text())
        seed(registry_path, approval_path, "orch-2")
        verify(registry_path, approval_path)
        second = json.loads(registry_path.read_text())
        assert "orch-1" in second["sessions"] and "orch-2" in second["sessions"]
        assert len(second["seed_history"]) == 2
        assert first["sessions"]["orch-1"] == second["sessions"]["orch-1"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--orchestrator-session")
    parser.add_argument("--output", default=CANONICAL_REGISTRY)
    parser.add_argument("--approval", default=CANONICAL_APPROVAL)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("SESSION_SEED_SELF_TEST=PASS")
        return 0
    if args.verify:
        verify(Path(args.output), Path(args.approval))
        print("SESSION_SEED_VERIFY=PASS")
        return 0
    seed(Path(args.output), Path(args.approval), args.orchestrator_session or "")
    print(f"SESSION_SEED=PASS registry={args.output} approval={args.approval}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

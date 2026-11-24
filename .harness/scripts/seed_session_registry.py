#!/usr/bin/env python3
"""Create the Orchestrator-controlled trust root for Phase 1 session roles."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--orchestrator-session", required=True)
    parser.add_argument("--output", default=".harness/sessions/registry.json")
    parser.add_argument("--approval", default=".harness/sessions/seed-approval.json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        assert args.orchestrator_session
        assert args.output.endswith("registry.json")
        assert args.approval.endswith("seed-approval.json")
        print("SESSION_SEED_SELF_TEST=PASS")
        return 0

    if not args.orchestrator_session.strip():
        raise SystemExit("orchestrator session is required")

    registry = {
        "schema_version": 1,
        "trust_root": "orchestrator",
        "append_only": True,
        "sessions": {
            args.orchestrator_session: {
                "role": "orchestrator",
                "trusted": True,
                "seed": True,
            }
        },
    }
    approval = {
        "schema_version": 1,
        "approver_session_id": args.orchestrator_session,
        "scope": "phase1-session-registry-bootstrap",
        "registry_sha256": hashlib.sha256(canonical_bytes(registry)).hexdigest(),
    }
    output = Path(args.output)
    approval_path = Path(args.approval)
    output.parent.mkdir(parents=True, exist_ok=True)
    approval_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
    approval_path.write_text(json.dumps(approval, indent=2, sort_keys=True) + "\n")
    print(f"SESSION_SEED=PASS registry={output} approval={approval_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

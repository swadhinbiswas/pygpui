from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.ci.common import GateError, canonical_repo_path, load_json, load_tasks


def test_canonical_repo_path_rejects_traversal_and_absolute_paths(
    tmp_path: Path,
) -> None:
    for value in (
        "../escape.json",
        "/tmp/escape.json",
        "evidence/../merge.json",
        "evidence\\merge.json",
    ):
        with pytest.raises(GateError) as caught:
            canonical_repo_path(tmp_path, value)
        assert caught.value.code == "identity"


def test_canonical_repo_path_accepts_normalized_task_evidence(tmp_path: Path) -> None:
    assert canonical_repo_path(tmp_path, "evidence/P1-TOOL-BRANCH01/merge.json") == (
        "evidence/P1-TOOL-BRANCH01/merge.json"
    )


def test_load_json_rejects_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"task_id":"one","task_id":"two"}\n', encoding="utf-8")
    with pytest.raises(GateError) as caught:
        load_json(path)
    assert caught.value.code == "json"


def test_load_tasks_accepts_harness_task_id_formats(tmp_path: Path) -> None:
    tasks = tmp_path / ".harness/TASKS.json"
    tasks.parent.mkdir(parents=True)
    tasks.write_text(
        json.dumps(
            {"tasks": [{"id": "P0-AP01"}, {"id": "P1-TOOL-BRANCH01"}, {"id": "H-001"}]}
        )
        + "\n",
        encoding="utf-8",
    )

    indexed = load_tasks(tmp_path)

    assert set(indexed) == {"P0-AP01", "P1-TOOL-BRANCH01", "H-001"}


def test_load_json_rejects_non_object_root(tmp_path: Path) -> None:
    path = tmp_path / "array.json"
    path.write_text(json.dumps([]) + "\n", encoding="utf-8")
    with pytest.raises(GateError) as caught:
        load_json(path)
    assert caught.value.code == "json"

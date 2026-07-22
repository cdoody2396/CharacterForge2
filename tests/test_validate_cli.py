"""§9 validator CLI: exit codes, every error printed with file and id,
summary counts, machine-readable JSON mode, missing-directory refusal."""

import json
import subprocess
import sys
from pathlib import Path

from conftest import FIXTURES, minimal_file

REPO_ROOT = Path(__file__).parent.parent


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "app.options.validate", *map(str, args)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_clean_directory_exits_zero():
    result = run_cli(FIXTURES / "valid_min")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "clean" in result.stdout


def test_summary_counts():
    result = run_cli(FIXTURES / "valid_min")
    assert "files: 1" in result.stdout
    assert "groups: 2" in result.stdout
    assert "options: 2" in result.stdout
    assert "retired: 1" in result.stdout
    assert "standard: 2" in result.stdout  # per-rating option counts
    assert "persona: 1" in result.stdout  # free-text slots found


def test_example_guard_end_to_end():
    # §0: the guard is enforced by code — the gatekeeper refuses example_
    # ids, naming file and id, exit 1.
    result = run_cli(FIXTURES / "example_guard")
    assert result.returncode == 1
    assert "EXAMPLE_ID_IN_DATA" in result.stdout
    assert "10_example_ids.json" in result.stdout
    assert "example_group" in result.stdout


def test_prints_every_error_not_just_first(tmp_path):
    (tmp_path / "00_bad_rating.json").write_text(
        json.dumps(minimal_file(rating="bogus")), encoding="utf-8"
    )
    (tmp_path / "10_bad_json.json").write_text("{broken", encoding="utf-8")
    result = run_cli(tmp_path)
    assert result.returncode == 1
    assert "00_bad_rating.json" in result.stdout
    assert "10_bad_json.json" in result.stdout


def test_error_lines_name_file_and_id(tmp_path):
    data = minimal_file()
    data["groups"][0]["kind"] = "bogus"
    (tmp_path / "00_bad.json").write_text(json.dumps(data), encoding="utf-8")
    result = run_cli(tmp_path)
    assert result.returncode == 1
    assert "00_bad.json" in result.stdout
    assert "g1" in result.stdout


def test_missing_directory_is_an_error(tmp_path):
    result = run_cli(tmp_path / "no_such_dir")
    assert result.returncode == 1
    assert "MISSING_DIRECTORY" in result.stdout


def test_json_mode_shape():
    result = run_cli("--json", FIXTURES / "valid_min")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["files"] == 1
    assert payload["groups"] == 2
    assert payload["options"] == 2
    assert payload["retired"] == 1
    assert payload["ratings"] == {"standard": 2, "mature": 0, "explicit": 0}
    assert payload["free_text_slots"] == {"identity": 0, "persona": 1}
    assert payload["errors"] == []


def test_json_mode_reports_errors():
    result = run_cli("--json", FIXTURES / "example_guard")
    assert result.returncode == 1
    payload = json.loads(result.stdout)
    codes = {e["code"] for e in payload["errors"]}
    assert "EXAMPLE_ID_IN_DATA" in codes
    guard = next(e for e in payload["errors"] if e["code"] == "EXAMPLE_ID_IN_DATA")
    assert guard["file"] == "10_example_ids.json"
    assert guard["id"] in ("example_group", "fx_group/example_option")


def test_multiple_directories_merge_in_order(tmp_path):
    d1 = tmp_path / "d1"
    d2 = tmp_path / "d2"
    d1.mkdir()
    d2.mkdir()
    (d1 / "00.json").write_text(json.dumps(minimal_file()), encoding="utf-8")
    (d2 / "00.json").write_text(
        json.dumps(
            {
                "format": 1,
                "rating": "standard",
                "groups": [
                    {"id": "g1", "options": [{"id": "opt_b", "label": "B"}]}
                ],
            }
        ),
        encoding="utf-8",
    )
    result = run_cli("--json", d1, d2)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["files"] == 2
    assert payload["groups"] == 1  # merged, not duplicated
    assert payload["options"] == 2


def test_shipped_data_directory_is_clean():
    # §0 structural guard 1 ("ships empty") ended by design at stage O2: the
    # harvest populated the tree. The standing invariant is the gate itself —
    # the shipped data validates clean at the harvested counts.
    result = run_cli("--json", REPO_ROOT / "app" / "data" / "options")
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["errors"] == []
    # O2b counts: the 92_piercings fragment returned (gate ruled piercings
    # identity), adding 1 file and its 2 explicit options to the O2 tree.
    assert payload["files"] == 13
    assert payload["groups"] == 135  # 137 emitted entries, 2 fragments merge
    assert payload["options"] == 2359
    assert payload["ratings"] == {"standard": 2334, "mature": 0, "explicit": 25}

"""Startup laws (O5_INPUTS §C/§D/§E/§J): fail-loud, every error named;
first run creates the layout; the drop-in loads after the maintained
tree; an error in either source refuses start.
"""

import json

import pytest

from app.spine import build_context
from app.spine.errors import (
    CATALOG_EMPTY,
    DATA_ROOT_UNWRITABLE,
    MAINTAINED_TREE_MISSING,
    StartupRefusal,
)
from tests.conftest import minimal_file, record_catalog_dir
from tests.spine_helpers import make_ctx


def refuse_startup(match, fn, *args, **kwargs):
    with pytest.raises(StartupRefusal) as excinfo:
        fn(*args, **kwargs)
    assert match in str(excinfo.value), excinfo.value
    return excinfo.value


class TestCleanStart:
    def test_first_run_creates_the_layout(self, tmp_path):
        ctx = make_ctx(tmp_path)
        root = ctx.paths.data_root
        for sub in ("records", "artifacts", "db", "audit"):
            assert (root / sub).is_dir()
        assert len(ctx.catalog) == 10
        assert ctx.token
        assert ctx.version

    def test_restart_over_an_existing_root_is_clean(self, tmp_path):
        make_ctx(tmp_path)
        again = make_ctx(tmp_path)
        assert len(again.catalog) == 10


class TestFailLoudRefusals:
    def test_catalog_error_refuses_naming_the_file(self, tmp_path):
        refusal = refuse_startup(
            "50_bad.json",
            make_ctx,
            tmp_path,
            extra_files={"50_bad.json": minimal_file(rating="not_a_rating")},
        )
        assert len(refusal.failures) == 1

    def test_safety_data_error_refuses_distinctly(self, tmp_path):
        empty_safety = tmp_path / "empty_safety"
        empty_safety.mkdir()
        refuse_startup(
            "SAFETY_DATA_DIR_INVALID", make_ctx, tmp_path, safety_data_dir=empty_safety
        )

    def test_unwritable_root_refuses_distinctly(self, tmp_path):
        blocker = tmp_path / "blocker"
        blocker.write_text("a file where a directory must go", encoding="utf-8")
        refuse_startup(
            DATA_ROOT_UNWRITABLE, build_context, blocker / "root"
        )

    def test_missing_maintained_tree_refuses(self, tmp_path):
        refuse_startup(
            MAINTAINED_TREE_MISSING,
            make_ctx,
            tmp_path,
            options_dirs=[tmp_path / "absent"],
        )

    def test_empty_maintained_tree_refuses(self, tmp_path):
        empty = tmp_path / "empty_options"
        empty.mkdir()
        refuse_startup(CATALOG_EMPTY, make_ctx, tmp_path, options_dirs=[empty])

    def test_every_error_is_named_not_just_the_first(self, tmp_path):
        empty_safety = tmp_path / "empty_safety"
        empty_safety.mkdir()
        with pytest.raises(StartupRefusal) as excinfo:
            make_ctx(
                tmp_path,
                extra_files={"50_bad.json": minimal_file(rating="not_a_rating")},
                safety_data_dir=empty_safety,
            )
        message = str(excinfo.value)
        assert "50_bad.json" in message
        assert "SAFETY_DATA_DIR_INVALID" in message
        assert len(excinfo.value.failures) >= 2


class TestDropIn:
    def test_dropin_loads_after_the_maintained_tree(self, tmp_path):
        maintained = record_catalog_dir(tmp_path)
        dropin = tmp_path / "dropin"
        dropin.mkdir()
        (dropin / "10_extra.json").write_text(
            json.dumps(
                {
                    "format": 1,
                    "rating": "standard",
                    "groups": [
                        {
                            "id": "extra_flair",
                            "label": "Extra Flair",
                            "kind": "pick_one",
                            "home": "persona",
                            "options": [{"id": "sparkle", "label": "Sparkle"}],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        ctx = make_ctx(tmp_path, options_dirs=[maintained, dropin])
        ids = ctx.catalog.group_ids()
        assert "extra_flair" in ids
        assert ids[-1] == "extra_flair"  # loaded after the maintained tree
        assert len(ctx.catalog) == 11

    def test_absent_dropin_directory_is_merely_absent(self, tmp_path):
        maintained = record_catalog_dir(tmp_path)
        ctx = make_ctx(
            tmp_path, options_dirs=[maintained, tmp_path / "no_dropin_here"]
        )
        assert len(ctx.catalog) == 10

    def test_error_in_the_dropin_refuses_start(self, tmp_path):
        maintained = record_catalog_dir(tmp_path)
        dropin = tmp_path / "dropin"
        dropin.mkdir()
        # Re-declaring a maintained group's locked keys is a merge error;
        # the drop-in cannot mutate the frozen tree (§E).
        (dropin / "10_clash.json").write_text(
            json.dumps(
                {
                    "format": 1,
                    "rating": "standard",
                    "groups": [
                        {
                            "id": "species",
                            "label": "Species",
                            "kind": "pick_one",
                            "home": "identity",
                            "options": [{"id": "fox", "label": "Fox"}],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        refusal = refuse_startup(
            "10_clash.json", make_ctx, tmp_path, options_dirs=[maintained, dropin]
        )
        assert "MERGE_LOCKED_KEY" in str(refusal)

    def test_error_in_the_maintained_tree_refuses_start(self, tmp_path):
        refuse_startup(
            "50_bad.json",
            make_ctx,
            tmp_path,
            extra_files={"50_bad.json": {"format": 1, "rating": "standard"}},
        )

"""Orphan surfacing (O5_INPUTS §F.4/§J, N9): a record written under a
richer catalog loads under a poorer one with its orphans reported on
load and counted on list — written but inert, never a load error.
"""

import json

from app.record import errors as E
from tests.conftest import RECORD_STD_FILE
from tests.spine_helpers import (
    auth_headers,
    create_character,
    make_ctx,
    spine_client,
)


def test_orphans_surface_on_load_and_list(tmp_path):
    ctx = make_ctx(tmp_path)
    with spine_client(ctx) as client:
        headers = auth_headers(ctx)
        cid = create_character(client, ctx)
        assert (
            client.post(
                f"/records/{cid}/rating", headers=headers, json={"rating": "explicit"}
            ).status_code
            == 200
        )
        assert (
            client.post(
                f"/records/{cid}/selections",
                headers=headers,
                json={"group_id": "kink", "value": "k1"},
            ).status_code
            == 200
        )

    # The same data root under a catalog missing the explicit file: the
    # kink group no longer exists — its held pick is an orphan.
    poorer = tmp_path / "poorer_options"
    poorer.mkdir()
    (poorer / "00_std.json").write_text(
        json.dumps(RECORD_STD_FILE), encoding="utf-8"
    )
    ctx2 = make_ctx(tmp_path, options_dirs=[poorer])

    with spine_client(ctx2) as client:
        headers = auth_headers(ctx2)
        loaded = client.get(f"/records/{cid}", headers=headers)
        assert loaded.status_code == 200
        orphans = loaded.json()["orphans"]
        assert orphans == [
            {
                "location": "persona",
                "group_id": "kink",
                "option_id": None,
                "reason": E.UNKNOWN_GROUP,
            }
        ]

        listing = client.get("/records", headers=headers).json()["records"]
        assert listing[0]["orphan_count"] == 1

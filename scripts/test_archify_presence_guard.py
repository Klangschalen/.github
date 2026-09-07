#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from archify_presence_guard import check_repository, load_policy, safe_path


POLICY = {
    "schema_version": 1,
    "policy_id": "SS-ARCHIFY-PRESENCE-001",
    "upstream": {"version": "2.16.0", "commit": "c" * 40},
    "architecture": {"canonical_home": "Klangschalen/zentrale"},
    "repositories": {
        "Klangschalen/zentrale": {
            "required_paths": ["map/source.json", "map/view.html"],
            "required_fragments": {"map/source.json": ["archify-pin"]},
        }
    },
}


def write_policy(root: Path) -> Path:
    path = root / "policy.json"
    path.write_text(json.dumps(POLICY), encoding="utf-8")
    return path


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        policy = load_policy(write_policy(root))

        errors, mode = check_repository(policy, "Klangschalen/anderes-repo", root)
        assert errors == []
        assert mode == "CENTRAL_DERIVED_VIEW"

        errors, mode = check_repository(policy, "Klangschalen/zentrale", root)
        assert mode == "LOCAL_PROTECTED_INTEGRATION"
        assert len(errors) == 2

        (root / "map").mkdir()
        (root / "map/source.json").write_text("archify-pin", encoding="utf-8")
        (root / "map/view.html").write_text("<html></html>", encoding="utf-8")
        errors, _ = check_repository(policy, "Klangschalen/zentrale", root)
        assert errors == []

        (root / "map/source.json").write_text("changed", encoding="utf-8")
        errors, _ = check_repository(policy, "Klangschalen/zentrale", root)
        assert errors == ["Pflichtinhalt fehlt in map/source.json: archify-pin"]

        try:
            safe_path(root, "../escape")
        except ValueError:
            pass
        else:
            raise AssertionError("Pfadflucht muss blockiert werden")

    print("5 Archify-Löschschutztests bestanden")


if __name__ == "__main__":
    main()

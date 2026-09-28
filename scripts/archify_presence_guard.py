#!/usr/bin/env python3
"""Fail closed when a protected Sound-Spirit Archify integration disappears."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath


def safe_path(root: Path, relative: str) -> Path:
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts:
        raise ValueError(f"unsicherer Policy-Pfad: {relative}")
    return root.joinpath(*posix.parts)


def load_policy(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("unbekannte schema_version")
    if data.get("policy_id") != "SS-ARCHIFY-PRESENCE-001":
        raise ValueError("unerwartete policy_id")
    repositories = data.get("repositories")
    if not isinstance(repositories, dict) or not repositories:
        raise ValueError("repositories fehlt oder ist leer")
    return data


def check_repository(policy: dict, repository: str, root: Path) -> tuple[list[str], str]:
    rule = policy["repositories"].get(repository)
    if rule is None:
        return [], "CENTRAL_DERIVED_VIEW"

    errors: list[str] = []
    for relative in rule.get("required_paths", []):
        target = safe_path(root, relative)
        if not target.is_file():
            errors.append(f"Pflichtdatei fehlt: {relative}")
        elif target.stat().st_size == 0:
            errors.append(f"Pflichtdatei ist leer: {relative}")

    for relative, fragments in rule.get("required_fragments", {}).items():
        target = safe_path(root, relative)
        if not target.is_file():
            continue
        content = target.read_text(encoding="utf-8", errors="strict")
        for fragment in fragments:
            if fragment not in content:
                errors.append(f"Pflichtinhalt fehlt in {relative}: {fragment}")

    return errors, "LOCAL_PROTECTED_INTEGRATION"


def build_summary(repository: str, mode: str, errors: list[str], policy: dict) -> str:
    upstream = policy["upstream"]
    status = "ROT" if errors else "GRUEN"
    lines = [
        f"# [{status}] Archify-Löschschutz",
        "",
        f"- Repository: `{repository}`",
        f"- Abdeckung: `{mode}`",
        f"- Archify: `{upstream['version']}` / `{upstream['commit']}`",
        f"- Kanonische Heimat: `{policy['architecture']['canonical_home']}`",
        "",
    ]
    if errors:
        lines += ["## Blockierende Abweichungen", ""]
        lines += [f"- {error}" for error in errors]
    elif mode == "CENTRAL_DERIVED_VIEW":
        lines.append("Dieses Repository braucht keine Archify-Kopie; es wird durch die zentrale Lesesicht abgedeckt.")
    else:
        lines.append("Alle geschützten Archify-Dateien und Versionsbindungen sind vorhanden.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()

    try:
        policy = load_policy(args.policy)
        errors, mode = check_repository(policy, args.repo, args.root)
        summary = build_summary(args.repo, mode, errors, policy)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        summary = f"# [ROT] Archify-Löschschutz\n\nPolicy oder Prüfstand ungültig: {error}\n"
        errors = [str(error)]

    print(summary)
    if args.summary:
        args.summary.write_text(summary, encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Fail-closed contract tests for the reusable Doku-Lint workflow."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "doku-lint.yml"
DOCS = ROOT / ".github" / "workflows" / "README.md"

EXPECTED_TYPES = {
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "test",
    "chore",
    "perf",
    "build",
    "ci",
    "revert",
    "policy",
}


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label} fehlt: {needle}")


def extract_default_types(workflow: str) -> set[str]:
    match = re.search(
        r"(?m)^      allowed_commit_types:\n(?:        .*\n)*?        default: \"([^\"]+)\"$",
        workflow,
    )
    if not match:
        raise AssertionError("Default fuer allowed_commit_types fehlt")
    return {item.strip() for item in match.group(1).split(",") if item.strip()}


def extract_subject_pattern(workflow: str) -> re.Pattern[str]:
    match = re.search(
        r"CONVENTIONAL_SUBJECT_PATTERN:\s*'([^']+)'",
        workflow,
    )
    if not match:
        raise AssertionError("CONVENTIONAL_SUBJECT_PATTERN fehlt")
    return re.compile(match.group(1))


def test_exact_pr_head(workflow: str) -> None:
    require(
        workflow,
        "SOURCE_COMMIT: ${{ github.event.pull_request.head.sha || github.sha }}",
        "PR-Head-Auswahl",
    )
    require(workflow, "ref: ${{ env.SOURCE_COMMIT }}", "Checkout des PR-Heads")
    require(
        workflow,
        'git log -1 --pretty=%s "$SOURCE_COMMIT"',
        "Commit-Pruefung gegen PR-Head",
    )
    require(
        workflow,
        'git diff --name-only "$BASE_COMMIT"..."$SOURCE_COMMIT"',
        "Diff gegen Basis und PR-Head",
    )
    if "git diff --name-only HEAD~1" in workflow:
        raise AssertionError("Unsicherer HEAD~1-Fallback ist wieder vorhanden")


def test_commit_contract(workflow: str) -> None:
    types = extract_default_types(workflow)
    missing = EXPECTED_TYPES - types
    if missing:
        raise AssertionError(f"Erlaubte Commit-Typen fehlen: {sorted(missing)}")

    block = re.search(
        r"(?m)^      commit_format_warn_only:\n(?:        .*\n)*?        default: (true|false)$",
        workflow,
    )
    if not block or block.group(1) != "false":
        raise AssertionError("Gate 3 muss standardmaessig blockieren")

    pattern = extract_subject_pattern(workflow)
    valid = (
        "policy: define output contract",
        "docs(policy): explain output contract",
        "fix!: change behavior",
        "feat(agent-runtime)!: change behavior",
    )
    invalid = (
        "Policy: wrong case",
        "Merge pull request #12",
        "free form title",
    )

    for subject in valid:
        if not pattern.match(subject):
            raise AssertionError(f"Gueltiger Titel wird abgelehnt: {subject}")
    for subject in invalid:
        if pattern.match(subject):
            raise AssertionError(f"Ungueltiger Titel wird akzeptiert: {subject}")


def test_documentation(workflow: str, docs: str) -> None:
    require(docs, "exakten PR-Head", "Dokumentation der Quellbindung")
    require(docs, "`policy:`", "Dokumentation des Richtlinien-Typs")
    require(docs, "`commit_format_warn_only: false`", "Dokumentation des harten Gates")

    for commit_type in sorted(extract_default_types(workflow)):
        require(docs, f"`{commit_type}`", f"Dokumentierter Commit-Typ {commit_type}")


def main() -> int:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    docs = DOCS.read_text(encoding="utf-8")

    test_exact_pr_head(workflow)
    test_commit_contract(workflow)
    test_documentation(workflow, docs)

    print("Doku-Lint-Vertrag: PASS")
    print(f"Gepruefte Commit-Typen: {', '.join(sorted(extract_default_types(workflow)))}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Doku-Lint-Vertrag: FAIL - {exc}", file=sys.stderr)
        raise SystemExit(1)

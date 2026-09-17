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


def extract_pattern(workflow: str, variable: str) -> re.Pattern[str]:
    match = re.search(rf"{re.escape(variable)}:\s*'([^']+)'", workflow)
    if not match:
        raise AssertionError(f"{variable} fehlt")
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

    pattern = extract_pattern(workflow, "CONVENTIONAL_SUBJECT_PATTERN")
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


def test_post_merge_push_contract(workflow: str) -> None:
    require(
        workflow,
        'if [ "${{ github.event_name }}" = "push" ]; then',
        "Push-spezifische Gate-3-Behandlung",
    )
    require(
        workflow,
        'git rev-list --parents -n1 "$SOURCE_COMMIT"',
        "Erkennung echter Merge-Commits",
    )
    require(
        workflow,
        'committer_email="$(git log -1 --pretty=%ce "$SOURCE_COMMIT")"',
        "Erkennung GitHub-erzeugter PR-Commits",
    )
    require(
        workflow,
        '"noreply@github.com"',
        "GitHub-Commit-Erkennung",
    )
    require(
        workflow,
        '[[ "$message" =~ \\(#[0-9]+\\)$ ]]',
        "PR-Nummer im GitHub-Commit-Titel",
    )
    require(
        workflow,
        "Gate 3 + Gate 3b) blockierend geprueft",
        "Begruendung fuer Merge-Commit-Ausnahme verweist auf Gate 3b",
    )


def extract_step(workflow: str, step_name: str) -> str:
    """Isoliert den Text EINES Steps (bis zum naechsten '      - name:' oder Dateiende).

    Ohne diese Isolierung koennen require()-Pruefungen an einem Merkmal eines
    ANDEREN Steps vorbeischauen - z.B. traegt Gate 2 ebenfalls
    "if: github.event_name == 'pull_request'". Eine reine Teilstring-Suche
    ueber die gesamte Datei wuerde das nicht von Gate 3b unterscheiden.
    """
    start = workflow.index(f"      - name: {step_name}")
    rest = workflow[start + len(f"      - name: {step_name}"):]
    next_step = re.search(r"\n      - name:", rest)
    end = start + len(f"      - name: {step_name}") + (next_step.start() if next_step else len(rest))
    return workflow[start:end]


def test_gate_3b_pr_title_contract(workflow: str) -> None:
    """Gate 3b prueft den PR-Titel, den Gate 3 nie sieht (Squash-Merge-Luecke)."""
    require(
        workflow,
        "Gate 3b - Conventional PR-Titel",
        "Gate-3b-Schritt fehlt",
    )

    gate_3b_step = extract_step(workflow, "Gate 3b - Conventional PR-Titel")
    require(
        gate_3b_step,
        "if: github.event_name == 'pull_request'",
        "Gate 3b muss auf pull_request begrenzt sein",
    )
    require(
        gate_3b_step,
        "PR_TITLE: ${{ github.event.pull_request.title }}",
        "Gate 3b muss den echten PR-Titel aus dem Event lesen",
    )
    require(
        gate_3b_step,
        'if [[ "$PR_TITLE" =~ $CONVENTIONAL_SUBJECT_PATTERN ]]',
        "Gate 3b muss dasselbe Muster wie Gate 3 verwenden",
    )
    require(
        gate_3b_step,
        "COMMIT_FORMAT_WARN_ONLY: ${{ inputs.commit_format_warn_only }}",
        "Gate 3b muss denselben Schalter wie Gate 3 respektieren",
    )

    # Gate 3b muss als eigener Schritt NACH Gate 3 stehen, nicht dessen
    # bestehende Pruefung ersetzen - sonst verliert Gate 3 seine Wirkung auf
    # echte direkte Pushes.
    gate3_index = workflow.index("Gate 3 - Conventional Head-Commit")
    gate3b_index = workflow.index("Gate 3b - Conventional PR-Titel")
    if gate3b_index < gate3_index:
        raise AssertionError("Gate 3b darf Gate 3 nicht vorausgehen oder ersetzen")

    pattern = extract_pattern(workflow, "CONVENTIONAL_SUBJECT_PATTERN")
    # Der reale Anlass: alle Branch-Commits konform, der PR-Titel nicht.
    real_case_title = "Produktdaten-Lücke messen: die Angaben stehen im Text, aber nicht im Schema (#19)"
    if pattern.match(real_case_title):
        raise AssertionError(
            "Der PR-Titel aus dem realen Anlass (website-audit PR #19) muesste "
            "von Gate 3b abgelehnt werden, wird aber vom Muster akzeptiert"
        )
    if not pattern.match("feat(audit): Luecke zwischen Produkttext und Product-Schema messen"):
        raise AssertionError(
            "Ein konformer PR-Titel darf vom selben Muster nicht abgelehnt werden"
        )


def test_changelog_contract(workflow: str) -> None:
    pattern = extract_pattern(workflow, "CHANGELOG_PATH_PATTERN")
    valid = (
        "CHANGELOG.md",
        "CHANGELOG.d/2026-09-04-doku-lint.md",
        "CHANGELOG.d/github/doku-lint.md",
    )
    invalid = (
        "docs/CHANGELOG.md",
        "CHANGELOG.d/note.txt",
        "CHANGELOG.d/",
    )

    for path in valid:
        if not pattern.match(path):
            raise AssertionError(f"Gueltiger Changelog-Beleg wird abgelehnt: {path}")
    for path in invalid:
        if pattern.match(path):
            raise AssertionError(f"Ungueltiger Changelog-Beleg wird akzeptiert: {path}")

    require(
        workflow,
        'grep -E "$CHANGELOG_PATH_PATTERN"',
        "Anwendung des Changelog-Pfadmusters",
    )
    require(
        workflow,
        "CHANGELOG.md oder CHANGELOG.d/*.md",
        "Verstaendliche Fehlermeldung fuer Changelog-Belege",
    )


def test_documentation(workflow: str, docs: str) -> None:
    require(docs, "exakten PR-Head", "Dokumentation der Quellbindung")
    require(docs, "`policy:`", "Dokumentation des Richtlinien-Typs")
    require(docs, "`commit_format_warn_only: false`", "Dokumentation des harten Gates")
    require(docs, "`CHANGELOG.d/", "Dokumentation der Changelog-Schnipsel")
    require(docs, "Gate 3b", "Dokumentation von Gate 3b")
    require(docs, "PR-Titel", "Dokumentation der PR-Titel-Pruefung")

    for commit_type in sorted(extract_default_types(workflow)):
        require(docs, f"`{commit_type}`", f"Dokumentierter Commit-Typ {commit_type}")


def main() -> int:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    docs = DOCS.read_text(encoding="utf-8")

    test_exact_pr_head(workflow)
    test_commit_contract(workflow)
    test_post_merge_push_contract(workflow)
    test_gate_3b_pr_title_contract(workflow)
    test_changelog_contract(workflow)
    test_documentation(workflow, docs)

    print("Doku-Lint-Vertrag: PASS")
    print(f"Gepruefte Commit-Typen: {', '.join(sorted(extract_default_types(workflow)))}")
    print("Changelog-Belege: CHANGELOG.md oder CHANGELOG.d/*.md")
    print("Push-Merge-Commits: synthetischer GitHub-Titel wird nicht doppelt blockierend geprueft")
    print("Gate 3b: PR-Titel wird vor dem Squash-Merge gegen das Conventional-Commit-Format geprueft")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Doku-Lint-Vertrag: FAIL - {exc}", file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
from __future__ import annotations

import org_action_runtime_audit as audit


def test_parse_uses_ignores_comments_and_keeps_lines() -> None:
    text = """steps:
  # - uses: actions/checkout@v4
  - uses: actions/checkout@abc
  - name: Setup
    uses: actions/setup-python@def # note
"""
    uses = audit.parse_uses(text, "repo", ".github/workflows/test.yml")
    assert [(item.line, item.spec) for item in uses] == [
        (3, "actions/checkout@abc"),
        (5, "actions/setup-python@def"),
    ]


def test_parse_action_ref() -> None:
    action = audit.parse_action_ref("owner/repo/sub/action@v2")
    assert action == audit.ActionRef("owner", "repo", "sub/action", "v2")
    assert audit.parse_action_ref("./local") is None
    assert audit.parse_action_ref("docker://alpine:3") is None
    assert audit.parse_action_ref("owner/repo/.github/workflows/x.yml@main") is None


def test_runtime_and_pin_classification() -> None:
    use = audit.Use("target", ".github/workflows/test.yml", 7, "actions/checkout@v4")
    action = audit.parse_action_ref(use.spec)
    findings = audit.classify_use(use, action, "runs:\n  using: node20\n", "Klangschalen", "node24")
    assert {item.kind for item in findings} == {"runtime", "pin"}


def test_current_sha_pinned_action_is_clean() -> None:
    sha = "a" * 40
    use = audit.Use("target", "w.yml", 1, f"actions/checkout@{sha}")
    action = audit.parse_action_ref(use.spec)
    assert audit.classify_use(use, action, "runs:\n  using: 'node24'\n", "Klangschalen", "node24") == []


def test_internal_action_does_not_require_external_pin() -> None:
    use = audit.Use("target", "w.yml", 1, "Klangschalen/shared/action@main")
    action = audit.parse_action_ref(use.spec)
    assert audit.classify_use(use, action, "runs:\n  using: node24\n", "Klangschalen", "node24") == []


def test_report_is_red_when_scan_incomplete() -> None:
    report = audit.build_report(
        organization="Klangschalen", generated_at="2026-08-28T00:00:00Z",
        required_node="node24", repo_count=41, workflow_count=70, use_count=100,
        findings=[], errors=["nicht lesbar"],
    )
    assert "[ROT]" in report
    assert "Scan unvollständig" in report


def test_report_is_yellow_for_findings() -> None:
    finding = audit.Finding("runtime", "repo", "w.yml", 4, "a/b@v1", "node20")
    report = audit.build_report(
        organization="Klangschalen", generated_at="2026-08-28T00:00:00Z",
        required_node="node24", repo_count=1, workflow_count=1, use_count=1,
        findings=[finding], errors=[],
    )
    assert "[GELB]" in report
    assert "`w.yml:4`" in report


def _run() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as error:
            failures += 1
            print(f"FAIL {test.__name__}: {error}")
    print(f"\n{len(tests) - failures}/{len(tests)} Tests bestanden.")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(_run())

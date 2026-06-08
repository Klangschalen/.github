#!/usr/bin/env python3
"""Tests fuer org_doku_audit.py (ohne Netz/gh). Aufruf:

    python3 scripts/test_org_doku_audit.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_module_path = Path(__file__).with_name("org_doku_audit.py")
_spec = importlib.util.spec_from_file_location("org_doku_audit", _module_path)
audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit)


def test_parse_repo_list_skips_archived_and_sorts() -> None:
    raw = '[{"name":"zebra","isArchived":false},' \
          '{"name":"alpha","isArchived":false},' \
          '{"name":"altlast","isArchived":true}]'
    assert audit.parse_repo_list(raw) == ["alpha", "zebra"]


def test_parse_repo_list_handles_garbage() -> None:
    assert audit.parse_repo_list("kein json") == []


def test_summarize() -> None:
    results = {
        "voll": {"README.md": True, "STATUS.md": True},
        "luecke": {"README.md": True, "STATUS.md": False},
    }
    stats = audit.summarize(results)
    assert stats == {
        "repos_total": 2,
        "repos_complete": 1,
        "repos_incomplete": 1,
        "missing_files_total": 1,
    }


def test_build_report_green_when_all_complete() -> None:
    results = {"repo-a": {name: True for name in audit.REQUIRED_FILES}}
    report = audit.build_report(results, audit.REQUIRED_FILES, "2026-05-31T03:00:00Z")
    assert "[GRUEN]" in report
    assert "<!-- org-doku-audit -->" in report
    assert "`repo-a`" in report
    assert "**X**" not in report


def test_build_report_yellow_and_marks_gaps() -> None:
    files = {name: True for name in audit.REQUIRED_FILES}
    files["STATUS.md"] = False
    files["CHANGELOG.md"] = False
    results = {"repo-b": files}
    report = audit.build_report(results, audit.REQUIRED_FILES, "2026-05-31T03:00:00Z")
    assert "[GELB]" in report
    assert "**X**" in report
    assert "**2**" in report


def test_drift_cell_active_over_threshold_is_highlighted() -> None:
    assert audit.drift_cell(68, active=True, threshold=5) == "**+68**"


def test_drift_cell_active_under_threshold_not_highlighted() -> None:
    assert audit.drift_cell(3, active=True, threshold=5) == "+3"


def test_drift_cell_inactive_repo_no_alarm() -> None:
    # 99 Commits Drift, aber Repo seit Wochen nicht gepusht -> kein Alarm.
    assert audit.drift_cell(99, active=False, threshold=5) == "—"


def test_drift_cell_missing_status_is_neutral() -> None:
    assert audit.drift_cell(None, active=True, threshold=5) == "—"


def test_count_drift_only_active_over_threshold() -> None:
    drift = {
        "alt-aktiv": {"active": True, "commits_since": 68},   # zaehlt
        "klein-aktiv": {"active": True, "commits_since": 2},  # unter Schwelle
        "alt-inaktiv": {"active": False, "commits_since": 40},  # inaktiv
        "ohne-status": {"active": True, "commits_since": None},  # keine STATUS.md
    }
    assert audit.count_drift(drift, threshold=5) == 1


def test_build_report_with_drift_adds_column_and_metric() -> None:
    files = {name: True for name in audit.REQUIRED_FILES}
    results = {"repo-c": files}
    drift = {"repo-c": {"active": True, "commits_since": 68}}
    report = audit.build_report(results, audit.REQUIRED_FILES,
                                "2026-06-08T03:00:00Z", drift=drift)
    assert "DRIFT" in report
    assert "**+68**" in report
    assert "veraltet" in report
    assert "[GELB]" in report  # Drift macht den Bericht gelb, auch wenn alle Dateien da


def test_build_report_without_drift_is_backward_compatible() -> None:
    # Alte Signatur (ohne drift) -> keine DRIFT-Spalte, GRUEN bei Vollstaendigkeit.
    results = {"repo-a": {name: True for name in audit.REQUIRED_FILES}}
    report = audit.build_report(results, audit.REQUIRED_FILES, "2026-06-08T03:00:00Z")
    assert "DRIFT" not in report
    assert "[GRUEN]" in report


def _run() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as error:
            failures += 1
            print(f"FAIL {test.__name__}: {error}")
    print(f"\n{len(tests) - failures}/{len(tests)} Tests bestanden.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run())

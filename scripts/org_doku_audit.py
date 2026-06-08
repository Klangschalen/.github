#!/usr/bin/env python3
"""Org-weiter Doku-Audit ueber alle Klangschalen-Repos.

Prueft pro Repo, ob die Pflicht-Dokumentationsdateien existieren, und baut einen
Markdown-Sammelbericht mit Ampel-Tabelle. Der Bericht wird vom Workflow als
(immer dasselbe) Issue in Klangschalen/.github gepostet bzw. aktualisiert.

Netzwerkzugriffe laufen ueber die `gh` CLI (im Workflow vorhanden). Die reine
Berichts-Logik (build_report, parse_repo_list, summarize) ist davon getrennt
und ohne Netz testbar: `python3 scripts/test_org_doku_audit.py`.

Aufruf im Workflow:
    python3 scripts/org_doku_audit.py --org Klangschalen --out report.md
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone

REQUIRED_FILES = [
    "README.md",
    "CHANGELOG.md",
    "STATUS.md",
    "LICENSE",
    "SECURITY.md",
    ".gitignore",
    ".editorconfig",
]

# Drift = STATUS.md hinkt dem Code hinterher. Praesenz allein reicht nicht: eine
# alte STATUS.md bei +68 Commits ist "vorhanden", aber wertlos. Diese zweite
# Dimension faengt genau das (Anlass: claude-config 2026-06-08).
#
# Bewusst KEINE "nur aktive Repos"-Grenze (Frank 2026-06-08): eine veraltete
# STATUS.md ist veraltet, egal ob der letzte Push gestern oder vor 3 Wochen war.
# Die Drift haengt allein an "Commits seit letztem STATUS.md-Stand", nicht am Push-Alter.
DRIFT_THRESHOLD = 5   # Drift ab >N Commits seit letztem STATUS.md-Stand


def parse_repo_list(json_text: str) -> list[str]:
    """Liest `gh repo list --json name,isArchived`-Ausgabe; ueberspringt Archivierte."""
    try:
        repos = json.loads(json_text)
    except json.JSONDecodeError:
        return []
    return sorted(
        repo["name"]
        for repo in repos
        if isinstance(repo, dict) and repo.get("name") and not repo.get("isArchived")
    )


def summarize(results: dict[str, dict[str, bool]]) -> dict[str, int]:
    """Zaehlt Repos gesamt / vollstaendig / mit Luecken + Gesamtzahl fehlender Dateien."""
    total = len(results)
    complete = sum(1 for files in results.values() if all(files.values()))
    missing_files = sum(
        1 for files in results.values() for present in files.values() if not present
    )
    return {
        "repos_total": total,
        "repos_complete": complete,
        "repos_incomplete": total - complete,
        "missing_files_total": missing_files,
    }


def drift_cell(commits_since, threshold: int = DRIFT_THRESHOLD) -> str:
    """Tabellen-Label der STATUS-Drift-Spalte (reine Logik, ohne Netz testbar).

    `commits_since is None`  -> STATUS.md fehlt/unbekannt (Praesenz-Spalte zeigt das).
    > threshold              -> hervorgehobener Drift-Wert (egal wie alt der Push).
    """
    if commits_since is None:
        return "—"
    if commits_since > threshold:
        return f"**+{commits_since}**"
    return f"+{commits_since}" if commits_since > 0 else "ok"


def count_drift(drift: dict, threshold: int = DRIFT_THRESHOLD) -> int:
    """Zaehlt Repos, deren STATUS.md > threshold Commits hinterherhinkt (ohne Aktiv-Grenze)."""
    return sum(
        1
        for info in drift.values()
        if (info.get("commits_since") or 0) > threshold
    )


def build_report(
    results: dict[str, dict[str, bool]],
    required_files: list[str],
    generated_at: str,
    drift: dict | None = None,
) -> str:
    """Baut den Markdown-Sammelbericht (Ampel-Tabelle + Kennzahlen).

    `drift` ist optional: ein dict {repo: {"commits_since": int|None}}.
    Fehlt es (None), bleibt der Bericht wie zuvor (Praesenz-only, rueckwaerts-kompatibel).
    Liegt es vor, kommt eine DRIFT-Spalte + Drift-Kennzahl dazu.
    """
    stats = summarize(results)
    drift_count = count_drift(drift) if drift else 0
    has_gap = stats["repos_incomplete"] > 0 or drift_count > 0
    health = "GELB" if has_gap else "GRUEN"

    short = {"README.md": "READ", "CHANGELOG.md": "CHLOG", "STATUS.md": "STAT",
             "LICENSE": "LIC", "SECURITY.md": "SEC", ".gitignore": "GIT",
             ".editorconfig": "EDIT"}
    header_cells = [short.get(name, name) for name in required_files]

    lines = [
        "<!-- org-doku-audit -->",
        f"# [{health}] Org Doku-Audit {generated_at[:10]}",
        "",
        f"**Repos geprueft:** {stats['repos_total']}  ",
        f"**Vollstaendig:** {stats['repos_complete']}  ",
        f"**Mit Luecken:** {stats['repos_incomplete']}  ",
        f"**Fehlende Dateien gesamt:** {stats['missing_files_total']}",
    ]
    if drift is not None:
        lines.append(f"**STATUS.md veraltet (>{DRIFT_THRESHOLD} Commits seit Stand):** {drift_count}")
    lines += [
        "",
        "Spalten: " + " · ".join(f"`{short.get(n, n)}`={n}" for n in required_files),
        "",
    ]

    drift_header = " DRIFT |" if drift is not None else ""
    drift_sep = ":--:|" if drift is not None else ""
    lines += [
        "| Repo | " + " | ".join(header_cells) + " | Luecken |" + drift_header,
        "|---|" + "|".join([":--:"] * len(required_files)) + "|:--:|" + drift_sep,
    ]

    for repo in sorted(results):
        files = results[repo]
        cells = ["OK" if files.get(name) else "**X**" for name in required_files]
        gaps = sum(1 for name in required_files if not files.get(name))
        gap_label = "—" if gaps == 0 else f"**{gaps}**"
        row = f"| `{repo}` | " + " | ".join(cells) + f" | {gap_label} |"
        if drift is not None:
            info = drift.get(repo, {})
            row += f" {drift_cell(info.get('commits_since'))} |"
        lines.append(row)

    drift_legend = (
        " · `DRIFT` = Commits seit letztem STATUS.md-Stand "
        f"(hervorgehoben ab >{DRIFT_THRESHOLD}, unabhaengig vom Push-Alter)"
        if drift is not None else ""
    )
    lines += [
        "",
        "> `OK` = vorhanden · `X` = fehlt" + drift_legend + ". Quelle der Pflichtliste: "
        "`CHECK-STANDARD.md` bzw. `doku-lint.yml` in `Klangschalen/.github`.",
        "",
        f"*Automatisch erzeugt am {generated_at} von `org-doku-audit.yml`.*",
    ]
    return "\n".join(lines) + "\n"


def _gh(args: list[str]) -> str:
    """Fuehrt `gh <args>` aus und gibt stdout zurueck ("" bei Fehler)."""
    try:
        completed = subprocess.run(
            ["gh", *args], capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"  gh-Fehler ({' '.join(args)}): {error}", file=sys.stderr)
        return ""
    if completed.returncode != 0:
        print(
            f"  gh rc={completed.returncode} ({' '.join(args)}): "
            f"{completed.stderr.strip()[:160]}",
            file=sys.stderr,
        )
    return completed.stdout


def list_repos(org: str) -> list[str]:
    return parse_repo_list(
        _gh(["repo", "list", org, "--no-archived", "--limit", "200",
             "--json", "name,isArchived"])
    )


def file_exists(org: str, repo: str, path: str) -> bool:
    """True wenn die Datei im Default-Branch existiert (gh api contents -> 200)."""
    try:
        completed = subprocess.run(
            ["gh", "api", "-i", f"repos/{org}/{repo}/contents/{path}"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    first_line = completed.stdout.splitlines()[0] if completed.stdout else ""
    return " 200" in first_line


def collect_results(org: str, repos: list[str], required_files: list[str]) -> dict:
    results: dict[str, dict[str, bool]] = {}
    for repo in repos:
        results[repo] = {name: file_exists(org, repo, name) for name in required_files}
        print(f"  geprueft: {repo}", file=sys.stderr)
    return results


def default_branch(org: str, repo: str) -> str:
    """Default-Branch eines Repos; "master" bei Fehler."""
    raw = _gh(["api", f"repos/{org}/{repo}", "--jq", ".default_branch"]).strip()
    return raw or "master"


def status_last_commit_date(org: str, repo: str, branch: str) -> str | None:
    """ISO-Datum des letzten STATUS.md-Commits auf dem Default-Branch; None wenn keins."""
    raw = _gh(["api",
               f"repos/{org}/{repo}/commits?path=STATUS.md&sha={branch}&per_page=1",
               "--jq",
               'if type=="array" then (.[0].commit.committer.date // "") else "" end']).strip()
    return raw or None


def commits_since(org: str, repo: str, branch: str, since_date: str) -> int:
    """Commits auf dem Default-Branch seit `since_date`, ohne den STATUS-Commit selbst."""
    raw = _gh(["api",
               f"repos/{org}/{repo}/commits?sha={branch}&since={since_date}&per_page=100",
               "--jq", "length"]).strip()
    try:
        count = int(raw or "0")
    except ValueError:
        count = 0
    return max(0, count - 1)


def collect_drift(org: str, repos: list[str]) -> dict:
    """Erhebt pro Repo die STATUS.md-Drift (Commits seit letztem STATUS.md-Stand)."""
    drift: dict[str, dict] = {}
    for repo in repos:
        branch = default_branch(org, repo)
        sdate = status_last_commit_date(org, repo, branch)
        since = commits_since(org, repo, branch, sdate) if sdate else None
        drift[repo] = {"commits_since": since}
        print(f"  drift: {repo} commits_since={since}", file=sys.stderr)
    return drift


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--org", default="Klangschalen")
    parser.add_argument("--out", required=True, help="Markdown-Output-Pfad")
    args = parser.parse_args()

    repos = list_repos(args.org)
    if not repos:
        print("Keine Repos gefunden (Token-Rechte? gh eingeloggt?).", file=sys.stderr)
        return 1

    results = collect_results(args.org, repos, REQUIRED_FILES)
    drift = collect_drift(args.org, repos)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = build_report(results, REQUIRED_FILES, generated_at, drift=drift)

    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(report)

    stats = summarize(results)
    print(report)
    print(
        f"Audit: {stats['repos_total']} Repos, "
        f"{stats['repos_incomplete']} mit Luecken, "
        f"{stats['missing_files_total']} fehlende Dateien, "
        f"{count_drift(drift)} mit veralteter STATUS.md.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

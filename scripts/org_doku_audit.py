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


def build_report(
    results: dict[str, dict[str, bool]],
    required_files: list[str],
    generated_at: str,
) -> str:
    """Baut den Markdown-Sammelbericht (Ampel-Tabelle + Kennzahlen)."""
    stats = summarize(results)
    health = "GRUEN" if stats["repos_incomplete"] == 0 else "GELB"

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
        "",
        "Spalten: " + " · ".join(f"`{short.get(n, n)}`={n}" for n in required_files),
        "",
        "| Repo | " + " | ".join(header_cells) + " | Luecken |",
        "|---|" + "|".join([":--:"] * len(required_files)) + "|:--:|",
    ]

    for repo in sorted(results):
        files = results[repo]
        cells = ["OK" if files.get(name) else "**X**" for name in required_files]
        gaps = sum(1 for name in required_files if not files.get(name))
        gap_label = "—" if gaps == 0 else f"**{gaps}**"
        lines.append(f"| `{repo}` | " + " | ".join(cells) + f" | {gap_label} |")

    lines += [
        "",
        "> `OK` = vorhanden · `X` = fehlt. Quelle der Pflichtliste: "
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
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = build_report(results, REQUIRED_FILES, generated_at)

    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(report)

    stats = summarize(results)
    print(report)
    print(
        f"Audit: {stats['repos_total']} Repos, "
        f"{stats['repos_incomplete']} mit Luecken, "
        f"{stats['missing_files_total']} fehlende Dateien.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

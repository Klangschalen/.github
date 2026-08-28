#!/usr/bin/env python3
"""Audit active GitHub Actions workflows across an organization.

The scanner reads only workflow files directly below ``.github/workflows`` on
each non-archived repository's default branch. It reports two supply-chain
risks:

* JavaScript actions whose ``action.yml`` targets an older Node runtime.
* External actions that are not pinned to a full 40-character commit SHA.

Network access is deliberately isolated in the ``GitHub`` class. Parsing,
classification, and report generation are testable without credentials.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from urllib.parse import quote


USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*['\"]?([^'\"\s#]+)", re.MULTILINE)
NODE_RE = re.compile(r"^\s*using:\s*['\"]?(node\d+)", re.MULTILINE | re.IGNORECASE)
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


@dataclass(frozen=True)
class ActionRef:
    owner: str
    repo: str
    path: str
    ref: str

    @property
    def spec(self) -> str:
        target = f"{self.owner}/{self.repo}"
        if self.path:
            target += f"/{self.path}"
        return f"{target}@{self.ref}"


@dataclass(frozen=True)
class Use:
    repo: str
    workflow: str
    line: int
    spec: str


@dataclass(frozen=True)
class Finding:
    kind: str
    repo: str
    workflow: str
    line: int
    action: str
    detail: str


def parse_uses(text: str, repo: str, workflow: str) -> list[Use]:
    """Return active ``uses:`` entries; commented examples are ignored."""
    uses: list[Use] = []
    for match in USES_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        uses.append(Use(repo, workflow, line, match.group(1)))
    return uses


def parse_action_ref(spec: str) -> ActionRef | None:
    """Parse a remote action; return None for local, Docker, or reusable workflows."""
    if spec.startswith("./") or spec.startswith("docker://") or "@" not in spec:
        return None
    target, ref = spec.rsplit("@", 1)
    parts = target.split("/")
    if len(parts) < 2 or not ref:
        return None
    path = "/".join(parts[2:])
    if path.endswith((".yml", ".yaml")):
        return None
    return ActionRef(parts[0], parts[1], path, ref)


def extract_node_runtime(manifest: str) -> str | None:
    match = NODE_RE.search(manifest)
    return match.group(1).lower() if match else None


def is_full_sha(ref: str) -> bool:
    return bool(FULL_SHA_RE.fullmatch(ref))


def classify_use(
    use: Use,
    action: ActionRef,
    manifest: str,
    organization: str,
    required_node: str,
) -> list[Finding]:
    findings: list[Finding] = []
    runtime = extract_node_runtime(manifest)
    if runtime and runtime != required_node:
        findings.append(Finding(
            "runtime", use.repo, use.workflow, use.line, action.spec,
            f"deklariert {runtime}; erwartet {required_node}",
        ))
    if action.owner.lower() != organization.lower() and not is_full_sha(action.ref):
        findings.append(Finding(
            "pin", use.repo, use.workflow, use.line, action.spec,
            "externe Action nicht auf vollständige Commit-SHA gepinnt",
        ))
    return findings


def build_report(
    *,
    organization: str,
    generated_at: str,
    required_node: str,
    repo_count: int,
    workflow_count: int,
    use_count: int,
    findings: list[Finding],
    errors: list[str],
) -> str:
    status = "ROT" if errors else ("GELB" if findings else "GRUEN")
    runtime_count = sum(item.kind == "runtime" for item in findings)
    pin_count = sum(item.kind == "pin" for item in findings)
    lines = [
        "<!-- org-action-runtime-audit -->",
        f"# [{status}] Org Action-Runtime-Audit {generated_at[:10]}",
        "",
        f"**Organisation:** `{organization}`  ",
        f"**Repos / aktive Workflow-Dateien / uses:** {repo_count} / {workflow_count} / {use_count}  ",
        f"**Veraltete Node-Runtimes:** {runtime_count}  ",
        f"**Ungepinnte externe Actions:** {pin_count}  ",
        f"**Nicht vollständig lesbare Stellen:** {len(errors)}",
        "",
        f"Soll-Runtime: `{required_node}`. Gezählt werden nur aktive `.yml`/`.yaml`-Dateien direkt unter `.github/workflows` im Default-Branch; Archive, `.disabled` und kommentierte Beispiele zählen nicht.",
        "",
    ]
    if findings:
        lines += [
            "## Befunde",
            "",
            "| Art | Repo | Workflow:Zeile | Action | Befund |",
            "|---|---|---|---|---|",
        ]
        labels = {"runtime": "Runtime", "pin": "SHA-Pin"}
        for item in sorted(findings, key=lambda x: (x.repo, x.workflow, x.line, x.kind)):
            lines.append(
                f"| {labels[item.kind]} | `{item.repo}` | `{item.workflow}:{item.line}` | "
                f"`{item.action}` | {item.detail} |"
            )
        lines.append("")
    if errors:
        lines += ["## Scan unvollständig", ""]
        lines += [f"- {error}" for error in errors]
        lines.append("")
    if not findings and not errors:
        lines += ["Keine Abweichung gefunden.", ""]
    lines += [
        "## Bedeutung",
        "",
        "- Runtime-Befund: Die Action läuft nicht nativ auf der festgelegten Runner-Runtime.",
        "- SHA-Pin-Befund: Ein beweglicher Tag kann sich ohne Änderung im aufrufenden Repo verändern.",
        "- ROT bedeutet: Der Scan selbst war unvollständig; fehlende Daten werden nie als sauber gewertet.",
        "",
        f"*Automatisch erzeugt am {generated_at} von `org-action-runtime-audit.yml`.*",
    ]
    return "\n".join(lines) + "\n"


class GitHub:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def _run(self, args: list[str], *, raw: bool = False) -> str | None:
        command = ["gh", *args]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as error:
            self.errors.append(f"`{' '.join(command)}`: {error}")
            return None
        if completed.returncode != 0:
            detail = completed.stderr.strip().splitlines()[-1:] or [f"rc={completed.returncode}"]
            self.errors.append(f"`{' '.join(command)}`: {detail[0][:200]}")
            return None
        return completed.stdout if raw else completed.stdout.strip()

    def json(self, endpoint: str) -> object | None:
        raw = self._run(["api", endpoint])
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as error:
            self.errors.append(f"`{endpoint}`: ungültiges JSON ({error})")
            return None

    def raw(self, endpoint: str, *, record_missing: bool = True) -> str | None:
        before = len(self.errors)
        value = self._run([
            "api", "-H", "Accept: application/vnd.github.raw+json", endpoint,
        ], raw=True)
        if value is None and not record_missing and len(self.errors) > before:
            self.errors.pop()
        return value

    def repositories(self, organization: str) -> list[tuple[str, str]]:
        raw = self._run([
            "repo", "list", organization, "--no-archived", "--limit", "200",
            "--json", "name,isArchived,defaultBranchRef",
        ])
        if raw is None:
            return []
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as error:
            self.errors.append(f"Repo-Liste: ungültiges JSON ({error})")
            return []
        repos = []
        for item in data:
            branch = (item.get("defaultBranchRef") or {}).get("name")
            if item.get("name") and branch and not item.get("isArchived"):
                repos.append((item["name"], branch))
        return sorted(repos)

    def workflows(self, organization: str, repo: str, branch: str) -> list[tuple[str, str]]:
        endpoint = f"repos/{organization}/{repo}/contents/.github/workflows?ref={quote(branch, safe='')}"
        before = len(self.errors)
        data = self.json(endpoint)
        if data is None:
            # A missing workflow directory is normal, not an incomplete scan.
            if len(self.errors) > before:
                last = self.errors[-1]
                if "404" in last or "Not Found" in last:
                    self.errors.pop()
            return []
        if not isinstance(data, list):
            self.errors.append(f"`{organization}/{repo}`: Workflow-Verzeichnis ist keine Liste")
            return []
        result = []
        for item in data:
            name = item.get("name", "")
            if item.get("type") == "file" and name.endswith((".yml", ".yaml")):
                result.append((item["path"], branch))
        return result

    def workflow_text(self, organization: str, repo: str, path: str, branch: str) -> str | None:
        encoded = "/".join(quote(part, safe="") for part in PurePosixPath(path).parts)
        return self.raw(f"repos/{organization}/{repo}/contents/{encoded}?ref={quote(branch, safe='')}")

    def manifest(self, action: ActionRef) -> str | None:
        base = f"repos/{action.owner}/{action.repo}/contents/"
        if action.path:
            base += "/".join(quote(part, safe="") for part in PurePosixPath(action.path).parts) + "/"
        ref = quote(action.ref, safe="")
        first = self.raw(f"{base}action.yml?ref={ref}", record_missing=False)
        if first is not None:
            return first
        return self.raw(f"{base}action.yaml?ref={ref}", record_missing=False)


def scan(
    organization: str,
    required_node: str,
    min_repos: int = 1,
) -> tuple[int, int, int, list[Finding], list[str]]:
    github = GitHub()
    repos = github.repositories(organization)
    if not repos:
        github.errors.append("Keine Repositories gefunden; Token-Rechte oder Anmeldung prüfen.")
        return 0, 0, 0, [], github.errors
    if len(repos) < min_repos:
        github.errors.append(
            f"Nur {len(repos)} Repositories sichtbar; mindestens {min_repos} erwartet. "
            "ORG_AUDIT_TOKEN und Repository-Zugriff prüfen."
        )

    all_uses: list[Use] = []
    workflow_count = 0
    for repo, branch in repos:
        for path, workflow_branch in github.workflows(organization, repo, branch):
            text = github.workflow_text(organization, repo, path, workflow_branch)
            if text is None:
                continue
            workflow_count += 1
            all_uses.extend(parse_uses(text, repo, path))

    manifests: dict[ActionRef, str | None] = {}
    findings: list[Finding] = []
    for use in all_uses:
        action = parse_action_ref(use.spec)
        if action is None:
            continue
        if action not in manifests:
            manifests[action] = github.manifest(action)
        manifest = manifests[action]
        if manifest is None:
            github.errors.append(f"`{use.repo}/{use.workflow}:{use.line}`: Manifest für `{action.spec}` nicht lesbar")
            continue
        findings.extend(classify_use(use, action, manifest, organization, required_node))

    # Avoid duplicate messages from a missing action.yml + action.yaml pair or repeated uses.
    errors = list(dict.fromkeys(github.errors))
    findings = list(dict.fromkeys(findings))
    return len(repos), workflow_count, len(all_uses), findings, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--org", default="Klangschalen")
    parser.add_argument("--required-node", default="node24")
    parser.add_argument(
        "--min-repos", type=int, default=1,
        help="Fail-closed, wenn weniger nicht-archivierte Repositories sichtbar sind",
    )
    parser.add_argument("--out", required=True)
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args()

    repo_count, workflow_count, use_count, findings, errors = scan(
        args.org, args.required_node.lower(), args.min_repos
    )
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = build_report(
        organization=args.org,
        generated_at=generated_at,
        required_node=args.required_node.lower(),
        repo_count=repo_count,
        workflow_count=workflow_count,
        use_count=use_count,
        findings=findings,
        errors=errors,
    )
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(report)
    print(report)
    if errors:
        return 2
    if findings and args.fail_on_findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

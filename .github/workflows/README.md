# Zentrale Klangschalen-Workflows

## doku-lint.yml

Wiederverwendbare Action, die in jedem Klangschalen-Repo per `uses:`
eingebunden wird. Prueft 3 Gates:

1. Pflicht-Dateien vorhanden (LICENSE, CHANGELOG, STATUS, CONTRIBUTING, SECURITY, ...)
2. CHANGELOG.md beruehrt bei Code-Aenderung
3. Conventional Commit Format

### Einbindung in einem Repo

```yaml
# .github/workflows/doku-lint.yml im Ziel-Repo
name: Doku-Lint
on: [push, pull_request]
jobs:
  lint:
    uses: Klangschalen/.github/.github/workflows/doku-lint.yml@main
    with:
      pflicht_dateien: "README.md,LICENSE,CHANGELOG.md,STATUS.md,CONTRIBUTING.md,SECURITY.md,.editorconfig,.gitignore"
      warn_only: true
```

### Modi

- `warn_only: true` (Default): meldet als Warnung, blockt PR nicht
- `warn_only: false`: meldet als Fehler, blockt PR (rote Pruefung)

Empfehlung: 2 Wochen `warn_only: true`, dann auf `false` umstellen.

## claim-lint.yml

Wiederverwendbare Action, die PR-Beschreibungen und neue CHANGELOG-Zeilen
gegen unbelegte Vollstaendigkeits-Behauptungen prueft ("vollstaendig",
"alles geprueft", "komplett geprueft" ohne begleitende Zahlen wie
"X von Y" oder "X/Y"). Rein deterministisch (Bash/Regex), kein LLM-Call,
keine Kosten, keine Latenz.

**Hintergrund:** portiert dieselbe Pruef-Logik wie der lokale PostToolUse-
Hook `claude-config/hooks/no-fake-completeness.sh` (seit 07.04.2026 aktiv),
der nur auf Franks Maschine feuert - nicht in Cloud-Sessions oder
Background-Subagenten. Genau dort ist am 16.08.2026 in
`engineering-principles` PR #12 eine unbelegte Vollstaendigkeits-Behauptung
durchgerutscht (siehe `engineering-principles/LEARNINGS.md` L-035/L-036).

### Einbindung in einem Repo

```yaml
# .github/workflows/claim-lint.yml im Ziel-Repo
name: Claim-Lint
on: [pull_request]
permissions:
  contents: read
  pull-requests: read
jobs:
  claim-lint:
    uses: Klangschalen/.github/.github/workflows/claim-lint.yml@main
    with:
      warn_only: true
    permissions:
      contents: read
      pull-requests: read
    secrets: inherit
```

### Modi

- `warn_only: true` (Default): meldet als Warnung, blockt PR nicht
- `warn_only: false`: meldet als Fehler, blockt PR (rote Pruefung)

Empfehlung: wie bei doku-lint.yml zunaechst `warn_only: true`, nach
Bewaehrung auf `false` umstellen.

## org-action-runtime-audit.yml

Taeglicher organisationsweiter Waechter fuer aktive GitHub-Actions-Workflows.
Er liest mit `ORG_AUDIT_TOKEN` alle nicht archivierten Repositories und
aktualisiert ein einziges Sammel-Issue in `Klangschalen/.github`.

Er meldet:

1. JavaScript-Actions, deren `action.yml` nicht `node24` verwendet.
2. Externe Actions ohne vollständigen 40-stelligen Commit-SHA-Pin.
3. Unvollständige Scans, insbesondere wenn weniger als 41 Repositories sichtbar sind.

Der dritte Punkt ist fail-closed: Verliert das Token Zugriff, wird der Lauf rot
und darf nicht als sauber interpretiert werden. Aktuelle Befunde bleiben
zunächst ein weicher, sichtbarer Bestand im Sammel-Issue; die einzelnen
Korrekturen laufen kontrolliert als PR je Repository.


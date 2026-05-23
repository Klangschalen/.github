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

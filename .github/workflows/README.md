# Zentrale Klangschalen-Workflows

## doku-lint.yml

Der wiederverwendbare Doku-Lint prüft drei getrennte Gates:

1. Pflicht-Dateien sind vorhanden.
2. Code-Änderungen besitzen einen Changelog-Beleg.
3. Der letzte Quell-Commit nutzt ein erlaubtes Conventional-Commit-Format.

Bei Pull Requests lädt der Workflow immer den **exakten PR-Head**. Er prüft
nicht den von GitHub erzeugten synthetischen Merge-Commit. Damit bleibt das
Ergebnis unabhängig von der Checkout-Voreinstellung und zeigt den tatsächlich
eingereichten Commit.

### Changelog-Belege

Code-Änderungen können auf zwei Arten dokumentiert werden:

- Die bestehende Stammdatei `CHANGELOG.md` wird ergänzt.
- Ein versionierter Schnipsel unter `CHANGELOG.d/*.md` wird hinzugefügt.

Schnipsel eignen sich für große oder häufig geänderte Changelogs. Sie halten
den Pull Request klein und vermeiden, dass mehrere Arbeitszweige dieselbe
Stammdatei gleichzeitig ändern. Textdateien außerhalb von `CHANGELOG.d/` und
andere Dateiendungen zählen nicht als Beleg.

Beispiel:

```text
CHANGELOG.d/2026-09-04-doku-lint-central-contract.md
```

### Erlaubte Commit-Typen

Der Standard erlaubt diese Typen:

- `feat`
- `fix`
- `docs`
- `style`
- `refactor`
- `test`
- `chore`
- `perf`
- `build`
- `ci`
- `revert`
- `policy`

Richtlinien können direkt mit `policy:` beginnen. Alternativ passt
`docs(policy):`, wenn vor allem die Dokumentation einer Regel geändert wird.

Beispiele:

```text
policy: require canonical pull-request links
docs(policy): explain the canonical-link rule
fix(doku-lint): check the exact pull-request head
```

### Einbindung in einem Repository

```yaml
# .github/workflows/doku-lint.yml im Ziel-Repository
name: Doku-Lint

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

permissions:
  contents: read

jobs:
  lint:
    uses: Klangschalen/.github/.github/workflows/doku-lint.yml@<40-STELLIGE-SHA>
    with:
      pflicht_dateien: "README.md,LICENSE,CHANGELOG.md,STATUS.md,CONTRIBUTING.md,SECURITY.md,.editorconfig,.gitignore"
      warn_only: true
      commit_format_warn_only: false
    permissions:
      contents: read
    secrets: inherit
```

Eine vollständige Commit-SHA schützt vor unbemerkten Änderungen des zentralen
Workflows. `@main` verteilt neue Versionen sofort, bietet aber keine feste
Version für einen bereits geprüften Caller.

### Modi

- `warn_only: true` macht Gate 1 und Gate 2 zu Hinweisen.
- `warn_only: false` blockiert bei fehlenden Dateien oder fehlendem Changelog-Beleg.
- `commit_format_warn_only: false` blockiert Gate 3. Das ist der Standard.
- `commit_format_warn_only: true` dient nur einer klar begrenzten Übergangsphase.

Caller dürfen `allowed_commit_types` überschreiben. Jede Abweichung muss im
Repository dokumentiert und getestet werden. Der organisationsweite Standard
enthält `policy`, damit Richtlinien-Commits nicht erneut an einer versteckten
Regex scheitern.

### Fehler lesen

Die Ausgabe nennt:

- den geprüften Quell-Commit,
- den gefundenen Commit-Titel,
- den nicht erlaubten Typ,
- alle erlaubten Typen,
- ein passendes Beispiel für Richtlinien,
- den fehlenden Changelog-Beleg und die betroffenen Code-Dateien.

Ein Draft-Pull-Request bleibt unabhängig davon ein Draft. Der Doku-Lint ändert
keinen Review- oder Freigabestatus.

## doku-lint-contract.yml

Der Vertragstest läuft bei Änderungen am Doku-Lint. Er verhindert diese
Rückfälle:

- Checkout des synthetischen Merge-Commits,
- Commit-Prüfung ohne explizite Quell-SHA,
- Rückkehr des unsicheren `HEAD~1`-Fallbacks,
- Entfernung des Typs `policy`,
- Entfernung von `CHANGELOG.d/*.md` als gültigem Beleg,
- versehentliches Zurückstellen von Gate 3 auf Warnmodus,
- Abweichung zwischen Workflow und Dokumentation.

## claim-lint.yml

Der wiederverwendbare Claim-Lint prüft PR-Beschreibungen und neue
Changelog-Zeilen gegen unbelegte Vollständigkeitsbehauptungen. Die Prüfung
arbeitet deterministisch mit Bash und regulären Ausdrücken.

### Einbindung

```yaml
name: Claim-Lint

on: [pull_request]

permissions:
  contents: read
  pull-requests: read

jobs:
  claim-lint:
    uses: Klangschalen/.github/.github/workflows/claim-lint.yml@<40-STELLIGE-SHA>
    with:
      warn_only: true
    permissions:
      contents: read
      pull-requests: read
    secrets: inherit
```

## org-action-runtime-audit.yml

Der tägliche organisationsweite Wächter prüft aktive GitHub-Actions-Workflows.
Er meldet insbesondere:

1. JavaScript-Actions ohne Node 24.
2. Externe Actions ohne vollständigen Commit-SHA-Pin.
3. Unvollständige Scans mit zu geringer Repository-Abdeckung.

Der Abdeckungsfehler arbeitet fail-closed. Einzelne technische Befunde bleiben
sichtbar und werden kontrolliert über Pull Requests behoben.

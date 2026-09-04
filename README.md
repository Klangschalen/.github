# Klangschalen Org-Verwaltung

Dieses Repository enthält organisationsweite Standards, die andere
Klangschalen-Repositories einbinden.

## Was hier liegt

| Datei | Zweck |
|---|---|
| `.github/workflows/doku-lint.yml` | Wiederverwendbarer Doku-Lint mit Prüfung des exakten PR-Heads |
| `.github/workflows/doku-lint-contract.yml` | Fail-closed Rückfalltest für Quellbindung, Commit-Typen und Dokumentation |
| `.github/workflows/claim-lint.yml` | Prüft unbelegte Vollständigkeitsbehauptungen |
| `.github/workflows/org-doku-audit.yml` | Nächtlicher Doku-Audit über alle sichtbaren Repositories |
| `.github/workflows/org-action-runtime-audit.yml` | Prüft Action-Runtime und vollständige SHA-Pins |
| `.github/workflows/README.md` | Erklärt Einbindung, Modi und erlaubte Commit-Typen |
| `scripts/org_doku_audit.py` | Baut den organisationsweiten Doku-Bericht |
| `scripts/test_org_doku_audit.py` | Testet die Bericht-Logik ohne Netz |
| `scripts/test_doku_lint_contract.py` | Sichert den Doku-Lint-Vertrag gegen Rückfälle |

## Zwei Ebenen der Doku-Kontrolle

1. **Pro Pull Request:** `doku-lint.yml` prüft Pflicht-Dateien, den
   `CHANGELOG.md`-Touch und das Commit-Format. Bei Pull Requests bindet er sich
   an den exakten Quell-Commit statt an GitHubs synthetischen Merge-Commit.
2. **Nächtlich:** `org-doku-audit.yml` prüft alle sichtbaren, nicht
   archivierten Repositories und pflegt ein gemeinsames Sammel-Issue.

Der zentrale Commit-Standard erlaubt unter anderem `policy:`. Dadurch können
Richtlinien klar benannt werden, ohne an einer versteckten Typenliste zu
scheitern. Der eigene Vertragstest hält Workflow und Dokumentation synchron.

**Voraussetzung für den vollständigen nächtlichen Lauf:** Das Secret
`ORG_AUDIT_TOKEN` braucht organisationsweit `Contents: read` sowie
`Issues: write` auf diesem Repository. Ohne das Secret sieht der Workflow nur
den Umfang des normalen `GITHUB_TOKEN`.

## Rollout neuer Repositories

`Klangschalen/repo-template` enthält den Caller für den zentralen Doku-Lint.
Produktive Caller sollten eine geprüfte 40-stellige Commit-SHA verwenden.
Die aktuelle Einbindung und alle Schalter stehen in
`.github/workflows/README.md`.

## Hilfe

team@sound-spirit.de

# Klangschalen Org-Verwaltung

Dieses Repo (`.github` in der Organisation) enthaelt organisations-weite
Standards, die andere Repos einbinden:

- `.github/workflows/doku-lint.yml` - wiederverwendbare Doku-Lint-Action
- `.github/workflows/org-doku-audit.yml` - naechtlicher org-weiter Doku-Audit

## Was hier liegt

| Datei | Zweck |
|---|---|
| `.github/workflows/doku-lint.yml` | Zentrale Doku-Linter-Action, alle Repos binden sie ein (per PR) |
| `.github/workflows/org-doku-audit.yml` | Naechtlicher Audit ueber ALLE Repos, postet Sammel-Issue |
| `.github/workflows/README.md` | Erklaerung wie Repos die Action einbinden |
| `scripts/org_doku_audit.py` | Audit-Logik (Pflichtdateien pro Repo pruefen, Bericht bauen) |
| `scripts/test_org_doku_audit.py` | Tests der Bericht-Logik (ohne Netz) |

## Zwei Ebenen der Doku-Kontrolle

1. **Pro PR (sofort):** `doku-lint.yml` als reusable Workflow im jeweiligen Repo
   einbinden. Prueft beim Pull Request: Pflicht-Dateien vorhanden, CHANGELOG bei
   Code-Aenderung mit beruehrt, Conventional-Commit-Format.
2. **Naechtlich (Gesamtbild):** `org-doku-audit.yml` laeuft taeglich 03:00 UTC
   (und manuell via *Actions -> Run workflow*) und prueft in **allen** nicht-
   archivierten Repos, ob die Pflichtdateien existieren. Ergebnis: **ein**
   Sammel-Issue "Org Doku-Audit (automatisch)" mit Ampel-Tabelle, das bei jedem
   Lauf aktualisiert wird.

**Voraussetzung fuer den vollen naechtlichen Lauf:** ein Secret `ORG_AUDIT_TOKEN`
(Fine-grained PAT mit *Contents: read* org-weit + *Issues: write* auf `.github`).
Ohne dieses Secret nutzt der Workflow `GITHUB_TOKEN` und sieht nur dieses Repo.

## Roll-out neuer Repos

Nutze `Klangschalen/repo-template` als Vorlage (Use this template).
Die Workflow-Definition ist da bereits eingebunden.

## Hilfe

team@sound-spirit.de

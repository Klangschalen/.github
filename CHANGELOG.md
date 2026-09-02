# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Geändert

- fix(doku-lint): Gate 3 prueft bei Pull Requests den PR-Titel statt `git log -1` und nutzt den vollen Ausdruck aus claude-config `rules/commit-nachrichten-norm.md` (Klammer-Zusatz erlaubt, `ci`/`build`/`perf`/`style`/`revert` ergaenzt). Anlass: Nightly Repo-Check meldete am 01.09.2026 19 von 32 Commits faelschlich als unsauber, weil sie einen Zusatz wie `feat(hwg):` trugen; ausserdem prueft der letzte Rohcommit nie den PR-Titel, der bei Squash-Merge (`squash_merge_commit_title=PR_TITLE`) zur endgueltigen Commit-Nachricht wird. Details: `plans/commit-nachrichten-sauber-nightly.md` in claude-config.
- feat(actions): organisationsweiten Runtime-/SHA-Pin-Audit mit täglichem Sammel-Issue und fail-closed Zugriffskontrolle ergänzen
- chore(actions): zentrale Workflows auf Node-24-Actions mit vollständigen Commit-SHA-Pins aktualisieren
- feat(audit): Pflichtliste in KERN + Hygiene staffeln (#10)

[Unreleased]: https://github.com/Klangschalen/.github/commits/main

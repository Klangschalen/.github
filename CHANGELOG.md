# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Geändert

- fix(doku-lint): Code-Änderungen akzeptieren wahlweise `CHANGELOG.md` oder versionierte Schnipsel unter `CHANGELOG.d/*.md`
- test(doku-lint): positive und negative Pfadfälle sichern den Changelog-Beleg gegen Rückfälle
- docs(doku-lint): Einsatz und Grenzen von Changelog-Schnipseln erklären
- fix(doku-lint): Pull Requests werden am exakten Quell-Commit statt am synthetischen GitHub-Merge-Commit geprüft
- fix(doku-lint): Gate 3 erhält den eigenen Schalter `commit_format_warn_only` und blockiert standardmäßig
- feat(doku-lint): `policy` ist ein erlaubter Commit-Typ; Caller können die Typen über `allowed_commit_types` gezielt erweitern
- test(doku-lint): ein fail-closed Vertragstest schützt Quellbindung, Typenliste, Gate-Modus und Dokumentation vor Rückfällen
- docs(doku-lint): erlaubte Typen, Fehlerhilfe und sichere Caller-Einbindung dokumentieren
- fix(security): Gitleaks prüft Pull Requests nur noch im Bereich Basis-SHA bis Quell-SHA; fremde offene Zweige können den aktuellen Pull Request nicht mehr rot färben
- test(security): ein eigener Vertragslauf verhindert die Rückkehr zu `detect --source .` ohne begrenzten Git-Bereich
- feat(actions): organisationsweiten Runtime-/SHA-Pin-Audit mit täglichem Sammel-Issue und fail-closed Zugriffskontrolle ergänzen
- chore(actions): zentrale Workflows auf Node-24-Actions mit vollständigen Commit-SHA-Pins aktualisieren
- feat(audit): Pflichtliste in KERN + Hygiene staffeln (#10)

[Unreleased]: https://github.com/Klangschalen/.github/commits/main

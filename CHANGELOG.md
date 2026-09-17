# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Geändert

- fix(doku-lint): neues Gate 3b prüft bei Pull Requests zusätzlich den PR-Titel selbst gegen das Conventional-Commit-Format. Ursache: PR #26 (06.09.2026) hat Gate 3 auf Push für GitHub-erzeugte PR-/Squash-Commits bewusst abgeschaltet, weil der PR-Head bereits geprüft galt - das gilt aber nur für den letzten Branch-Commit, nicht für den PR-Titel. Bei einem Squash-Merge wird der PR-Titel unverändert zum Commit-Titel auf dem Zielzweig; ein PR mit konformen Einzel-Commits, aber nicht-konformem Titel, lief deshalb ungeprüft durch. Konkret beobachtet: `Klangschalen/website-audit` PR #19 (17.09.2026) - Commits `feat(audit): ...`/`fix(audit): ...` konform, Titel `Produktdaten-Lücke messen: ...` nicht, genau dieser Titel wurde zum Commit auf `master`.
- test(doku-lint): Vertragstest um Fälle für Gate 3b ergänzt (konformer/nicht-konformer PR-Titel, erlaubte/nicht erlaubte Typen)
- docs(doku-lint): Kommentarkopf erklärt die Squash-Merge-Lücke und warum Gate 3b sie schließt

### Hinzugefügt

- feat(michael-spiegel): wiederverwendbarer Workflow `michael-spiegel.yml` trägt den Ordner `uebergabe-michael/` eines internen Repositorys nach `Klangschalen/michael-arbeitsuebergabe` unter `eingang/<quell-repository>/` (push-basiert, Token nur in der Quelle, fail-closed gegen Zugangsdaten, interne Akten und Personendaten, löscht im Ziel nie); Vertragstest `scripts/test_michael_spiegel_contract.py` und Workflow `michael-spiegel-contract.yml`

### Geändert (frühere Einträge)

- fix(doku-lint): GitHub-erzeugte Merge-/PR-Commits werden auf dem Push nach einem bereits geprüften Pull Request nicht erneut wegen ihres synthetischen Titels blockiert; echte direkte Push-Commits bleiben hart am Conventional-Commit-Format geprüft
- test(doku-lint): Push-/Merge-Erkennung und GitHub-PR-Commit-Ausnahme sind im Vertragscheck abgesichert
- docs(doku-lint): das Verhalten nach Merge sowie die Grenze zu echten direkten Pushes ist dokumentiert
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

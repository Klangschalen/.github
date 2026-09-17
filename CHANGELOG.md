# Changelog

## 2026-09-17 - Der Deckungs-Waechter war zu 80 Prozent blind

`hwg-cross-repo-coverage.yml` las genau **einen von fuenf** Konsumenten - und schrieb das
sogar hin: `Deckung: HWG-Kernspiegel 1/5 Konsumenten gelesen`, dazu vier Mal
`Konsument nicht im Checkout (nicht pruefbar)`. Ausgecheckt wurden nur `quality-system`
(die Quelle) und `pl-sets`.

**Was das gekostet hat, ist belegbar:** Als der HWG-Spiegel am 31.08.2026 in VIER Repos
gleichzeitig veraltete, sah dieser Ablauf nur `pl-sets`. Die drei anderen (`adk-agents`,
`agenten-systeme`, `unified-agent-system`) fielen erst am 17.09. auf - siebzehn Tage spaeter
und ueber einen ganz anderen Weg. Haette er alle fuenf gelesen, waere der Drift sofort in
voller Breite sichtbar gewesen.

Ergaenzt: `adk-agents`, `unified-agent-system`, `claude-config`, `settext-studio`.

`continue-on-error` ist Absicht: Ein Konsument, der sich nicht auschecken laesst (fehlendes
Token, umbenanntes oder geloeschtes Repo), darf den ganzen Lauf nicht killen. Er erscheint
dann wie bisher als "nicht im Checkout" im Deckungsbericht - weniger Abdeckung, aber nie
falsches Gruen.

Zu `settext-studio` ausdruecklich: Ob dieses Repo noch existiert, liess sich am 17.09. **nicht**
pruefen - es liegt ausserhalb des Zugriffs der messenden Sitzung. Der Checkout steht trotzdem
drin, weil `continue-on-error` den Fehlerfall abfaengt. Die drei anderen wurden vor dem Einbau
geprueft: alle erreichbar, keines archiviert.


Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

## [Unreleased]

### Hinzugefügt

- feat(michael-spiegel): wiederverwendbarer Workflow `michael-spiegel.yml` trägt den Ordner `uebergabe-michael/` eines internen Repositorys nach `Klangschalen/michael-arbeitsuebergabe` unter `eingang/<quell-repository>/` (push-basiert, Token nur in der Quelle, fail-closed gegen Zugangsdaten, interne Akten und Personendaten, löscht im Ziel nie); Vertragstest `scripts/test_michael_spiegel_contract.py` und Workflow `michael-spiegel-contract.yml`

### Geändert

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

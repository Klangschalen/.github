# Changelog

## 2026-09-28 - HWG-Deckungslauf checkt agenten-systeme aus statt ein Repo, das es nicht gibt

`hwg-cross-repo-coverage.yml` war seit dem 17.09. jeden Tag rot, auch nach dem Eintragen von
ORG_AUDIT_TOKEN: Er checkte "Klangschalen/settext-studio" aus (GitHub: "Not Found", Lauf
36461139499) und den fuenften GitHub-Verbraucher agenten-systeme gar nicht. Der Checker
meldete deshalb "HWG-Kernspiegel 4/6" mit Rueckgabewert 2. settext-studio ist laut
`quality-system/tests/check-textdaten-drift.py` (HWG_KONSUMENTEN, `github_actions: False`)
ein lokales Arbeitsverzeichnis, kein Repo. Jetzt: agenten-systeme wird ausgecheckt, der
settext-studio-Checkout ist weg. Erwartung: "PASS (GitHub-Umfang) - 5/5 GitHub-Verbraucher".
Gefunden ueber den Waechter ueber den Waechtern (zentrale Issue 266, Buendel 1, nach
Korrektur).
## 2026-09-28 - Runtime-Audit schreibt sein Sammel-Issue wieder mit dem Lauf-Token

Seit ORG_AUDIT_TOKEN gesetzt ist (28.09.2026, bewusst nur lesend), scheiterte der
Schritt "Sammel-Issue erstellen oder aktualisieren" in `org-action-runtime-audit.yml`:
"Resource not accessible by personal access token (updateIssue)" (Laeufe 36462507615,
36462731681). Vorher griff der Rueckfall auf GITHUB_TOKEN mit `issues: write`. Jetzt
liest der Audit org-weit mit ORG_AUDIT_TOKEN und schreibt das Issue im eigenen Repo
mit `github.token`. Ein Lese-Token darf nie zum Schreib-Token werden, nur weil es da ist.

## 2026-09-28 - Archify-Löschschutz: Schutzlogik zuerst, Workflow danach

Pull Request 20 (02.09.2026) bringt den organisationsweiten Archify-Löschschutz:
Richtlinie `config/archify-presence-policy.json`, Prüfung
`scripts/archify_presence_guard.py`, Negativtests
`scripts/test_archify_presence_guard.py` und den Workflow
`archify-presence-guard.yml`. Der Workflow holt die Schutzlogik bewusst immer
von `main` dieses Repositories - so kann kein Pull Request Archify und den
Wächter gemeinsam entfernen. Genau deshalb war der PR rot (Lauf 33681861824,
02.09.2026): sein eigener Workflow suchte `test_archify_presence_guard.py` auf
`main`, wo die Datei noch nicht lag ("No such file or directory").

Den Bezug auf `main` zu lockern hiesse, den Schutz zu schwächen. Stattdessen
kommen Richtlinie, Prüfung und Tests mit diesem Eintrag zuerst auf `main`
(hier, ohne Workflow); der Workflow und die README-Erklärung folgen in Pull
Request 20, dessen Prüfung damit die Schutzlogik auf `main` findet. Gemessen
vor dem Merge: `python3 scripts/test_archify_presence_guard.py` meldet 5 von 5
bestanden; die Prüfung gegen dieses Repository mit der Richtlinie liefert GRUEN,
sobald der Workflow (PR 20) dazukommt.

## 2026-09-28 - Gate 3 macht aktualisierte Pull Requests nicht mehr rot

Wer im Pull Request "Update branch" drueckt, bekommt von GitHub den Kopf-Commit
`Merge branch 'main' into <zweig>`. Gate 3 bewertete diesen synthetischen Titel bei
`pull_request` wie einen Autoren-Commit und meldete ihn rot - belegt an
Klangschalen/unified-agent-system PR 18 (Lauf 36428109273, 28.09.2026: "Head-Commit ...
hat kein Conventional-Commit-Format: 'Merge branch 'master' into claude/...'"). Die
Push-Ausnahme fuer Merge-Commits gab es schon; sie galt nur nicht fuer `pull_request`.

Jetzt gilt sie auch dort: ein Merge-Commit am PR-Kopf wird nicht bewertet, der PR-Titel
bleibt durch Gate 3b blockierend geprueft, ein gewoehnlicher Kopf-Commit weiter durch Gate 3.
Ersetzt den Konflikt-Entwurf PR 19 (02.09.2026), dessen PR-Titel-Teil PR 28 bereits als
Gate 3b abdeckt. Vertragstest `scripts/test_doku_lint_contract.py` um
`test_gate_3_pr_merge_head_contract` ergaenzt (Mutationsprobe: Ausnahme entfernt -> FAIL).

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

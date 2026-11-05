#!/usr/bin/env python3
"""Vertragstest fuer .github/workflows/michael-spiegel.yml.

Zwei Haelften:
1. Statisch: der Workflow bleibt ein reiner workflow_call ohne eigene Ausloeser, das Token
   heisst spiegel_token, die Quelle wird ohne Zugangsdaten ausgecheckt, Actions sind auf
   volle Commit-SHAs gepinnt, nichts wird geloescht, die Abweisungs-Muster sind da.
2. Dynamisch: das Kopierskript wird zwischen den Markern SPIEGEL-SKRIPT-ANFANG/ENDE aus dem
   Workflow geschnitten und gegen Testordner ausgefuehrt - in beide Richtungen (kopiert, was
   erlaubt ist; weist fail-closed ab, was verboten ist; loescht nie).

Aufruf: python3 scripts/test_michael_spiegel_contract.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "michael-spiegel.yml"
README = ROOT / ".github" / "workflows" / "README.md"


def skript() -> str:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["spiegel"]["steps"]
    run = next(s["run"] for s in steps if s.get("id") == "kopie")
    a = run.index("# --- SPIEGEL-SKRIPT-ANFANG ---")
    e = run.index("# --- SPIEGEL-SKRIPT-ENDE ---")
    return "set -euo pipefail\n" + run[a:e]


def lauf(quelle: Path, ziel_wurzel: Path, repo: str = "Klangschalen/test-quelle",
         sha: str = "0123456789abcdef0123456789abcdef01234567") -> subprocess.CompletedProcess:
    out = ziel_wurzel.parents[1] / "github_output.txt"
    env = dict(os.environ)
    env.update({
        "QUELLE": str(quelle),
        "ZIEL": str(ziel_wurzel / repo.split("/")[1]),
        "ZIEL_WURZEL": str(ziel_wurzel),
        "QUELL_REPO": repo,
        "QUELL_SHA": sha,
        "QUELL_ORDNER": "uebergabe-michael",
        "GITHUB_OUTPUT": str(out),
    })
    return subprocess.run(["bash", "-c", skript()], env=env, capture_output=True, text=True)


class Statisch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.doc = yaml.safe_load(cls.text)
        # PyYAML liest den Schluessel "on" als True
        cls.on = cls.doc.get("on", cls.doc.get(True))

    def test_nur_workflow_call_kein_eigener_ausloeser(self):
        self.assertEqual(list(self.on.keys()), ["workflow_call"])

    def test_secret_heisst_spiegel_token_und_ist_pflicht(self):
        self.assertTrue(self.on["workflow_call"]["secrets"]["spiegel_token"]["required"])

    def test_ziel_ist_michaels_uebergabe_repo(self):
        self.assertEqual(self.on["workflow_call"]["inputs"]["ziel_repository"]["default"],
                         "Klangschalen/michael-arbeitsuebergabe")
        self.assertEqual(self.on["workflow_call"]["inputs"]["quell_ordner"]["default"], "uebergabe-michael")

    def test_quelle_ohne_zugangsdaten_ziel_mit_token(self):
        steps = self.doc["jobs"]["spiegel"]["steps"]
        quelle, ziel = steps[0], steps[1]
        self.assertEqual(quelle["with"]["path"], "quelle")
        self.assertFalse(quelle["with"]["persist-credentials"])
        self.assertEqual(ziel["with"]["path"], "ziel")
        self.assertEqual(ziel["with"]["token"], "${{ secrets.spiegel_token }}")
        self.assertEqual(ziel["with"]["fetch-depth"], 0)

    def test_actions_auf_volle_sha_gepinnt(self):
        for uses in re.findall(r"uses:\s*(\S+)", self.text):
            self.assertRegex(uses, r"@[0-9a-f]{40}$", uses)

    def test_nichts_wird_geloescht_und_push_nur_im_commit_schritt(self):
        self.assertNotRegex(self.text, r"\brm\s+-r")
        self.assertNotIn("git rm", self.text)
        self.assertEqual(self.text.count("git push"), 1)
        self.assertIn('if [ "${TROCKENLAUF}" = "true" ]', self.text)

    def test_abweisungs_muster_vorhanden(self):
        for muster in ("arbeitsjournal", "evidenzakte", "kunden", "adress", "\\.env", "PRIVATE KEY", "ghp_"):
            self.assertIn(muster, self.text, muster)

    def test_readme_beschreibt_den_ablauf(self):
        t = README.read_text(encoding="utf-8")
        self.assertIn("## michael-spiegel.yml", t)
        self.assertIn("MICHAEL_SPIEGEL_TOKEN", t)
        self.assertIn("uebergabe-michael/", t)


class Dynamisch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="spiegel-"))
        self.quelle = self.tmp / "quelle" / "uebergabe-michael"
        self.ziel = self.tmp / "ziel" / "eingang"
        self.quelle.mkdir(parents=True)
        self.ziel.mkdir(parents=True)

    def test_erlaubte_dateien_werden_mit_pfad_kopiert(self):
        (self.quelle / "2026-09-05-thema").mkdir()
        (self.quelle / "2026-09-05-thema" / "befund.html").write_text("<h1>Befund</h1>", encoding="utf-8")
        (self.quelle / "2026-09-05-thema" / "diagnose.php").write_text("<?php echo 'x';", encoding="utf-8")
        r = lauf(self.quelle, self.ziel)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        z = self.ziel / "test-quelle"
        self.assertTrue((z / "2026-09-05-thema" / "befund.html").is_file())
        self.assertTrue((z / "2026-09-05-thema" / "diagnose.php").is_file())
        self.assertIn("Commit: 0123456", (z / "QUELLE.txt").read_text(encoding="utf-8"))
        self.assertTrue((self.ziel / "README.md").is_file())
        self.assertIn("dateien=2", (self.tmp / "github_output.txt").read_text())

    def test_env_datei_weist_alles_ab(self):
        (self.quelle / "befund.html").write_text("ok", encoding="utf-8")
        (self.quelle / ".env").write_text("DB_PASSWORD=x", encoding="utf-8")
        r = lauf(self.quelle, self.ziel)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ABGEWIESEN", r.stdout)
        self.assertFalse((self.ziel / "test-quelle" / "befund.html").exists(), "fail-closed: nichts kopiert")

    def test_personendaten_im_namen_weisen_ab(self):
        (self.quelle / "kunden-export.csv").write_text("a;b", encoding="utf-8")
        r = lauf(self.quelle, self.ziel)
        self.assertEqual(r.returncode, 1)
        self.assertIn("Personendaten", r.stdout)

    def test_schluessel_im_inhalt_weist_ab(self):
        (self.quelle / "notiz.md").write_text("token: ghp_" + "A" * 30, encoding="utf-8")
        r = lauf(self.quelle, self.ziel)
        self.assertEqual(r.returncode, 1)
        self.assertIn("schluesselaehnlicher Inhalt", r.stdout)

    def test_fehlender_ordner_ist_kein_fehler(self):
        r = lauf(self.tmp / "gibt-es-nicht", self.ziel)
        self.assertEqual(r.returncode, 0)
        self.assertIn("dateien=0", (self.tmp / "github_output.txt").read_text())

    def test_interne_readme_im_quellordner_bleibt_zuhause(self):
        (self.quelle / "README.md").write_text("interne Anleitung", encoding="utf-8")
        (self.quelle / "2026-09-05-x").mkdir()
        (self.quelle / "2026-09-05-x" / "LIES-MICH.md").write_text("fuer Michael", encoding="utf-8")
        r = lauf(self.quelle, self.ziel)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertFalse((self.ziel / "test-quelle" / "README.md").exists())
        self.assertTrue((self.ziel / "test-quelle" / "2026-09-05-x" / "LIES-MICH.md").is_file())
        self.assertIn("dateien=1", (self.tmp / "github_output.txt").read_text())

    def test_im_ziel_wird_nie_geloescht(self):
        alt = self.ziel / "test-quelle" / "alte-uebergabe.html"
        alt.parent.mkdir(parents=True)
        alt.write_text("bleibt", encoding="utf-8")
        (self.quelle / "neu.html").write_text("neu", encoding="utf-8")
        r = lauf(self.quelle, self.ziel)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(alt.read_text(encoding="utf-8"), "bleibt")

    def test_identische_quelle_bewahrt_metadaten_bytegenau(self):
        (self.quelle / "LIES-MICH.md").write_text("Auftrag", encoding="utf-8")
        self.assertEqual(lauf(self.quelle, self.ziel).returncode, 0)
        meta = self.ziel / "test-quelle" / "QUELLE.txt"
        # Feste alte Uhrzeit beweist, dass der zweite Lauf nicht neu schreibt.
        meta.write_text(re.sub(r"Zeitpunkt.*", "Zeitpunkt (UTC): 2000-01-01T00:00:00Z",
                               meta.read_text()), encoding="utf-8")
        vorher = meta.read_bytes()
        r = lauf(self.quelle, self.ziel)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(meta.read_bytes(), vorher)
        self.assertIn("geaendert=0", (self.tmp / "github_output.txt").read_text())

    def test_neuer_quell_commit_aktualisiert_bindung_auch_bei_gleichem_inhalt(self):
        (self.quelle / "LIES-MICH.md").write_text("Auftrag", encoding="utf-8")
        self.assertEqual(lauf(self.quelle, self.ziel).returncode, 0)
        sha = "a" * 40
        r = lauf(self.quelle, self.ziel, sha=sha)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("Commit: " + sha, (self.ziel / "test-quelle" / "QUELLE.txt").read_text())

    def test_abweichende_zielkopie_wird_erneut_hergestellt(self):
        (self.quelle / "LIES-MICH.md").write_text("Auftrag", encoding="utf-8")
        self.assertEqual(lauf(self.quelle, self.ziel).returncode, 0)
        kopie = self.ziel / "test-quelle" / "LIES-MICH.md"
        kopie.write_text("abweichend", encoding="utf-8")
        r = lauf(self.quelle, self.ziel)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(kopie.read_text(), "Auftrag")


class GitUndPullRequest(unittest.TestCase):
    """Echte lokale Git-Pushes; nur GitHub-PR-API ist simuliert."""
    def setUp(self):
        self.tmp_obj = tempfile.TemporaryDirectory(prefix="spiegel-git-")
        self.addCleanup(self.tmp_obj.cleanup)
        self.tmp = Path(self.tmp_obj.name)
        self.remote = self.tmp / "remote.git"
        self.seed = self.tmp / "seed"
        self.ziel = self.tmp / "ziel"
        self.quelle = self.tmp / "quelle" / "uebergabe-michael"
        self.quelle.mkdir(parents=True)
        (self.quelle / "LIES-MICH.md").write_text("Auftrag", encoding="utf-8")
        self.git(self.tmp, "init", "--bare", str(self.remote))
        self.git(self.tmp, "clone", str(self.remote), str(self.seed))
        self.git(self.seed, "config", "user.name", "Test")
        self.git(self.seed, "config", "user.email", "test@example.invalid")
        self.git(self.seed, "checkout", "-b", "main")
        (self.seed / "README.md").write_text("Ziel", encoding="utf-8")
        self.git(self.seed, "add", "README.md")
        self.git(self.seed, "commit", "-m", "chore: initial")
        self.git(self.seed, "push", "origin", "main")
        self.git(self.tmp, "clone", "--branch", "main", str(self.remote), str(self.ziel))
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        gh = self.bin / "gh"
        gh.write_text("""#!/usr/bin/env python3
import os, sys
from pathlib import Path
root = Path(os.environ["FAKE_GH_ROOT"])
args = sys.argv[1:]
with (root / "calls").open("a") as f:
    f.write(" ".join(args) + "\\n")
head = args[args.index("--head") + 1]
pr = root / ("pr-" + head.replace("/", "-"))
if args[:2] == ["pr", "list"]:
    if os.environ.get("FAIL_PR_LIST"):
        sys.exit(2)
    if pr.exists():
        print(pr.read_text())
elif args[:2] == ["pr", "create"]:
    pr.write_text("https://example.invalid/pull/1")
    print(pr.read_text())
else:
    sys.exit(3)
""", encoding="utf-8")
        gh.chmod(0o755)
        self.env = dict(os.environ, QUELL_REPO="Klangschalen/test-quelle",
                        QUELL_SHA="0" * 40, ZIEL_ZWEIG="main",
                        ZIEL_REPO="Klangschalen/test-ziel", ZIEL_ORDNER="eingang",
                        QUELL_ORDNER="uebergabe-michael", TROCKENLAUF="false",
                        ANZAHL="1", GITHUB_OUTPUT=str(self.tmp / "output"),
                        RUNNER_TEMP=str(self.tmp), FAKE_GH_ROOT=str(self.tmp),
                        PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        doc = yaml.safe_load(WORKFLOW.read_text())
        steps = doc["jobs"]["spiegel"]["steps"]
        self.prepare = next(s["run"] for s in steps if s.get("id") == "vorbereiten")
        self.publish = steps[-1]["run"]

    def git(self, cwd, *args):
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout.strip()

    def run_shell(self, script):
        return subprocess.run(["bash", "-c", script], cwd=self.tmp, env=self.env,
                              capture_output=True, text=True)

    def transfer(self):
        r = self.run_shell(self.prepare)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.env["SPIEGEL_ZWEIG"] = "michael-spiegel/test-quelle/" + self.env["QUELL_SHA"]
        z = self.ziel / "eingang"
        z.mkdir(exist_ok=True)
        r = lauf(self.quelle, z, sha=self.env["QUELL_SHA"])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.run_shell(self.publish)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def test_wiederholung_keine_neuen_commits_oder_prs_auch_nach_merge(self):
        self.transfer()
        sha = self.git(self.ziel, "rev-parse", "HEAD")
        meta = (self.ziel / "eingang/test-quelle/QUELLE.txt").read_bytes()
        self.transfer()
        self.assertEqual(self.git(self.ziel, "rev-parse", "HEAD"), sha)
        self.assertEqual((self.ziel / "eingang/test-quelle/QUELLE.txt").read_bytes(), meta)
        calls = (self.tmp / "calls").read_text()
        self.assertEqual(calls.count("pr create "), 1)
        self.git(self.seed, "fetch", "origin")
        self.git(self.seed, "merge", "--ff-only", "origin/" + self.env["SPIEGEL_ZWEIG"])
        self.git(self.seed, "push", "origin", "main")
        self.transfer()
        self.assertEqual((self.tmp / "calls").read_text(), calls)

    def test_neuer_quellstand_neuer_pr_ohne_historische_dateien_zu_loeschen(self):
        self.transfer()
        self.git(self.seed, "fetch", "origin")
        self.git(self.seed, "merge", "--ff-only", "origin/" + self.env["SPIEGEL_ZWEIG"])
        self.git(self.seed, "push", "origin", "main")
        (self.quelle / "LIES-MICH.md").unlink()
        (self.quelle / "neuer-auftrag.md").write_text("Neuer Auftrag")
        self.env["QUELL_SHA"] = "a" * 40
        self.transfer()
        self.assertTrue((self.ziel / "eingang/test-quelle/LIES-MICH.md").exists())
        self.assertTrue((self.ziel / "eingang/test-quelle/neuer-auftrag.md").exists())
        self.assertEqual((self.tmp / "calls").read_text().count("pr create "), 2)

    def test_fortgeschrittener_zielzweig_bleibt_erhalten_ohne_pr_duplikat(self):
        self.transfer()
        (self.seed / "anderer-bereich.md").write_text("Andere Arbeit", encoding="utf-8")
        self.git(self.seed, "add", "anderer-bereich.md")
        self.git(self.seed, "commit", "-m", "docs: other area")
        self.git(self.seed, "push", "origin", "main")
        self.transfer()
        self.assertEqual((self.ziel / "anderer-bereich.md").read_text(), "Andere Arbeit")
        self.assertEqual((self.tmp / "calls").read_text().count("pr create "), 1)

    def test_trockenlauf_ohne_push_und_pr(self):
        self.env["TROCKENLAUF"] = "true"
        self.transfer()
        self.assertFalse((self.tmp / "calls").exists())
        remote = self.git(self.tmp, "--git-dir=" + str(self.remote), "branch", "--list")
        self.assertNotIn("michael-spiegel", remote)

    def test_fehler_beim_pr_lesen_erzeugt_keinen_doppelten_pr(self):
        self.transfer()
        self.env["FAIL_PR_LIST"] = "1"
        r = self.run_shell(self.publish)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual((self.tmp / "calls").read_text().count("pr create "), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)


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


def lauf(quelle: Path, ziel_wurzel: Path, repo: str = "Klangschalen/test-quelle") -> subprocess.CompletedProcess:
    out = ziel_wurzel.parents[1] / "github_output.txt"
    env = dict(os.environ)
    env.update({
        "QUELLE": str(quelle),
        "ZIEL": str(ziel_wurzel / repo.split("/")[1]),
        "ZIEL_WURZEL": str(ziel_wurzel),
        "QUELL_REPO": repo,
        "QUELL_SHA": "0123456789abcdef0123456789abcdef01234567",
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


if __name__ == "__main__":
    unittest.main(verbosity=1)

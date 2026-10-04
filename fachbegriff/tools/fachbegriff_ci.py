#!/usr/bin/env python3
"""Fachbegriff-Sperre als CI-Schritt fuer ein fremdes Repo (Klartext-Bericht).

Prueft alle Dateien eines ausgecheckten Repos, die auf die angegebenen Muster
passen, mit ``tools/fachbegriff_sperre.py`` (Quelle ``wissen/messverfahren.json``)
und schreibt einen Bericht, den ein Mensch ohne Repo-Kenntnis versteht:
WAS gefunden wurde, WARUM es gesperrt ist, WAS stattdessen gilt.

Rueckgabewerte (stehen ausdruecklich im Protokoll):
  0  keine Treffer, oder Treffer im Meldemodus (--warn-only)
  1  Treffer im Sperrmodus
  2  NICHT PRUEFBAR (Quelle oder Werkzeug fehlt) - gilt nie als "in Ordnung";
     im Meldemodus wird daraus eine Warnung, der Schritt bleibt gruen.

Aufruf (so ruft der wiederverwendbare Workflow in Klangschalen/.github ihn auf):
  python tools/fachbegriff_ci.py --wurzel ../repo --muster "**/*.md" --muster "**/*.html" \
      --ausnahme "(^|/)(learnings|archiv|rules-archiv|node_modules|vendor)/" --warn-only
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))

STANDARD_AUSNAHME = (
    r"(^|/)(learnings|archiv|rules-archiv|node_modules|vendor|\.git)/"
    r"|(^|/)CHANGELOG(\.d/|\.md$)"
    r"|(^|/)OFFENE-AUFGABEN\.md$"
)


def _passt(rel_posix: str, muster: str) -> bool:
    """``**/*.md`` soll auch Dateien in der Wurzel treffen (fnmatch verlangt sonst einen Schraegstrich)."""
    if fnmatch.fnmatch(rel_posix, muster):
        return True
    return muster.startswith("**/") and fnmatch.fnmatch(rel_posix, muster[3:])


def dateien_im_repo(wurzel: Path, muster: list[str], ausnahme: str) -> list[Path]:
    """Alle von Git verwalteten Dateien, die auf ein Muster passen und nicht ausgenommen sind."""
    try:
        roh = subprocess.run(
            ["git", "-C", str(wurzel), "ls-files", "-z"],
            check=True, capture_output=True,
        ).stdout.decode("utf-8", "replace").split("\0")
    except (subprocess.CalledProcessError, FileNotFoundError):
        roh = [str(p.relative_to(wurzel)) for p in wurzel.rglob("*") if p.is_file()]
    regel = re.compile(ausnahme) if ausnahme else None
    treffer: list[Path] = []
    for rel in roh:
        if not rel:
            continue
        rel_posix = rel.replace(os.sep, "/")
        if regel and regel.search(rel_posix):
            continue
        if any(_passt(rel_posix, m) for m in muster):
            treffer.append(wurzel / rel)
    return sorted(treffer)


def pruefe_dateien(dateien: list[Path], wurzel: Path) -> list[dict]:
    from fachbegriff_sperre import lade, pruefe  # noqa: WPS433 (bewusst spaet, Quelle kann fehlen)

    daten = lade()
    befunde: list[dict] = []
    for datei in dateien:
        try:
            text = datei.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for t in pruefe(text, daten):
            zeile = text.count("\n", 0, t["position"]) + 1
            befunde.append({
                "datei": str(datei.relative_to(wurzel)).replace(os.sep, "/"),
                "zeile": zeile,
                "fund": t["fund"],
                "grund": t["grund"],
                "stattdessen": t["stattdessen"],
            })
    return befunde


def bericht(befunde: list[dict], anzahl_dateien: int, warn_only: bool) -> str:
    """Klartext fuer Menschen: WAS, WARUM, WAS TUN - plus Sammelbefund je gesperrtem Begriff."""
    zeilen = [f"Geprueft: {anzahl_dateien} Dateien. Treffer: {len(befunde)}."]
    if not befunde:
        zeilen.append("Kein gesperrter Fachbegriff gefunden.")
        return "\n".join(zeilen)
    je_fund: dict[str, int] = {}
    for b in befunde:
        schl = b["fund"].lower()
        je_fund[schl] = je_fund.get(schl, 0) + 1
    zeilen.append("Sammelbefund (dieselbe Ursache, eine Korrektur je Begriff):")
    for fund, n in sorted(je_fund.items(), key=lambda kv: -kv[1]):
        beispiel = next(b for b in befunde if b["fund"].lower() == fund)
        zeilen.append(f"  - '{fund}' {n}x: {beispiel['grund']} Stattdessen: {beispiel['stattdessen']}")
    zeilen.append("Fundstellen:")
    for b in befunde[:200]:
        zeilen.append(f"  {b['datei']}:{b['zeile']}  '{b['fund']}'")
    if len(befunde) > 200:
        zeilen.append(f"  ... und {len(befunde) - 200} weitere")
    modus = "MELDEMODUS: Schritt bleibt gruen, Befund ist trotzdem echt." if warn_only else "SPERRMODUS: Schritt ist rot."
    zeilen.append(modus)
    return "\n".join(zeilen)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wurzel", required=True, help="Pfad zum ausgecheckten Repo, das geprueft wird")
    ap.add_argument("--muster", action="append", default=None, help="Glob, mehrfach erlaubt (Standard: **/*.md, **/*.html)")
    ap.add_argument("--ausnahme", default=STANDARD_AUSNAHME, help="Regex auf den relativen Pfad; Treffer werden uebersprungen")
    ap.add_argument("--warn-only", action="store_true", help="Treffer melden, Schritt bleibt gruen")
    ap.add_argument("--zusammenfassung", default=os.environ.get("GITHUB_STEP_SUMMARY"), help="Datei fuer den Bericht (GitHub-Schrittzusammenfassung)")
    a = ap.parse_args(argv)

    wurzel = Path(a.wurzel).resolve()
    muster = a.muster or ["**/*.md", "**/*.html"]
    if not wurzel.is_dir():
        print(f"NICHT PRUEFBAR (Rueckgabewert 2): Wurzel {wurzel} fehlt.")
        return 2
    if not (HIER / "fachbegriff_sperre.py").exists() or not (HIER.parent / "wissen" / "messverfahren.json").exists():
        print("NICHT PRUEFBAR (Rueckgabewert 2): Werkzeug oder Quelle wissen/messverfahren.json fehlt.")
        return 2

    dateien = dateien_im_repo(wurzel, muster, a.ausnahme)
    befunde = pruefe_dateien(dateien, wurzel)
    text = bericht(befunde, len(dateien), a.warn_only)
    print(text)
    if a.zusammenfassung:
        try:
            with open(a.zusammenfassung, "a", encoding="utf-8") as fh:
                fh.write("## Fachbegriff-Sperre\n\n```\n" + text + "\n```\n")
        except OSError:
            pass
    if befunde and os.environ.get("GITHUB_ACTIONS"):
        for b in befunde[:50]:
            print(f"::warning file={b['datei']},line={b['zeile']}::Gesperrter Fachbegriff '{b['fund']}'. {b['grund']} Stattdessen: {b['stattdessen']}")
    if befunde and not a.warn_only:
        print("Rueckgabewert 1.")
        return 1
    print("Rueckgabewert 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

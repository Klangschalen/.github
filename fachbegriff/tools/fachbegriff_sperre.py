"""Fachbegriff-Sperre fuer das Messverfahren - greift ohne Erinnerung.

Liest die EINE Quelle wissen/messverfahren.json (Owner-Entscheidung 29.09./03.10.2026:
mehrere Toene je Schale, tiefster Ton und erster Ton darueber, Zuordnung bei hoechstens
1 % Abweichung, kein 'Grundton', keine 'exakte Frequenz', nichts 'gestimmt') und prueft
beliebigen Text dagegen. Kein Modell, keine Datenbank.

Aufruf:
  python tools/fachbegriff_sperre.py --text "..."        # Treffer als JSON, Rueckgabe 1 bei Treffer
  python tools/fachbegriff_sperre.py --datei seite.html  # dito fuer eine Datei
  python tools/fachbegriff_sperre.py --selbsttest        # in beide Richtungen
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

QUELLE = Path(__file__).resolve().parents[1] / "wissen" / "messverfahren.json"
_WORTZEICHEN = "[^\\W_]"


def lade(pfad: Path = QUELLE) -> dict:
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    for schluessel in ("entschieden", "gesperrt"):
        if not isinstance(daten.get(schluessel), list) or not daten[schluessel]:
            raise ValueError(f"{pfad}: '{schluessel}' fehlt oder ist leer")
    return daten


_VERWORFEN = re.compile(r"<(s|del)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)


def _ist_bezeichner(text: str, m: "re.Match[str]") -> bool:
    """Code-Bezeichner und Datenschluessel (grundton_freq_hz, md.grundton_hz) sind kein Fliesstext.

    Ein Fund zaehlt nicht, wenn er einen Unterstrich enthaelt oder direkt an einen
    Unterstrich oder Punkt-Zugriff grenzt. Die Schluessel sind Datenvertraege mit dem
    ML-Modell und der Textpipeline (Fachrunde 05.10.2026 entscheidet ueber Umbenennung).
    """
    if "_" in m.group(0):
        return True
    vor = text[m.start() - 1] if m.start() > 0 else " "
    nach = text[m.end()] if m.end() < len(text) else " "
    return vor in "_." or nach == "_"


def pruefe(text: str, daten: dict | None = None) -> list[dict]:
    """Liefert je Fund: fund, grund, stattdessen, position. Leer = frei.

    Durchgestrichener Text (<s>...</s> oder <del>...</del>) gilt als ausdruecklich
    verworfen und wird nicht geprueft - so kann eine Seite sagen, welches Wort
    nicht mehr gilt, ohne es zu verwenden.
    """
    daten = daten or lade()
    text = _VERWORFEN.sub(lambda m: " " * len(m.group(0)), text)
    treffer = []
    for sperre in daten["gesperrt"]:
        for m in re.finditer(sperre["muster"], text, flags=re.IGNORECASE | re.UNICODE):
            if _ist_bezeichner(text, m):
                continue
            treffer.append({"fund": m.group(0), "grund": sperre["grund"],
                            "stattdessen": sperre["stattdessen"], "position": m.start()})
    return sorted(treffer, key=lambda t: t["position"])


def fakten_als_text(daten: dict | None = None) -> str:
    """Die entschiedenen Fakten als Zeilen - fuer Modell-Prompts und Protokolle."""
    daten = daten or lade()
    return "\n".join(f"- {e['fakt']}" for e in daten["entschieden"])


def selbsttest() -> int:
    rot = ["auf eine exakte Frequenz ausgemessen", "Gemessener Grundton in Hz",
           "Jede Klangschale hat eine eigene Frequenz", "nach Cousto gestimmt", "der stärkste Ton"]
    gruen = ["Weicht ein Ton höchstens 1 % von einem Planetenton ab, wird er diesem zugeordnet.",
             "Maßgeblich sind der tiefste Ton und der erste Ton darüber.", fakten_als_text()]
    fehler = [s for s in rot if not pruefe(s)] + [s for s in gruen if pruefe(s)]
    for s in fehler:
        print(f"SELBSTTEST FEHLER: {s!r}")
    print(f"Selbsttest: {len(rot)} rot erkannt, {len(gruen)} gruen frei, {len(fehler)} Fehler")
    return 1 if fehler else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--text")
    ap.add_argument("--datei", type=Path)
    ap.add_argument("--selbsttest", action="store_true")
    a = ap.parse_args(argv)
    if a.selbsttest:
        return selbsttest()
    text = a.text if a.text is not None else a.datei.read_text(encoding="utf-8")
    treffer = pruefe(text)
    print(json.dumps(treffer, ensure_ascii=False, indent=1))
    return 1 if treffer else 0


if __name__ == "__main__":
    sys.exit(main())

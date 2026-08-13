#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generiert eine HTML-Merge-Checkliste fuer die CHANGELOG-Nachruestung.

Zieht den ECHTEN aktuellen Status jeder PR per `gh pr view` (state, isDraft,
mergeable, mergeStateStatus) - kein blindes Abhaken. Vor UND nach dem Merge
ausfuehrbar: die Seite spiegelt immer den realen GitHub-Stand.

Aufruf:  python scripts/merge_checkliste_html.py
Ausgabe: ausgaben/<heute>/01_changelog-merge-checkliste.html
"""
from __future__ import annotations

import html
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ORG = "Klangschalen"
# Repo -> PR-Nummer (Branch docs/changelog-init), Stand 2026-06-09
PRS = {
    ".github": 11, "Gstack-": 8, "adk-agents": 7, "agent-templates": 6,
    "content-engine": 7, "design-sound-spirit": 5, "klangschalen-analyse": 4,
    "knowledge": 10, "life-design-app": 6, "profihost-server": 6,
    "projekt-board": 8, "schnittstellen-doku": 6, "security-monitoring": 7,
    "sf-analyse": 5, "shop-api-test": 7, "shop-tuner-dokumentation": 27,
    "weboffice": 7, "website-audit": 9, "zentrale": 71,
}
# Repo ohne PR (leeres Git-Repo, kein Base-Branch moeglich)
GAMBIO = "gambio-modul-content"


def gh_json(repo: str, num: int) -> dict:
    proc = subprocess.run(
        ["gh", "pr", "view", str(num), "--repo", f"{ORG}/{repo}",
         "--json", "state,isDraft,mergeable,mergeStateStatus,url,mergedAt,title"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()}
    return json.loads(proc.stdout)


def classify(d: dict) -> tuple[str, str, bool]:
    """Gibt (label, css_klasse, ist_erledigt) zurueck."""
    if d.get("error"):
        return ("Fehler", "err", False)
    if d.get("state") == "MERGED" or d.get("mergedAt"):
        return ("Gemerged", "merged", True)
    if d.get("state") == "CLOSED":
        return ("Geschlossen (nicht gemerged)", "err", False)
    draft = d.get("isDraft")
    mss = d.get("mergeStateStatus", "")
    if mss == "BLOCKED":
        return ("Offen - durch Branch-Schutz blockiert", "blocked", False)
    if draft:
        return ("Offen - noch Entwurf", "draft", False)
    return ("Offen - bereit zum Merge", "ready", False)


def main() -> None:
    rows = []
    done = 0
    for repo in sorted(PRS):
        d = gh_json(repo, PRS[repo])
        label, cls, is_done = classify(d)
        if is_done:
            done += 1
        rows.append({
            "repo": repo, "num": PRS[repo],
            "url": d.get("url", f"https://github.com/{ORG}/{repo}/pull/{PRS[repo]}"),
            "label": label, "cls": cls, "done": is_done,
        })

    total = len(rows)
    pct = round(done / total * 100) if total else 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    tr = []
    for i, r in enumerate(rows, 1):
        repo = html.escape(r["repo"])
        tr.append(f"""      <tr data-key="{repo}" class="{r['cls']}">
        <td class="num">{i}</td>
        <td class="repo">{repo}</td>
        <td><a href="{r['url']}" target="_blank" rel="noopener">PR #{r['num']} oeffnen</a></td>
        <td><span class="badge {r['cls']}">{html.escape(r['label'])}</span></td>
        <td class="chk"><input type="checkbox" {'checked disabled' if r['done'] else ''} data-repo="{repo}"></td>
      </tr>""")
    rows_html = "\n".join(tr)

    all_done_banner = (
        '<div class="banner ok">Alle 19 CHANGELOG-PRs sind gemerged. Nichts vergessen.</div>'
        if done == total else
        f'<div class="banner todo">Noch <b>{total - done}</b> von {total} offen - erst fertig, wenn alle gruen sind.</div>'
    )

    doc = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CHANGELOG-Nachruestung - Merge-Checkliste</title>
<style>
  :root {{ --ok:#16a34a; --ready:#2563eb; --blocked:#ea580c; --draft:#6b7280; --err:#dc2626; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; margin:0; background:#f8fafc; color:#0f172a; }}
  .wrap {{ max-width:980px; margin:0 auto; padding:24px 16px 60px; }}
  h1 {{ font-size:1.6rem; margin:0 0 4px; }}
  .stand {{ color:#64748b; font-size:.85rem; margin-bottom:20px; }}
  .progress-wrap {{ background:#e2e8f0; border-radius:999px; height:28px; overflow:hidden; margin:8px 0; }}
  .progress {{ height:100%; background:var(--ok); width:{pct}%; transition:width .4s; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:600; font-size:.85rem; }}
  .counter {{ font-size:1.1rem; font-weight:600; margin:14px 0 4px; }}
  .banner {{ padding:12px 16px; border-radius:10px; font-weight:600; margin:14px 0 24px; }}
  .banner.ok {{ background:#dcfce7; color:#166534; }}
  .banner.todo {{ background:#fef9c3; color:#854d0e; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  th,td {{ padding:10px 12px; text-align:left; border-bottom:1px solid #f1f5f9; font-size:.92rem; }}
  th {{ background:#f1f5f9; font-size:.78rem; text-transform:uppercase; letter-spacing:.03em; color:#475569; }}
  td.num {{ color:#94a3b8; width:36px; }}
  td.repo {{ font-family:ui-monospace,Menlo,Consolas,monospace; font-weight:600; }}
  td.chk {{ text-align:center; }}
  input[type=checkbox] {{ width:20px; height:20px; cursor:pointer; }}
  a {{ color:#2563eb; text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:999px; font-size:.78rem; font-weight:600; color:#fff; white-space:nowrap; }}
  .badge.merged {{ background:var(--ok); }} .badge.ready {{ background:var(--ready); }}
  .badge.blocked {{ background:var(--blocked); }} .badge.draft {{ background:var(--draft); }}
  .badge.err {{ background:var(--err); }}
  tr.merged {{ background:#f0fdf4; }}
  .card {{ background:#fff; border-radius:12px; padding:16px 20px; margin-top:22px; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  .card h2 {{ font-size:1.05rem; margin:0 0 10px; }}
  .card.warn {{ border-left:5px solid var(--blocked); }}
  .card.info {{ border-left:5px solid var(--ready); }}
  .card.gambio {{ border-left:5px solid var(--draft); }}
  ul {{ margin:6px 0; padding-left:20px; }} li {{ margin:4px 0; }}
  code {{ background:#f1f5f9; padding:1px 6px; border-radius:5px; font-size:.85em; }}
  .reset {{ margin-top:10px; font-size:.8rem; color:#94a3b8; cursor:pointer; background:none; border:none; text-decoration:underline; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>CHANGELOG-Nachruestung - Merge-Checkliste</h1>
  <div class="stand">Echter GitHub-Status, gezogen am {now}. Neu erzeugbar mit
    <code>python scripts/merge_checkliste_html.py</code>.</div>

  <div class="counter"><span id="liveCount">{done}</span> / {total} gemerged</div>
  <div class="progress-wrap"><div class="progress" id="bar">{pct}%</div></div>
  {all_done_banner}

  <table>
    <thead><tr><th>#</th><th>Repository</th><th>Pull Request</th><th>Status (echt)</th><th>Haken</th></tr></thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
  <button class="reset" onclick="if(confirm('Manuelle Haken zuruecksetzen?')){{localStorage.removeItem('chlog-merge');location.reload();}}">manuelle Haken zuruecksetzen</button>

  <div class="card warn">
    <h2>Sonderfall 1: adk-agents braucht Extra-Handgriff</h2>
    <p><code>adk-agents</code> ist <b>BLOCKED</b> (Branch-Schutz). Normaler Merge scheitert.
    Optionen: Branch-Schutz kurz lockern, Admin-Merge (<code>gh pr merge 7 --repo Klangschalen/adk-agents --squash --admin</code>),
    oder bewusst auslassen. Diese Zeile bleibt rot/orange, bis das geklaert ist.</p>
  </div>

  <div class="card gambio">
    <h2>Sonderfall 2: gambio-modul-content (kein PR moeglich)</h2>
    <p>Das Repo <code>{GAMBIO}</code> ist ein <b>leeres Git-Repo</b> (kein Commit, kein Default-Branch),
    deshalb gibt es hier keinen PR zum Abhaken. Frank-Entscheid: Repo entfernen, initialisieren
    (README+CHANGELOG als ersten Commit) oder aus dem Audit-Scope nehmen. Steht in OFFENE-AUFGABEN.md.</p>
  </div>

  <div class="card info">
    <h2>Was Claude nach dem Merge uebernimmt</h2>
    <ul>
      <li>Org-Doku-Audit neu ausloesen: <code>gh workflow run org-doku-audit.yml --repo Klangschalen/.github</code></li>
      <li>Messen im Issue <a href="https://github.com/Klangschalen/.github/issues/7" target="_blank" rel="noopener">.github #7</a>:
          KERN-Luecke-Repos sollten von <b>24 auf 21</b> fallen, CHLOG-Luecken von <b>20 auf 1</b> (nur gambio bleibt).</li>
      <li>Ehrliche Grenze: nur 3 Repos (Gstack-, security-monitoring, shop-tuner-dokumentation) fallen ganz aus der
          KERN-Liste - die anderen 16 vermissen zusaetzlich README oder STATUS und bleiben drin.</li>
    </ul>
  </div>
</div>
<script>
  // Manuelle Haken (fuer den Fall, dass Frank selbst merged) in localStorage merken.
  const KEY='chlog-merge';
  const saved=JSON.parse(localStorage.getItem(KEY)||'{{}}');
  document.querySelectorAll('input[type=checkbox]').forEach(cb=>{{
    const repo=cb.dataset.repo;
    if(!cb.disabled && saved[repo]) cb.checked=true;
    cb.addEventListener('change',()=>{{
      saved[repo]=cb.checked; localStorage.setItem(KEY,JSON.stringify(saved)); recount();
    }});
  }});
  function recount(){{
    const all=[...document.querySelectorAll('input[type=checkbox]')];
    const n=all.filter(c=>c.checked).length, t=all.length;
    document.getElementById('liveCount').textContent=n;
    const bar=document.getElementById('bar'), p=Math.round(n/t*100);
    bar.style.width=p+'%'; bar.textContent=p+'%';
  }}
  recount();
</script>
</body>
</html>
"""

    out_dir = Path(__file__).resolve().parent.parent / "ausgaben" / datetime.now().strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "01_changelog-merge-checkliste.html"
    out.write_text(doc, encoding="utf-8")
    print(f"Geschrieben: {out}")
    print(f"Status: {done}/{total} gemerged ({pct}%)")
    for r in rows:
        if not r["done"]:
            print(f"  offen: {r['repo']:26} {r['label']}")


if __name__ == "__main__":
    main()

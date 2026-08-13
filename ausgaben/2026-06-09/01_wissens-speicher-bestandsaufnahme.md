# Sound-Spirit Wissens-Infrastruktur - Bestandsaufnahme 2026-06-09

## SPEICHER - Physische Ablageorte & Struktur

| Speicher | Ort | Technik | Inhalt | Zeilen/Knoten | Status | Jüngst |
|----------|-----|---------|--------|---------------|--------|---------|
| **WISSENSGRAPH v13** | `C:/Users/Frank/wissensgraph-bau/knowledge-graph/out/` | Supabase Schema (geplant) + JSON Export | 704 Konzept-Knoten, 726 Beziehungen, alle status='draft' | 704 Knoten / 726 Kanten | ENTWURF (nicht deployed) | 2026-06-08 12:22 |
| **knowledge.db (SQLite)** | `D:/Agenten Systeme/unified-agent-system/mcp-servers/knowledge-base/` | SQLite3 + knowledge_atoms Tabelle | 69 Sound-Spirit-Fakten-Atome (Planetentoene) | 69 Zeilen | LIVE | 2026-03-22 18:37 |
| **PL-SETS Supabase** | Supabase planning-Schema + separate Tabellen | PostgreSQL (Supabase REST) | `planetentoene` (26 Töne mit 44 Feldern), `titel_pool`, `learnings`, `konzepte` (geplant) | 26 + generierte Titel | LIVE (partiell) | 2026-06-04 |
| **Planning idea_scores** | Supabase planning-Schema | PostgreSQL (Supabase REST) | 273+ Wissens-Knoten (Klangschalenwissen), parent_id + tags + embedding_vector | 273 Einträge | LIVE | 2026-05-26 |
| **Junction-Tabelle idea_parents** | Supabase planning-Schema | PostgreSQL (Supabase REST) | 278 Eltern-Kind-Verknüpfungen (primary + secondary) | 278 Einträge | LIVE | 2026-05-26 |

**Evidenz:**
- wissensgraph: `grep -c "INSERT INTO wissensgraph.konzepte" lade.sql` = 704 (2026-06-08 12:22)
- wissensgraph: `grep -c "INSERT INTO wissensgraph.beziehungen" lade.sql` = 726
- knowledge.db: Dateigröße 40K, Modifikation 2026-03-22 18:37
- PL-SETS: docs/architektur/supabase-schema.md Dateimodifikation 2026-06-09 15:45
- idea_scores: klangschalenwissen-knowledge-base.md Spur C.3 (273 primary + 5 secondary = 278 junction)

---

## PLAENE - Aktive Entwicklungs-Roadmaps & Done-Status

| Plan-Datei | Status | Was BEREITS GEBAUT | Done-Kriterium | Blockers |
|-----------|--------|-------------------|----------------|----------|
| **klangschalenwissen-knowledge-base.md** | IN_ARBEIT | C.1-C.4 erledigt: 302 Atome extrahiert, 273 als Knoten in idea_scores importiert, 21 E-E-A-T-FAQ-Antworten generiert | 100 Knowledge-Knoten + 20 EEAT-Antworten + messbarer SERP-Boost + Frank-Sign-off | C.5 Human-in-the-Loop, C.7 Live-Veröffentlichung |
| **wiki-llm-knowledge-graph-stufe1.md** | LIVE (Spur 1a abgeschlossen) | 1a Migration-SQL erfolgreich angewendet, 233 idea_scores mit embedding_vector gefüllt, 106 Verknüpfungen in planning.idea_relations, 22 parent_ids gesetzt | 6/6 Done-Kriterien erfüllt | Spur 1b (Embedding-API-Wahl) wartet auf Frank-Sign-off |
| **wissensgraph-hitl-freigabe.md** | OFFEN | Schritt 0 abgeschlossen: 704 Konzepte geparst, 221 hwg_sensitiv=true identifiziert, 22 Medizin-Begriffe auf tier_sicht=1 (BLOCKER) | 0 draft-Status, 0 Verbotsbegriffe auf tier_sicht=1, Stichprobe bestanden | Korrektur-SQL muss angewendet werden (Frank-Entscheid auf 22 Medizin-Begriffe), ETL-Überschreib-Verhalten unklar |
| **junction-tabelle-mehrfach-eltern.md** | ENTWURF | Spur A.2 erledigt: 278 Einträge (273 primary + 5 secondary) via Junction-Import | Mindestens 5 Knoten mit 2+ Eltern, BOARD Multi-Parent-Hinweis | A.1-A.5 noch nicht umgesetzt, aber Funktionalität faktisch live |
| **wissens-integration-v3-extra-session.md** | ENTWURF (Folge-Session geplant) | 0 - komplett noch zu bauen (V3.1 Frank-Diktate, V3.5 Verifizierungs-Pipeline, V3.7 Review-UI) | V3.1 (>=5 Diktate) + V3.5 (50 Atome verifiziert) + V3.7 (Review-UI exists) | Frank-Diktate-Export, WordPress-Crawler-Domain-Freigabe, Windows-DB-Export (Klangschalen + Planetenschalen) |

**Evidenz:**
- klangschalenwissen: Spur C.3 `add_secondary_parents.py` hat 5 sekundäre Eltern aus `verwandt:` Frontmatter ergänzt
- wiki-llm-knowledge-graph: Spur 1a.4 "erfolgreich angewendet von Frank/Supabase 2026-05-25 16:45"
- wissensgraph-hitl-freigabe: Schritt 0 Befund in ausgaben/2026-06-09/03_wissensgraph-abschottung-befund.html (22 Medizin-Begriffe auf tier_sicht=1)
- junction-tabelle: klangschalenwissen Spur C.3 "278 Einträgen (273 primary + 5 secondary)"

---

## KONKURRENZ & DOPPELUNGEN - Kritische Überlappungen

| Konflikt | Speicher A | Speicher B | SSoT-Kandidat | Problem | Lösung |
|----------|-----------|-----------|----------------|---------|---------|
| **Wo lebt das Klangschalen-Kernwissen?** | wissensgraph v13 (704 Knoten) | knowledge.db (69 Atome) | wissensgraph v13 (jünger, vollständiger) | wissensgraph ist ENTWURF (noch nicht deployed), knowledge.db ist alt (2026-03-22), idea_scores (273) ist eine Teilliste | Wissensgraph-v13 muss deployed werden, dann ist es SSoT; knowledge.db wird zum Read-Only-Archiv |
| **Planetentöne-Quelle** | PL-SETS.planetentoene (26 Töne mit 44 Feldern) | wissensgraph.konzepte (Subset der 704) | PL-SETS (Quelle für alle anderen) | Doppeltes Daten-halten (einmal aktiv mit 44 Feldern, einmal als statisches Konzept) | PL-SETS bleibt Quelle, wissensgraph referenziert via skos:exactMatch oder wikidata-URL |
| **Idee/Plan-Hierarchie** | planning.idea_scores (parent_id + idea_relations) | wissensgraph.beziehungen + konzepte | planning.idea_scores (für Pläne), wissensgraph (für Wissens-Semantik) | idea_scores vermischt Pläne mit Wissens-Knoten, zwei verschiedene Domänen | Klare Rollentrennung: idea_scores = Task-/Plan-Hierarchie, wissensgraph = semantische Konzept-Graphen |
| **E-E-A-T-Content-Generator** | Zwei Versionen: eeat_content_generator.py + eeat_content_generator_v2.py | beide unter tools/ | eeat_content_generator_v2.py | Unklar welche aktiv ist, Wartungs-Splitter | Git-History prüfen, alte Version löschen (evidence_ref Commit-Datum) |

**Evidenz:**
- wissensgraph-schema.sql Kommentar: "Ziel-Store-Entscheidung Frank 2026-06-08: eigene Tabellen im Schema `wissensgraph`, NICHT planning.idea_scores"
- PL-SETS schema.md: planetentoene Zeile 6 "Stand: 2026-06-04. Verbindung: supabase_client.py"
- knowledge.db Modifikation 2026-03-22 vs wissensgraph 2026-06-08

---

## JÜNGSTER STAND - Chronologische Aktivität (neueste zuerst)

| Datum/Uhrzeit | Was | Wer | Beleg |
|---|---|---|---|
| 2026-06-09 17:05 | Auto-Pläne generiert (Chakra-Entscheidung, ETL-Überschreib-Verhalten) | Auto-System | auto-2026-06-09-entscheide-die-4-chakra-faelle.md |
| 2026-06-09 12:22 | wissensgraph-komplett.sql & lade.sql finalisiert (704 Knoten, 726 Kanten, alle draft) | ETL | bericht.md im out/ Verzeichnis |
| 2026-06-09 15:45 | PL-SETS supabase-schema.md letzte Änderung | PL-SETS Entwicklung | Datei-Modifikation |
| 2026-06-08 12:22 | wissensgraph konzepte.json & beziehungen.json generiert | wissensgraph-bau | wissensgraph_schema.sql Kommentar (Frank 2026-06-08) |
| 2026-05-26 19:30 | klangschalen-atome-board.html generiert (302 Atome visualisiert) | Claude | 18_klangschalen-atome-board.html Datei-Datum |
| 2026-05-26 | Klangschalenwissen-Plan: C.1-C.4 abgeschlossen, 273 Knoten importiert | Claude + Frank | klangschalenwissen-knowledge-base.md Spur C.1-C.4 |
| 2026-05-25 | wiki-llm-knowledge-graph Spur 1a Migration erfolgreich angewendet | Frank | wiki-llm-knowledge-graph-stufe1.md Spur 1a.4 |
| 2026-03-22 | knowledge.db zuletzt aktualisiert (69 Atome) | Antiker Importlauf | knowledge.db Datei-Modifikation 18:37 |

---

## ZUSAMMENFASSUNG - 3 WELTEN, 1 SSOT-PROBLEM

### Die 3 Wissens-Speicher heute (2026-06-09):

1. **wissensgraph v13** (Projekt: `wissensgraph-bau/`)
   - 704 Knoten (Konzepte: Planetenschalen, Chakras, Wirkungen, etc.)
   - 726 Kanten (Beziehungen mit Prädiakten: hat_chakra, hat_wirkung, etc.)
   - Status: ALLE `status='draft'` - nichts freigegeben, HITL-Gate blockiert Veröffentlichung
   - HWG-Problem: 0 Knoten auf tier_sicht=3 (internal_only), 22 Medizin-Begriffe auf tier_sicht=1 (public) - BLOCKER vor Freigabe
   - Schema: eigene Supabase-Tabellen (wissensgraph.konzepte, wissensgraph.beziehungen)
   - Modell: v13 mit 4-Ebenen-Ontologie (Wissen | Intent | Content | Personas)

2. **knowledge.db (SQLite)** (Projekt: `unified-agent-system/mcp-servers/knowledge-base/`)
   - 69 Sound-Spirit-Fakten-Atome (Planetentöne-Registry, alt)
   - Status: LIVE, aber stagnant (zuletzt 2026-03-22)
   - Rolle: ReadOnly-Archiv, MCP-Server nutzt es als Basis
   - Gefahr: veraltet gegenüber wissensgraph

3. **planning.idea_scores** (Supabase planning-Schema)
   - 273 Wissens-Knoten (aus Klangschalen-Recherche 2026-05-26)
   - 278 Verknüpfungen via Junction-Tabelle idea_parents
   - Status: LIVE, aktiv wachsend
   - Problem: vermischt Pläne (parent_id als Task-Hierarchie) mit Wissens-Knoten (tags=['wissens-knoten'], tier-Klassifikation)
   - Rolle: heute de-facto-Speicher für Klangschalen-Atome, aber nicht dafür gebaut

### Die Entscheidung die getroffen werden muss:

**SSoT-Frage:** Welcher Speicher wird die Single Source of Truth für Sound-Spirit-Wissen?

| Option | Pro | Contra |
|--------|-----|--------|
| A: wissensgraph v13 wird SSoT | • Eigenes Schema (Ontologie-Modell), nicht Eigenbau-Hybrid • Modell vollständig (4 Ebenen, Tier-Klassifikation, HWG-Gate) • 704 Knoten vs 273 idea_scores | • Noch im ENTWURF (status=draft), HWG-Blocker, Frank-Sign-off ausstehend • Deployment offen • ETL-Überschreib-Verhalten unklar (Welle-2-Stabilität) |
| B: planning.idea_scores wird SSoT | • Live, aktiv bearbeitet • Integration mit Plänen (parent_id) • Embedding-Vektoren schon gefüllt | • Hybrid mit Task-Plänen, nicht sauber für Wissen allein • 273 vs 704 Knoten (lückenhafte Coverage) • Sprachlich nicht als "Knowledge-Base" benannt |
| C: Hybrid-SSoT (wissensgraph + idea_scores) | • Best-of-both: semantische Konzepte + Klangschalen-Spezifika • Weniger Umbauten | • Zwei Schreibziele, Sync-Problem • Doppelte Wahrheit bei Änderungen • Wartungs-Splitter |

---

## KLARE BEFUNDE FÜR FRANK

1. **Wissensgraph ist bereit, aber blockiert.** 704 Konzepte sind extrahiert und strukturiert, aber `status='draft'` + 22 HWG-Fehler verhindern jede Freigabe. Korrektur-SQL existiert (ausgaben/2026-06-09/03_korrektur_tier3_medizin.sql), braucht aber Frank-Entscheidung auf 22 Begriffe.

2. **knowledge.db ist Archiv geworden.** Die 69 Atome sind so alt (2026-03-22), dass idea_scores + wissensgraph sie überholt haben. Weiter nutzen als Read-Only via MCP, aber nicht als Quelle neu einspeisen.

3. **idea_scores ist ein Hybrid ohne Klarheit.** 273 Klangschalen-Knoten + 22 parent_ids + Embedding-Vektoren live - aber it's vermischt mit Task-Plänen (parent_id-Semantik). Die "Mehrfach-Eltern" über Junction-Tabelle sind bereits funktionsfähig (278 Einträge), aber nicht dokumentiert als Features.

4. **Drei Quellen, aber EINE fehlende Integrationsschicht.** WordPress-Crawler, Diktate-Import, DB-Exports (Klangschalen, Planetenschalen) sind alle geplant in wissens-integration-v3 - aber alle blockiert bis klar ist: wohin die Daten? wissensgraph oder idea_scores?

---

## NÄCHSTER SCHRITT (Imperativ - kein Fragezeichen)

**Entscheide die SSoT-Frage und weise die Wiederaufbau-Arbeit zu.** Beide Pfade sind technisch machbar:
- **Pfad A (wissensgraph):** 3-4 Tage HWG-Freigaben + ETL-Stabilitäet, dann Deployment + Migration idea_scores -> wissensgraph als Read-Only-Mirror.
- **Pfad B (idea_scores):** Sofort produktiv, aber idea_scores-Schema mit Wissens-Domänen-Feldern erweitern (Tier-Klassifikation, HWG-Flag, Ontologie-Attribute), Junction-Tabelle dokumentieren, dann erst Quellen-Integration.

Ohne diese Entscheidung bleibt alles hängend. Die Diktate, WordPress, DBs warten alle auf die Antwort "wohin mit diesen Daten?"

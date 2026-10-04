# Fachbegriff-Sperre, Spiegel für die CI aller Repos

Dieser Ordner ist eine **Kopie** aus `Klangschalen/wissensgraph` (`tools/fachbegriff_sperre.py`,
`tools/fachbegriff_ci.py`, `wissen/messverfahren.json`). Die Quelle bleibt wissensgraph; dort
werden Fakten und Muster gepflegt. Die Kopie liegt hier, weil dieses Repo öffentlich ist und der
wiederverwendbare Workflow `fachbegriff-sperre.yml` sie ohne Geheimnis auschecken kann; wissensgraph
ist privat, und in pl-sets, zentrale und klangschalen-analyse gab es kein Token dafür (gemessen
04.10.2026: dort lief die Sperre nur als "NICHT PRUEFBAR").

Drift-Schutz: Die CI von wissensgraph vergleicht bei jedem Lauf die drei Dateien byte-gleich mit
dieser Kopie (`raw.githubusercontent.com/Klangschalen/.github/main/fachbegriff/...`) und wird rot,
wenn sie auseinanderlaufen. Wer wissensgraph ändert, aktualisiert im selben Zug diese Kopie.

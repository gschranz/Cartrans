# JS-Cartrans – neue Website (Testversion)

Statische Website mit kleinem Python-Dienst, ausgeliefert mit **Caddy**, gebaut wie das TEK-Projekt (Railway-fähig über `Dockerfile`).

## Aufbau
| Pfad | Inhalt |
|---|---|
| `*.html` | fertige Seiten, von `build.py` erzeugt: **nicht direkt bearbeiten** |
| `src/pages/` | Seiteninhalte mit Platzhaltern (`{{bild:…}}`, `{{partial:…}}`, `{{TEL1}}` …), `_ort.html` = Vorlage der Ortsseiten |
| `src/partials/` | Notruf-Knöpfe, Schlussband, Transportformular, Rückruf |
| `build.py` | Kopf/Fuß, Bilder, Karte, Galerie, FAQ, Ortsseiten, JSON-LD, Sitemap. Kontaktdaten zentral in `K` |
| `css/base.css` | gesamtes Design (Tokens oben), `css/fonts.css` lokale Schriften |
| `js/core.js` | Textanimationen, Menü, Standort per WhatsApp, Tabs, Galerie, Formulare, Klickzählung |
| `bilder/` | aufbereitete Fotos (AVIF/WebP/JPG, 640–1920 px), erzeugt von `tools/bilder.py` aus `../original/bilder` |
| `server/api.py` | Anfragen (`/api/anfrage`), Klickzählung (`/api/zaehler`), Checkliste (`/api/checkliste`); lokal auch Webserver |
| `betreiber/offene-punkte.html` | Checkliste „Was wir von Cartrans noch brauchen“ zum Abhaken |
| `tools/` | `bilder.py`, `shot.mjs` (ganzseitige Screenshots), `klick.mjs` (Interaktionstest), `pruefen.mjs` (Qualitätsprüfung) |

## Ändern
```bash
python tools/bilder.py   # nur wenn Fotos dazukommen (Katalog oben in der Datei)
python build.py          # Seiten neu erzeugen
node tools/pruefen.mjs   # alle Seiten auf 5 Breiten prüfen (Server muss laufen)
```

## Lokal ansehen
Launch-Konfiguration `cartrans` (Port 8796) startet `server/api.py` mit `STATIC_DIR`, dann funktionieren auch Formulare,
saubere Adressen (`/kontakt`) und die Weiterleitungen von den alten Wix-Adressen.
Checkliste lokal: http://localhost:8796/betreiber/offene-punkte.html?k=test123

## Railway
Deploy per `Dockerfile`. Volume unter `/data` einhängen (Anfragen, Zähler, Checkliste).
Umgebungsvariablen: `CHECKLIST_KEY` (Schlüssel zum Abhaken, Link dann `…/offene-punkte.html?k=SCHLÜSSEL`),
`STATS_KEY` (Auswertung `/api/zaehler?k=…`), für E-Mails `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `MAIL_TO`, `MAIL_FROM`.
Ohne SMTP werden Anfragen nur in `/data/anfragen.jsonl` gespeichert.

## Vor dem Livegang
Siehe Checkliste: Impressum ergänzen, Datenschutz freigeben, Kennzeichen auf Fotos klären, Partner-Freigaben, Domain/E-Mail-Zugang.

"""Kleiner Dienst für die Cartrans-Website. Nur Python-Standardbibliothek.

Läuft im Container hinter Caddy auf 127.0.0.1:$API_PORT, Caddy leitet /api/* hierher.
Lokal (STATIC_DIR gesetzt) liefert er zusätzlich die Website aus, inkl. sauberer Adressen
(/kontakt -> kontakt.html) und der Weiterleitungen von den alten Wix-Adressen.

  POST /api/anfrage        Transportanfrage oder Rückruf -> DATA_DIR/anfragen.jsonl (+ E-Mail, wenn SMTP gesetzt)
  POST /api/zaehler        {"art": "anruf"|"whatsapp", "seite": "/..."} -> Tageszähler, ohne IP oder Cookies
  GET  /api/zaehler?k=...  Auswertung (nur mit STATS_KEY)
  GET  /api/checkliste     Stand der Betreiber-Checkliste
  POST /api/checkliste     {"id": "...", "done": true|false}   Header X-Checkliste-Schluessel, wenn CHECKLIST_KEY gesetzt

Umgebung: DATA_DIR (/data), API_PORT (8081), STATIC_DIR, CHECKLIST_KEY, STATS_KEY,
          SMTP_HOST, SMTP_PORT (587), SMTP_USER, SMTP_PASS, MAIL_TO (office@cartrans.at), MAIL_FROM
"""
import hmac, json, os, re, smtplib, sys, tempfile, threading, time
from email.message import EmailMessage
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs

DATA_DIR = os.environ.get("DATA_DIR", "/data")
PORT = int(os.environ.get("API_PORT", "8081"))
STATIC_DIR = os.environ.get("STATIC_DIR", "")
CHECKLIST_KEY = os.environ.get("CHECKLIST_KEY", "")
STATS_KEY = os.environ.get("STATS_KEY", "")
MAIL_TO = os.environ.get("MAIL_TO", "office@cartrans.at")

WEITERLEITUNG = {  # alte Wix-Adressen -> neue Seiten
    "/contact-2": "/kontakt", "/unsere-leistungen": "/pannenhilfe", "/unsere-arbeit": "/einsaetze",
    "/partner": "/ueber-uns#partner", "/agb-s": "/agb", "/book-online": "/", "/recipes": "/",
}
FELDER = {"typ": 20, "name": 120, "telefon": 40, "email": 160, "nachricht": 2000, "fahrzeug": 160, "art": 60,
          "fahrbereit": 10, "von": 200, "nach": 200, "datum": 20, "hinweis": 500, "seite": 120, "firma": 160}
ID_MUSTER = re.compile(r"^[a-z0-9]{1,20}-\d{1,3}$")

sperre = threading.Lock()
letzte = {}  # IP -> Zeitpunkte der letzten Anfragen (nur im Speicher, für die Drosselung)


def pfad(name):
    return os.path.join(DATA_DIR, name)


def json_laden(name, leer):
    try:
        with open(pfad(name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return leer


def json_sichern(name, daten):
    os.makedirs(DATA_DIR, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR, prefix=".tmp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False)
    os.replace(tmp, pfad(name))


def mail_senden(daten):
    host = os.environ.get("SMTP_HOST")
    if not host:
        return
    titel = "Transportanfrage" if daten.get("typ") == "transport" else "Rückrufbitte"
    m = EmailMessage()
    m["Subject"] = f"Website: {titel} von {daten.get('name', '')}"
    m["From"] = os.environ.get("MAIL_FROM", os.environ.get("SMTP_USER", MAIL_TO))
    m["To"] = MAIL_TO
    if daten.get("email"):
        m["Reply-To"] = daten["email"]
    m.set_content("\n".join(f"{k}: {v}" for k, v in daten.items()))
    with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587")), timeout=15) as s:
        s.starttls()
        if os.environ.get("SMTP_USER"):
            s.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASS", ""))
        s.send_message(m)


class Handler(SimpleHTTPRequestHandler):
    server_version = "cartrans"
    sys_version = ""
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".webmanifest": "application/manifest+json",
                      ".avif": "image/avif", ".webp": "image/webp", ".woff2": "font/woff2", ".svg": "image/svg+xml"}

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=STATIC_DIR or None, **kw)

    def log_message(self, fmt, *args):
        sys.stderr.write("api %s\n" % (fmt % args))

    def antwort(self, code, daten):
        roh = json.dumps(daten, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(roh)))
        self.end_headers()
        self.wfile.write(roh)

    def eingabe(self, maximal=8192):
        try:
            laenge = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if laenge <= 0 or laenge > maximal:
            return None
        try:
            return json.loads(self.rfile.read(laenge).decode("utf-8"))
        except ValueError:
            return None

    def ip(self):
        return (self.headers.get("X-Forwarded-For") or self.client_address[0]).split(",")[0].strip()

    # ---------------------------------------------------------- GET
    def do_GET(self):
        teile = urlsplit(self.path)
        p = teile.path
        if p == "/api/checkliste":
            with sperre:
                d = json_laden("checkliste.json", {"done": {}, "stand": time.strftime("%Y-%m-%d")})
            return self.antwort(200, {**d, "schreibschutz": bool(CHECKLIST_KEY)})
        if p == "/api/zaehler":
            k = parse_qs(teile.query).get("k", [""])[0]
            if not STATS_KEY or not hmac.compare_digest(k, STATS_KEY):
                return self.antwort(403, {"fehler": "schluessel"})
            with sperre:
                return self.antwort(200, json_laden("zaehler.json", {}))
        if p.startswith("/api/"):
            return self.antwort(404, {"fehler": "unbekannt"})
        if not STATIC_DIR:
            return self.antwort(404, {"fehler": "unbekannt"})
        # lokale Vorschau: Weiterleitungen und saubere Adressen wie auf dem Server (Caddy)
        if p.rstrip("/") in WEITERLEITUNG:
            self.send_response(301)
            self.send_header("Location", WEITERLEITUNG[p.rstrip("/")])
            self.end_headers()
            return
        voll = os.path.join(STATIC_DIR, p.lstrip("/"))
        if p != "/" and not os.path.splitext(p)[1] and os.path.isfile(voll.rstrip("/") + ".html"):
            self.path = p.rstrip("/") + ".html" + (("?" + teile.query) if teile.query else "")
        elif p != "/" and not os.path.exists(voll):
            return self._404()
        return super().do_GET()

    def _404(self):
        try:
            with open(os.path.join(STATIC_DIR, "404.html"), "rb") as f:
                roh = f.read()
        except OSError:
            roh = b"404"
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        self.end_headers()
        self.wfile.write(roh)

    def end_headers(self):
        if STATIC_DIR and not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    # ---------------------------------------------------------- POST
    def do_POST(self):
        p = urlsplit(self.path).path
        if p == "/api/anfrage":
            return self.anfrage()
        if p == "/api/zaehler":
            return self.zaehler()
        if p == "/api/checkliste":
            return self.checkliste()
        return self.antwort(404, {"fehler": "unbekannt"})

    def anfrage(self):
        d = self.eingabe()
        if not isinstance(d, dict):
            return self.antwort(400, {"fehler": "format"})
        if d.get("website"):  # Honigtopf: Bots füllen das versteckte Feld aus
            return self.antwort(200, {"ok": True})
        jetzt = time.time()
        with sperre:
            zeiten = [t for t in letzte.get(self.ip(), []) if jetzt - t < 600]
            if len(zeiten) >= 5:
                return self.antwort(429, {"fehler": "zu_viele"})
            zeiten.append(jetzt)
            letzte[self.ip()] = zeiten
        sauber = {k: str(d.get(k, ""))[:n].strip() for k, n in FELDER.items() if d.get(k)}
        if sauber.get("typ") not in ("transport", "rueckruf") or not sauber.get("name") or len(re.sub(r"\D", "", sauber.get("telefon", ""))) < 6:
            return self.antwort(400, {"fehler": "pflichtfelder"})
        if d.get("einwilligung") not in ("on", True, "true"):
            return self.antwort(400, {"fehler": "einwilligung"})
        sauber["eingang"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with sperre:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(pfad("anfragen.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(sauber, ensure_ascii=False) + "\n")
        try:
            mail_senden(sauber)
        except Exception as fehler:  # Anfrage ist gespeichert, Mailfehler nur protokollieren
            sys.stderr.write(f"api mail fehlgeschlagen: {fehler}\n")
        return self.antwort(200, {"ok": True})

    def zaehler(self):
        d = self.eingabe(512)
        if not isinstance(d, dict) or d.get("art") not in ("anruf", "whatsapp"):
            return self.antwort(400, {"fehler": "format"})
        seite = re.sub(r"[^a-z0-9/\-]", "", str(d.get("seite", "/")).lower())[:60] or "/"
        tag = time.strftime("%Y-%m-%d")
        with sperre:
            z = json_laden("zaehler.json", {})
            eintrag = z.setdefault(tag, {})
            schluessel = f'{d["art"]} {seite}'
            eintrag[schluessel] = eintrag.get(schluessel, 0) + 1
            json_sichern("zaehler.json", z)
        return self.antwort(200, {"ok": True})

    def checkliste(self):
        if CHECKLIST_KEY and not hmac.compare_digest(self.headers.get("X-Checkliste-Schluessel", ""), CHECKLIST_KEY):
            return self.antwort(403, {"fehler": "schluessel"})
        d = self.eingabe(2048)
        if not isinstance(d, dict):
            return self.antwort(400, {"fehler": "format"})
        pid, erledigt = d.get("id"), d.get("done")
        if not isinstance(pid, str) or not ID_MUSTER.match(pid) or not isinstance(erledigt, bool):
            return self.antwort(400, {"fehler": "format"})
        with sperre:
            daten = json_laden("checkliste.json", {"done": {}})
            if erledigt:
                if pid not in daten["done"] and len(daten["done"]) >= 500:
                    return self.antwort(400, {"fehler": "voll"})
                daten["done"][pid] = True
            else:
                daten["done"].pop(pid, None)
            daten["stand"] = time.strftime("%Y-%m-%d")
            try:
                json_sichern("checkliste.json", daten)
            except OSError:
                return self.antwort(500, {"fehler": "speichern"})
        return self.antwort(200, {**daten, "schreibschutz": bool(CHECKLIST_KEY)})


if __name__ == "__main__":
    host = "127.0.0.1"
    print(f"Cartrans-API auf {host}:{PORT}, Ablage {DATA_DIR}" + (f", Website aus {STATIC_DIR}" if STATIC_DIR else ""), flush=True)
    ThreadingHTTPServer((host, PORT), Handler).serve_forever()

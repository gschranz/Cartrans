"""Erzeugt die fertigen HTML-Seiten aus src/pages und src/partials.

  python build.py

Platzhalter in den Seiten:
  {{bild:slug|sizes|eager|klasse}}   <picture> mit AVIF/WebP/JPG und festen Maßen
  {{icon:name}}                       SVG-Symbol aus assets/icons.svg
  {{partial:name}}                    Baustein aus src/partials/name.html
  {{galerie}} {{fracht}} {{karte}} {{partner}} {{faq:gruppe}} {{orte}}
  {{TEL1}} {{TEL1_HREF}} {{TEL2}} {{TEL2_HREF}} {{WA_HREF}} {{MAIL}} {{JAHR}}

Jede Seite beginnt mit einem Kommentar  <!--meta {...json...} -->
"""
import html, json, math, os, re, sys, datetime

HIER = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HIER, "src")
DOMAIN = "https://www.cartrans.at"

K = {
    "TEL1": "0660 107 70 52", "TEL1_HREF": "tel:+436601077052",
    "TEL2": "0664 731 130 51", "TEL2_HREF": "tel:+4366473113051",
    "WA_NR": "436601077052",
    "MAIL": "office@cartrans.at",
    "STRASSE": "Jasmingasse 2", "PLZ": "2601", "ORT": "Eggendorf",
    "JAHR": str(datetime.date.today().year),
}
K["WA_HREF"] = "https://wa.me/" + K["WA_NR"]

NAV = [
    ("pannenhilfe", "/pannenhilfe", "Notdienst"),
    ("transporte", "/transporte", "Transporte"),
    ("autohaeuser", "/autohaeuser", "Autohäuser"),
    ("einsaetze", "/einsaetze", "Einsätze"),
    ("ueber-uns", "/ueber-uns", "Über uns"),
    ("kontakt", "/kontakt", "Kontakt"),
]

KAT = {"sportwagen": "Sportwagen", "oldtimer": "Oldtimer", "unfall": "Unfall & Bergung",
       "motorrad": "Motorrad", "ueberstellung": "Überstellung", "fuhrpark": "Fuhrpark"}

PARTNER = [
    ("EP-Carserviss", "Eggendorf", "Mietwagen nach der Panne"),
    ("Autohaus Narowetz", "Brunn am Gebirge", None),
    ("car.acho GmbH", "Brunn am Gebirge", None),
    ("Kopf Roman Transportservice", "Sierndorf", None),
    ("Kfz-Meisterbetrieb Vivod", "Breitenfurt", None),
    ("Autohaus Willander", "Wien-Liesing", None),
]

# Karte: Mittelpunkt Eggendorf (ungefähr), Maßstab 8 px je km
MITTE = (47.866, 16.305)
PX_KM = 8.0
ORTE_KARTE = [
    ("Wien", 48.208, 16.373, "o"), ("Mödling", 48.086, 16.283, "w"), ("Wiener Neudorf", 48.083, 16.316, "o+"),
    ("Brunn a. G.", 48.107, 16.285, "w+"), ("Baden", 48.006, 16.234, "w"), ("Bad Vöslau", 47.966, 16.214, "w+"),
    ("Ebreichsdorf", 47.961, 16.404, "o+"), ("Wiener Neustadt", 47.815, 16.243, "w"), ("Neunkirchen", 47.720, 16.080, "w"),
    ("Mattersburg", 47.737, 16.397, "o+"), ("Eisenstadt", 47.845, 16.520, "o"), ("Leobersdorf", 47.930, 16.215, "w+"),
]
STRASSEN = [
    ("A2", [(48.160, 16.330), (48.110, 16.322), (48.060, 16.312), (48.010, 16.292), (47.960, 16.262), (47.905, 16.250),
            (47.850, 16.262), (47.800, 16.252), (47.752, 16.182), (47.700, 16.112), (47.655, 16.060)], (48.035, 16.300)),
    ("S4", [(47.800, 16.252), (47.772, 16.318), (47.742, 16.392)], (47.772, 16.318)),
    ("A3", [(48.050, 16.325), (47.992, 16.378), (47.932, 16.420), (47.872, 16.470), (47.815, 16.530)], (47.932, 16.420)),
]

# Ortsseiten für Google (ohne Menüeintrag). Texte bewusst je Ort eigenständig.
ORTSSEITEN = [
    {
        "slug": "abschleppdienst-wiener-neustadt", "ort": "Wiener Neustadt", "lat": 47.815, "lon": 16.243,
        "titel": "Abschleppdienst Wiener Neustadt", "bild": "audi-r8-nacht",
        "desc": "Abschleppdienst und Pannenhilfe in Wiener Neustadt, rund um die Uhr. JS-Cartrans aus Eggendorf: Abschleppen, Starthilfe, Unfallbergung. Tel. 0660 107 70 52.",
        "h1": ["Abschleppdienst", "Wiener Neustadt"],
        "lead": "Liegengeblieben in Wiener Neustadt, am Knoten oder auf der S4? Wir sitzen direkt nebenan in Eggendorf und sind Tag und Nacht erreichbar.",
        "absaetze": [
            "Von unserem Standort in Eggendorf nach Wiener Neustadt sind es rund {km} Kilometer. Damit gehört die Stadt zu unserem engsten Einsatzgebiet: vom Stadtgebiet über die Gewerbegebiete bis zu den Umlandgemeinden wie Theresienfeld, Felixdorf, Lichtenwörth und Katzelsdorf.",
            "Typische Einsätze rund um Wiener Neustadt sind Pannen auf der A2 Südautobahn und der S4 Mattersburger Schnellstraße, Unfallfahrzeuge nach Kollisionen im Stadtverkehr und Starthilfe an kalten Morgen. Nicht fahrbereite Fahrzeuge bringen wir in die Werkstatt Ihrer Wahl.",
        ],
        "strassen": ["A2 Südautobahn", "S4 Mattersburger Schnellstraße", "B17 Triester Straße", "B21", "B26", "B53"],
    },
    {
        "slug": "abschleppdienst-baden", "ort": "Baden", "lat": 48.006, "lon": 16.234,
        "titel": "Abschleppdienst Baden", "bild": "unfall-suv",
        "desc": "Abschleppdienst und Pannenhilfe im Bezirk Baden, 24/7. Abschleppen, Starthilfe, Unfallbergung und Fahrzeugtransporte. JS-Cartrans, Tel. 0660 107 70 52.",
        "h1": ["Abschleppdienst", "Baden"],
        "lead": "Panne in Baden, Bad Vöslau oder auf der A2 Richtung Wien? Rufen Sie an, wir sind rund um die Uhr unterwegs.",
        "absaetze": [
            "Baden liegt rund {km} Kilometer nördlich von unserem Standort in Eggendorf. Wir fahren im ganzen Bezirk: Baden, Bad Vöslau, Traiskirchen, Leobersdorf, Kottingbrunn, Oberwaltersdorf und Umgebung.",
            "Auf der A2 zwischen Leobersdorf und dem Knoten Guntramsdorf ist viel Verkehr, entsprechend oft bleibt jemand liegen. Ob Reifenschaden auf dem Pannenstreifen, leere Batterie am Parkplatz der Therme oder ein Unfallfahrzeug: Wir laden Ihr Auto sicher auf und bringen es dorthin, wo es repariert werden soll.",
        ],
        "strassen": ["A2 Südautobahn", "A3 Südost Autobahn", "B17 Triester Straße", "B210", "B212"],
    },
    {
        "slug": "abschleppdienst-moedling", "ort": "Mödling", "lat": 48.086, "lon": 16.283,
        "titel": "Abschleppdienst Mödling", "bild": "unfall-bmw-z4-feuerwehr",
        "desc": "Abschleppdienst Mödling, Wiener Neudorf, Brunn am Gebirge: Pannenhilfe, Abschleppen und Überstellungen rund um die Uhr. JS-Cartrans, Tel. 0660 107 70 52.",
        "h1": ["Abschleppdienst", "Mödling"],
        "lead": "Im Bezirk Mödling sind wir oft unterwegs, auch weil zwei unserer Partnerbetriebe in Brunn am Gebirge sitzen.",
        "absaetze": [
            "Mödling liegt rund {km} Kilometer von unserem Standort in Eggendorf entfernt. Wir kommen nach Mödling, Wiener Neudorf, Brunn am Gebirge, Maria Enzersdorf, Perchtoldsdorf, Guntramsdorf und in die Gemeinden rundherum.",
            "Rund um das Gewerbegebiet an der Triester Straße, die A2 und die A21 Außenring Autobahn gibt es viel Verkehr und viele Autohäuser. Neben Pannenhilfe und Abschleppen übernehmen wir hier häufig Überstellungen zwischen Kunden, Werkstätten und Autohäusern, etwa für unsere Partner Autohaus Narowetz und car.acho in Brunn am Gebirge.",
        ],
        "strassen": ["A2 Südautobahn", "A21 Außenring Autobahn", "B17 Triester Straße", "B11"],
    },
    {
        "slug": "pannenhilfe-a2", "ort": "A2 Südautobahn", "lat": 47.960, "lon": 16.262,
        "titel": "Pannenhilfe A2 Südautobahn", "bild": "unfall-front",
        "desc": "Panne auf der A2 Südautobahn zwischen Wien und Wiener Neustadt? JS-Cartrans hilft rund um die Uhr: Abschleppen, Unfallbergung, Pannenhilfe. Tel. 0660 107 70 52.",
        "h1": ["Pannenhilfe", "A2 Südautobahn"],
        "lead": "Liegengeblieben auf der A2? Erst in Sicherheit bringen, dann anrufen. Wir kommen, Tag und Nacht.",
        "absaetze": [
            "Unser Standort in Eggendorf liegt nur wenige Minuten von der A2 entfernt, zwischen den Anschlussstellen Wiener Neustadt und Baden. Von hier sind wir schnell in beiden Richtungen unterwegs: nach Norden Richtung Wien und nach Süden Richtung Seebenstein und Wechsel.",
            "Auf der Autobahn gilt: Warnblinker an, Warnweste anziehen, bevor Sie aussteigen, und alle Mitfahrenden hinter die Leitplanke. Merken Sie sich die nächste Kilometertafel am Fahrbahnrand oder senden Sie uns Ihren Standort per WhatsApp, dann finden wir Sie sofort.",
        ],
        "strassen": ["A2 Wien bis Wiener Neustadt", "A2 Richtung Seebenstein", "Knoten Wiener Neustadt (S4)", "Knoten Guntramsdorf (A3)"],
    },
]

FAQ = {
    "notdienst": [
        ("Kommen Sie auch nachts, am Wochenende und an Feiertagen?",
         "Ja. Wir sind 24 Stunden am Tag, 365 Tage im Jahr erreichbar, auch an Sonn- und Feiertagen."),
        ("Was muss ich am Telefon sagen?",
         "Wo Sie stehen (Straße, Autobahn-Kilometer oder Standort per WhatsApp), welches Fahrzeug es ist, was passiert ist und ob es noch fährt. Sagen Sie uns auch, ob der Schlüssel da ist und wohin das Fahrzeug soll."),
        ("Wohin bringen Sie mein Fahrzeug?",
         "Dorthin, wo es hin soll: in Ihre Werkstatt, zu Ihnen nach Hause oder zu einem unserer Partnerbetriebe. Sagen Sie es uns beim Anruf."),
        ("Fahren Sie auch ins Ausland?",
         "Ja, Abschleppungen und Fahrzeugtransporte übernehmen wir im In- und Ausland. Rufen Sie an, dann klären wir Strecke und Termin."),
        ("Was kostet ein Einsatz?",
         "Das hängt von Strecke, Fahrzeug und Aufwand ab. Fragen Sie beim Anruf einfach nach. Bezahlt wird nach dem Einsatz bar oder mit Karte, sofern nichts anderes vereinbart ist."),
        ("Kann ich einen Auftrag stornieren?",
         "Ja. Kostenlos ist das, solange unser Fahrzeug noch nicht losgefahren ist. Danach verrechnen wir die bis dahin entstandenen Kosten."),
        ("Bekomme ich einen Ersatzwagen?",
         "Über unseren Partnerbetrieb EP-Carserviss können wir Ihnen nach einer Panne einen Mietwagen vermitteln. Sprechen Sie uns darauf an."),
    ],
    "transport": [
        ("Wie wird mein Fahrzeug gesichert?",
         "Wir verladen auf einem Autotransportanhänger und sichern jedes Fahrzeug mit Spanngurten an den Rädern. Tiefe Sportwagen laden wir mit flachen Auffahrrampen."),
        ("Muss das Fahrzeug fahrbereit sein?",
         "Nein. Wir transportieren auch Fahrzeuge, die nicht mehr fahren, etwa nach einem Unfall oder bei einem Motorschaden."),
        ("Wie schnell bekomme ich ein Angebot?",
         "Schicken Sie uns die Anfrage mit Start, Ziel und Fahrzeug. Wir melden uns mit einem Angebot telefonisch oder per E-Mail."),
        ("Transportieren Sie auch Motorräder?",
         "Ja, Motorräder, Motocross-Maschinen und Roller transportieren wir ebenfalls."),
    ],
}


# ---------------------------------------------------------------- Hilfen
BILDER = {b["slug"]: b for b in json.load(open(os.path.join(HIER, "bilder", "bilder.json"), encoding="utf-8"))}


def e(t):
    return html.escape(str(t), quote=True)


def icon(name, klasse=""):
    k = f' class="{klasse}"' if klasse else ""
    return f'<svg{k} aria-hidden="true" focusable="false"><use href="/assets/icons.svg#{name}"></use></svg>'


def bild(slug, sizes="100vw", eager=False, klasse="", alt=None):
    b = BILDER[slug]
    fx, fy = b["fokus"]
    srcset = lambda fmt: ", ".join(f"/bilder/{slug}-{w}.{fmt} {w}w" for w in b["breiten"])
    laden = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    k = f' class="{klasse}"' if klasse else ""
    alt = b["alt"] if alt is None else alt
    return (f'<picture><source type="image/avif" srcset="{srcset("avif")}" sizes="{sizes}">'
            f'<source type="image/webp" srcset="{srcset("webp")}" sizes="{sizes}">'
            f'<img{k} src="/bilder/{slug}-{b["jpg"]}.jpg" width="{b["w"]}" height="{b["h"]}" alt="{e(alt)}" '
            f'{laden} decoding="async" style="object-position:{fx}% {fy}%"></picture>')


def km(lat, lon, lat0=MITTE[0], lon0=MITTE[1]):
    dy = (lat - lat0) * 111.2
    dx = (lon - lon0) * 111.2 * math.cos(math.radians(lat0))
    return dx, dy


# ---------------------------------------------------------------- Bausteine
def galerie():
    zaehl = {}
    for b in BILDER.values():
        zaehl[b["kat"]] = zaehl.get(b["kat"], 0) + 1
    knoepfe = [f'<button type="button" aria-pressed="true" data-filter="alle">Alle<small>{len(BILDER)}</small></button>']
    for k, name in KAT.items():
        if k in zaehl:
            knoepfe.append(f'<button type="button" aria-pressed="false" data-filter="{k}">{e(name)}<small>{zaehl[k]}</small></button>')
    items = []
    for i, b in enumerate(BILDER.values()):
        titel, _, art = b["titel"].partition(" · ")
        items.append(
            f'<li data-kat="{b["kat"]}"><button type="button" data-lk="{i}" data-gross="/bilder/{b["slug"]}-{b["breiten"][-1]}.webp" '
            f'data-titel="{e(b["titel"])}" aria-label="{e(b["titel"])} vergrößern">'
            f'{bild(b["slug"], "(min-width:1100px) 25vw, (min-width:700px) 33vw, 50vw")}'
            f'<span class="g-text">{e(titel)}<small>{e(art or KAT[b["kat"]])}</small></span></button></li>')
    return (f'<div class="filter" role="group" aria-label="Einsätze filtern">{"".join(knoepfe)}</div>'
            f'<ul class="galerie" id="galerie">{"".join(items)}</ul>'
            '<dialog class="leuchtkasten" id="leuchtkasten" aria-label="Bildansicht">'
            f'<div class="lk-kopf"><span id="lk-zahl"></span><button type="button" class="lk-zu" data-lk-zu aria-label="Schließen">{icon("zu")}</button></div>'
            f'<div class="lk-buehne"><img id="lk-bild" alt=""><button type="button" class="lk-nav zurueck" data-lk-schritt="-1" aria-label="Vorheriges Bild">{icon("pfeil-links")}</button>'
            f'<button type="button" class="lk-nav vor" data-lk-schritt="1" aria-label="Nächstes Bild">{icon("pfeil")}</button></div>'
            '<p class="lk-text" id="lk-text" aria-live="polite"></p></dialog>')


FRACHT = [
    ("lamborghini-orange", "Lamborghini", "Überstellung"),
    ("mustang-rot", "Ford Mustang", "Oldtimer · Prüfstelle"),
    ("audi-r8-nacht", "Audi R8", "Nachttransport"),
    ("bmw-m3-e36", "BMW M3 E36", "Sammlerfahrzeug"),
    ("ktm-motocross", "KTM", "Motorrad"),
    ("audi-rs6-avant", "Audi RS 6", "Überstellung"),
    ("mustang-gruen", "Ford Mustang", "Oldtimer"),
    ("ram-pickup", "RAM Pick-up", "Transport"),
]


def fracht():
    li = []
    for slug, name, art in FRACHT:
        li.append(f'<li><figure><div class="f-bild">{bild(slug, "(min-width:1100px) 30vw, (min-width:700px) 46vw, 78vw")}</div>'
                  f'<figcaption><b>{e(name)}</b><span>{e(art)}</span></figcaption></figure></li>')
    return f'<ul class="fracht" id="fracht" tabindex="0" aria-label="Transportbeispiele, seitlich wischen">{"".join(li)}</ul>'


def karte():
    W, H = 1000, 760
    cx, cy = W / 2, H / 2 + 20
    P = lambda lat, lon: (cx + km(lat, lon)[0] * PX_KM, cy - km(lat, lon)[1] * PX_KM)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-labelledby="karte-titel karte-desc">',
         '<title id="karte-titel">Einsatzgebiet von JS-Cartrans</title>',
         '<desc id="karte-desc">Schematische Karte mit Eggendorf in der Mitte und Ringen in 10, 25 und 40 Kilometern Entfernung. '
         'Eingezeichnet sind Wien, Mödling, Baden, Wiener Neustadt, Neunkirchen, Eisenstadt und weitere Orte sowie die A2, A3 und S4.</desc>',
         '<defs><radialGradient id="gebiet-verlauf"><stop offset="0" stop-color="#ff7b1c" stop-opacity=".22"/><stop offset="1" stop-color="#ff7b1c" stop-opacity="0"/></radialGradient></defs>',
         f'<circle class="gebiet" cx="{W / 2:.0f}" cy="{H / 2 + 20:.0f}" r="{25 * PX_KM:.0f}"/>']
    for r in (10, 25, 40):
        s.append(f'<circle class="ring" cx="{cx:.0f}" cy="{cy:.0f}" r="{r * PX_KM:.0f}"/>')
        s.append(f'<text class="ring-label" x="{cx + r * PX_KM * .71 + 6:.0f}" y="{cy + r * PX_KM * .71 + 4:.0f}">{r} KM</text>')
    for name, punkte, lab in STRASSEN:
        d = " ".join(("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(P(a, o) for a, o in punkte))
        s.append(f'<path class="strasse" d="{d}"/>')
        lx, ly = P(*lab)
        s.append(f'<rect class="strasse-schild" x="{lx - 21:.0f}" y="{ly - 13:.0f}" width="42" height="26" rx="4"/>'
                 f'<text class="strasse-label" x="{lx:.0f}" y="{ly + 5.5:.0f}" text-anchor="middle" fill="#fff">{name}</text>')
    for name, lat, lon, seite in ORTE_KARTE:
        x, y = P(lat, lon)
        neben = ' nebenort' if seite.endswith("+") else ""
        anker, dx = ("start", 12) if seite.startswith("o") else ("end", -12)
        s.append(f'<g class="ortpunkt{neben}"><circle class="ort" cx="{x:.1f}" cy="{y:.1f}" r="4"/>'
                 f'<text class="ort-label" x="{x + dx:.1f}" y="{y + 7:.1f}" text-anchor="{anker}">{e(name)}</text></g>')
    s.append(f'<circle class="zentrale-puls" cx="{cx:.0f}" cy="{cy:.0f}" r="14"/>'
             f'<circle class="zentrale" cx="{cx:.0f}" cy="{cy:.0f}" r="9"/>'
             f'<text class="zentrale-label" x="{cx + 20:.0f}" y="{cy + 10:.0f}">Eggendorf</text>')
    s.append(f'<text class="kompass" x="{W - 30}" y="40" text-anchor="end">N ↑</text></svg>')
    return (f'<figure class="karte" style="margin:0">{"".join(s)}</figure>'
            '<p class="karte-hinweis">Schematische Darstellung. Einsätze darüber hinaus in ganz Österreich und im Ausland nach Absprache.</p>')


def partner(hell=True):
    li = "".join(f'<li><b>{e(n)}</b><span>{e(o)}{" · " + e(z) if z else ""}</span></li>' for n, o, z in PARTNER)
    return f'<ul class="partner">{li}</ul>'


def faq(gruppe):
    items = "".join(f'<details><summary>{e(f)}</summary><div class="antwort"><p>{e(a)}</p></div></details>' for f, a in FAQ[gruppe])
    return f'<div class="faq">{items}</div>'


def orte():
    return '<ul class="orte">' + "".join(f'<li><a href="/{o["slug"]}">{e(o["titel"])}</a></li>' for o in ORTSSEITEN) + "</ul>"


# ---------------------------------------------------------------- Seitenrahmen
def json_ld_firma():
    return {
        "@context": "https://schema.org",
        "@type": ["AutomotiveBusiness", "EmergencyService"],
        "@id": DOMAIN + "/#firma",
        "name": "JS-Cartrans e.U.",
        "legalName": "JS-Cartrans e.U.",
        "description": "Abschleppdienst, Pannenhilfe und Fahrzeugtransporte rund um die Uhr aus Eggendorf bei Wiener Neustadt.",
        "url": DOMAIN + "/",
        "logo": DOMAIN + "/assets/logo.svg",
        "image": DOMAIN + "/bilder/og-bild.jpg",
        "telephone": "+43 660 1077052",
        "email": K["MAIL"],
        "vatID": "ATU81959604",
        "address": {"@type": "PostalAddress", "streetAddress": K["STRASSE"], "postalCode": K["PLZ"],
                    "addressLocality": K["ORT"], "addressRegion": "Niederösterreich", "addressCountry": "AT"},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
                                       "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                                       "opens": "00:00", "closes": "23:59"}],
        "areaServed": ["Wiener Neustadt", "Bezirk Wiener Neustadt-Land", "Bezirk Baden", "Bezirk Mödling", "Wien", "Niederösterreich", "Burgenland"],
        "knowsAbout": ["Abschleppdienst", "Pannenhilfe", "Starthilfe", "Unfallbergung", "Fahrzeugtransport", "Oldtimertransport", "Motorradtransport"],
    }


def kopf(meta, aktiv):
    titel = meta["title"]
    pfad = meta["pfad"]
    kanon = DOMAIN + (pfad if pfad != "/" else "/")
    og = meta.get("og", "og-bild.jpg")
    ld = [json_ld_firma()]
    if pfad != "/":
        kette = [{"@type": "ListItem", "position": 1, "name": "Start", "item": DOMAIN + "/"},
                 {"@type": "ListItem", "position": 2, "name": meta.get("krumen", titel.split(" | ")[0]), "item": kanon}]
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": kette})
    if meta.get("faq"):
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f, "acceptedAnswer": {"@type": "Answer", "text": a}} for f, a in FAQ[meta["faq"]]]})
    ld_html = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    robots = '<meta name="robots" content="noindex">' if meta.get("noindex") else ""
    nav = "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if s == aktiv else ""}{" class=\"notdienst\"" if s == "pannenhilfe" else ""}>{e(t)}</a></li>' for s, h, t in NAV)
    menue = "".join(f'<li style="--i:{i}"><a href="{h}"{" aria-current=\"page\"" if s == aktiv else ""}>{e(t)}<small>{"24/7" if s == "pannenhilfe" else ""}</small></a></li>' for i, (s, h, t) in enumerate(NAV))
    return f"""<!doctype html>
<html lang="de-AT" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titel)}</title>
<meta name="description" content="{e(meta["desc"])}">
{robots}<link rel="canonical" href="{kanon}">
<meta name="theme-color" content="#121417">
<meta name="format-detection" content="telephone=no">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_AT">
<meta property="og:site_name" content="JS-Cartrans">
<meta property="og:title" content="{e(titel)}">
<meta property="og:description" content="{e(meta["desc"])}">
<meta property="og:url" content="{kanon}">
<meta property="og:image" content="{DOMAIN}/bilder/{og}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="preload" href="/assets/fonts/big-shoulders-display-500-900-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/barlow-400-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/css/fonts.css">
<link rel="stylesheet" href="/css/base.css">
<script>document.documentElement.classList.replace('no-js','js')</script>
{ld_html}
</head>
<body data-seite="{aktiv}">
<a class="sprung" href="#inhalt">Zum Inhalt</a>
<header class="kopf" id="kopf">
  <div class="wrap">
    <a class="marke" href="/" aria-label="JS-Cartrans, zur Startseite">
      {LEUCHTE}
      <span><b>Cartrans</b><small>Abschleppdienst &amp; Transporte</small></span>
    </a>
    <nav class="nav" aria-label="Hauptnavigation"><ul>{nav}</ul></nav>
    <a class="kopf-ruf" href="{K["TEL1_HREF"]}" data-zaehlen="anruf"><small class="live"><i></i>24/7</small><b>{K["TEL1"]}</b></a>
    <button class="menue-knopf" type="button" aria-expanded="false" aria-controls="menue" aria-label="Menü öffnen"><span></span></button>
  </div>
</header>
<div class="menue" id="menue" hidden>
  <nav aria-label="Menü"><ul>{menue}</ul></nav>
  <div class="menue-fuss">
    <a class="btn btn--notruf" href="{K["TEL1_HREF"]}" data-zaehlen="anruf">{icon("telefon")}Anrufen <span class="nr">{K["TEL1"]}</span></a>
    <a class="btn btn--rand" href="{K["WA_HREF"]}" data-standort data-zaehlen="whatsapp">{icon("standort")}Standort per WhatsApp</a>
  </div>
</div>
<main id="inhalt">
"""


LEUCHTE = ('<svg class="leuchte" viewBox="0 0 32 32" aria-hidden="true">'
           '<path d="M6 25h20v4H6z" fill="currentColor"/>'
           '<path d="M8.5 25a7.5 8 0 0 1 15 0z" fill="#ff7b1c"/>'
           '<path d="M16 3v5M5 8l3.3 3.3M27 8l-3.3 3.3M1.5 18H6M26 18h4.5" stroke="#ff7b1c" stroke-width="2.2" stroke-linecap="round"/></svg>')


def fuss():
    nav = "".join(f'<li><a href="{h}">{e(t)}</a></li>' for s, h, t in NAV)
    ortlinks = "".join(f'<li><a href="/{o["slug"]}">{e(o["titel"])}</a></li>' for o in ORTSSEITEN)
    return f"""</main>
<footer class="fuss">
  <div class="wrap">
    <div class="fuss-gitter">
      <div class="fuss-marke"><b>Cart<span class="o">rans</span></b>
        <p>JS-Cartrans e.U. · Abschleppdienst, Pannenhilfe und Fahrzeugtransporte aus Eggendorf, rund um die Uhr.</p></div>
      <div><h2>Notdienst 24/7</h2><ul>
        <li><a class="fuss-ruf" href="{K["TEL1_HREF"]}" data-zaehlen="anruf">{K["TEL1"]}</a></li>
        <li><a href="{K["TEL2_HREF"]}" data-zaehlen="anruf">{K["TEL2"]}</a></li>
        <li><a href="{K["WA_HREF"]}" data-standort data-zaehlen="whatsapp">WhatsApp mit Standort</a></li>
        <li><a href="mailto:{K["MAIL"]}">{K["MAIL"]}</a></li>
        <li>{K["STRASSE"]}, {K["PLZ"]} {K["ORT"]}</li></ul></div>
      <div><h2>Seiten</h2><ul>{nav}</ul></div>
      <div><h2>Einsatzgebiet</h2><ul>{ortlinks}</ul></div>
    </div>
    <div class="fuss-unten">
      <span>© {K["JAHR"]} JS-Cartrans e.U.</span>
      <ul><li><a href="/impressum">Impressum</a></li><li><a href="/datenschutz">Datenschutz</a></li><li><a href="/agb">AGB</a></li></ul>
    </div>
  </div>
</footer>
<nav class="notrufleiste" aria-label="Notruf">
  <a class="ruf" href="{K["TEL1_HREF"]}" data-zaehlen="anruf">{icon("telefon")}Jetzt anrufen</a>
  <a class="ort" href="{K["WA_HREF"]}" data-standort data-zaehlen="whatsapp">{icon("standort")}Standort senden</a>
</nav>
<script src="/js/core.js" defer></script>
</body>
</html>
"""


# ---------------------------------------------------------------- Ersetzen
def ersetzen(text, tiefe=0):
    def ph(m):
        name, _, arg = m.group(1).partition(":")
        if name == "bild":
            teile = arg.split("|")
            return bild(teile[0], teile[1] if len(teile) > 1 and teile[1] else "100vw",
                        len(teile) > 2 and teile[2] == "eager", teile[3] if len(teile) > 3 else "")
        if name == "icon":
            n, _, k = arg.partition("|")
            return icon(n, k)
        if name == "partial":
            with open(os.path.join(SRC, "partials", arg + ".html"), encoding="utf-8") as f:
                return ersetzen(f.read(), tiefe + 1)
        if name == "faq":
            return faq(arg)
        if name in ("galerie", "fracht", "karte", "partner", "orte"):
            return globals()[name]()
        if name == "LEUCHTE":
            return LEUCHTE
        if name in K:
            return K[name]
        raise KeyError(f"unbekannter Platzhalter {{{{{m.group(1)}}}}}")
    return re.sub(r"\{\{([A-Za-z0-9_]+(?::[^}]*)?)\}\}", ph, text)


def seite(quelltext, name):
    m = re.match(r"\s*<!--meta\s+(\{.*?\})\s*-->", quelltext, re.S)
    if not m:
        raise ValueError(f"{name}: meta fehlt")
    meta = json.loads(m.group(1))
    inhalt = ersetzen(quelltext[m.end():])
    return kopf(meta, meta.get("nav", "")) + inhalt + fuss(), meta


def ortsseiten():
    with open(os.path.join(SRC, "pages", "_ort.html"), encoding="utf-8") as f:
        vorlage = f.read()
    for o in ORTSSEITEN:
        dx, dy = km(o["lat"], o["lon"])
        dist = round(math.hypot(dx, dy))
        absaetze = "".join(f'<p data-reveal>{e(a.format(km=dist))}</p>' for a in o["absaetze"])
        strassen = "".join(f"<li><span>{e(s)}</span></li>" for s in o["strassen"])
        andere = "".join(f'<li><a href="/{x["slug"]}">{e(x["titel"])}</a></li>' for x in ORTSSEITEN if x is not o)
        meta = {"title": f'{o["titel"]} · 24/7 | JS-Cartrans', "desc": o["desc"], "pfad": "/" + o["slug"],
                "nav": "", "krumen": o["titel"], "faq": "notdienst"}
        t = (vorlage.replace("[[H1A]]", e(o["h1"][0])).replace("[[H1B]]", e(o["h1"][1])).replace("[[LEAD]]", e(o["lead"]))
             .replace("[[ORT]]", e(o["ort"])).replace("[[BILD]]", o["bild"]).replace("[[ABSAETZE]]", absaetze)
             .replace("[[STRASSEN]]", strassen).replace("[[ANDERE]]", andere).replace("[[TITEL]]", e(o["titel"])))
        yield o["slug"], "<!--meta " + json.dumps(meta, ensure_ascii=False) + " -->" + t


def og_bild():
    from PIL import Image, ImageDraw
    ziel = os.path.join(HIER, "bilder", "og-bild.jpg")
    quelle = os.path.join(HIER, "..", "original", "bilder")
    datei = next(f for f in os.listdir(quelle) if f.startswith("713fba_c99a0e5b"))
    from PIL import ImageOps
    im = ImageOps.exif_transpose(Image.open(os.path.join(quelle, datei))).convert("RGB")
    w, h = im.size
    zh = round(w * 630 / 1200)
    y0 = round(h * .38)
    im = im.crop((0, y0, w, y0 + zh)).resize((1200, 630), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle((0, 0, 1200, 630), fill=(18, 20, 23, 110))
    d.rectangle((0, 560, 1200, 630), fill=(255, 123, 28, 255))
    for x in range(-70, 1200, 36):
        d.polygon([(x, 560), (x + 18, 560), (x + 88, 630), (x + 70, 630)], fill=(18, 20, 23, 255))
    im.save(ziel, quality=84, optimize=True, progressive=True)


def main():
    pages = os.path.join(SRC, "pages")
    fertig = []
    quellen = [(f[:-5], open(os.path.join(pages, f), encoding="utf-8").read())
               for f in sorted(os.listdir(pages)) if f.endswith(".html") and not f.startswith("_")]
    quellen += list(ortsseiten())
    for name, text in quellen:
        out, meta = seite(text, name)
        ziel = os.path.join(HIER, name + ".html") if "/" not in name else os.path.join(HIER, name + ".html")
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        with open(ziel, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
        if not meta.get("noindex"):
            fertig.append(meta["pfad"])
        print(f"  {name}.html")
    heute = datetime.date.today().isoformat()
    urls = "".join(f"<url><loc>{DOMAIN}{p}</loc><lastmod>{heute}</lastmod></url>" for p in fertig)
    with open(os.path.join(HIER, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    if not os.path.exists(os.path.join(HIER, "bilder", "og-bild.jpg")):
        og_bild()
    print(f"{len(quellen)} Seiten erzeugt, Sitemap mit {len(fertig)} Adressen.")


if __name__ == "__main__":
    sys.exit(main())

"""Bereitet die Originalfotos aus ../original/bilder für die Website auf.

- dreht Handyfotos nach EXIF richtig
- einheitlicher Look (etwas weniger Sättigung, etwas mehr Kontrast)
- je Bild drei Breiten als AVIF und WebP, dazu ein JPG als Rückfall
- schreibt bilder/bilder.json (Maße, Beschriftung, Kategorie) für build.py

Aufruf:  python tools/bilder.py
"""
import json, os, sys
from PIL import Image, ImageOps, ImageEnhance

HIER = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HIER)
QUELLE = os.path.join(WEB, "..", "original", "bilder")
ZIEL = os.path.join(WEB, "bilder")
BREITEN = (640, 1280, 1920)

# Kennung (Anfang des Wix-Dateinamens) -> slug, Beschriftung, Kategorie, Alt-Text, Bildausschnitt (x, y in %)
KATALOG = [
    ("c99a0e5b", "audi-r8-nacht", "Audi R8 · Nachttransport", "sportwagen", "Grauer Audi R8 nachts auf einem Autotransportanhänger unter Straßenlaternen", (50, 55)),
    ("583f27f9", "lamborghini-orange", "Lamborghini · Überstellung", "sportwagen", "Orangefarbener Lamborghini auf dem Anhänger vor einer Halle", (50, 50)),
    ("526e88de", "lamborghini-schwarz", "Lamborghini · Transport", "sportwagen", "Schwarzer Lamborghini auf dem Autotransportanhänger", (50, 45)),
    ("68cf2f25", "lamborghini-heck", "Lamborghini · gesichert verladen", "sportwagen", "Schwarzer Lamborghini von hinten, mit Spanngurten auf dem Anhänger gesichert", (50, 55)),
    ("bddcb511", "bmw-m3-e36", "BMW M3 E36 · Transport", "sportwagen", "Violetter BMW M3 der Baureihe E36 auf dem Anhänger", (50, 55)),
    ("76846c63", "audi-tt-berge", "Audi TT · Überstellung", "sportwagen", "Weißer Audi TT mit Streifen auf dem Anhänger, im Hintergrund Berge", (55, 50)),
    ("d677ae35", "audi-tt-grau", "Audi TT · Transport", "sportwagen", "Grauer Audi TT auf dem Anhänger bei Sonnenschein", (55, 55)),
    ("e60f2475", "audi-rs-front", "Audi RS · Überstellung", "sportwagen", "Grauer Audi RS von vorne auf dem Anhänger", (50, 50)),
    ("eadc5870", "audi-rs6-avant", "Audi RS 6 Avant · Transport", "sportwagen", "Schwarzer Audi RS 6 Avant von hinten auf dem Anhänger", (50, 55)),
    ("e6fa59d6", "mercedes-cls", "Mercedes CLS · Transport", "ueberstellung", "Schwarzer Mercedes CLS auf der Ladefläche des Anhängers", (50, 45)),
    ("2edaa3ce", "mustang-rot", "Ford Mustang · Oldtimer zur Prüfstelle", "oldtimer", "Roter Ford Mustang Oldtimer auf dem Anhänger vor einer Kfz-Prüfstelle", (50, 45)),
    ("a12ef432", "mustang-gruen", "Ford Mustang · Oldtimer", "oldtimer", "Grüner Ford Mustang Oldtimer auf dem Anhänger im Herbstlicht", (50, 50)),
    ("b5d50831", "mustang-gruen-heck", "Ford Mustang · Oldtimer", "oldtimer", "Grüner Ford Mustang von hinten auf dem Anhänger", (40, 55)),
    ("bb8e7d36", "ktm-motocross", "KTM · Motorradtransport", "motorrad", "Orange KTM Motocross-Maschine auf einem kleinen Anhänger an der Tankstelle", (50, 55)),
    ("fc087b2c", "ram-pickup", "RAM Pick-up · Transport", "ueberstellung", "Violetter RAM Pick-up auf dem Autotransportanhänger", (50, 50)),
    ("a8ac6a29", "vw-crafter", "VW Crafter · Überstellung", "ueberstellung", "Weißer VW Crafter Transporter auf dem Anhänger", (50, 45)),
    ("00bde3ca", "autohaus-mercedes", "Überstellung ins Autohaus", "ueberstellung", "VW Touareg mit Anhänger und Mercedes vor einem Mercedes-Benz Autohaus", (45, 60)),
    ("16a4d3b8", "konvoi", "Zwei Gespanne · Doppelüberstellung", "ueberstellung", "Zwei Zugfahrzeuge mit Anhängern transportieren zwei gelbe Neuwagen", (50, 50)),
    ("672bd171", "unfall-bmw-z4-feuerwehr", "BMW Z4 · Unfallbergung", "unfall", "Unfallbeschädigter weißer BMW Z4 auf dem Anhänger vor einem Feuerwehrhaus", (40, 60)),
    ("9a0413a4", "unfall-bmw-z4", "BMW Z4 · Unfallfahrzeug", "unfall", "Weißer BMW Z4 mit stark beschädigter Front auf dem Anhänger", (50, 55)),
    ("eb848b03", "unfall-front", "Unfallfahrzeug · Abtransport", "unfall", "Dunkles Unfallfahrzeug mit zerstörter Front auf dem Anhänger", (50, 60)),
    ("df5382c3", "unfall-suv", "Unfall-SUV · Bergung", "unfall", "Schwarzer SUV mit abgerissenem Vorderrad auf dem Anhänger", (40, 50)),
    ("a46c4b25", "unfall-weiss", "Unfallfahrzeug · Abtransport", "unfall", "Weißes Auto mit Frontschaden auf dem Anhänger", (50, 50)),
    ("f6ed3df9", "unfall-audi", "Unfallfahrzeug · Abtransport", "unfall", "Weißer Audi mit geöffneter, verbogener Motorhaube auf dem Anhänger", (50, 50)),
    ("76d7ad29", "fuhrpark-koffer", "Fuhrpark · Touareg mit Kofferanhänger", "fuhrpark", "Grauer VW Touareg mit geschlossenem Kofferanhänger", (50, 60)),
    ("e52ed4ff", "fuhrpark-touareg", "Fuhrpark · Zugfahrzeug VW Touareg", "fuhrpark", "Schwarzer VW Touareg mit eingeschalteten Scheinwerfern in der Abenddämmerung", (60, 55)),
    # Stockfoto (kein eigener Einsatz, daher nicht in der Galerie). Lizenz: original/fremdbilder/LIZENZ.txt
    ("pexels-5056745", "hero-warndreieck", "Warndreieck auf der Straße", "stock", "Warndreieck auf einer Landstraße in der Abenddämmerung, im Hintergrund ein Auto mit Licht", (72, 70)),
]
FREMD = {"pexels-5056745": os.path.join(WEB, "..", "original", "fremdbilder", "pexels-5056745-lucas-pezeta.jpg")}
GROSS = {"hero-warndreieck": (640, 1280, 1920, 2560)}


def look(im):
    im = ImageEnhance.Color(im).enhance(0.9)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    return im


def main():
    os.makedirs(ZIEL, exist_ok=True)
    dateien = {f.split("_")[1][:8]: f for f in os.listdir(QUELLE) if f.startswith("713fba_")}
    meta = []
    for kenn, slug, titel, kat, alt, fokus in KATALOG:
        quelle = FREMD.get(kenn) or os.path.join(QUELLE, dateien[kenn])
        im = ImageOps.exif_transpose(Image.open(quelle)).convert("RGB")
        if kat != "stock":
            im = look(im)
        w, h = im.size
        stufen = GROSS.get(slug, BREITEN)
        breiten = [b for b in stufen if b < w] + [min(w, stufen[-1])]
        breiten = sorted(set(breiten))
        for b in breiten:
            klein = im.resize((b, round(h * b / w)), Image.LANCZOS) if b != w else im
            klein.save(os.path.join(ZIEL, f"{slug}-{b}.avif"), quality=52, speed=6)
            klein.save(os.path.join(ZIEL, f"{slug}-{b}.webp"), quality=78, method=6)
        mitte = breiten[min(1, len(breiten) - 1)]
        fall = im.resize((mitte, round(h * mitte / w)), Image.LANCZOS)
        fall.save(os.path.join(ZIEL, f"{slug}-{mitte}.jpg"), quality=80, optimize=True, progressive=True)
        meta.append({"slug": slug, "titel": titel, "kat": kat, "alt": alt, "w": w, "h": h,
                     "breiten": breiten, "jpg": mitte, "fokus": fokus})
        print(f"{slug:28} {w}x{h} -> {breiten}", flush=True)
    with open(os.path.join(ZIEL, "bilder.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main())

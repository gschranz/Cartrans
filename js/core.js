/* JS-Cartrans · Seitenlogik (ohne Fremdbibliotheken)
   Die Seite funktioniert auch ohne JavaScript: alle Anruf- und WhatsApp-Links sind echte Links. */
(function () {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const ruhig = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const WA_NR = '436601077052';

  /* ---------- Hinweis-Einblendung ---------- */
  let toastEl, toastTimer;
  function hinweis(text, dauer = 3200) {
    if (!toastEl) { toastEl = document.createElement('div'); toastEl.className = 'hinweis-toast'; toastEl.setAttribute('role', 'status'); document.body.appendChild(toastEl); }
    toastEl.textContent = text; toastEl.classList.add('da');
    clearTimeout(toastTimer); toastTimer = setTimeout(() => toastEl.classList.remove('da'), dauer);
  }

  /* ---------- Kopfzeile ---------- */
  const kopf = $('#kopf');
  const aufScroll = () => kopf && kopf.classList.toggle('ist-gescrollt', scrollY > 8);
  addEventListener('scroll', aufScroll, { passive: true }); aufScroll();

  /* ---------- Handy-Menü ---------- */
  const knopf = $('.menue-knopf'), menue = $('#menue');
  function menueSetzen(auf) {
    if (!menue) return;
    knopf.setAttribute('aria-expanded', String(auf));
    knopf.setAttribute('aria-label', auf ? 'Menü schließen' : 'Menü öffnen');
    document.documentElement.style.overflow = auf ? 'hidden' : '';
    if (auf) { menue.hidden = false; void menue.offsetWidth; menue.classList.add('offen'); }
    else { menue.classList.remove('offen'); setTimeout(() => { if (!menue.classList.contains('offen')) menue.hidden = true; }, 400); }
  }
  if (knopf) knopf.addEventListener('click', () => menueSetzen(knopf.getAttribute('aria-expanded') !== 'true'));
  addEventListener('keydown', e => { if (e.key === 'Escape' && knopf && knopf.getAttribute('aria-expanded') === 'true') { menueSetzen(false); knopf.focus(); } });
  if (menue) menue.addEventListener('click', e => { if (e.target.closest('a')) menueSetzen(false); });
  matchMedia('(min-width:1100px)').addEventListener('change', m => { if (m.matches) menueSetzen(false); });

  /* ---------- Überschriften in Wörter zerlegen ---------- */
  function zerlegen(el) {
    let i = 0;
    const gehe = knoten => {
      Array.from(knoten.childNodes).forEach(n => {
        if (n.nodeType === 3) {
          const teile = n.textContent.split(/(\s+)/);
          const frag = document.createDocumentFragment();
          teile.forEach(t => {
            if (!t) return;
            if (/^\s+$/.test(t)) { frag.appendChild(document.createTextNode(' ')); return; }
            const w = document.createElement('span'); w.className = 'w';
            const inner = document.createElement('span'); inner.textContent = t; inner.style.setProperty('--i', i++);
            w.appendChild(inner); frag.appendChild(w);
          });
          n.replaceWith(frag);
        } else if (n.nodeType === 1 && !n.classList.contains('w')) gehe(n);
      });
    };
    el.setAttribute('aria-label', el.textContent.replace(/\s+/g, ' ').trim());
    gehe(el);
    $$('.w', el).forEach(w => w.setAttribute('aria-hidden', 'true'));
  }
  $$('[data-split]').forEach(zerlegen);

  /* ---------- Zählwerk: Ziffern rollen auf die Telefonnummer ---------- */
  $$('[data-zaehlwerk]').forEach(el => {
    const text = el.dataset.zaehlwerk; let i = 0;
    el.textContent = '';
    for (const c of text) {
      if (/\d/.test(c)) {
        const z = document.createElement('span'); z.className = 'z';
        const spur = document.createElement('span'); spur.style.setProperty('--i', i++);
        for (let k = 0; k < 20; k++) { const d = document.createElement('i'); d.textContent = k % 10; spur.appendChild(d); }
        spur.dataset.ziel = 10 + Number(c);
        z.appendChild(spur); el.appendChild(z);
      } else { const l = document.createElement('span'); l.className = 'luecke'; el.appendChild(l); }
    }
    el.setAttribute('aria-hidden', 'true');
    el.dataset.reveal = '';
    // Jede Spalte so breit wie ihre Zielziffer, sonst klafft nach der schmalen „1“ eine Lücke
    const breiten = () => {
      const mess = document.createElement('span'); mess.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap';
      el.appendChild(mess);
      const gr = parseFloat(getComputedStyle(el).fontSize) || 1;
      $$('.z', el).forEach(z => { mess.textContent = String(z.firstChild.dataset.ziel - 10); z.style.width = (mess.getBoundingClientRect().width / gr) + 'em'; });
      mess.remove();
    };
    (document.fonts ? document.fonts.ready : Promise.resolve()).then(breiten);
    if (ruhig) $$('.z > span', el).forEach(s => { s.style.transform = `translateY(${-s.dataset.ziel * 0.86}em)`; });
  });

  /* ---------- Einblenden beim Scrollen ---------- */
  const ziele = $$('[data-split],[data-reveal],[data-bild-reveal]');
  const zeigen = el => {
    el.classList.add('ist-da');
    if (el.matches('[data-zaehlwerk]')) $$('.z > span', el).forEach(s => { s.style.transform = `translateY(${-s.dataset.ziel * 0.86}em)`; });
  };
  if ('IntersectionObserver' in window && !ruhig) {
    const io = new IntersectionObserver(eintraege => {
      eintraege.forEach(en => { if (en.isIntersecting) { zeigen(en.target); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
    ziele.forEach(el => io.observe(el));
  } else ziele.forEach(zeigen);

  /* ---------- Standort per WhatsApp ---------- */
  function waLink(text) { return 'https://wa.me/' + WA_NR + '?text=' + encodeURIComponent(text); }
  $$('[data-standort]').forEach(a => a.addEventListener('click', e => {
    if (!('geolocation' in navigator)) return; // normaler Link öffnet WhatsApp ohne Standort
    e.preventDefault();
    hinweis('Standort wird ermittelt … bitte Freigabe erlauben.', 9000);
    let fertig = false;
    const weiter = text => { if (fertig) return; fertig = true; location.href = waLink(text); };
    navigator.geolocation.getCurrentPosition(pos => {
      const { latitude: la, longitude: lo, accuracy: gen } = pos.coords;
      hinweis('Standort gefunden, WhatsApp öffnet sich.');
      weiter(`Hallo JS-Cartrans, ich brauche Hilfe.\nMein Standort: https://maps.google.com/?q=${la.toFixed(6)},${lo.toFixed(6)} (auf ca. ${Math.round(gen)} m genau)\nFahrzeug: \nWas ist passiert: `);
    }, () => {
      hinweis('Kein Standort verfügbar. Bitte beschreiben Sie in WhatsApp, wo Sie stehen.', 5000);
      weiter('Hallo JS-Cartrans, ich brauche Hilfe.\nIch stehe hier (Straße, Ort oder Autobahn-Kilometer): \nFahrzeug: \nWas ist passiert: ');
    }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 });
  }));

  /* ---------- Anonyme Zählung von Anruf- und WhatsApp-Klicks ---------- */
  document.addEventListener('click', e => {
    const a = e.target.closest('[data-zaehlen]'); if (!a) return;
    try { navigator.sendBeacon('/api/zaehler', new Blob([JSON.stringify({ art: a.dataset.zaehlen, seite: location.pathname })], { type: 'application/json' })); } catch (err) { /* egal */ }
  });

  /* ---------- Nummer kopieren (nur Geräte mit Maus) ---------- */
  if (matchMedia('(hover:hover) and (pointer:fine)').matches && navigator.clipboard) {
    $$('[data-kopieren]').forEach(b => {
      b.hidden = false;
      b.addEventListener('click', () => navigator.clipboard.writeText(b.dataset.kopieren).then(() => hinweis('Nummer kopiert: ' + b.dataset.kopieren)));
    });
  }

  /* ---------- Was ist passiert? (Tabs) ---------- */
  const tabs = $$('.vorfall-wahl [role="tab"]');
  function tabWaehlen(t, fokus) {
    tabs.forEach(x => {
      const an = x === t;
      x.setAttribute('aria-selected', String(an)); x.tabIndex = an ? 0 : -1;
      $('#' + x.getAttribute('aria-controls')).hidden = !an;
    });
    if (fokus) t.focus();
    t.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: ruhig ? 'auto' : 'smooth' });
  }
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => tabWaehlen(t));
    t.addEventListener('keydown', e => {
      const n = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      if (n) { e.preventDefault(); tabWaehlen(tabs[(i + n + tabs.length) % tabs.length], true); }
      if (e.key === 'Home') { e.preventDefault(); tabWaehlen(tabs[0], true); }
      if (e.key === 'End') { e.preventDefault(); tabWaehlen(tabs[tabs.length - 1], true); }
    });
  });

  /* ---------- Transport-Leiste blättern ---------- */
  const fracht = $('#fracht');
  $$('[data-fracht]').forEach(b => b.addEventListener('click', () => {
    const karte = fracht.querySelector('li');
    fracht.scrollBy({ left: Number(b.dataset.fracht) * (karte.offsetWidth + 18), behavior: ruhig ? 'auto' : 'smooth' });
  }));

  /* ---------- Galerie mit Filter und Leuchtkasten ---------- */
  const galerie = $('#galerie');
  if (galerie) {
    const eintraege = $$('li', galerie);
    $$('.filter button').forEach(b => b.addEventListener('click', () => {
      $$('.filter button').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
      const f = b.dataset.filter;
      eintraege.forEach(li => {
        const sichtbar = f === 'alle' || li.dataset.kat === f;
        li.hidden = !sichtbar;
        li.classList.remove('rein'); if (sichtbar && !ruhig) { void li.offsetWidth; li.classList.add('rein'); }
      });
    }));
    const lk = $('#leuchtkasten'), lkBild = $('#lk-bild'), lkText = $('#lk-text'), lkZahl = $('#lk-zahl');
    let aktuell = 0, ausloeser = null;
    const sichtbare = () => eintraege.filter(li => !li.hidden).map(li => li.querySelector('button'));
    function zeige(knopfEl) {
      const liste = sichtbare(); aktuell = liste.indexOf(knopfEl);
      lkBild.src = knopfEl.dataset.gross; lkBild.alt = knopfEl.querySelector('img').alt;
      lkText.textContent = knopfEl.dataset.titel;
      lkZahl.textContent = `${aktuell + 1} / ${liste.length}`;
    }
    function schritt(n) { const liste = sichtbare(); zeige(liste[(aktuell + n + liste.length) % liste.length]); }
    galerie.addEventListener('click', e => {
      const b = e.target.closest('button[data-lk]'); if (!b) return;
      ausloeser = b; zeige(b);
      if (lk.showModal) lk.showModal(); else lk.setAttribute('open', '');
      document.documentElement.style.overflow = 'hidden';
    });
    lk.addEventListener('close', () => { document.documentElement.style.overflow = ''; if (ausloeser) ausloeser.focus(); });
    $$('[data-lk-schritt]', lk).forEach(b => b.addEventListener('click', () => schritt(Number(b.dataset.lkSchritt))));
    $('[data-lk-zu]', lk).addEventListener('click', () => lk.close());
    lk.addEventListener('click', e => { if (e.target === lk || e.target.classList.contains('lk-buehne')) lk.close(); });
    lk.addEventListener('keydown', e => { if (e.key === 'ArrowRight') schritt(1); if (e.key === 'ArrowLeft') schritt(-1); });
    let x0 = null;
    lk.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
    lk.addEventListener('touchend', e => { if (x0 === null) return; const dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 50) schritt(dx < 0 ? 1 : -1); x0 = null; });
  }

  /* ---------- Formulare ---------- */
  const MELDUNG = {
    name: 'Bitte geben Sie Ihren Namen an.',
    telefon: 'Bitte geben Sie eine Telefonnummer an, unter der wir Sie erreichen.',
    fahrzeug: 'Bitte nennen Sie Marke und Modell.',
    von: 'Bitte geben Sie an, wo wir das Fahrzeug abholen.',
    nach: 'Bitte geben Sie an, wohin das Fahrzeug soll.',
    email: 'Diese E-Mail-Adresse sieht nicht vollständig aus.',
  };
  function pruefen(bereich) {
    let erstesFalsch = null;
    $$('input[required], input[type="email"]', bereich).forEach(inp => {
      if (inp.type === 'checkbox' || inp.type === 'radio') return;
      const wert = inp.value.trim();
      let ok = inp.required ? wert.length > 1 : true;
      if (ok && inp.name === 'telefon') ok = wert.replace(/\D/g, '').length >= 6;
      if (ok && inp.type === 'email' && wert) ok = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(wert);
      const f = document.getElementById(inp.id + '-f');
      inp.setAttribute('aria-invalid', String(!ok));
      if (f) { f.textContent = ok ? '' : (MELDUNG[inp.name] || 'Bitte ausfüllen.'); inp.setAttribute('aria-describedby', f.id); }
      if (!ok && !erstesFalsch) erstesFalsch = inp;
    });
    const ein = $('input[name="einwilligung"]', bereich);
    if (ein) {
      const f = $('[data-fehler-einwilligung]', bereich.closest('form'));
      if (!ein.checked) { if (f) f.textContent = 'Bitte bestätigen Sie die Einwilligung.'; erstesFalsch = erstesFalsch || ein; }
      else if (f) f.textContent = '';
    }
    if (erstesFalsch) erstesFalsch.focus();
    return !erstesFalsch;
  }

  $$('form[data-formular]').forEach(form => {
    const stufen = $$('[data-stufe]', form), marken = $$('.stufen li', form), ansage = $('[data-stufen-ansage]', form);
    let st = 0;
    const namen = ['Fahrzeug', 'Strecke', 'Kontakt'];
    function stufe(n) {
      st = n;
      stufen.forEach((s, i) => { s.hidden = i !== n; });
      marken.forEach((m, i) => { m.classList.toggle('aktiv', i === n); m.classList.toggle('erledigt', i < n); });
      if (ansage) ansage.textContent = `Schritt ${n + 1} von ${stufen.length}: ${namen[n]}`;
      const erstes = $('input:not([type=radio]), textarea', stufen[n]); if (erstes) erstes.focus({ preventScroll: true });
      form.scrollIntoView({ block: 'start', behavior: ruhig ? 'auto' : 'smooth' });
    }
    $$('[data-weiter]', form).forEach(b => b.addEventListener('click', () => { if (pruefen(stufen[st])) stufe(st + 1); }));
    $$('[data-zurueck]', form).forEach(b => b.addEventListener('click', () => stufe(st - 1)));
    form.addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.target.tagName === 'INPUT' && stufen.length && st < stufen.length - 1) { e.preventDefault(); $('[data-weiter]', stufen[st]).click(); }
    });

    form.addEventListener('submit', async e => {
      e.preventDefault();
      if (!pruefen(stufen.length ? stufen[st] : form)) return;
      const daten = Object.fromEntries(new FormData(form).entries());
      daten.typ = form.dataset.formular; daten.seite = location.pathname;
      const status = $('.form-status', form), senden = $('button[type="submit"]', form);
      senden.disabled = true; const alt = senden.innerHTML; senden.textContent = 'Wird gesendet …';
      try {
        const r = await fetch('/api/anfrage', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(daten) });
        if (!r.ok) throw new Error(r.status);
        $$('fieldset.stufe, .feld, .feld-reihe, .einwilligung, .stufen, .stufe-knoepfe, [data-fehler-einwilligung], .klein, form > div:not(.form-status)', form).forEach(x => { x.hidden = true; x.style.display = 'none'; });
        status.className = 'form-status ok'; status.hidden = false;
        status.innerHTML = daten.typ === 'transport'
          ? '<h3>Anfrage ist da</h3><p>Danke! Wir melden uns mit einem Angebot. Eilt es? Rufen Sie an: <a href="tel:+436601077052">0660 107 70 52</a>.</p>'
          : '<h3>Wir rufen zurück</h3><p>Danke! Wir melden uns so bald wie möglich unter der angegebenen Nummer.</p>';
        status.setAttribute('tabindex', '-1'); status.focus();
      } catch (err) {
        const text = Object.entries(daten).filter(([k]) => !['website', 'einwilligung', 'seite'].includes(k)).map(([k, v]) => `${k}: ${v}`).join('\n');
        status.className = 'form-status'; status.hidden = false;
        status.innerHTML = '<h3>Senden hat nicht geklappt</h3><p>Die Verbindung zum Server ist gerade nicht möglich. Schicken Sie die Anfrage per <a id="ersatz-mail" href="#">E-Mail</a> oder rufen Sie an: <a href="tel:+436601077052">0660 107 70 52</a>.</p>';
        $('#ersatz-mail', status).href = 'mailto:office@cartrans.at?subject=' + encodeURIComponent(daten.typ === 'transport' ? 'Transportanfrage' : 'Rückruf') + '&body=' + encodeURIComponent(text);
        senden.disabled = false; senden.innerHTML = alt;
      }
    });
  });
})();

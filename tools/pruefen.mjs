// Prüft alle Seiten in Edge headless: seitliches Überlaufen, h1, Alt-Texte, kaputte Bilder, Konsolenfehler
import { spawn } from 'node:child_process';
import { mkdtempSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
for (const f of ['js/core.js']) { try { execFileSync(process.execPath, ['--check', f]); } catch (e) { console.log(`SYNTAXFEHLER in ${f}:
` + e.stderr); process.exit(1); } }
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const basis = process.argv[2] || 'http://localhost:8796';
const breiten = [360, 390, 768, 1024, 1440];
const seiten = readdirSync('.').filter(f => f.endsWith('.html')).map(f => '/' + f.replace(/\.html$/, '').replace(/^index$/, ''));
seiten.push('/betreiber/offene-punkte.html');
const port = 9950 + Math.floor(Math.random() * 40);
const edge = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'p-'))}`, 'about:blank'], { stdio: 'ignore' });
const pause = ms => new Promise(r => setTimeout(r, ms));
let ziel; for (let i = 0; i < 50 && !ziel; i++) { try { ziel = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); } catch { await pause(150); } }
const ws = new WebSocket(ziel.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r, { once: true }));
let n = 0; const offen = new Map(); const fehler = [];
ws.addEventListener('message', m => { const d = JSON.parse(m.data); if (d.id && offen.has(d.id)) { offen.get(d.id)(d); offen.delete(d.id); }
  if (d.method === 'Runtime.exceptionThrown') fehler.push(d.params.exceptionDetails.exception?.description?.split('\n')[0]);
  if (d.method === 'Log.entryAdded' && d.params.entry.level === 'error') fehler.push(d.params.entry.text + ' ' + (d.params.entry.url || '')); });
const cdp = (method, params = {}) => new Promise(r => { const id = ++n; offen.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
await cdp('Runtime.enable'); await cdp('Log.enable');
let probleme = 0;
for (const s of seiten) {
  for (const b of breiten) {
    fehler.length = 0;
    await cdp('Emulation.setDeviceMetricsOverride', { width: b, height: 900, deviceScaleFactor: 1, mobile: b < 700 });
    await cdp('Page.navigate', { url: basis + s }); await pause(900);
    const r = (await cdp('Runtime.evaluate', { returnByValue: true, awaitPromise: true, expression: `(async()=>{
      for (let y=0;y<document.body.scrollHeight;y+=700){scrollTo(0,y);await new Promise(r=>setTimeout(r,30));}
      await new Promise(r=>setTimeout(r,500));
      const breit=[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.right>innerWidth+1&&!e.closest('.fracht,.vorfall-wahl,.laufband,.rundum,.hero-glut,.sprung,.menue,.leuchtkasten,.hinweis-toast')&&getComputedStyle(e).position!=='fixed'}).slice(0,3).map(e=>e.tagName+'.'+e.className);
      return {ueber: document.documentElement.scrollWidth-innerWidth, breit, h1: document.querySelectorAll('h1').length,
        ohneAlt: [...document.querySelectorAll('img:not([alt])')].length,
        kaputt: [...document.querySelectorAll('img')].filter(i=>i.complete&&i.naturalWidth===0&&i.src).map(i=>i.src).slice(0,3),
        titel: document.title.length, desc: (document.querySelector('meta[name=description]')||{}).content?.length||0}})()` })).result.result.value;
    const p = [];
    if (r.ueber > 0) p.push(`überläuft ${r.ueber}px ${r.breit.join(' ')}`);
    if (r.h1 !== 1) p.push(`h1=${r.h1}`);
    if (r.ohneAlt) p.push(`img ohne alt: ${r.ohneAlt}`);
    if (r.kaputt.length) p.push(`kaputt: ${r.kaputt.join(' ')}`);
    if (fehler.length) p.push(`Fehler: ${[...new Set(fehler)].join(' | ')}`);
    if (b === 1440 && (r.titel > 70 || r.desc > 170 || r.desc < 70)) p.push(`Titel ${r.titel} / Beschreibung ${r.desc} Zeichen`);
    if (p.length) { probleme++; console.log(`${s} @${b}: ${p.join('; ')}`); }
  }
}
console.log(`${seiten.length} Seiten × ${breiten.length} Breiten geprüft, ${probleme} mit Befund.`);
ws.close(); edge.kill(); process.exit(0);

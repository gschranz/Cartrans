// Ganzseitige Bildschirmfotos über Edge (headless, DevTools-Protokoll), ohne Zusatzpakete.
// node tools/shot.mjs <url> <breite> <höhe> <datei.png> [mobil]
// Scrollt die Seite einmal durch, damit alle Einblend-Animationen auslösen.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [url, w = '1440', h = '900', datei = 'shot.png', mobil] = process.argv.slice(2);
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
const port = 9300 + Math.floor(Math.random() * 500);
const profil = mkdtempSync(join(tmpdir(), 'shot-'));
const edge = spawn(EDGE, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profil}`, '--hide-scrollbars', '--no-first-run', 'about:blank'], { stdio: 'ignore' });
const pause = ms => new Promise(r => setTimeout(r, ms));

let ziel;
for (let i = 0; i < 50 && !ziel; i++) {
  try { ziel = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); } catch { await pause(150); }
}
const ws = new WebSocket(ziel.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));
let n = 0; const offen = new Map();
ws.addEventListener('message', m => { const d = JSON.parse(m.data); if (d.id && offen.has(d.id)) { offen.get(d.id)(d); offen.delete(d.id); } });
const cdp = (method, params = {}) => new Promise(r => { const id = ++n; offen.set(id, r); ws.send(JSON.stringify({ id, method, params })); });

const W = +w, H = +h, istMobil = mobil === 'mobil';
await cdp('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: istMobil });
if (istMobil) await cdp('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
await cdp('Page.enable');
await cdp('Page.navigate', { url });
await pause(1800);
const hoehe = (await cdp('Runtime.evaluate', { expression: 'document.documentElement.scrollHeight', returnByValue: true })).result.result.value;
for (let y = 0; y < hoehe; y += Math.round(H * 0.6)) { await cdp('Runtime.evaluate', { expression: `scrollTo(0,${y})` }); await pause(160); }
await pause(1400);
await cdp('Runtime.evaluate', { expression: 'scrollTo(0,0)' });
await pause(600);
const voll = (await cdp('Runtime.evaluate', { expression: 'document.documentElement.scrollHeight', returnByValue: true })).result.result.value;
const bild = await cdp('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { x: 0, y: 0, width: W, height: Math.min(voll, 16000), scale: 1 } });
writeFileSync(datei, Buffer.from(bild.result.data, 'base64'));
console.log(`${datei}  ${W}x${voll}`);
ws.close(); edge.kill();
process.exit(0);

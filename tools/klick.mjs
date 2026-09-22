// Interaktionstest in Edge headless: node tools/klick.mjs <url> <breite> <höhe> <datei.png> "<js vor dem Foto>"
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const [url, w, h, datei, js] = process.argv.slice(2);
const port = 9800 + Math.floor(Math.random() * 150);
const edge = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'k-'))}`, '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
const pause = ms => new Promise(r => setTimeout(r, ms));
let ziel; for (let i = 0; i < 50 && !ziel; i++) { try { ziel = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); } catch { await pause(150); } }
const ws = new WebSocket(ziel.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r, { once: true }));
let n = 0; const offen = new Map();
ws.addEventListener('message', m => { const d = JSON.parse(m.data); if (d.id && offen.has(d.id)) { offen.get(d.id)(d); offen.delete(d.id); } });
const cdp = (method, params = {}) => new Promise(r => { const id = ++n; offen.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
await cdp('Emulation.setDeviceMetricsOverride', { width: +w, height: +h, deviceScaleFactor: 1, mobile: +w < 700 });
await cdp('Page.navigate', { url }); await pause(1800);
const r = await cdp('Runtime.evaluate', { expression: `(async()=>{${js}})()`, awaitPromise: true, returnByValue: true });
console.log(JSON.stringify(r.result.result.value ?? r.result));
await pause(900);
const bild = await cdp('Page.captureScreenshot', { format: 'png' });
writeFileSync(datei, Buffer.from(bild.result.data, 'base64'));
ws.close(); edge.kill(); process.exit(0);

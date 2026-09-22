// Misst auf Handy- und Tablet-Breite alle Bedienelemente: abgeschnitten, zu klein oder außerhalb des sichtbaren Bereichs
import { spawn } from 'node:child_process';
import { mkdtempSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const basis = 'http://localhost:8796';
const seiten = readdirSync('.').filter(f => f.endsWith('.html')).map(f => '/' + f.replace(/\.html$/, '').replace(/^index$/, ''));
const port = 9700 + Math.floor(Math.random() * 90);
const edge = spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'e-'))}`, 'about:blank'], { stdio: 'ignore' });
const pause = ms => new Promise(r => setTimeout(r, ms));
let ziel; for (let i = 0; i < 50 && !ziel; i++) { try { ziel = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); } catch { await pause(150); } }
const ws = new WebSocket(ziel.webSocketDebuggerUrl); await new Promise(r => ws.addEventListener('open', r, { once: true }));
let n = 0; const offen = new Map();
ws.addEventListener('message', m => { const d = JSON.parse(m.data); if (d.id && offen.has(d.id)) { offen.get(d.id)(d); offen.delete(d.id); } });
const cdp = (method, params = {}) => new Promise(r => { const id = ++n; offen.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
for (const b of [360, 390, 768, 1024]) for (const s of seiten) {
  await cdp('Emulation.setDeviceMetricsOverride', { width: b, height: 850, deviceScaleFactor: 1, mobile: b < 700 });
  await cdp('Page.navigate', { url: basis + s }); await pause(700);
  const r = (await cdp('Runtime.evaluate', { returnByValue: true, awaitPromise: true, expression: `(async()=>{
    document.querySelectorAll('[data-reveal],[data-split],[data-bild-reveal]').forEach(e=>e.classList.add('ist-da'));
    await new Promise(r=>setTimeout(r,1300));
    const out=[];
    document.querySelectorAll('main a, main button, main input:not([type=hidden]), main select, main textarea, main label').forEach(e=>{
      if (e.closest('[hidden],.honig,.leuchtkasten,.sr-only')) return;
      const st=getComputedStyle(e); if (st.display==='none'||st.visibility==='hidden') return;
      const r=e.getBoundingClientRect(); if (!r.width) return;
      const name=(e.textContent||e.getAttribute('aria-label')||e.name||'').trim().replace(/\s+/g,' ').slice(0,28);
      // abgeschnitten durch Vorfahren mit overflow
      let p=e.parentElement; while(p&&p!==document.body){const ps=getComputedStyle(p); if(/(hidden|auto|scroll|clip)/.test(ps.overflowX)){const pr=p.getBoundingClientRect(); if(r.right>pr.right+1||r.left<pr.left-1){out.push('abgeschnitten: '+name+' in .'+p.className.split(' ')[0]);break;}} p=p.parentElement;}
      if (r.right>innerWidth+1||r.left<-1) out.push('außerhalb: '+name);
      const klein=(e.matches('a,button')&&!e.closest('p,li.brot,.brotkrumen,dd,.rechtstext,.fuss,.antwort,.einwilligung,.klein,.ausweich,.form-status'))&&r.height<40;
      if (klein) out.push('klein '+Math.round(r.height)+'px: '+name);
    });
    return [...new Set(out)];})()` })).result.result.value;
  if (r.length) console.log(`${s} @${b}: ${r.join(' | ')}`);
}
ws.close(); edge.kill(); process.exit(0);

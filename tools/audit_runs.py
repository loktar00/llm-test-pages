"""Execution audit: load every published run headlessly, record JS errors and
whether anything actually renders. Verdict per run -> audit.json."""
import asyncio, json, os, functools, threading, http.server, socketserver

REPO = r'D:\dev\llm-test-pages'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8484
WORKERS = 6

man = json.load(open(os.path.join(BASE_DIR, 'gallery-out', 'manifest.json'), encoding='utf-8'))

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=REPO)
socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.ThreadingTCPServer(('127.0.0.1', PORT), Handler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()

from playwright.async_api import async_playwright

PAINT_CHECK = """
() => {
  const cs = document.querySelectorAll('canvas');
  let painted = false;
  for (const c of cs) {
    try {
      const ctx = c.getContext('2d');
      if (!ctx) { painted = true; continue; }   // webgl etc: benefit of doubt
      const w = Math.min(c.width, 400), h = Math.min(c.height, 300);
      if (!w || !h) continue;
      const d = ctx.getImageData(0, 0, w, h).data;
      for (let i = 0; i < d.length; i += 397) {
        if (d[i] || d[i+1] || d[i+2] || d[i+3]) { painted = true; break; }
      }
    } catch (e) { painted = true; }             // tainted/webgl: assume ok
    if (painted) break;
  }
  const domVisible = document.body && document.body.innerText.trim().length > 0
      || document.querySelectorAll('div,section,svg,img,video').length > 3;
  return { nCanvas: cs.length, painted, domVisible };
}
"""

async def audit(browser, sem, r, results):
    async with sem:
        try:
            await asyncio.wait_for(_audit(browser, r, results), timeout=45)
        except asyncio.TimeoutError:
            results.append({**r, 'ok': False, 'jsErrors': ['AUDIT-TIMEOUT: page wedged the browser'], 'renders': False})

async def _audit(browser, r, results):
    url = f"http://127.0.0.1:{PORT}/{r['section']}/{r['stem']}/{r['runId']}/"
    if True:
        errors = []
        try:
            ctx = await browser.new_context(viewport={'width': 800, 'height': 500})
            page = await ctx.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)[:160]))
            page.on('console', lambda m: errors.append(m.text[:160]) if m.type == 'error' else None)
            try:
                await page.goto(url, timeout=20000, wait_until='domcontentloaded')
            except Exception as e:
                errors.append('NAV: ' + str(e)[:120])
            await page.wait_for_timeout(4500)
            try:
                paint = await page.evaluate(PAINT_CHECK)
            except Exception:
                paint = {'nCanvas': 0, 'painted': False, 'domVisible': False}
            await ctx.close()
            js_errors = [e for e in errors if not e.startswith('Failed to load resource')]
            renders = paint['painted'] or (paint['nCanvas'] == 0 and paint['domVisible'])
            ok = (len(js_errors) == 0) and renders
            results.append({**r, 'ok': ok, 'jsErrors': js_errors[:3], 'renders': renders})
        except Exception as e:
            results.append({**r, 'ok': False, 'jsErrors': ['AUDIT: ' + str(e)[:120]], 'renders': False})

async def main():
    results = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        sem = asyncio.Semaphore(WORKERS)
        await asyncio.gather(*(audit(browser, sem, r, results) for r in man))
        await browser.close()
    json.dump(results, open(os.path.join(BASE_DIR, 'audit.json'), 'w', encoding='utf-8'), indent=1)
    from collections import Counter
    c = Counter()
    for r in results:
        key = r['modelName']
        c[(key, 'ok' if r['ok'] else 'broken')] += 1
    for k in sorted(c):
        print(f'{k[0]:42s} {k[1]:7s} {c[k]}')
    print(f"TOTAL ok={sum(1 for r in results if r['ok'])} broken={sum(1 for r in results if not r['ok'])}")

asyncio.run(main())
httpd.shutdown()

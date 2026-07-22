import json, os, shutil, html
from collections import defaultdict

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-out')
REPO = r'D:\dev\llm-test-pages'
manifest = json.load(open(os.path.join(SRC, 'manifest.json'), encoding='utf-8'))

CSS = """
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh;
    font-family: -apple-system, "Segoe UI", Inter, Roboto, "Helvetica Neue", sans-serif;
    background: #0d1117; color: #e6edf3; padding: 3rem 1.5rem 4rem; }
  .wrap { max-width: 860px; margin: 0 auto; }
  a.back { color: #8d96a0; text-decoration: none; font-size: 0.85rem; }
  a.back:hover { color: #58a6ff; }
  h1 { margin: 1.25rem 0 0.35rem; font-size: clamp(1.6rem, 5vw, 2.4rem); font-weight: 650; letter-spacing: -0.02em; }
  p.brief { color: #8d96a0; line-height: 1.65; max-width: 64ch; }
  .cards { display: grid; gap: 0.8rem; margin-top: 2rem; }
  a.card { display: block; padding: 1.1rem 1.4rem; border: 1px solid #30363d;
    border-radius: 10px; background: #161b22; color: #e6edf3; text-decoration: none;
    transition: border-color .15s, background .15s; }
  a.card:hover { border-color: #4493f8; background: #1b2230; }
  .card-top { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
  .name { font-size: 1.05rem; font-weight: 650; }
  .muted { color: #8d96a0; font-size: 0.85rem; }
  .badges { display: flex; gap: .45rem; margin-top: .55rem; flex-wrap: wrap; }
  .b { font-size: .7rem; padding: .18rem .6rem; border-radius: 99px; font-weight: 600; }
  .b.complete { background: rgba(63,185,80,.12); color: #3fb950; border: 1px solid rgba(63,185,80,.35); }
  .b.truncated { background: rgba(210,153,34,.12); color: #d29922; border: 1px solid rgba(210,153,34,.35); }
  .b.degenerated { background: rgba(248,81,73,.12); color: #f85149; border: 1px solid rgba(248,81,73,.35); }
  footer { color: #6e7681; font-size: .8rem; margin-top: 3rem; }
  /* live-thumbnail grid (section pages) */
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; margin-top: 2rem; }
  a.tile { display: block; border: 1px solid #30363d; border-radius: 10px; overflow: hidden;
    background: #161b22; color: #e6edf3; text-decoration: none;
    transition: border-color .15s; }
  a.tile:hover { border-color: #4493f8; }
  .thumbwrap { position: relative; aspect-ratio: 16/10; overflow: hidden; background: #010409; }
  .thumbwrap video { width: 100%; height: 100%; object-fit: cover; display: block; }
  .tile-cap { display: flex; justify-content: space-between; align-items: baseline; gap: .5rem;
    padding: .65rem .85rem; }
  .tile-cap .name { font-size: .85rem; }
  /* compare view (prompt pages) */
  .panels { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(480px, 100%), 1fr));
    gap: 1.2rem; margin-top: 2rem; }
  .panel { border: 1px solid #30363d; border-radius: 10px; overflow: hidden;
    background: #161b22; }
  .panel-head { display: flex; justify-content: space-between; align-items: center; gap: .6rem;
    flex-wrap: wrap; padding: .7rem 1rem; }
  .panel-head .name { font-weight: 650; font-size: .95rem; }
  .panel-head a.full { color: #58a6ff; text-decoration: none; font-size: .8rem; }
  .panel-head a.full:hover { text-decoration: underline; }
  .panel iframe { display: block; width: 100%; height: 430px; border: 0; background: #010409; }
  .liveslot { position: relative; cursor: pointer; }
  .liveslot video { display: block; width: 100%; aspect-ratio: 16/10; object-fit: cover; background: #010409; }
  .liveslot .hint { position: absolute; bottom: .6rem; right: .75rem; font-size: .7rem;
    font-weight: 600; color: #e6edf3;
    background: rgba(13,17,23,.72); border: 1px solid #30363d;
    padding: .28rem .65rem; border-radius: 99px; pointer-events: none; }
  .liveslot:hover .hint { border-color: #4493f8; background: rgba(27,34,48,.9); }
  .wrap.wide { max-width: 1240px; }
"""

def page(title, back, back_label, brief, body_html, wide=False):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
  <div class="wrap{' wide' if wide else ''}">
    <a class="back" href="{back}">&larr; {html.escape(back_label)}</a>
    <h1>{html.escape(title)}</h1>
    <p class="brief">{brief}</p>
{body_html}
    <footer>github.com/loktar00/llm-test-pages</footer>
  </div>
</body>
</html>
"""

SECTIONS = {
    'canvas': ('Canvas Demos', 'Full-length baseline runs of the visual-llm canvas prompt set: autonomous '
               'screensavers, physics toys, and sims, each a single self-contained HTML file. Every prompt '
               'has a Qwen3.6 35B baseline and its expert-pruned REAP192 counterpart for comparison.'),
    'frontend': ('Frontend Web', 'Full-length baseline runs of the frontend-web prompt set: component-level '
                 'UI design — glassmorphic cards, dashboards, pure-CSS art — each a single self-contained '
                 'HTML file generated by Qwen3.6 35B.'),
    'deviations': ('Deviations', 'Concepts adapted from loktar00&rsquo;s original creative-coding archive '
                   '(<a href="https://github.com/loktar00/demos-and-deviations" style="color:#58a6ff">demos-and-deviations</a>) '
                   'and reinterpreted by the models: raycast lighting, metaballs, screen-melt, self-weaving '
                   'tapestries, autonomous landers. Base vs expert-pruned REAP192, side by side.'),
}

by_section = defaultdict(lambda: defaultdict(list))
for r in manifest:
    by_section[r['section']][r['stem']].append(r)

# copy run dirs into repo
for section, stems in by_section.items():
    for stem, runs in stems.items():
        for r in runs:
            src = os.path.join(SRC, section, stem, r['runId'])
            dst = os.path.join(REPO, section, stem, r['runId'])
            if not os.path.isdir(src):
                continue  # already in the repo from a previous build
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            preview = os.path.join(dst, 'preview.webm')
            stash = os.path.join(REPO, section, stem, r['runId'] + '.keep')
            if os.path.isfile(preview):
                shutil.move(preview, stash)
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            if os.path.isfile(stash):
                shutil.move(stash, preview)
        # prompt.json + live compare view
        title = stem.replace('-', ' ').title()
        pj = {'promptSlug': stem, 'promptTitle': title, 'runCount': len(runs)}
        open(os.path.join(REPO, section, stem, 'prompt.json'), 'w', encoding='utf-8').write(json.dumps(pj, indent=2))
        panels = []
        for r in sorted(runs, key=lambda x: x['runId']):
            panels.append(f"""      <div class="panel">
        <div class="panel-head">
          <span class="name">{html.escape(r['modelName'])}</span>
          <span class="muted">{r['tokens']} tok &middot; <span class="b {r['status']}">{r['status']}</span></span>
          <a class="full" href="./{r['runId']}/">open full &rarr;</a>
        </div>
        <div class="liveslot" data-src="./{r['runId']}/" data-title="{html.escape(r['modelName'])}">
          <video src="./{r['runId']}/preview.webm" muted loop autoplay playsinline preload="metadata"></video>
          <span class="hint">&#9654; click to run live</span>
        </div>
      </div>""")
        swap_js = """    <script>
    // panels show the recorded preview; clicking swaps in the live demo
    document.querySelectorAll('.liveslot').forEach((s) => {
      s.addEventListener('click', () => {
        const f = document.createElement('iframe');
        f.src = s.dataset.src;
        f.title = s.dataset.title;
        s.replaceWith(f);
      }, { once: true });
    });
    </script>"""
        body = '    <div class="panels">\n' + '\n'.join(panels) + '\n    </div>\n' + swap_js
        open(os.path.join(REPO, section, stem, 'index.html'), 'w', encoding='utf-8').write(
            page(title, '../', SECTIONS[section][0],
                 f'{len(runs)} run(s), live. Add a model, get a panel.', body, wide=True))

# section indexes: live-thumbnail grid, baseline run per prompt
for section, stems in by_section.items():
    title, brief = SECTIONS[section]
    tiles = []
    for stem in sorted(stems):
        runs = stems[stem]
        base = next((r for r in runs if r['runId'] == 'qwen3-6-35b'), runs[0])
        tiles.append(f"""      <a class="tile" href="./{stem}/">
        <div class="thumbwrap"><video data-src="./{stem}/{base['runId']}/preview.webm" muted loop playsinline preload="none" title="{html.escape(stem)}"></video></div>
        <div class="tile-cap"><span class="name">{html.escape(stem.replace('-', ' ').title())}</span>
        <span class="muted">{len(runs)}</span></div>
      </a>""")
    observer_js = """    <script>
    // recorded previews: load + play near the viewport, pause + release far away
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        const v = e.target.querySelector('video');
        if (e.isIntersecting) {
          if (!v.src) v.src = v.dataset.src;
          v.play().catch(() => {});
        } else if (v.src) { v.pause(); }
      }
    }, { rootMargin: '300px 0px' });
    document.querySelectorAll('.thumbwrap').forEach((t) => io.observe(t));
    </script>"""
    body = '    <div class="grid">\n' + '\n'.join(tiles) + '\n    </div>\n' + observer_js
    open(os.path.join(REPO, section, 'index.html'), 'w', encoding='utf-8').write(
        page(title, '../', 'LLM Test Pages', brief, body, wide=True))

n_runs = len(manifest)
n_canvas = sum(1 for r in manifest if r['section'] == 'canvas')
n_frontend = n_runs - n_canvas
print(f'site built: {n_runs} runs ({n_canvas} canvas, {n_frontend} frontend), '
      f'{sum(len(s) for s in by_section.values())} prompt galleries')

import json, os, shutil, html, base64
from collections import defaultdict

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gallery-out')
REPO = r'D:\dev\llm-test-pages'
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
manifest = json.load(open(os.path.join(SRC, 'manifest.json'), encoding='utf-8'))


def _data_uri(path):
    ext = path.rsplit('.', 1)[-1].lower()
    mime = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg'}[ext]
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()


# Jason's avatar, inlined so every page (at any depth) stays self-contained.
AVATAR = _data_uri(os.path.join(ASSETS, 'avatar-loktar.jpg'))

# Compact per-model labels for the tile badges. Everything else (which models
# exist, their run counts, the filter bar) is derived from the manifest — this
# map only supplies a short human label, with a first-word fallback for new
# models so newly-benched runs light up without a code change.
SHORT_LABELS = {
    'qwen3-6-35b': '35B',
    'qwen3-6-27b-q8xl': '27B',
    'qwen3-6-35b-contrast160': 'C160',
    'qwen3-6-35b-reap192': 'REAP',
    'qwen3-7-max': '3.7',
    'qwen3-8-max-preview': '3.8',
    'laguna-s-2-1-q8': 'Laguna',
    'glm-5-2-contrast160-iq3': 'GLM',
}


def short_label(run_id, model_name):
    if run_id in SHORT_LABELS:
        return SHORT_LABELS[run_id]
    words = model_name.split()
    return words[0] if words else run_id

# Video-brand palette: light cool-gray page + white cards by default, inverted dark
# mode. Colours come straight from the compare-video compositor (compose.py).
CSS = """
  :root {
    color-scheme: light;
    --bg: #e9ecf3;
    --card: #ffffff;
    --card-hover: #f4f6fb;
    --border: #dfe3ec;
    --border-hover: #b7c0d6;
    --text: #111318;
    --text-2: #656d76;
    --text-3: #8b929c;
    --accent: #0969da;
    --accent-soft: rgba(9,105,218,.12);
    --pill-bg: rgba(17,19,24,.05);
    --media-bg: #0a0a0a;
    --shadow: 0 1px 3px rgba(31,35,40,.14), 0 8px 24px rgba(31,35,40,.06);
    --shadow-hover: 0 2px 6px rgba(31,35,40,.16), 0 14px 34px rgba(31,35,40,.10);
    --ok-fg: #1a7f37; --ok-bg: rgba(26,127,55,.10); --ok-bd: rgba(26,127,55,.30);
    --warn-fg: #9a6700; --warn-bg: rgba(154,103,0,.10); --warn-bd: rgba(154,103,0,.30);
    --err-fg: #cf222e; --err-bg: rgba(207,34,46,.10); --err-bd: rgba(207,34,46,.30);
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      color-scheme: dark;
      --bg: #0d1117;
      --card: #161b22;
      --card-hover: #1b2230;
      --border: #30363d;
      --border-hover: #4493f8;
      --text: #e6edf3;
      --text-2: #8d96a0;
      --text-3: #6e7681;
      --accent: #58a6ff;
      --accent-soft: rgba(88,166,255,.15);
      --pill-bg: rgba(230,237,243,.08);
      --media-bg: #010409;
      --shadow: 0 1px 2px rgba(1,4,9,.5), 0 8px 24px rgba(1,4,9,.35);
      --shadow-hover: 0 2px 6px rgba(1,4,9,.6), 0 14px 34px rgba(1,4,9,.45);
      --ok-fg: #3fb950; --ok-bg: rgba(63,185,80,.12); --ok-bd: rgba(63,185,80,.35);
      --warn-fg: #d29922; --warn-bg: rgba(210,153,34,.12); --warn-bd: rgba(210,153,34,.35);
      --err-fg: #f85149; --err-bg: rgba(248,81,73,.12); --err-bd: rgba(248,81,73,.35);
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --bg: #0d1117;
    --card: #161b22;
    --card-hover: #1b2230;
    --border: #30363d;
    --border-hover: #4493f8;
    --text: #e6edf3;
    --text-2: #8d96a0;
    --text-3: #6e7681;
    --accent: #58a6ff;
    --accent-soft: rgba(88,166,255,.15);
    --pill-bg: rgba(230,237,243,.08);
    --media-bg: #010409;
    --shadow: 0 1px 2px rgba(1,4,9,.5), 0 8px 24px rgba(1,4,9,.35);
    --shadow-hover: 0 2px 6px rgba(1,4,9,.6), 0 14px 34px rgba(1,4,9,.45);
    --ok-fg: #3fb950; --ok-bg: rgba(63,185,80,.12); --ok-bd: rgba(63,185,80,.35);
    --warn-fg: #d29922; --warn-bg: rgba(210,153,34,.12); --warn-bd: rgba(210,153,34,.35);
    --err-fg: #f85149; --err-bg: rgba(248,81,73,.12); --err-bd: rgba(248,81,73,.35);
  }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh;
    font-family: "Segoe UI", system-ui, -apple-system, "Arial Black", Arial, sans-serif;
    background: var(--bg); color: var(--text); padding: 3rem 1.5rem 4rem;
    -webkit-font-smoothing: antialiased; }
  .wrap { max-width: 860px; margin: 0 auto; }
  .wrap.wide { max-width: 1240px; }
  a.back { color: var(--text-2); text-decoration: none; font-size: 0.85rem; font-weight: 600; }
  a.back:hover { color: var(--accent); }
  h1 { margin: 1.25rem 0 0.4rem; font-size: clamp(1.7rem, 5vw, 2.5rem);
    font-weight: 900; letter-spacing: -0.035em; line-height: 1.05; }
  p.brief { color: var(--text-2); line-height: 1.65; max-width: 64ch; font-weight: 450; }
  p.brief a { color: var(--accent); }

  /* theme toggle */
  #theme-toggle { position: fixed; top: 14px; right: 14px; z-index: 50;
    width: 40px; height: 40px; border-radius: 12px; cursor: pointer;
    display: inline-flex; align-items: center; justify-content: center;
    background: var(--card); color: var(--text-2);
    border: 1px solid var(--border); box-shadow: var(--shadow);
    transition: color .15s, border-color .15s, background .15s; }
  #theme-toggle:hover { color: var(--text); border-color: var(--border-hover); }
  #theme-toggle .icon-sun { display: none; }
  #theme-toggle .icon-moon { display: block; }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) #theme-toggle .icon-sun { display: block; }
    :root:not([data-theme="light"]) #theme-toggle .icon-moon { display: none; }
  }
  :root[data-theme="dark"] #theme-toggle .icon-sun { display: block; }
  :root[data-theme="dark"] #theme-toggle .icon-moon { display: none; }
  :root[data-theme="light"] #theme-toggle .icon-sun { display: none; }
  :root[data-theme="light"] #theme-toggle .icon-moon { display: block; }

  /* section list cards */
  .cards { display: grid; gap: 0.8rem; margin-top: 2rem; }
  a.card { display: block; padding: 1.1rem 1.4rem; border: 1px solid var(--border);
    border-radius: 14px; background: var(--card); color: var(--text); text-decoration: none;
    box-shadow: var(--shadow);
    transition: border-color .15s, background .15s, box-shadow .15s, transform .15s; }
  a.card:hover { border-color: var(--border-hover); background: var(--card-hover);
    box-shadow: var(--shadow-hover); transform: translateY(-1px); }
  .card-top { display: flex; align-items: baseline; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
  .name { font-size: 1.05rem; font-weight: 800; letter-spacing: -0.01em; }
  .muted { color: var(--text-3); font-size: 0.85rem; font-weight: 600; }
  .runid { color: var(--text-2); font-size: 0.82rem; margin-top: 0.4rem; line-height: 1.5; }

  .badges { display: flex; gap: .45rem; margin-top: .55rem; flex-wrap: wrap; }
  .b { font-size: .7rem; padding: .18rem .6rem; border-radius: 99px; font-weight: 700;
    text-transform: lowercase; }
  .b.complete { background: var(--ok-bg); color: var(--ok-fg); border: 1px solid var(--ok-bd); }
  .b.truncated { background: var(--warn-bg); color: var(--warn-fg); border: 1px solid var(--warn-bd); }
  .b.degenerated { background: var(--err-bg); color: var(--err-fg); border: 1px solid var(--err-bd); }
  .b.repaired { background: var(--warn-bg); color: var(--warn-fg); border: 1px solid var(--warn-bd); }

  /* model filter bar (section pages) */
  .filterbar { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1.7rem; }
  .chip { display: inline-flex; align-items: center; gap: .45rem; cursor: pointer;
    font-family: inherit; font-size: .82rem; font-weight: 700; letter-spacing: -0.01em;
    padding: .4rem .8rem; border-radius: 999px; white-space: nowrap;
    background: var(--card); color: var(--text); border: 1px solid var(--border);
    box-shadow: var(--shadow); transition: border-color .15s, background .15s, color .15s; }
  .chip:hover { border-color: var(--border-hover); }
  .chip .c-count { color: var(--text-3); font-weight: 700; font-size: .74rem; }
  .chip.active { background: var(--accent-soft); color: var(--accent);
    border-color: var(--accent); font-weight: 800; }
  .chip.active .c-count { color: var(--accent); }

  /* live-thumbnail grid (section pages) */
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1rem; margin-top: 1.2rem; }
  a.tile { display: block; border: 1px solid var(--border); border-radius: 14px; overflow: hidden;
    background: var(--card); color: var(--text); text-decoration: none; box-shadow: var(--shadow);
    transition: border-color .15s, box-shadow .15s, transform .15s; }
  a.tile:hover { border-color: var(--border-hover); box-shadow: var(--shadow-hover); transform: translateY(-2px); }
  .grid a.tile.is-hidden { display: none; }
  @keyframes tileIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: none; } }
  .grid.filtering a.tile:not(.is-hidden) { animation: tileIn .18s ease both; }
  .thumbwrap { position: relative; aspect-ratio: 16/10; overflow: hidden; background: var(--media-bg); }
  .thumbwrap video { width: 100%; height: 100%; object-fit: cover; display: block; }
  .tile-cap { display: flex; justify-content: space-between; align-items: flex-start; gap: .5rem;
    padding: .7rem .9rem; }
  .cap-main { min-width: 0; }
  .tile-cap .name { font-size: .9rem; }
  .tile-cap .muted { flex: none; padding-top: .05rem; }
  .tile-badges { display: flex; flex-wrap: wrap; gap: .3rem; margin-top: .45rem; }
  .mb { font-size: .64rem; font-weight: 700; line-height: 1; letter-spacing: .01em;
    padding: .2rem .38rem; border-radius: 6px; white-space: nowrap;
    background: var(--pill-bg); color: var(--text-2); border: 1px solid var(--border); }

  /* featured side-by-side compare video */
  .feature { margin-top: 2rem; background: var(--card); border: 1px solid var(--border);
    border-radius: 14px; overflow: hidden; box-shadow: var(--shadow); }
  .feature-head { padding: .85rem 1.1rem; font-weight: 900; font-size: 1rem;
    letter-spacing: -0.02em; color: var(--text); border-bottom: 1px solid var(--border); }
  .feature video { display: block; width: 100%; background: var(--media-bg); }

  /* compare view (prompt pages) */
  .panels { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(480px, 100%), 1fr));
    gap: 1.2rem; margin-top: 2rem; }
  .panel { border: 1px solid var(--border); border-radius: 14px; overflow: hidden;
    background: var(--card); box-shadow: var(--shadow); }
  .panel-head { display: flex; justify-content: space-between; align-items: center; gap: .6rem;
    flex-wrap: wrap; padding: .8rem 1.05rem; border-bottom: 1px solid var(--border); }
  .panel-head .name { font-weight: 800; font-size: .98rem; letter-spacing: -0.01em; }
  .panel-meta { display: flex; align-items: center; gap: .6rem; }
  .panel-meta .tok { color: var(--text-3); font-size: .78rem; font-weight: 600; }
  .panel-head a.full { color: var(--accent); text-decoration: none; font-size: .8rem; font-weight: 600; }
  .panel-head a.full:hover { text-decoration: underline; }
  .panel iframe { display: block; width: 100%; height: 430px; border: 0; background: var(--media-bg); }
  .liveslot { position: relative; cursor: pointer; }
  .liveslot video { display: block; width: 100%; aspect-ratio: 16/10; object-fit: cover; background: var(--media-bg); }
  .liveslot .hint { position: absolute; bottom: .6rem; right: .75rem; font-size: .7rem;
    font-weight: 700; color: #fff;
    background: rgba(13,17,23,.72); border: 1px solid rgba(255,255,255,.18);
    padding: .28rem .65rem; border-radius: 99px; pointer-events: none; }
  .liveslot:hover .hint { background: rgba(9,105,218,.85); border-color: rgba(255,255,255,.3); }

  /* footer wordmark */
  footer { display: flex; align-items: center; gap: .7rem; flex-wrap: wrap;
    margin-top: 3rem; padding-top: 1.4rem; border-top: 1px solid var(--border);
    color: var(--text-3); font-size: .82rem; }
  footer a { text-decoration: none; color: inherit; }
  footer .me { display: inline-flex; align-items: center; gap: .5rem; }
  footer .me .avatar { width: 28px; height: 28px; border-radius: 50%; object-fit: cover;
    border: 1px solid var(--border); flex: none; }
  footer .me .handle { font-weight: 900; letter-spacing: -0.01em; color: var(--text);
    font-size: .92rem; }
  footer .me:hover .handle { color: var(--accent); }
  footer .dot { color: var(--text-3); }
  footer .repo:hover { color: var(--accent); }
"""

# Runs before paint so the stored theme never flashes the wrong palette.
HEAD_SCRIPT = ("<script>(function(){try{var t=localStorage.getItem('theme');"
               "if(t)document.documentElement.dataset.theme=t;}catch(e){}})();</script>")

TOGGLE_HTML = """<button id="theme-toggle" type="button" aria-label="Toggle dark mode" title="Toggle dark mode">
    <svg class="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
    <svg class="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
  </button>"""

TOGGLE_SCRIPT = """<script>(function(){
    var btn=document.getElementById('theme-toggle');
    if(!btn)return;
    btn.addEventListener('click',function(){
      var root=document.documentElement, cur=root.dataset.theme;
      if(!cur)cur=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
      var next=cur==='dark'?'light':'dark';
      root.dataset.theme=next;
      try{localStorage.setItem('theme',next);}catch(e){}
    });
  })();</script>"""

FOOTER_HTML = f"""<footer>
      <a class="me" href="https://x.com/loktar00"><img class="avatar" src="{AVATAR}" alt="loktar00" width="28" height="28"><span class="handle">@loktar00</span></a>
      <span class="dot">&middot;</span>
      <a class="repo" href="https://github.com/loktar00/llm-test-pages">github.com/loktar00/llm-test-pages</a>
    </footer>"""


def page(title, back, back_label, brief, body_html, wide=False):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
{HEAD_SCRIPT}
<style>{CSS}</style>
</head>
<body>
  {TOGGLE_HTML}
  <div class="wrap{' wide' if wide else ''}">
    <a class="back" href="{back}">&larr; {html.escape(back_label)}</a>
    <h1>{html.escape(title)}</h1>
    <p class="brief">{brief}</p>
{body_html}
    {FOOTER_HTML}
  </div>
  {TOGGLE_SCRIPT}
</body>
</html>
"""

ROOT_TITLE = 'Local AI Model Demos'
ROOT_BRIEF = ('Self-contained HTML demos produced by local language models &mdash; each published with the '
              'model that generated it, base against expert-pruned, side by side.')
ROOT_BODY = """    <div class="cards">
      <a class="card" href="./virtual-boy-website/">
        <div class="card-top">
          <span class="name">Virtual Boy Website</span>
          <span class="muted">1 run</span>
        </div>
      </a>
      <a class="card" href="./canvas/">
        <div class="card-top">
          <span class="name">Canvas Demos</span>
          <span class="muted">122 runs &middot; 66 prompts</span>
        </div>
        <div class="runid">Full-length baselines of the visual-llm canvas prompt set &mdash; Qwen3.6 35B, base vs expert-pruned REAP192, side by side</div>
      </a>
      <a class="card" href="./frontend/">
        <div class="card-top">
          <span class="name">Frontend Web</span>
          <span class="muted">36 runs</span>
        </div>
        <div class="runid">Full-length baselines of the frontend-web prompt set &mdash; component-level UI design by Qwen3.6 35B</div>
      </a>
      <a class="card" href="./deviations/">
        <div class="card-top">
          <span class="name">Deviations</span>
          <span class="muted">40 runs &middot; 20 prompts</span>
        </div>
        <div class="runid">Concepts from the original demos-and-deviations archive, reinterpreted by the models &mdash; base vs REAP192</div>
      </a>
    </div>"""

ROOT_PAGE = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ROOT_TITLE}</title>
{HEAD_SCRIPT}
<style>{CSS}</style>
</head>
<body>
  {TOGGLE_HTML}
  <div class="wrap">
    <h1>{ROOT_TITLE}</h1>
    <p class="brief">{ROOT_BRIEF}</p>
{ROOT_BODY}
    {FOOTER_HTML}
  </div>
  {TOGGLE_SCRIPT}
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
                   '(<a href="https://github.com/loktar00/demos-and-deviations">demos-and-deviations</a>) '
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
          <span class="panel-meta">
            <span class="tok">{r['tokens']} tok</span>
            <span class="b {r['status']}">{r['status']}</span>
            <a class="full" href="./{r['runId']}/">open full &rarr;</a>
          </span>
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
        # optional side-by-side comparison video: rendered above the panels when present
        feature = ''
        if os.path.isfile(os.path.join(REPO, section, stem, 'compare.mp4')):
            feature = ('    <div class="feature">\n'
                       '      <div class="feature-head">Side-by-side</div>\n'
                       '      <video controls playsinline preload="metadata" src="./compare.mp4"></video>\n'
                       '    </div>\n')
        body = feature + '    <div class="panels">\n' + '\n'.join(panels) + '\n    </div>\n' + swap_js
        open(os.path.join(REPO, section, stem, 'index.html'), 'w', encoding='utf-8').write(
            page(title, '../', SECTIONS[section][0],
                 f'{len(runs)} run(s), live. Add a model, get a panel.', body, wide=True))

# section indexes: model filter bar + live-thumbnail grid, baseline preview per prompt
for section, stems in by_section.items():
    title, brief = SECTIONS[section]
    # models present in this section, straight from the manifest, with prompt counts
    model_names = {}
    model_stems = defaultdict(set)
    for stem, runs in stems.items():
        for r in runs:
            model_names[r['runId']] = r['modelName']
            model_stems[r['runId']].add(stem)
    # most-run models first, then alphabetical by short label — a stable order shared
    # by the filter chips and each tile's badge row
    order = sorted(model_stems, key=lambda rid: (-len(model_stems[rid]), short_label(rid, model_names[rid])))

    chips = [f'<button class="chip active" type="button" data-all>All <span class="c-count">{len(stems)}</span></button>']
    for rid in order:
        chips.append(f'<button class="chip" type="button" data-model="{html.escape(rid)}">'
                     f'{html.escape(model_names[rid])} <span class="c-count">{len(model_stems[rid])}</span></button>')
    filterbar = '    <div class="filterbar">\n      ' + '\n      '.join(chips) + '\n    </div>'

    tiles = []
    for stem in sorted(stems):
        runs = stems[stem]
        base = next((r for r in runs if r['runId'] == 'qwen3-6-35b'), runs[0])
        rids = sorted((r['runId'] for r in runs), key=lambda rid: order.index(rid))
        data_models = ' '.join(rids)
        pills = ''.join(
            f'<span class="mb" title="{html.escape(model_names[rid])}">{html.escape(short_label(rid, model_names[rid]))}</span>'
            for rid in rids)
        tiles.append(f"""      <a class="tile" href="./{stem}/" data-models="{data_models}">
        <div class="thumbwrap"><video data-src="./{stem}/{base['runId']}/preview.webm" muted loop playsinline preload="none" title="{html.escape(stem)}"></video></div>
        <div class="tile-cap">
          <div class="cap-main"><span class="name">{html.escape(stem.replace('-', ' ').title())}</span>
          <div class="tile-badges">{pills}</div></div>
          <span class="muted">{len(runs)}</span>
        </div>
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
    filter_js = """    <script>
    // manifest-driven model filter: single-select chips show/hide tiles by data-models
    (function () {
      const grid = document.querySelector('.grid');
      const chips = Array.from(document.querySelectorAll('.chip'));
      const allChip = document.querySelector('.chip[data-all]');
      function apply(model) {
        grid.querySelectorAll('a.tile').forEach((t) => {
          const ok = !model || (' ' + t.dataset.models + ' ').includes(' ' + model + ' ');
          t.classList.toggle('is-hidden', !ok);
        });
        grid.classList.remove('filtering'); void grid.offsetWidth; grid.classList.add('filtering');
      }
      chips.forEach((c) => c.addEventListener('click', () => {
        const model = c.dataset.model || '';
        const wasActive = c.classList.contains('active');
        chips.forEach((x) => x.classList.remove('active'));
        if (model && wasActive) { allChip.classList.add('active'); apply(''); }
        else { c.classList.add('active'); apply(model); }
      }));
    })();
    </script>"""
    body = filterbar + '\n    <div class="grid">\n' + '\n'.join(tiles) + '\n    </div>\n' + observer_js + filter_js
    open(os.path.join(REPO, section, 'index.html'), 'w', encoding='utf-8').write(
        page(title, '../', 'Home', brief, body, wide=True))

# root landing page
open(os.path.join(REPO, 'index.html'), 'w', encoding='utf-8').write(ROOT_PAGE)

n_runs = len(manifest)
n_canvas = sum(1 for r in manifest if r['section'] == 'canvas')
n_frontend = n_runs - n_canvas
print(f'site built: {n_runs} runs ({n_canvas} canvas, {n_frontend} frontend), '
      f'{sum(len(s) for s in by_section.values())} prompt galleries')

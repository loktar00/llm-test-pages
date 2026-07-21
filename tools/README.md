# Gallery pipeline tools

The comparison gallery is data-driven: `manifest.json` is the source of truth
(one entry per run: section/stem/runId/modelName/status/chars/tokens), and the
scripts regenerate everything from it plus a staging directory of run folders.

- `build_site.py` — copies staged run dirs into the repo (preserving existing
  `preview.webm` files), writes `prompt.json` per prompt, and regenerates every
  prompt compare page and section grid. Staging layout:
  `<staging>/<section>/<stem>/<runId>/{index.html,meta.json}`. Edit the SRC /
  REPO constants at the top when running from a new machine or session.
- `record_previews.py` — serves the repo and records a 6s 480x300 preview.webm
  via headless Chromium for every manifest run missing one.
- `audit_runs.py` — the execution audit: loads every run headlessly, fails
  anything with uncaught JS errors or nothing visibly rendered. Site policy:
  only audit-passing runs stay in the manifest.

Flow for adding a model's runs (see the `new-llm-bench` skill): stage run
dirs and merge manifest entries, run build_site.py, audit if not already
audited, run record_previews.py, then commit and push.

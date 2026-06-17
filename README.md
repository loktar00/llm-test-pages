# LLM Test Pages

Static designs produced by language models in our benchmark suite, published
alongside the model that created them and hosted via GitHub Pages.

Each design is the **single self-contained HTML file** the model returned for a
given prompt, extracted verbatim from the benchmark recording.

## Structure

```
/
├── index.html                      Root landing page
└── <prompt-name>/
    ├── index.html                  Gallery of runs for this prompt
    └── <run-id>/
        └── index.html              A model's design (run-id encodes model + timestamp)
```

## Live site

https://loktar00.github.io/llm-test-pages/

## Pages

- **Virtual Boy Website** — premium retro-tech collector microsite
  - `glm-5-2-260616-234104` — GLM 5.2

# Chunking Strategies Benchmark

## What this experiment does

This experiment systematically evaluates three chunking strategies across seven
distinct data types found in educational documents. The goal is to find, for
each data type, which strategy (and which parameter settings) preserves the
content's structure well enough to be useful for downstream retrieval.

**Chunking strategies tested:**

| Strategy | Notebook origin | Input format |
| --- | --- | --- |
| Fixed / Recursive (`RecursiveCharacterTextSplitter`) | `01-modules/01-tools/02-chunk/01-character-splitting.ipynb` | raw `str` |
| Semantic / Adaptive (sentence-embed-cosine-group) | `01-modules/01-tools/02-chunk/01-character-splitting.ipynb` | raw `str` |
| Docling Hybrid (`HybridChunker`) | `01-modules/01-tools/02-chunk/02-token-aware-chunking.ipynb` | `DoclingDocument` |

**Data types covered (all seven present in `fixture_all_types.md`):**

1. Continuous prose (curriculum rationale)
2. Hierarchical headings (three nested levels)
3. Dense multi-row, multi-column table (curriculum indicators)
4. Python code block (function with docstring, loop, indentation)
5. Mathematical expressions and formulas (fractions, decimals, LaTeX)
6. Student Q&A exam submission (question prompt + multi-step answer)
7. Diagram / chart caption with ASCII visual

## How to run

```bash
cd anacodic-agentic-cookbook
pip install -r requirements.txt -r 01-modules/01-tools/02-chunk/requirements.txt
jupyter notebook 02-experiments/maanas-chunking-eval/01-chunking-benchmark.ipynb
```

No API key, GPU, or network access is required. This notebook primarily
evaluates chunk boundaries and content integrity; the fixed and Hybrid paths do
not call an embedding model. The semantic path uses a deterministic, offline
hash-vector stub only so its grouping code can run. Production embedding-model
selection and retrieval evaluation are deferred to a later stage.

## What it scored

One fixture document (`fixture_all_types.md`), structure checks only — no
embedding model, no retrieval. From the notebook's Step 7 run (outputs are
stripped from the committed notebook, so the table is copied here):

```
Configuration                Chunks   Words      Table%  Code  Math  Q&A  Diag
default-200w-0ov                 10   58–195       50%    ✓     ✓    ✓    ✓
default-400w-0ov                  4   352–399     100%    ✓     ✓    ✗    ✓
default-800w-0ov                  2   734–789     100%    ✗     ✓    ✓    ✓
heading-400w-50ov                 5   190–381     100%    ✓     ✓    ✓    ✓
markdown-400w-50ov                6   57–395      100%    ✗     ✓    ✓    ✓
semantic-τ=0.70                  10   31–381      100%    ✗     ✓    ✗    ✓
semantic-τ=0.90                  10   30–236       50%    ✗     ✓    ✗    ✗
hybrid-256tok                    20   30–139      100%    ✗     ✓    ✓    ✗
hybrid-512tok                    11   32–247      100%    ✓     ✓    ✓    ✓
hybrid-1024tok                    9   32–436      100%    ✓     ✓    ✓    ✓
```
(22 configurations in the notebook; representative rows shown.)

Table% = share of table chunks that keep the column header. Fixed and semantic
chunkers emit the table as pipe rows, so a cut below the header strands the
rows (50% at 200 words / τ=0.90). Docling's HybridChunker rebuilds the table
key-value — the column name rides on every value — so a cut cannot strand it.
The checker reads both forms and prints `n/a` when it finds no table rows,
instead of a score.

**Recommendation (Step 8):** Docling Hybrid, `max_tokens=512`, for documents
with tables, code or math. On this one fixture several configurations pass
every check (e.g. `heading-400w-50ov`, `default-400w-50ov`, `hybrid-512tok`,
`hybrid-1024tok`), so the checks alone do not single out a winner. The
recommendation rests on what Hybrid *guarantees* — the header rides on every
table value, chunks carry their section path — while the fixed and semantic
splitters pass only when the word budget happens to land well (they fail at
200 words and at τ ≥ 0.80).

## What this does NOT show yet

- Structure is a proxy. Nobody has measured whether a surviving table is
  actually *retrieved* better — that needs a retrieval metric (recall@k) on a
  question set, which is the next task.
- One hand-built document. Results on real PDFs may differ.
- The semantic path uses an offline hash stub, not a real embedding model, so
  its groupings are wiring-only (the notebook says so in Step 8).

## Review history

Reviewed and fixed on 2026-09-24 before merge: the table checker originally
matched only pipe rows, so every Docling run reported `100% (0/0)`; it now
recognises both serializations and returns `None` when nothing is measured.
A re-run of `01-modules/.../02-token-aware-chunking.ipynb` was dropped from the
PR (outputs only).


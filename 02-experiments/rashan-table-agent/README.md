# rashan-t — Reasoning, tool-using agent for biomedical table QA

**Status:** scaffolded 2026-10-02, no runs yet.

## What this experiment is

Build an autonomous agent that **reasons** (plan → act → reflect) and **uses tools**
(table-aware extract/chunk, retrieve, grounding gate) to answer biomedical
questions whose answers live in a **table**, and measure:

1. **Baseline vs table-aware** answered rate (the ablation delta — the headline).
2. **Stage attribution** of failures: extract / structure / chunk / index / generate.
3. **Reliability** under non-deterministic retrieval: mean ± spread over N runs.

## Data

**SciTableQA**, Biology subset (MIT license, HuggingFace `Kehindeajayi01/SciTableQA`).
Human-verified gold QA over standalone scientific tables; the Biology domain is
real biomedical/genetics papers. Cached under `data/` — **gitignored, never commit**
(it is 893 MB and we keep the repo clean).

## Reused from the cookbook (not rebuilt)

| component | source |
|---|---|
| reasoning loop | `01-modules/04-orchestrate/04-plan-act-reflect.ipynb` |
| tool specs / tool selection | `01-modules/01-tools/07-as-a-tool/01,02,03` |
| table-aware extract + chunk | `01-tools/01-extract/02`, `01-tools/02-chunk/02` |
| retrieval + grounding gate | `01-tools/04-retrieve/*`, `01-tools/05-gate/01` |
| N-times variance runner | `02-experiments/amaresh-eval-harness/` |

## Scores

| notebook | config | metric | dim | result |
|---|---|---|---|---|
| _pending_ | _pending_ | _pending_ | _pending_ | _PENDING RUN_ |

## Notebooks

Written to [NOTEBOOK_STANDARD.md](../NOTEBOOK_STANDARD.md): one action per cell,
capabilities table first, a "Step N" header before each cell, real output read
before the next step. Built incrementally.

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

## Notebooks — read these in order

These are **walkthroughs**: they import the real modules in this folder and drive
them, rather than re-implementing anything. Written to
[NOTEBOOK_STANDARD.md](../NOTEBOOK_STANDARD.md) — one action per code cell, a
"Step N" header before each, and real output read before the next step.

| # | Notebook | What you learn | Needs a key |
|---|---|---|---|
| 01 | `01_the_data.ipynb` | what a benchmark item is; lookup vs compute; the label check | no |
| 02 | `02_scoring.ipynb` | what "correct" means, and three real scorer bugs | no |
| 03 | `03_baseline.ipynb` | the plain model call the agent must beat | yes |
| 04 | `04_the_agent.ipynb` | the tools, the tool-call trace, abstention | yes |
| 05 | `05_the_experiment.ipynb` | repeats, spread, cost — turning answers into a claim | yes |

Outputs are saved so the notebooks can be read without running them. Where a cell
needs a model and no provider was available at commit time, the cell is left
unexecuted and the notebook says so at the top.

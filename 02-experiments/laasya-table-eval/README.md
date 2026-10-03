# laasya-table-eval — Evaluation & failure analysis for the table-QA agent

**Owner:** Laasya (first-author evaluation contribution)
**Status:** scaffolded 2026-10-02.

## What this folder is

This is the **evaluation half** of the table-QA agent paper. The agent itself is
built in `../rashan-table-agent/`. Your job here is to take the agent's answers
and turn them into the paper's **results**:

1. **Accuracy by reasoning type** — how often the agent is right, split by
   question type (Cell Selection, Arithmetic, Counting, ...).
2. **Ablation delta** — naive-text vs table-aware: how much the table tool helps.
3. **Failure analysis** — of the wrong answers, where did it go wrong.

You do all of this by reading CSV files (the agent's outputs) and computing
numbers + a figure from them. You do **not** need to run the model yourself.

## The one rule

> **Only ever edit files inside THIS folder (`laasya-table-eval/`).**
> Never change anything in `rashan-table-agent/` or elsewhere.

That rule is what lets several people work in the same repo without breaking
each other's work.

## What's in here

| file / folder | what it is |
|---|---|
| `SETUP_FIRST.md` | do this once before anything else |
| `FIRST_TASK.md` | your exact first task, step by step |
| `analyze_results.py` | reads result CSVs and prints accuracy + makes a figure |
| `results-input/` | drop the agent's CSVs here (handed to you by Rashan) |
| `results/` | your outputs land here (tables, figures) |

Written to [NOTEBOOK_STANDARD.md](../NOTEBOOK_STANDARD.md) when you add notebooks:
one action per cell, look at the output before the next step.

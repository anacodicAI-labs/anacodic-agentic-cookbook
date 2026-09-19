# Chunking Strategies Benchmark

## What this experiment does

This experiment systematically evaluates three chunking strategies across seven
distinct data types found in educational documents. The goal is to find, for
each data type, which strategy (and which parameter settings) preserves the
content's structure well enough to be useful for downstream retrieval.

**Chunking strategies tested:**

| Strategy | Notebook origin | Input format |
| --- | --- | --- |
| Fixed / Recursive (`RecursiveCharacterTextSplitter`) | `01-modules/02-chunk/01-character-splitting.ipynb` | raw `str` |
| Semantic / Adaptive (sentence-embed-cosine-group) | `01-modules/02-chunk/01-character-splitting.ipynb` | raw `str` |
| Docling Hybrid (`HybridChunker`) | `01-modules/02-chunk/02-token-aware-chunking.ipynb` | `DoclingDocument` |

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
pip install -r requirements.txt -r 01-modules/02-chunk/requirements.txt
jupyter notebook 02-experiments/maanas-chunking-eval/01-chunking-benchmark.ipynb
```

No API key, GPU, or network access is required. This notebook primarily
evaluates chunk boundaries and content integrity; the fixed and Hybrid paths do
not call an embedding model. The semantic path uses a deterministic, offline
hash-vector stub only so its grouping code can run. Production embedding-model
selection and retrieval evaluation are deferred to a later stage.

## What it scored

See the comparative benchmark table in the notebook's Step 7 output.


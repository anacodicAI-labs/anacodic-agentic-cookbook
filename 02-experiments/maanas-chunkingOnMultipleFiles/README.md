# Multi-File Chunking Benchmark — COVID-QA Corpus

## What this experiment does

This experiment extends chunking strategy evaluation from single synthetic fixtures to **real-world biomedical research papers at scale**. We benchmark chunking strategies across the 137 COVID-QA research papers parsed by AnacodicAI's production Docling pipeline (from [`anacodicai-labs/covidqa-bench`](https://huggingface.co/datasets/anacodicai-labs/covidqa-bench)).

Rather than reading flat strings, these papers contain complex, authentic scientific document elements:
- Multi-row clinical tables (patient demographics, trial outcomes, drug dosages)
- Scientific diagrams, microscopy images, and charts with descriptive captions
- Deep multi-level heading hierarchies (Introduction > Methods > Trial Design > Statistical Analysis)
- Mathematical expressions, chemical notations, and numeric laboratory values
- Citations, author affiliations, and structured bibliographies

## Strategies compared

| Strategy | Engine | Input format | Contextual mechanism | Cost / Rate limits |
| :--- | :--- | :--- | :--- | :--- |
| **1. Recursive Character Splitter** | LangChain `RecursiveCharacterTextSplitter` | Flat Markdown / string | None (isolated text windows with token overlap) | Free (local CPU) |
| **2. Semantic Chunking** | Regex sentence split + similarity grouping | Flat Markdown / string | Groups adjacent sentences by cosine threshold $\tau$ | Free (local CPU) |
| **3. Docling Hybrid Chunker** | Docling `HybridChunker` | Typed `DoclingDocument` AST | Native Docling contextualization (`chunker.contextualize()`, `repeat_table_header=True`, `always_emit_headings=True`, and token overlap tail) | Free (local CPU) |

All three strategies use Docling's tokenizer with a **512-token chunking target** and
**50-token overlap**. The recursive and semantic outputs are capped at 512 tokens; the
semantic strategy first groups sentences by similarity, then splits oversized groups.
Docling uses the same configured target, but its final recorded text can exceed 512 after
contextualization or overlap. Table-aware header repetition remains specific to Docling.

## The Data: `anacodicai-labs/covidqa-bench`

The data comes from the official benchmark repository:
- **`parsed_questions_137.tar.zst`** (1.7 GB download, ~2.6 GB unpacked): The 137 papers that contain expert-annotated COVID-QA questions.
- **`gold/questions.jsonl`** (1,852 questions + answers): The ground truth containing exact answer text spans written by medical experts.
- Unpacks to `data/02_parsed/covidqa/<paper_slug>/` containing master `<paper>.docling.json` files, extracted tables, and images.

Because papers are already parsed by Docling into `.docling.json`, **no GPU or expensive PDF parsing is required**! You can directly load each `DoclingDocument` via `DoclingDocument.load_from_json(path)`.

## Intrinsic Pre-Retrieval Evaluation Metrics

Rather than waiting for downstream retrieval or generation, this notebook measures chunk quality directly at the ingestion stage:
1. **Answer Span Preservation:** Tests whether the expert's `gold_answer` is preserved 100% intact within **a single chunk** vs fragmented across a boundary.
2. **Table Header & Schema Retention:** Evaluates whether split clinical tables retain their column header row (`|---|`).
3. **Contextual Breadcrumb Attachment:** Evaluates whether chunks carry their hierarchical section path (`section_path`).
4. **Token Size Distribution & Variance:** Measures chunk consistency and detects erratic outliers.
5. **Observability Integration (Langfuse):** Optional logging of chunking evaluation scores into a trackable dashboard.

## How to run

1. Ensure your virtual environment is active:
   ```bash
   .venv\Scripts\activate
   ```
2. Launch Jupyter:
   ```bash
   jupyter notebook 02-experiments/maanas-chunkingOnMultipleFiles/01-covidqa-chunking-benchmark.ipynb
   ```
3. Run the cells step-by-step to inspect how each strategy handles real-world scientific documents.

Langfuse experiment logging uses the Python SDK's `run_experiment` API (Langfuse SDK 4 or later).
Install it with `pip install "langfuse>=4.0"` and set `LANGFUSE_PUBLIC_KEY`,
`LANGFUSE_SECRET_KEY`, and (for non-default regions) `LANGFUSE_BASE_URL` in your environment
or `.env`. Without credentials, the benchmark still runs locally and skips dashboard logging.

Follows [`NOTEBOOK_STANDARD.md`](../NOTEBOOK_STANDARD.md): one action per cell, capabilities table upfront, and detailed educational step-by-step explanations.

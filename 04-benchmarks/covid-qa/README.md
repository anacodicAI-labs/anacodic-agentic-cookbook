# covid-qa — a public medical RAG benchmark, parsed with our production pipeline

2,019 questions written by biomedical experts over 147 full-text COVID-19
research articles ([COVID-QA](https://github.com/deepset-ai/COVID-QA), deepset,
Apache-2.0). Every answer is a marked span of its article, so all the standard
RAG metrics can be computed: context recall, context precision, faithfulness,
answer relevancy, answer correctness, Recall@k.

The articles are fetched as **PDFs** and parsed with **the same code and
settings as the guidelines-generator Ontario corpus** — so a number here says
something about our real pipeline, not about a toy one.

## Get the data — you do not need to parse anything

The parse needs a GPU and the guidelines-generator pipeline. It has been run
once and is shared as a zip (ask Rashan for the link):

```
covidqa_parsed_2026-10-05.zip      137 question papers                     2.2 GB
covidqa_with_distractors_…zip      + ~1,500 same-topic papers, no questions  (coming)
```

Unzip it so this folder has a `data/` directory (or a `data` symlink). Never
commit it — it is gitignored.

## What is in `data/`

| path | what | start here if you are… |
|---|---|---|
| `02_parsed/covidqa/<paper>/` | master `.docling.json` + `assets/` + `links.json` + `manifest.json` | **comparing chunkers** — re-chunk from these |
| `02_parsed/covidqa_derived/` | sections, tables with cells, figures, references, bibliography | reading structure |
| `03_chunked/covidqa/chunks.jsonl` | production chunks: `chunk_id, paper_slug, chunk_type, section_path, pages, text, embed_text, caption, title` | **scoring retrieval** |
| `gold/questions.jsonl` | `question, gold_answer, paper_id, gold_chunk_ids, match` | **computing metrics** |
| `manifest.csv` | article → PMC ID, DOI, licence, why it was or wasn't fetched | everyone |
| `table_count_check.json` | tables in our parse vs PMC's XML, per paper | checking tables |
| `SHARE_README.txt` | the run record | everyone |

## The numbers (production run, 2026-10-05)

```
articles     137 / 147 parsed (CC0 / CC BY PDFs) — 10 have no redistributable PDF
             (6 not in PMC, 2 retracted, 2 no PDF / licence) → 1,852 / 2,019 questions
parse        137 ok · 0 failed · derive 137 ok, every item reconciled
tables       282 derived · 0 lost vs PMC XML · 40 papers truly have none ·
             16 papers show extra tables (tables split across pages)
chunks       5,949 · 861 table chunks · DOI on 106 / 137 papers (77%)
gold         1,852 questions: exact 94% · fuzzy 5% · none 1%
```

Chunker (identical to guidelines-generator / specialistRAG): Docling
HybridChunker · tiktoken for `text-embedding-3-large` · 512 tokens ·
`repeat_table_header` · `merge_peers` · `always_emit_headings` · contextualize.

## Two scoring rules that matter

1. **`gold_chunk_ids` fit the 512-token production chunks only.** If you re-chunk
   (256, 1024, a different splitter), score "does a top-k chunk contain the gold
   answer" with the same text match `build_gold.py` uses — not chunk IDs.
2. **`match = none` counts answers the parse lost.** Report it; part of it is
   COVID-QA's own text being wrong (e.g. "32uC" where the PDF says 32 °C).

Write the embedding model, its dimension and the LLM next to every number.

## How the data was built (for the record)

```
python download.py                 # COVID-QA.json + 137 PDFs + manifest.csv
python download_distractors.py     # optional: 1,500 same-topic CC BY papers
# guidelines-generator, profile `covidqa` (config/corpus_profiles/covidqa.json):
GUIDELINE_CORPUS_PROFILE=covidqa python scripts/ingest/01_ingest_structured_corpus.py
GUIDELINE_CORPUS_PROFILE=covidqa python scripts/ingest/05_derive_from_native.py
GUIDELINE_CORPUS_PROFILE=covidqa python scripts/ingest/06_enrich_bibliographic.py
GUIDELINE_CORPUS_PROFILE=covidqa python scripts/ingest/03b_chunk_structured_corpus.py
python build_gold.py               # answer spans → gold chunk IDs
```

## Licences

Only CC0 / CC BY / CC BY-SA / CC BY-ND PDFs are fetched, and retracted papers
are skipped. If you share derived data, keep `manifest.csv` with it and
acknowledge "NIH NLM NCBI PubMed Central (PMC) Article Datasets"
(https://registry.opendata.aws/ncbi-pmc) and COVID-QA (deepset, Apache-2.0).

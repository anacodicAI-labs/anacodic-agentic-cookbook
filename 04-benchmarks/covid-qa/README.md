# covid-qa — a public medical RAG benchmark, parsed our way

2,019 questions written by biomedical experts over 147 full-text COVID-19
research articles ([COVID-QA](https://github.com/deepset-ai/COVID-QA), deepset,
Apache-2.0). Each answer is a marked span of the article, so every standard RAG
metric can be computed: context recall, context precision, faithfulness,
answer relevancy, answer correctness, Recall@k.

The articles are fetched as **PDFs** from the PMC Cloud Service and parsed with
**the same Docling + HybridChunker settings as guidelines-generator and
specialistRAG** — so results here say something about our real pipeline.

## Run it — three steps

```bash
pip install docling tiktoken          # once
python download.py                    # ~5 min · COVID-QA.json + 137 PDFs (206 MB)
python parse_docling.py               # GPU: minutes · CPU: ~2-5 min per article
python build_gold.py                  # answer spans → gold chunk IDs
```

Pilot first: `python download.py --limit 5` and `python parse_docling.py --limit 2`.

## What you get (all in `data/`, gitignored — never commit it)

| file | what | who uses it |
|---|---|---|
| `manifest.csv` | one row per article: PMC ID, DOI, licence, why a PDF was or wasn't fetched | everyone |
| `pdfs/PMC*.pdf` | 137 articles, CC BY or CC0 only | — |
| `docling/PMC*.json` | full DoclingDocument per article | Maanas — compare chunkers on the SAME parse |
| `chunks/chunk_meta.jsonl` | product-style chunks: `chunk_id, paper_id, chunk_type, section_path, pages, text, embed_text` | Amaresh — retrieval + scoring |
| `chunks/chunker_config.json` | exact chunker settings | everyone — record it next to every number |
| `gold/questions.jsonl` | `question, gold_answer, paper_id, gold_chunk_ids, match` | Amaresh — metrics |

## Coverage (download run, 2026-10-04)

```
137 / 147 articles as PDF (136 CC BY, 4 CC0 … ) → 1,852 / 2,019 questions (92%)
  6  not in PMC (CDC reports, preprints)  → chunked from the dataset's own text
  2  retracted                            → skipped
  2  no PDF / licence not recorded        → dataset text
pilot: 2 articles → 108 chunks (20 table) · 22 questions mapped (91% exact, 9% fuzzy, 0 lost)
```

Chunks from the dataset-text fallback carry `source="dataset_text"`; filter
them out to score the PDF pipeline alone.

## Rules

- **Licences:** only CC0 / CC BY / CC BY-SA / CC BY-ND PDFs are fetched. If you
  share derived data, keep `manifest.csv` with it (attribution) and acknowledge
  "NIH NLM NCBI PubMed Central (PMC) Article Datasets" and COVID-QA (deepset).
- **Never commit `data/`.** Share it outside git; anyone can rebuild it from
  the three scripts.
- Write the embedding model + dimension next to every number you report.

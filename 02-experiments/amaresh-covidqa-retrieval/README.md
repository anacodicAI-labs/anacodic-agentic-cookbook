# COVID-QA retrieval benchmark: BM25, dense, HNSW and hybrid

**Owner:** Amaresh Hebbar · **Stage:** `04-retrieve` · **Benchmark:** [`04-benchmarks/covid-qa`](../../04-benchmarks/covid-qa/) ([Hugging Face](https://huggingface.co/datasets/anacodicai-labs/covidqa-bench))

## What this answers

1. How well does each retriever find the gold chunk? Recall@k, Hit@k, Precision@k, MRR, nDCG@k and MAP@k, with 95% bootstrap confidence intervals.
2. Is the result stable when the same questions are run again?
3. How many questions are needed before a difference can be trusted?
4. Where does retrieval break: question papers only (137) versus the full corpus with 1,500 topic-matched decoy papers (1,637)?

Retrieval runs over the fixed production chunks (`chunks.jsonl`, 64,965 chunks, Docling HybridChunker at 512 tokens). Re-chunking is a separate experiment.

## Retrievers

| name | what it is |
|---|---|
| `bm25` | lexical baseline (bm25s, English stopwords) |
| `dense` | `BAAI/bge-small-en-v1.5`, exact cosine search (FAISS flat) |
| `dense_hnsw` | same embeddings, approximate search (FAISS HNSW, M=32, efSearch=32) |
| `hybrid` | reciprocal rank fusion of `bm25` and `dense` (k=60, depth 100) |

## Results (1,840 scorable questions)

nDCG@10, with 95% CI:

| retriever | questions only | full corpus with decoys |
|---|---|---|
| bm25 | **0.581** (0.562–0.599) | **0.466** (0.447–0.485) |
| hybrid | 0.544 | 0.459 |
| dense | 0.427 | 0.348 |
| dense_hnsw | 0.412 | 0.318 |

- BM25 is the best single retriever in both settings. With decoys, hybrid is not significantly different from BM25 (paired CI −0.006 to +0.020); on question papers only, BM25 beats hybrid (+0.037, significant).
- Adding decoy papers costs every retriever about 16–23% of its nDCG@10.
- With efSearch=32, the HNSW index returns 88% of the exact top 10 on the full corpus (97% on question papers only). Part of the HNSW gap reflects this setting.
- Five repeated runs give the same outcomes. BM25 and exact search are deterministic by design; dense search on GPU changed under 0.3% of top-10 lists with no change in hits.
- At this sample size, nDCG@10 differences of about ±0.02 can be resolved.
- 12 of 1,852 questions have no gold chunk (the answer was lost in parsing) and are listed in `results/excluded_questions.csv`.

## How to run

```bash
pip install bm25s faiss-cpu sentence-transformers huggingface_hub pandas matplotlib
jupyter notebook covidqa_retrieval_benchmark.ipynb
```

The data is downloaded from the Hugging Face dataset on first run. `COVIDQA_QUESTIONS` and `COVIDQA_CHUNKS` point to local copies instead. A GPU speeds up encoding but is not required.

## Files

| path | contents |
|---|---|
| `covidqa_retrieval_benchmark.ipynb` | the full benchmark, with executed outputs |
| `results/headline.csv`, `metric_grid.csv` | every metric at k = 1, 3, 5, 10, 20 |
| `results/paired_bootstrap.csv` | paired comparisons between retrievers |
| `results/stability.csv`, `scaling.csv`, `questions_needed.csv` | repeat runs and sample size |
| `results/diagnosis.csv`, `failures.csv` | where each retriever misses |
| `results/per_query.csv.gz` | per-question scores |
| `results/run_meta.json` | config, data hashes, library versions |

## Known gaps

- The `text_match` relevance view uses a light normaliser (lowercase and whitespace). `04-benchmarks/covid-qa/build_gold.py` also rejoins hyphenated line breaks and strips punctuation, so `text_match` undercounts slightly. The headline `chunk_id` scores are unaffected.
- Some questions do not name a paper ("What was the purpose of this study?"). They are kept in these numbers; the follow-up experiment, [`amaresh-embedder-comparison`](../amaresh-embedder-comparison/), reports both the full and the filtered set.

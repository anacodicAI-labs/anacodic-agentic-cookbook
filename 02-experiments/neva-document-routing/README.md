# Document routing — which reader does this page need?

**Owner:** Neva · **Stage:** `01-extract` · **Status:** starting

## The problem

A document arrives and something has to decide how to read it. A PDF can carry
a real text layer, or it can be a scan with no text at all, so the file
extension cannot decide. Two lab projects need the same answer:

- course material and student answer sheets (printed and handwritten)
- old scanned books (small type, low resolution)

This experiment builds the decision once, here, so both can reuse it.

```
   file in
     │
     ▼
   docling ──▶ look at the RESULT (not just "did it crash?")
     │            enough real text?  ── yes ──▶ ROAD A: use docling's text
     │            empty / mostly unreadable? ── ▶ ROAD B: rasterize → OCR
     ▼
   text + which road was taken + why
```

## Tasks, in order

1. **Build the test pile** (`sample-data/`). Five page types, each made from
   text you know, so the correct answer exists for every page. See
   [`sample-data/README.md`](sample-data/README.md).
2. **Write the router** (`01_router.ipynb`). Try docling first, inspect what
   came back, fall through to OCR when the text is empty or mostly
   unreadable. Print the road and the reason for every test page.
3. **Measure reading quality** (`02_quality_vs_resolution.ipynb`). CER for each
   page type, then at 300 / 200 / 150 / 100 dpi, and for large vs small type.
   The question: at what resolution or letter size does reading break?

Done means a number you chose and can defend at the call: which threshold
decides the road, and the CER curve with the point where it breaks.

## Metric

```
            S + D + I       S, D, I = characters substituted, deleted, inserted
   CER  =  -----------      to turn the output into the known text
                N           N = length of the known text. 0 = perfect.
```
WER is the same over words.

## Read first

| what | where | why |
|---|---|---|
| notebook rules | [`../NOTEBOOK_STANDARD.md`](../NOTEBOOK_STANDARD.md) | the cell rhythm for this folder |
| extract notebooks 01–04 | [`01-modules/01-tools/01-extract/`](../../01-modules/01-tools/01-extract/) | docling on a clean PDF, tables, orientation, OCR |
| rasterizer (PDF page → image) | `01-extract/03-orientation.ipynb` | three lines with `fitz`; copy it, don't rewrite it |
| illegible-line handling, OCR engines, CER/WER | manu-script: `engine/line_quality.py`, `engine/ocr_engines.py`, `eval/metrics.py` | already solved there; reuse them |

Rule: if a piece already exists, copy it and say where it came from.

## Folder layout

```
neva-document-routing/
├── README.md                          this file
├── sample-data/                       the test pile (known text + pages)
│   └── README.md                      what goes in it and how to make it
├── 01_router.ipynb                    task 2
├── 02_quality_vs_resolution.ipynb     task 3
└── results/                           CSVs + plots written by the notebooks
```

## Results

| page type | road taken | CER | notes |
|---|---|---|---|
| born-digital PDF | | | |
| scanned typed page | | | |
| handwritten scan | | | |
| old-book page | | | |
| image file (PNG) | | | |

Weekly update in the cookbook channel: DONE · NEXT · BLOCKED.

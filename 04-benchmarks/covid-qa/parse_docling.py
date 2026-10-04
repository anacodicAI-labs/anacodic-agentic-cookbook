"""Step 2 of 3 — parse every article with Docling and chunk it the PRODUCT way.

    python parse_docling.py                 # all articles (GPU strongly advised)
    python parse_docling.py --limit 2       # a quick check
    python parse_docling.py --device cpu    # force CPU

Chunking matches guidelines-generator / specialistRAG exactly
(services/structured_ingestion/docling_chunker.py):
    HybridChunker · tokenizer = OpenAI tiktoken for text-embedding-3-large ·
    max_tokens 512 · repeat_table_header · merge_peers · always_emit_headings ·
    contextualize (embed_text = heading path + chunk text)

Articles whose PDF could not be fetched (see data/manifest.csv) are chunked
from the article text COVID-QA ships, through the same chunker, and marked
source="dataset_text" so anyone can filter them out.

Output (gitignored):
    data/docling/PMC*.json        the full DoclingDocument — Maanas's input for
                                  comparing chunkers on the SAME parse
    data/chunks/chunk_meta.jsonl  one line per chunk — Amaresh's input for
                                  retrieval and scoring
    data/chunks/chunker_config.json   the exact settings, recorded with the chunks
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
CONFIG = {
    "tokenizer": "openai",
    "embed_model": "text-embedding-3-large",
    "max_tokens": 512,
    "repeat_table_header": True,
    "merge_peers": True,
    "always_emit_headings": True,
    "contextualize": True,
}


def build_converter(device: str):
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions()
    opts.do_table_structure = True
    opts.accelerator_options = AcceleratorOptions(
        device={"auto": AcceleratorDevice.AUTO, "cuda": AcceleratorDevice.CUDA,
                "cpu": AcceleratorDevice.CPU}[device])
    return DocumentConverter(
        allowed_formats=[InputFormat.PDF, InputFormat.MD],
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)},
    )


def build_chunker():
    import tiktoken
    from docling.chunking import HybridChunker
    from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer

    tok = OpenAITokenizer(tokenizer=tiktoken.encoding_for_model(CONFIG["embed_model"]),
                          max_tokens=CONFIG["max_tokens"])
    return HybridChunker(tokenizer=tok, repeat_table_header=CONFIG["repeat_table_header"],
                         merge_peers=CONFIG["merge_peers"],
                         always_emit_headings=CONFIG["always_emit_headings"])


def chunk_type(chunk) -> str:
    labels = {str(getattr(getattr(i, "label", ""), "value", getattr(i, "label", ""))).lower()
              for i in (chunk.meta.doc_items or [])}
    if "table" in labels:
        return "table"
    if labels & {"picture", "figure", "chart"}:
        return "figure"
    return "prose"


def pages(chunk) -> list[int]:
    return sorted({p.page_no for i in (chunk.meta.doc_items or [])
                   for p in (getattr(i, "prov", None) or [])})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    args = ap.parse_args()

    manifest = list(csv.DictReader(open(DATA / "manifest.csv")))
    articles = json.loads((DATA / "COVID-QA.json").read_text())["data"]
    (DATA / "docling").mkdir(parents=True, exist_ok=True)
    (DATA / "chunks").mkdir(parents=True, exist_ok=True)
    (DATA / "text").mkdir(parents=True, exist_ok=True)

    converter, chunker = build_converter(args.device), build_chunker()
    out = open(DATA / "chunks" / "chunk_meta.jsonl", "w")
    n_chunks = 0
    for row in manifest[: args.limit]:
        if row["status"].startswith("retracted"):
            continue
        idx = int(row["doc_index"])
        paper_id = row["pmcid"] or f"doc{idx:03d}"
        if row["status"] == "pdf":
            src, source = DATA / row["pdf"], "pdf"
        else:  # dataset text fallback, through the same chunker
            src = DATA / "text" / f"{paper_id}.md"
            src.write_text(articles[idx]["paragraphs"][0]["context"])
            source = "dataset_text"

        t0 = time.time()
        doc = converter.convert(src).document
        (DATA / "docling" / f"{paper_id}.json").write_text(json.dumps(doc.export_to_dict()))
        for k, ch in enumerate(chunker.chunk(dl_doc=doc)):
            embed_text = chunker.contextualize(ch) if CONFIG["contextualize"] else ch.text
            out.write(json.dumps({
                "chunk_id": f"{paper_id}:c{k}", "paper_id": paper_id, "doc_index": idx,
                "chunk_index": k, "chunk_type": chunk_type(ch), "source": source,
                "section_path": " > ".join(ch.meta.headings or []), "pages": pages(ch),
                "text": ch.text, "embed_text": embed_text,
            }) + "\n")
            n_chunks += 1
        print(f"{idx:>3} {paper_id:<12} {source:<12} {time.time() - t0:6.1f}s  total chunks {n_chunks}")
    out.close()
    (DATA / "chunks" / "chunker_config.json").write_text(json.dumps(CONFIG, indent=2))
    print(f"\n{n_chunks} chunks → data/chunks/chunk_meta.jsonl")


if __name__ == "__main__":
    main()

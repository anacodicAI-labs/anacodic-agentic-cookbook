"""Step 3 of 3 — turn COVID-QA answers into gold CHUNK IDs for our chunks.

    python build_gold.py

COVID-QA marks each answer as a span of the article text. Our chunks come from
Docling's parse of the PDF, so the text differs slightly (line breaks, hyphens,
ligatures). For each question we find the chunk(s) holding the answer:

    exact  — the normalised answer appears inside the chunk
    fuzzy  — no exact hit; best chunk covers >= 80% of the answer's words
    none   — not found (answer lost in parsing, or in a skipped section)

"none" is itself a finding: it counts answers the parse lost.

Output (gitignored): data/gold/questions.jsonl, one line per question:
    id, question, gold_answer, paper_id, gold_chunk_ids, match
These give context recall / precision and Recall@k directly; faithfulness and
answer relevancy need no gold at all; answer correctness uses gold_answer.
"""
from __future__ import annotations

import collections
import json
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"-\s*\n\s*", "", s)          # re-join hyphenated line breaks
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def main() -> None:
    chunks = [json.loads(l) for l in open(DATA / "chunks" / "chunk_meta.jsonl")]
    by_doc = collections.defaultdict(list)
    for c in chunks:
        by_doc[c["doc_index"]].append((c["chunk_id"], norm(c["text"]), set(norm(c["text"]).split())))
    articles = json.loads((DATA / "COVID-QA.json").read_text())["data"]

    (DATA / "gold").mkdir(exist_ok=True)
    stats = collections.Counter()
    with open(DATA / "gold" / "questions.jsonl", "w") as out:
        for idx, cand in by_doc.items():
            para = articles[idx]["paragraphs"][0]
            paper_id = chunks[[c["doc_index"] for c in chunks].index(idx)]["paper_id"]
            for qa in para["qas"]:
                ans = qa["answers"][0]["text"] if qa["answers"] else ""
                a = norm(ans)
                hits = [cid for cid, txt, _ in cand if a and a in txt]
                match = "exact"
                if not hits and a:
                    words = set(a.split())
                    best = max(cand, key=lambda c: len(words & c[2]))
                    if len(words & best[2]) / max(1, len(words)) >= 0.8:
                        hits, match = [best[0]], "fuzzy"
                if not hits:
                    match = "none"
                stats[match] += 1
                out.write(json.dumps({
                    "id": qa["id"], "question": qa["question"], "gold_answer": ans,
                    "paper_id": paper_id, "gold_chunk_ids": hits, "match": match,
                }) + "\n")
    total = sum(stats.values())
    print("gold mapping:", {k: f"{v} ({v/total:.0%})" for k, v in stats.items()},
          f"· {total} questions → data/gold/questions.jsonl")


if __name__ == "__main__":
    main()
